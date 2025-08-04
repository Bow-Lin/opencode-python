"""
LSP client implementation - pure client without language-specific parsing.
"""

import json
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .protocol import Position, Range, CompletionItem, Diagnostic, Location
from .transport import Transport
from .methods import LSPMethods
from .language import LanguageDetector


class LSPClient:
    """Pure LSP client for communicating with language servers."""

    def __init__(self):
        self.transport: Optional[Transport] = None
        self.methods: Optional[LSPMethods] = None
        self.language_detector = LanguageDetector()
        self.logger = logging.getLogger(__name__)
        self._active_servers: Dict[str, Transport] = {}

    def start_language_server(self, language: str, server_command: List[str]) -> bool:
        """Start a language server for the specified language."""
        try:
            transport = Transport(server_command)
            if transport.start():
                self._active_servers[language] = transport
                methods = LSPMethods(transport)

                # Initialize the server
                root_path = str(Path.cwd())
                if methods.initialize(root_path):
                    self.logger.info(f"Started language server for {language}")
                    return True
                else:
                    self.logger.error(
                        f"Failed to initialize language server for {language}"
                    )
                    transport.stop()
                    return False
            else:
                self.logger.error(f"Failed to start language server for {language}")
                return False
        except Exception as e:
            self.logger.error(f"Error starting language server for {language}: {e}")
            return False

    def get_language_server(self, file_path: str) -> Optional[LSPMethods]:
        """Get the appropriate language server for a file."""
        language = self.language_detector.detect_language(file_path)
        if not language:
            return None

        # Check if we have an active server for this language
        if language in self._active_servers:
            transport = self._active_servers[language]
            return LSPMethods(transport)

        # Try to start a server for this language
        server_command = self.language_detector.get_language_server_command(language)
        if server_command and self.start_language_server(language, server_command):
            return LSPMethods(self._active_servers[language])

        return None

    def get_completions(
        self, file_path: str, position: Position
    ) -> List[CompletionItem]:
        """Get completion items at the given position."""
        methods = self.get_language_server(file_path)
        if methods:
            return methods.text_document_completion(file_path, position)
        return []

    def get_diagnostics(self, file_path: str) -> List[Diagnostic]:
        """Get diagnostics for the given file."""
        methods = self.get_language_server(file_path)
        if methods:
            return methods.text_document_diagnostic(file_path)
        return []

    def get_definition(self, file_path: str, position: Position) -> Optional[Location]:
        """Get definition location for the symbol at the given position."""
        methods = self.get_language_server(file_path)
        if methods:
            return methods.text_document_definition(file_path, position)
        return None

    def get_implementation(self, file_path: str, position: Position) -> List[Location]:
        """Get implementation locations for the symbol at the given position."""
        methods = self.get_language_server(file_path)
        if methods:
            return methods.text_document_implementation(file_path, position)
        return []

    def get_hover(self, file_path: str, position: Position) -> Optional[Dict[str, Any]]:
        """Get hover information for the symbol at the given position."""
        methods = self.get_language_server(file_path)
        if methods:
            return methods.text_document_hover(file_path, position)
        return None

    def get_references(self, file_path: str, position: Position) -> List[Location]:
        """Get references for the symbol at the given position."""
        methods = self.get_language_server(file_path)
        if methods:
            return methods.text_document_references(file_path, position)
        return []

    def get_document_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """Get document symbols."""
        methods = self.get_language_server(file_path)
        if methods:
            return methods.text_document_document_symbol(file_path)
        return []

    def format_document(
        self, file_path: str, options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format the entire document."""
        methods = self.get_language_server(file_path)
        if methods:
            return methods.text_document_formatting(file_path, options)
        return []

    def notify_did_open(self, file_path: str, content: str):
        """Notify the server that a file was opened."""
        methods = self.get_language_server(file_path)
        if methods:
            language = self.language_detector.detect_language(file_path)
            methods.text_document_did_open(file_path, content, language or "plaintext")

    def notify_did_change(self, file_path: str, content: str, version: int = 1):
        """Notify the server that a file was changed."""
        methods = self.get_language_server(file_path)
        if methods:
            methods.text_document_did_change(file_path, content, version)

    def notify_did_close(self, file_path: str):
        """Notify the server that a file was closed."""
        methods = self.get_language_server(file_path)
        if methods:
            methods.text_document_did_close(file_path)

    def notify_did_save(self, file_path: str, content: Optional[str] = None):
        """Notify the server that a file was saved."""
        methods = self.get_language_server(file_path)
        if methods:
            methods.text_document_did_save(file_path, content)

    def workspace_symbol(self, query: str) -> List[Dict[str, Any]]:
        """Search for symbols in the workspace."""
        # Use the first available server for workspace operations
        for methods in [
            LSPMethods(transport) for transport in self._active_servers.values()
        ]:
            symbols = methods.workspace_symbol(query)
            if symbols:
                return symbols
        return []

    def stop_all_servers(self):
        """Stop all language servers."""
        for language, transport in self._active_servers.items():
            try:
                transport.stop()
                self.logger.info(f"Stopped language server for {language}")
            except Exception as e:
                self.logger.error(f"Error stopping language server for {language}: {e}")
        self._active_servers.clear()

    def get_supported_languages(self) -> List[str]:
        """Get list of currently supported languages."""
        return list(self._active_servers.keys())

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_all_servers()
