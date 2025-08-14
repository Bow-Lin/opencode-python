from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from .tools import BaseTool, ToolInfo, ToolExecutionResponse
from .lsp_tools import get_lsp_tools


# Detailed description for the tool used in ToolInfo
diagnoseDescription = """Code diagnostics tool powered by Language Server Protocol (LSP) analysis.

WHEN TO USE THIS TOOL:
- Use when you want to analyse a specific file for potential issues
- Helpful for identifying syntax errors and warnings reported by LSP servers

HOW TO USE:
- Provide the path of the file you want to analyse

LIMITATIONS:
- Results depend on available language servers
- If no server is available for the file type, diagnostics may be empty"""


@dataclass
class DiagnoseParams:
    """Parameters for DiagnoseTool."""

    path: str


class DiagnoseTool(BaseTool):
    """Tool that provides diagnostics using LSP tools."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="diagnose",
            description=diagnoseDescription,
            parameters={
                "path": {
                    "type": "string",
                    "description": "Path to the file to analyse",
                }
            },
        )

    async def execute(self, **kwargs) -> ToolExecutionResponse:
        params = DiagnoseParams(path=kwargs.get("path", ""))
        if not params.path:
            return ToolExecutionResponse.failure("Parameter 'path' is required.")

        file_path = Path(params.path).resolve()
        if not file_path.exists() or not file_path.is_file():
            return ToolExecutionResponse.failure(f"File does not exist: {params.path}")

        try:
            lsp = get_lsp_tools()
            result = lsp.analyze_file(str(file_path))
            if "error" in result:
                return ToolExecutionResponse.failure(f"LSP analysis error: {result['error']}")

            diagnostics: List[Dict] = result.get("diagnostics", [])
            lines = [f"File: {file_path}"]
            lines.append(f"Total lines: {result.get('total_lines')}")
            lines.append(f"Code lines: {result.get('code_lines')}")
            lines.append(f"Comment lines: {result.get('comment_lines')}")

            if diagnostics:
                severity_map = {1: "Error", 2: "Warning", 3: "Information", 4: "Hint"}
                lines.append("Diagnostics:")
                for diag in diagnostics:
                    rng = diag.get("range", {}).get("start", {})
                    line = rng.get("line", 0) + 1
                    character = rng.get("character", 0) + 1
                    severity = severity_map.get(diag.get("severity", 0), "Unknown")
                    message = diag.get("message", "")
                    lines.append(
                        f"  Line {line}, Col {character} [{severity}]: {message}"
                    )
            else:
                lines.append("No diagnostics found.")

            return ToolExecutionResponse.success(
                "\n".join(lines), metadata=str(len(diagnostics))
            )
        except Exception as e:
            return ToolExecutionResponse.failure(f"Diagnose error: {e}")
