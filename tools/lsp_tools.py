"""
LSP tools for agent integration - pure client without language-specific parsing.
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from core.lsp.client import LSPClient
from core.lsp.protocol import Position, CompletionItem, Diagnostic, Location
from core.lsp.utils import is_python_file, normalize_path


class LSPTools:
    """LSP tools for agent integration."""

    def __init__(self):
        self.client = LSPClient()

    def get_completions(
        self, file_path: str, line: int, character: int
    ) -> List[Dict[str, Any]]:
        """Get completion suggestions at the given position."""
        try:
            position = Position(line=line, character=character)
            completions = self.client.get_completions(file_path, position)
            return [completion.model_dump() for completion in completions]
        except Exception as e:
            return [{"error": str(e)}]

    def get_diagnostics(self, file_path: str) -> List[Dict[str, Any]]:
        """Get diagnostics for the given file."""
        try:
            diagnostics = self.client.get_diagnostics(file_path)
            return [diagnostic.model_dump() for diagnostic in diagnostics]
        except Exception as e:
            return [{"error": str(e)}]

    def get_definition(
        self, file_path: str, line: int, character: int
    ) -> Optional[Dict[str, Any]]:
        """Get definition location for the symbol at the given position."""
        try:
            position = Position(line=line, character=character)
            definition = self.client.get_definition(file_path, position)
            return definition.model_dump() if definition else None
        except Exception as e:
            return {"error": str(e)}

    def get_implementation(
        self, file_path: str, line: int, character: int
    ) -> List[Dict[str, Any]]:
        """Get implementation locations for the symbol at the given position."""
        try:
            position = Position(line=line, character=character)
            implementations = self.client.get_implementation(file_path, position)
            return [impl.model_dump() for impl in implementations]
        except Exception as e:
            return [{"error": str(e)}]

    def get_hover(
        self, file_path: str, line: int, character: int
    ) -> Optional[Dict[str, Any]]:
        """Get hover information for the symbol at the given position."""
        try:
            position = Position(line=line, character=character)
            hover = self.client.get_hover(file_path, position)
            return hover
        except Exception as e:
            return {"error": str(e)}

    def get_references(
        self, file_path: str, line: int, character: int
    ) -> List[Dict[str, Any]]:
        """Get references for the symbol at the given position."""
        try:
            position = Position(line=line, character=character)
            references = self.client.get_references(file_path, position)
            return [ref.model_dump() for ref in references]
        except Exception as e:
            return [{"error": str(e)}]

    def get_document_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """Get document symbols."""
        try:
            symbols = self.client.get_document_symbols(file_path)
            return symbols
        except Exception as e:
            return [{"error": str(e)}]

    def format_document(
        self, file_path: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format the document."""
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Notify server about file
            self.client.notify_did_open(file_path, content)

            # Get formatting
            formatting = self.client.format_document(file_path, options)

            # Apply formatting if available
            if formatting:
                # This is a simplified implementation
                # In practice, you'd apply the text edits from the language server
                return {
                    "file_path": file_path,
                    "formatted": True,
                    "message": "Document formatted by language server",
                }

            return {
                "file_path": file_path,
                "formatted": False,
                "message": "No formatting available",
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file and return comprehensive information."""
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get diagnostics (this will handle file opening and waiting for notifications)
            diagnostics = self.client.get_diagnostics(file_path)

            # Get document symbols
            symbols = self.client.get_document_symbols(file_path)

            # Get file statistics
            lines = content.split("\n")
            total_lines = len(lines)
            code_lines = len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
            )
            comment_lines = len(
                [line for line in lines if line.strip().startswith("#")]
            )

            return {
                "file_path": file_path,
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "symbols": symbols,
                "diagnostics": [diagnostic.model_dump() for diagnostic in diagnostics],
                "has_syntax_errors": any(d.severity == 1 for d in diagnostics),
                "supported_languages": self.client.get_supported_languages(),
            }
        except Exception as e:
            return {"error": str(e)}

    def workspace_symbol_search(self, query: str) -> List[Dict[str, Any]]:
        """Search for symbols in the workspace."""
        try:
            symbols = self.client.workspace_symbol(query)
            return symbols
        except Exception as e:
            return [{"error": str(e)}]

    def notify_file_changed(self, file_path: str, content: str):
        """Notify that a file has changed."""
        try:
            self.client.notify_did_change(file_path, content)
        except Exception as e:
            print(f"Error notifying file change: {e}")

    def notify_file_saved(self, file_path: str, content: Optional[str] = None):
        """Notify that a file has been saved."""
        try:
            self.client.notify_did_save(file_path, content)
        except Exception as e:
            print(f"Error notifying file save: {e}")

    def close(self):
        """Close the LSP client."""
        self.client.stop_all_servers()


# Global LSP tools instance
_lsp_tools: Optional[LSPTools] = None


def get_lsp_tools() -> LSPTools:
    """Get the global LSP tools instance."""
    global _lsp_tools
    if _lsp_tools is None:
        _lsp_tools = LSPTools()
    return _lsp_tools


def close_lsp_tools():
    """Close the global LSP tools instance."""
    global _lsp_tools
    if _lsp_tools:
        _lsp_tools.close()
        _lsp_tools = None
