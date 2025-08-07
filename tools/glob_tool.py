import os
from pathlib import Path
from typing import Optional
from tools import BaseTool, ToolInfo, ToolExecutionResponse


globDescription = """Fast file pattern matching tool that finds files by name and pattern, returning matching paths sorted by modification time (newest first).

WHEN TO USE THIS TOOL:
- Use when you need to find files by name patterns or extensions
- Great for finding specific file types across a directory structure
- Useful for discovering files that match certain naming conventions

HOW TO USE:
- Provide a glob pattern to match against file paths
- Optionally specify a starting directory (defaults to current working directory)
- Results are sorted with most recently modified files first

GLOB PATTERN SYNTAX:
- '*' matches any sequence of non-separator characters
- '**' matches any sequence of characters, including separators
- '?' matches any single non-separator character
- '[...]' matches any character in the brackets
- '[!...]' matches any character not in the brackets

COMMON PATTERN EXAMPLES:
- '*.js' - Find all JavaScript files in the current directory
- '**/*.js' - Find all JavaScript files in any subdirectory
- 'src/**/*.{ts,tsx}' - Find all TypeScript files in the src directory
- '*.{html,css,js}' - Find all HTML, CSS, and JS files

LIMITATIONS:
- Results are limited to 100 files (newest first)
- Does not search file contents (use Grep tool for that)
- Hidden files (starting with '.') are skipped

TIPS:
- For the most useful results, combine with the Grep tool: first find files with Glob, then search their contents with Grep
- When doing iterative exploration that may require multiple rounds of searching, consider using the Agent tool instead
- Always check if results are truncated and refine your search pattern if needed"""

class GlobTool(BaseTool):
    MAX_RESULTS = 100

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="glob",
            description=globDescription,
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "The glob pattern to match files (e.g., **/*.py)"
                },
                "path": {
                    "type": "string",
                    "description": "The directory to start search from. Defaults to current directory."
                }
            },
        )

    async def execute(self, pattern: Optional[str] = None, path: Optional[str] = None) -> ToolExecutionResponse:

        if not pattern:
            return ToolExecutionResponse.failure("Parameter 'pattern' is required.")

        if not path:
            path = os.getcwd()

        try:
            base = Path(path).resolve()
            if not base.exists():
                return ToolExecutionResponse.failure(f"Path not found: {base}")
            if not base.is_dir():
                return ToolExecutionResponse.failure(f"Path is not a directory: {base}")

            # 执行 glob 模式查找
            files = [
                f for f in base.glob(pattern)
                if f.is_file() and not f.name.startswith(".")
            ]

            # 按修改时间排序
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            truncated = False
            if len(files) > self.MAX_RESULTS:
                files = files[:self.MAX_RESULTS]
                truncated = True

            output = "\n".join(str(f) for f in files) or "No files found"
            if truncated:
                output += f"\n\n(Result truncated to {self.MAX_RESULTS} files.)"

            return ToolExecutionResponse.success(output, metadata=str(len(files)))

        except Exception as e:
            return ToolExecutionResponse.failure(f"Glob pattern error: {e}")
