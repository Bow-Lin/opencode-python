import os
import re
from pathlib import Path
from typing import Optional, List
from .tools import BaseTool, ToolInfo, ToolExecutionResponse


grepDescription = """Fast content search tool that finds files containing specific text or patterns, returning matching file paths sorted by modification time (newest first).

WHEN TO USE THIS TOOL:
- Use when you need to find files containing specific text or patterns
- Great for searching code bases for function names, variable declarations, or error messages
- Useful for finding all files that use a particular API or pattern

HOW TO USE:
- Provide a regex pattern to search for within file contents
- Set literal_text=true if you want to search for the exact text with special characters (recommended for non-regex users)
- Optionally specify a starting directory (defaults to current working directory)
- Optionally provide an include pattern to filter which files to search
- Results are sorted with most recently modified files first

REGEX PATTERN SYNTAX (when literal_text=false):
- Supports standard regular expression syntax
- 'function' searches for the literal text "function"
- 'log\..*Error' finds text starting with "log." and ending with "Error"
- 'import\s+.*\s+from' finds import statements in JavaScript/TypeScript

COMMON INCLUDE PATTERN EXAMPLES:
- '*.js' - Only search JavaScript files
- '*.{ts,tsx}' - Only search TypeScript files
- '*.go' - Only search Go files

LIMITATIONS:
- Results are limited to 100 files (newest first)
- Performance depends on the number of files being searched
- Very large binary files may be skipped
- Hidden files (starting with '.') are skipped

TIPS:
- For faster, more targeted searches, first use Glob to find relevant files, then use Grep
- When doing iterative exploration that may require multiple rounds of searching, consider using the Agent tool instead
- Always check if results are truncated and refine your search pattern if needed
- Use literal_text=true when searching for exact text containing special characters like dots, parentheses, etc."""

class GrepTool(BaseTool):
    MAX_RESULTS = 100

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="grep",
            description=grepDescription,
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern or literal text to search for"
                },
                "path": {
                    "type": "string",
                    "description": "Search root path (default: current directory)"
                },
                "include": {
                    "type": "string",
                    "description": "Glob-style file pattern filter (e.g., *.py or *.{js,ts})"
                },
                "literal_text": {
                    "type": "boolean",
                    "description": "Treat pattern as literal text if true"
                }
            }
        )

    async def execute(
        self,
        pattern: Optional[str] = None,
        path: Optional[str] = None,
        include: Optional[str] = None,
        literal_text: Optional[bool] = False
    ) -> ToolExecutionResponse:
        if not pattern:
            return ToolExecutionResponse.failure("Parameter 'pattern' is required.")

        try:
            root = Path(path or os.getcwd()).resolve()
            if not root.exists() or not root.is_dir():
                return ToolExecutionResponse.failure(f"Invalid directory: {root}")

            # 构建正则模式
            if literal_text:
                pattern = re.escape(pattern)
            try:
                regex = re.compile(pattern)
            except Exception as e:
                return ToolExecutionResponse.failure(f"Invalid regex pattern: {e}")

            matches = self._search_files(root, regex, include)
            matches.sort(key=lambda m: m["mod_time"], reverse=True)

            truncated = len(matches) > self.MAX_RESULTS
            if truncated:
                matches = matches[:self.MAX_RESULTS]

            output = self._format_output(matches)
            if truncated:
                output += f"\n(Result truncated to {self.MAX_RESULTS} files.)"

            return ToolExecutionResponse.success(output, metadata=str(len(matches)))

        except Exception as e:
            return ToolExecutionResponse.failure(f"Grep error: {e}")

    def _search_files(self, root: Path, regex: re.Pattern, include: Optional[str]) -> List[dict]:
        results = []
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                if fname.startswith("."):
                    continue
                file_path = Path(dirpath) / fname

                if include and not self._match_include(fname, include):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, start=1):
                            if regex.search(line):
                                results.append({
                                    "file": str(file_path),
                                    "mod_time": file_path.stat().st_mtime,
                                    "line_num": lineno,
                                    "line": line.rstrip()
                                })
                                break  # 每个文件只收录一次
                except Exception:
                    continue  # 跳过无法读取的文件
        return results

    def _match_include(self, filename: str, pattern: str) -> bool:
        import fnmatch
        # 支持 *.{js,ts} 多扩展名语法
        if "{" in pattern and "}" in pattern:
            ext_group = pattern[pattern.find("{")+1 : pattern.find("}")]
            for ext in ext_group.split(","):
                sub_pattern = pattern.replace("{" + ext_group + "}", ext)
                if fnmatch.fnmatch(filename, sub_pattern):
                    return True
            return False
        else:
            return fnmatch.fnmatch(filename, pattern)

    def _format_output(self, matches: List[dict]) -> str:
        if not matches:
            return "No matches found."

        output = []
        current_file = ""
        for match in matches:
            if match["file"] != current_file:
                output.append(f"{match['file']}:")
                current_file = match["file"]
            output.append(f"  Line {match['line_num']}: {match['line']}")
        return "\n".join(output)
