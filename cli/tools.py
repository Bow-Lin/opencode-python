"""
CLI tools module for executing math and file operations
"""
from typing import List

import typer

from tool_registry.registry import get_tool_info, list_tools, search_tools
from tools.file_tools import create_dir, list_dir, read_file, write_file
from tools.math_tools import add, divide, multiply, subtract

app = typer.Typer()


@app.command()
def list():
    """List all available tools"""
    all_tools = list_tools()
    typer.echo(f"Available tools ({len(all_tools)}):")

    # Group tools by category
    math_tools = search_tools("math")
    file_tools = search_tools("file")

    typer.echo("  Math tools:")
    for tool in math_tools:
        info = get_tool_info(tool)
        typer.echo(f"    {tool}: {info.description}")

    typer.echo("  File tools:")
    for tool in file_tools:
        info = get_tool_info(tool)
        typer.echo(f"    {tool}: {info.description}")


@app.command()
def math(
    operation: str = typer.Argument(
        ..., help="Math operation: add, subtract, multiply, divide"
    ),
    numbers: List[float] = typer.Argument(..., help="Numbers to operate on"),
):
    """Execute math operations"""
    try:
        if operation == "add":
            result = add(*numbers)
        elif operation == "subtract":
            result = subtract(*numbers)
        elif operation == "multiply":
            result = multiply(*numbers)
        elif operation == "divide":
            result = divide(*numbers)
        else:
            typer.echo(f"Unknown operation: {operation}")
            typer.echo("Available operations: add, subtract, multiply, divide")
            raise typer.Exit(1)

        typer.echo(f"Result: {result}")

    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def read(
    file_path: str = typer.Argument(..., help="Path to file to read"),
    encoding: str = typer.Option("utf-8", "--encoding", "-e", help="File encoding"),
):
    """Read content from a file"""
    try:
        content = read_file(file_path, encoding)
        typer.echo(content)
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def write(
    file_path: str = typer.Argument(..., help="Path to file to write"),
    content: str = typer.Argument(..., help="Content to write"),
    encoding: str = typer.Option("utf-8", "--encoding", "-e", help="File encoding"),
):
    """Write content to a file"""
    try:
        result = write_file(file_path, content, encoding)
        if result:
            typer.echo(f"Successfully wrote to {file_path}")
        else:
            typer.echo("Failed to write file")
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def ls(
    dir_path: str = typer.Argument(".", help="Directory to list"),
    files_only: bool = typer.Option(
        False, "--files-only", "-f", help="List only files"
    ),
    dirs_only: bool = typer.Option(
        False, "--dirs-only", "-d", help="List only directories"
    ),
):
    """List directory contents"""
    try:
        include_files = not dirs_only
        include_dirs = not files_only

        items = list_dir(dir_path, include_files, include_dirs)
        typer.echo(f"Directory contents of {dir_path}:")
        for item in items:
            typer.echo(f"  {item}")
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def mkdir(dir_path: str = typer.Argument(..., help="Directory path to create")):
    """Create a directory"""
    try:
        result = create_dir(dir_path)
        if result:
            typer.echo(f"Successfully created directory: {dir_path}")
        else:
            typer.echo("Failed to create directory")
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
