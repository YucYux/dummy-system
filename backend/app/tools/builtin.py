"""
Built-in tools for the Agent.
Add your custom tools here following the same pattern.
"""

import datetime
import math
from app.tools.registry import ToolRegistry
from app.services.rag_service import get_rag_service
from app.models.doc_library import get_embedding_status
from app.models.model_config import is_embedding_configured


def register_builtin_tools(registry: ToolRegistry):
    """Register all built-in tools to the registry."""
    
    # Tool 1: Calculator - Add two numbers
    registry.register(
        name="add",
        description="Add two numbers together. Use this when you need to perform addition.",
        parameters={
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "The first number"
                },
                "b": {
                    "type": "number",
                    "description": "The second number"
                }
            },
            "required": ["a", "b"]
        },
        handler=tool_add
    )
    
    # Tool 2: Calculator - Multiply two numbers
    registry.register(
        name="multiply",
        description="Multiply two numbers together. Use this when you need to perform multiplication.",
        parameters={
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "The first number"
                },
                "b": {
                    "type": "number",
                    "description": "The second number"
                }
            },
            "required": ["a", "b"]
        },
        handler=tool_multiply
    )
    
    # Tool 3: Get current time
    registry.register(
        name="get_current_time",
        description="Get the current date and time. Use this when you need to know what time it is.",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone name (e.g., 'UTC', 'Asia/Shanghai'). Defaults to local time.",
                    "default": "local"
                }
            },
            "required": []
        },
        handler=tool_get_current_time
    )
    
    # Tool 4: Calculate expression
    registry.register(
        name="calculate",
        description="Evaluate a mathematical expression. Supports basic operations (+, -, *, /, **) and common math functions (sqrt, sin, cos, tan, log, etc.).",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', 'sin(3.14159/2)')"
                }
            },
            "required": ["expression"]
        },
        handler=tool_calculate
    )
    
    # Tool 5: String utilities
    registry.register(
        name="string_utils",
        description="Perform various string operations: length, reverse, uppercase, lowercase, word_count.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to process"
                },
                "operation": {
                    "type": "string",
                    "enum": ["length", "reverse", "uppercase", "lowercase", "word_count"],
                    "description": "The operation to perform"
                }
            },
            "required": ["text", "operation"]
        },
        handler=tool_string_utils
    )
    
    # Tool 6: RAG - Search document libraries
    registry.register(
        name="search_documents",
        description="Search the user's document libraries for relevant information. Use this when you need to find information from documents that the user has uploaded. The search will look through all document libraries that the user has selected for this conversation.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query describing what information you're looking for"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of relevant chunks to retrieve (default: 5, max: 20)",
                    "default": 5
                }
            },
            "required": ["query"]
        },
        handler=tool_search_documents,
        requires_context=True
    )


# Tool implementations

def tool_add(a: float, b: float) -> dict:
    """Add two numbers."""
    result = a + b
    return {
        "result": result,
        "expression": f"{a} + {b} = {result}"
    }


def tool_multiply(a: float, b: float) -> dict:
    """Multiply two numbers."""
    result = a * b
    return {
        "result": result,
        "expression": f"{a} × {b} = {result}"
    }


def tool_get_current_time(timezone: str = "local") -> dict:
    """Get current time."""
    now = datetime.datetime.now()
    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "timezone": timezone
    }


def tool_calculate(expression: str) -> dict:
    """Evaluate a mathematical expression safely."""
    # Define allowed names for safe evaluation
    allowed_names = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "floor": math.floor,
        "ceil": math.ceil,
    }
    
    try:
        # Remove any potentially dangerous characters
        safe_expr = expression.replace("__", "")
        
        # Evaluate expression with only allowed names
        result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
        
        return {
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e)
        }


def tool_string_utils(text: str, operation: str) -> dict:
    """Perform string operations."""
    operations = {
        "length": lambda t: {"length": len(t)},
        "reverse": lambda t: {"reversed": t[::-1]},
        "uppercase": lambda t: {"uppercase": t.upper()},
        "lowercase": lambda t: {"lowercase": t.lower()},
        "word_count": lambda t: {"word_count": len(t.split())}
    }
    
    if operation not in operations:
        return {"error": f"Unknown operation: {operation}"}
    
    result = operations[operation](text)
    result["original"] = text
    result["operation"] = operation
    return result


def tool_search_documents(context: dict, query: str, top_k: int = 5) -> dict:
    """Search user's document libraries for relevant information."""
    user_id = context.get('user_id')
    library_ids = context.get('library_ids', [])
    
    if not user_id:
        return {"error": "User context not available"}
    
    if not library_ids:
        return {
            "error": "No document libraries selected for this conversation",
            "hint": "Please select document libraries to search in the conversation settings"
        }
    
    if not is_embedding_configured():
        return {"error": "Embedding model not configured. Please contact administrator."}
    
    status = get_embedding_status(user_id)
    if status.get('is_embedding'):
        return {"error": "Documents are being processed. Please try again later."}
    
    top_k = min(max(1, top_k), 20)
    
    try:
        rag_service = get_rag_service()
        results = rag_service.search(user_id, library_ids, query, top_k)
        
        if not results:
            return {
                "query": query,
                "results": [],
                "message": "No relevant documents found"
            }
        
        formatted_results = []
        for i, r in enumerate(results):
            formatted_results.append({
                "rank": i + 1,
                "content": r['content'],
                "source": r['source'],
                "relevance_score": round(r['score'], 4)
            })
        
        return {
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
        
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}
