"""
Tool Registry - Core registration logic for managing tools
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class ToolInfo:
    """Tool information structure"""

    name: str
    func: Callable
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: Optional[str] = None
    created_at: Optional[str] = None
    parameters: Optional[List[str]] = None
    signature: Optional[str] = None
    return_annotation: Optional[str] = None

    def __post_init__(self):
        """Set default description from function docstring if not provided"""
        if self.description is None and self.func.__doc__:
            self.description = self.func.__doc__.strip().split("\n")[0]


class ToolRegistry:
    """Tool registry for managing and organizing tools"""

    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}

    def register_tool(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        version: str = "1.0.0",
        author: Optional[str] = None,
        created_at: Optional[str] = None,
        parameters: Optional[List[str]] = None,
        signature: Optional[str] = None,
        return_annotation: Optional[str] = None,
    ) -> Callable:
        """
        Register a function as a tool with metadata

        Args:
            func: Function to register as a tool (for decorator usage)
            name: Custom name for the tool (defaults to function name)
            description: Tool description
            tags: List of tags for categorization
            version: Tool version
            author: Tool author
            created_at: Creation timestamp

        Returns:
            The original function (for decorator usage)
        """

        def decorator(f: Callable) -> Callable:
            tool_name = name or f.__name__

            tool_info = ToolInfo(
                name=tool_name,
                func=f,
                description=description,
                tags=tags or [],
                version=version,
                author=author,
                created_at=created_at,
                parameters=parameters,
                signature=signature,
                return_annotation=return_annotation,
            )

            self._tools[tool_name] = tool_info
            return f

        # Handle both decorator and function call cases
        if func is None:
            return decorator
        else:
            return decorator(func)

    # TODO: add cache to optimize the performance
    def get_tool(self, name: str) -> Optional[Callable]:
        """
        Get a tool function by name (backward compatibility)

        Args:
            name: Name of the tool to retrieve

        Returns:
            The tool function if found, None otherwise
        """
        tool_info = self._tools.get(name)
        return tool_info.func if tool_info else None

    def get_tool_func(self, name: str) -> Optional[Callable]:
        """
        Get a tool function by name (explicit method)

        Args:
            name: Name of the tool to retrieve

        Returns:
            The tool function if found, None otherwise
        """
        return self.get_tool(name)

    def get_tool_info(self, name: str) -> Optional[ToolInfo]:
        """
        Get tool information by name

        Args:
            name: Name of the tool

        Returns:
            ToolInfo object if found, None otherwise
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def list_tools_with_info(self) -> List[ToolInfo]:
        """
        List all registered tools with their information

        Returns:
            List of ToolInfo objects
        """
        return list(self._tools.values())

    def search_tools(self, tag: str) -> List[str]:
        """
        Search tools by tag

        Args:
            tag: Tag to search for

        Returns:
            List of tool names that have the specified tag
        """
        return [
            name for name, tool_info in self._tools.items() if tag in tool_info.tags
        ]


# Global registry instance
registry = ToolRegistry()


def register_tool(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    version: str = "1.0.0",
    author: Optional[str] = None,
    created_at: Optional[str] = None,
    parameters: Optional[List[str]] = None,
    signature: Optional[str] = None,
    return_annotation: Optional[str] = None,
) -> Callable:
    """
    Decorator to register a function as a tool with metadata

    Args:
        func: Function to register (for decorator usage)
        name: Custom name for the tool
        description: Tool description
        tags: List of tags for categorization
        version: Tool version
        author: Tool author
        created_at: Creation timestamp

    Returns:
        The original function
    """
    return registry.register_tool(
        func=func,
        name=name,
        description=description,
        tags=tags,
        version=version,
        author=author,
        created_at=created_at,
        parameters=parameters,
        signature=signature,
        return_annotation=return_annotation,
    )


def get_tool(name: str) -> Optional[Callable]:
    """
    Get a tool by name (backward compatibility)

    Args:
        name: Name of the tool to retrieve

    Returns:
        The tool function if found, None otherwise
    """
    return registry.get_tool(name)


def get_tool_func(name: str) -> Optional[Callable]:
    """
    Get a tool function by name (explicit method)

    Args:
        name: Name of the tool to retrieve

    Returns:
        The tool function if found, None otherwise
    """
    return registry.get_tool_func(name)


def get_tool_info(name: str) -> Optional[ToolInfo]:
    """
    Get tool information by name

    Args:
        name: Name of the tool

    Returns:
        ToolInfo object if found, None otherwise
    """
    return registry.get_tool_info(name)


def list_tools() -> List[str]:
    """
    List all registered tool names

    Returns:
        List of tool names
    """
    return registry.list_tools()


def list_tools_with_info() -> List[ToolInfo]:
    """
    List all registered tools with their information

    Returns:
        List of ToolInfo objects
    """
    return registry.list_tools_with_info()


def search_tools(tag: str) -> List[str]:
    """
    Search tools by tag

    Args:
        tag: Tag to search for

    Returns:
        List of tool names that have the specified tag
    """
    return registry.search_tools(tag)
