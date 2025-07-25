"""
Tool Registry - Tool management and registration system
"""
import inspect
from typing import Callable, List, Optional

from .registry import (
    ToolInfo,
    ToolRegistry,
    get_tool,
    get_tool_func,
    get_tool_info,
    list_tools,
    list_tools_with_info,
    register_tool,
    registry,
    search_tools,
)


def tool(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    version: str = "1.0.0",
    author: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Callable:
    """
    Decorator to register a function as a tool with automatic metadata
    extraction

    Args:
        func: Function to register (for decorator usage)
        name: Custom name for the tool (defaults to function name)
        description: Tool description (defaults to function docstring)
        tags: List of tags for categorization
        version: Tool version
        author: Tool author
        created_at: Creation timestamp

    Returns:
        The original function
    """

    def decorator(f: Callable) -> Callable:
        # Extract function metadata
        tool_name = name or f.__name__

        # Use function docstring as default description
        if description is None and f.__doc__:
            # Extract first line of docstring as description
            doc_lines = f.__doc__.strip().split("\n")
            auto_description = doc_lines[0].strip()
        else:
            auto_description = description

        # Extract parameter information using inspect
        sig = inspect.signature(f)
        param_info = {
            "parameters": list(sig.parameters.keys()),
            "signature": str(sig),
            "return_annotation": sig.return_annotation,
        }

        # Register the tool with extracted metadata
        register_tool(
            func=f,
            name=tool_name,
            description=auto_description,
            tags=tags,
            version=version,
            author=author,
            created_at=created_at,
            parameters=param_info["parameters"],
            signature=param_info["signature"],
            return_annotation=str(param_info["return_annotation"]),
        )

        return f

    # Handle both decorator and function call cases
    if func is None:
        return decorator
    else:
        return decorator(func)


__all__ = [
    "tool",
    "register_tool",
    "get_tool",
    "get_tool_func",
    "get_tool_info",
    "list_tools",
    "list_tools_with_info",
    "search_tools",
    "ToolRegistry",
    "ToolInfo",
    "registry",
]
