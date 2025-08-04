"""
LSP utility functions.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from .protocol import Position, Range


def uri_to_path(uri: str) -> str:
    """Convert URI to file path."""
    if uri.startswith("file://"):
        return urlparse(uri).path
    return uri


def path_to_uri(path: str) -> str:
    """Convert file path to URI."""
    if path.startswith("file://"):
        return path
    return f"file://{os.path.abspath(path)}"


def get_word_at_position(text: str, position: Position) -> Tuple[str, Range]:
    """Get the word at the given position in the text."""
    lines = text.split("\n")
    if position.line >= len(lines):
        return "", Range(start=position, end=position)

    line = lines[position.line]
    if position.character >= len(line):
        return "", Range(start=position, end=position)

    # Find word boundaries
    word_start = position.character
    while word_start > 0 and (
        line[word_start - 1].isalnum() or line[word_start - 1] == "_"
    ):
        word_start -= 1

    word_end = position.character
    while word_end < len(line) and (line[word_end].isalnum() or line[word_end] == "_"):
        word_end += 1

    word = line[word_start:word_end]
    word_range = Range(
        start=Position(line=position.line, character=word_start),
        end=Position(line=position.line, character=word_end),
    )

    return word, word_range


def get_line_at_position(text: str, position: Position) -> str:
    """Get the line at the given position."""
    lines = text.split("\n")
    if position.line >= len(lines):
        return ""
    return lines[position.line]


def get_indentation_level(line: str) -> int:
    """Get the indentation level of a line."""
    return len(line) - len(line.lstrip())


def is_inside_string(text: str, position: Position) -> bool:
    """Check if the position is inside a string literal."""
    lines = text.split("\n")
    if position.line >= len(lines):
        return False

    line = lines[position.line]
    if position.character >= len(line):
        return False

    # Simple check for string literals
    before_cursor = line[: position.character]

    # Count quotes
    single_quotes = before_cursor.count("'") - before_cursor.count("\\'")
    double_quotes = before_cursor.count('"') - before_cursor.count('\\"')

    # Check if we're inside a string
    if single_quotes % 2 == 1 or double_quotes % 2 == 1:
        return True

    return False


def is_inside_comment(text: str, position: Position) -> bool:
    """Check if the position is inside a comment."""
    lines = text.split("\n")
    if position.line >= len(lines):
        return False

    line = lines[position.line]
    if position.character >= len(line):
        return False

    # Check for line comment
    comment_pos = line.find("#")
    if comment_pos != -1 and position.character > comment_pos:
        return True

    return False


def get_python_imports(content: str) -> List[str]:
    """Extract Python import statements from content."""
    imports = []
    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith(("import ", "from ")):
            imports.append(line)

    return imports


def get_python_functions(content: str) -> List[Tuple[str, int]]:
    """Extract Python function definitions from content."""
    functions = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("def "):
            # Extract function name
            match = re.match(r"def\s+(\w+)", line)
            if match:
                functions.append((match.group(1), i + 1))

    return functions


def get_python_classes(content: str) -> List[Tuple[str, int]]:
    """Extract Python class definitions from content."""
    classes = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("class "):
            # Extract class name
            match = re.match(r"class\s+(\w+)", line)
            if match:
                classes.append((match.group(1), i + 1))

    return classes


def format_diagnostic_message(diagnostic: str, severity: str = "error") -> str:
    """Format diagnostic message for display."""
    severity_icons = {"error": "❌", "warning": "⚠️", "info": "ℹ️", "hint": "💡"}

    icon = severity_icons.get(severity, "❓")
    return f"{icon} {diagnostic}"


def validate_python_syntax(content: str) -> List[Tuple[str, int, int]]:
    """Validate Python syntax and return errors with line numbers."""
    import ast

    errors = []
    try:
        ast.parse(content)
    except SyntaxError as e:
        line = e.lineno if e.lineno else 1
        column = e.offset if e.offset else 0
        errors.append((str(e), line, column))
    except Exception as e:
        errors.append((str(e), 1, 0))

    return errors


def get_file_extension(file_path: str) -> str:
    """Get file extension from file path."""
    return Path(file_path).suffix.lower()


def is_python_file(file_path: str) -> bool:
    """Check if the file is a Python file."""
    return get_file_extension(file_path) == ".py"


def normalize_path(path: str) -> str:
    """Normalize file path."""
    return os.path.normpath(os.path.abspath(path))


def get_relative_path(base_path: str, target_path: str) -> str:
    """Get relative path from base path to target path."""
    try:
        return os.path.relpath(target_path, base_path)
    except ValueError:
        return target_path
