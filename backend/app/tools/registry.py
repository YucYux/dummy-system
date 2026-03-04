"""
Tool registry for managing and executing tools.
"""

from typing import Callable, Dict, Any, List


class ToolRegistry:
    """Registry for managing tools that can be called by the LLM."""
    
    def __init__(self):
        self._tools: Dict[str, dict] = {}
    
    def register(self, name: str, description: str, parameters: dict, handler: Callable):
        """
        Register a new tool.
        
        Args:
            name: Unique name for the tool
            description: Description of what the tool does
            parameters: JSON Schema for the tool's parameters
            handler: Function to execute when tool is called
        """
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def get_tools_schema(self) -> List[dict]:
        """Get tools in OpenAI function calling format."""
        tools = []
        for tool in self._tools.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return tools
    
    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())
    
    def get_tool(self, name: str) -> dict:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def execute(self, name: str, arguments: dict) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            
        Returns:
            Result from the tool execution
        """
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}
        
        try:
            result = tool["handler"](**arguments)
            return result
        except Exception as e:
            return {"error": str(e)}
