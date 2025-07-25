"""
File tools module providing basic file and directory operations
"""
import os
from typing import List

from tool_registry.registry import register_tool


@register_tool(
    name="read_file",
    description="Read content from a file",
    tags=["file", "io", "read"],
    version="1.0.0",
    author="OpenCode",
    parameters=[
        "file_path: Path to the file to read",
        "encoding: File encoding (default: utf-8)",
    ],
    return_annotation="str",
)
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Read content from a file

    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: utf-8)

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file cannot be read
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")


@register_tool(
    name="write_file",
    description="Write content to a file",
    tags=["file", "io", "write"],
    version="1.0.0",
    author="OpenCode",
    parameters=[
        "file_path: Path to the file to write",
        "content: Content to write",
        "encoding: File encoding (default: utf-8)",
    ],
    return_annotation="bool",
)
def write_file(file_path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    Write content to a file

    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        encoding: File encoding (default: utf-8)

    Returns:
        True if successful

    Raises:
        PermissionError: If file cannot be written
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")


@register_tool(
    name="list_dir",
    description="List contents of a directory",
    tags=["file", "directory", "list"],
    version="1.0.0",
    author="OpenCode",
    parameters=[
        "dir_path: Path to the directory to list",
        "include_files: Include files (default: True)",
        "include_dirs: Include directories (default: True)",
    ],
    return_annotation="List[str]",
)
def list_dir(
    dir_path: str = ".", include_files: bool = True, include_dirs: bool = True
) -> List[str]:
    """
    List contents of a directory

    Args:
        dir_path: Path to the directory to list (default: current directory)
        include_files: Whether to include files in the result
        include_dirs: Whether to include directories in the result

    Returns:
        List of file and directory names

    Raises:
        FileNotFoundError: If directory doesn't exist
        PermissionError: If directory cannot be accessed
    """
    try:
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not os.path.isdir(dir_path):
            raise FileNotFoundError(f"Path is not a directory: {dir_path}")

        items = []
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isfile(item_path) and include_files:
                items.append(item)
            elif os.path.isdir(item_path) and include_dirs:
                items.append(item)

        return sorted(items)
    except PermissionError:
        raise PermissionError(f"Permission denied: {dir_path}")


@register_tool(
    name="create_dir",
    description="Create a directory",
    tags=["file", "directory", "create"],
    version="1.0.0",
    author="OpenCode",
    parameters=[
        "dir_path: Path to the directory to create",
        "parents: Create parent directories if needed (default: True)",
    ],
    return_annotation="bool",
)
def create_dir(dir_path: str, parents: bool = True) -> bool:
    """
    Create a directory

    Args:
        dir_path: Path to the directory to create
        parents: Create parent directories if needed

    Returns:
        True if successful

    Raises:
        PermissionError: If directory cannot be created
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except PermissionError:
        raise PermissionError(f"Permission denied: {dir_path}")
