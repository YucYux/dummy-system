"""
Tool system for the Agent.
Tools are functions that can be called by the LLM.
"""

from app.tools.registry import ToolRegistry
from app.tools.builtin import register_builtin_tools

# Global tool registry
tool_registry = ToolRegistry()

# Register built-in tools
register_builtin_tools(tool_registry)


def get_tools_for_llm():
    """Get tools in OpenAI function calling format."""
    return tool_registry.get_tools_schema()


def execute_tool(tool_name: str, arguments: dict):
    """Execute a tool by name with given arguments."""
    return tool_registry.execute(tool_name, arguments)


def get_tool_names():
    """Get list of all available tool names."""
    return tool_registry.get_tool_names()
