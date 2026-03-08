"""
LLM service for handling model calls with streaming and tool support.
"""

import json
from app.models.model_config import get_model_by_id, get_default_model
from app.tools import get_tools_for_llm, execute_tool
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


SYSTEM_PROMPT = """You are a helpful AI assistant with access to various tools. 
When you need to perform calculations, get information, or complete tasks, use the available tools.
Always be helpful, accurate, and concise in your responses.
If you use a tool, explain what you're doing and share the results with the user."""
REASONING_NOTE = """This model is configured as a reasoning model. When the reasoning effort is {effort}, allow extra internal evaluation before answering, and prioritize clarity."""


def merge_reasoning_into_content(reasoning: str, content: str) -> str:
    """
    Merge reasoning into content for MiniMax Interleaved Chain-of-Thought.
    Format: <think>\n{reasoning}\n</think>\n{content}
    """
    if reasoning:
        return f"<think>\n{reasoning}\n</think>\n{content or ''}"
    return content


class LLMService:
    """Service for interacting with LLM APIs."""
    
    def __init__(self, model_id: str = None):
        """Initialize with a specific model or default."""
        from openai import OpenAI
        
        if model_id:
            self.model_config = get_model_by_id(model_id)
        else:
            self.model_config = get_default_model()
        
        if not self.model_config:
            raise ValueError("No model configuration available")
        
        self.client = OpenAI(
            api_key=self.model_config['api_key'],
            base_url=self.model_config['api_url']
        )
    
    def chat_stream(self, messages: list, use_tools: bool = True, reasoning_effort: str = None):
        """
        Stream chat completion with tool support.
        
        Yields events:
        - {"type": "content", "content": "..."}  - Text content
        - {"type": "reasoning", "content": "..."}  - Reasoning content (for MiniMax etc.)
        - {"type": "tool_call_start", "tool": "...", "id": "..."}  - Tool call starting
        - {"type": "tool_call_args", "args": "..."}  - Tool arguments (streaming)
        - {"type": "tool_call_end", "result": {...}}  - Tool call result
        - {"type": "done", "finish_reason": "...", "reasoning": "..."}  - Stream complete
        - {"type": "error", "message": "..."}  - Error occurred
        """
        
        try:
            # Prepare messages with system prompt
            effort = reasoning_effort or "auto"
            prompt = SYSTEM_PROMPT
            if self.model_config.get("is_reasoning", False):
                prompt = f"{SYSTEM_PROMPT}\n\n{REASONING_NOTE.format(effort=effort)}"
            full_messages = [{"role": "system", "content": prompt}] + messages
            
            # Prepare request parameters
            request_params = {
                "model": self.model_config['model_id'],
                "messages": full_messages,
                "stream": True,
                "max_tokens": config.DEFAULT_MAX_TOKENS,
                "temperature": config.DEFAULT_TEMPERATURE
            }
            
            # Add tools if enabled
            if use_tools:
                tools = get_tools_for_llm()
                if tools:
                    request_params["tools"] = tools
                    request_params["tool_choice"] = "auto"
            
            # Make streaming request
            response = self.client.chat.completions.create(**request_params)
            
            collected_content = ""
            collected_reasoning = ""
            tool_calls = {}
            use_interleaved_cot = (
                self.model_config.get("minimax_interleaved_cot", False)
                and self.model_config.get("is_reasoning", False)
            )
            
            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                
                if not delta:
                    continue
                
                # Handle text content
                if delta.content:
                    collected_content += delta.content
                    yield {"type": "content", "content": delta.content}
                
                # Handle reasoning content (only when MiniMax Interleaved CoT is enabled)
                if use_interleaved_cot and hasattr(delta, 'reasoning') and delta.reasoning:
                    collected_reasoning += delta.reasoning
                    yield {"type": "reasoning", "content": delta.reasoning}
                
                # Handle tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        tc_id = tc.id or list(tool_calls.keys())[-1] if tool_calls else None
                        
                        if tc.id:
                            # New tool call starting
                            tool_calls[tc.id] = {
                                "id": tc.id,
                                "name": tc.function.name if tc.function else "",
                                "arguments": ""
                            }
                            yield {
                                "type": "tool_call_start",
                                "id": tc.id,
                                "tool": tc.function.name if tc.function else ""
                            }
                        
                        if tc.function and tc.function.arguments:
                            # Streaming arguments
                            if tc_id and tc_id in tool_calls:
                                tool_calls[tc_id]["arguments"] += tc.function.arguments
                                yield {
                                    "type": "tool_call_args",
                                    "id": tc_id,
                                    "args": tc.function.arguments
                                }
                
                # Check finish reason
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason
                    
                    # Try to get reasoning from the chunk (only when Interleaved CoT is enabled)
                    if use_interleaved_cot and hasattr(chunk, 'choices') and chunk.choices:
                        choice = chunk.choices[0]
                        chunk_reasoning = None
                        if hasattr(choice, 'message') and choice.message and hasattr(choice.message, 'reasoning'):
                            chunk_reasoning = choice.message.reasoning
                        elif hasattr(choice, 'delta') and choice.delta and hasattr(choice.delta, 'reasoning') and choice.delta.reasoning:
                            chunk_reasoning = choice.delta.reasoning
                        if chunk_reasoning:
                            collected_reasoning += chunk_reasoning
                    
                    if finish_reason == "tool_calls":
                        # Execute tool calls
                        for tc_id, tc_data in tool_calls.items():
                            try:
                                args = json.loads(tc_data["arguments"])
                                result = execute_tool(tc_data["name"], args)
                                yield {
                                    "type": "tool_call_end",
                                    "id": tc_id,
                                    "tool": tc_data["name"],
                                    "arguments": args,
                                    "result": result
                                }
                            except json.JSONDecodeError as e:
                                yield {
                                    "type": "tool_call_end",
                                    "id": tc_id,
                                    "tool": tc_data["name"],
                                    "error": f"Invalid arguments: {str(e)}"
                                }
                    
                    # Include reasoning in the done event when Interleaved CoT is enabled
                    yield {
                        "type": "done",
                        "finish_reason": finish_reason,
                        "reasoning": (collected_reasoning if collected_reasoning else None) if use_interleaved_cot else None
                    }
        
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    def chat_with_tools(self, messages: list, max_iterations: int = 10, reasoning_effort: str = None):
        """
        Complete chat with automatic tool execution loop.
        
        This handles the full conversation including tool calls and their responses.
        For reasoning models (like MiniMax), it preserves reasoning history to improve
        Agent task success rates.
        
        Yields events throughout the process.
        """
        current_messages = messages.copy()
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            tool_calls_made = []
            assistant_content = ""
            assistant_reasoning = ""
            
            # Stream response
            for event in self.chat_stream(current_messages, reasoning_effort=reasoning_effort):
                yield event
                
                if event["type"] == "content":
                    assistant_content += event["content"]
                
                elif event["type"] == "reasoning":
                    assistant_reasoning += event["content"]
                
                elif event["type"] == "tool_call_end":
                    tool_calls_made.append(event)
                
                elif event["type"] == "done":
                    # Capture any reasoning from the done event
                    if event.get("reasoning"):
                        assistant_reasoning = event["reasoning"]
                    
                    if event["finish_reason"] != "tool_calls":
                        # No more tool calls, we're done
                        return
            
            # If tool calls were made, add them to messages and continue
            if tool_calls_made:
                # When MiniMax Interleaved CoT is enabled, merge reasoning into content
                use_interleaved_cot = (
                    self.model_config.get("minimax_interleaved_cot", False)
                    and self.model_config.get("is_reasoning", False)
                )
                merged_content = merge_reasoning_into_content(assistant_reasoning, assistant_content) if use_interleaved_cot else assistant_content
                
                # Add assistant message with tool calls (using merged content)
                assistant_msg = {
                    "role": "assistant",
                    "content": merged_content if merged_content else None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["tool"],
                                "arguments": json.dumps(tc["arguments"])
                            }
                        }
                        for tc in tool_calls_made
                    ]
                }
                current_messages.append(assistant_msg)
                
                # Add tool results
                for tc in tool_calls_made:
                    result_content = json.dumps(tc.get("result", tc.get("error", "Unknown error")))
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_content
                    })
            else:
                # No tool calls, we're done
                return