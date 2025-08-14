"""
Language detection for LSP.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class LanguageDetector:
    """Language detector for LSP."""

    def __init__(self):
        self.language_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascriptreact",
            ".tsx": "typescriptreact",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".txt": "plaintext",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".php": "php",
            ".rb": "ruby",
            ".scala": "scala",
            ".clj": "clojure",
            ".hs": "haskell",
            ".ml": "ocaml",
            ".fs": "fsharp",
            ".cs": "csharp",
            ".vb": "vb",
            ".sql": "sql",
            ".sh": "shellscript",
            ".ps1": "powershell",
            ".bat": "batch",
            ".cmd": "batch",
            ".dockerfile": "dockerfile",
            ".dockerignore": "ignore",
            ".gitignore": "ignore",
            ".gitattributes": "gitattributes",
            ".editorconfig": "editorconfig",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "ini",
            ".toml": "toml",
            ".lock": "json",  # package-lock.json, etc.
        }

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect the language of a file based on its extension."""
        path = Path(file_path)
        extension = path.suffix.lower()

        # Check for special cases
        if path.name.lower() in ["dockerfile", "makefile", "cmakelists.txt"]:
            return path.name.lower()

        # Check for common configuration files
        if path.name.lower() in [".gitignore", ".gitattributes", ".editorconfig"]:
            return path.name.lower()

        # Check for lock files
        if path.name.endswith(".lock"):
            return "json"

        # Return language based on extension
        return self.language_extensions.get(extension)

    def is_supported_language(self, file_path: str) -> bool:
        """Check if the file language is supported."""
        language = self.detect_language(file_path)
        return language is not None

    def get_language_server_command(self, language: str) -> Optional[list[str]]:
        """Get the language server command for a given language."""
        # Check if the language server is available
        server_commands = {
                    "python": [
            ["pyright-langserver", "--stdio"],  # Pyright (优先)
            ["pyright-langserver", "--stdio", "--project", "."],  # Pyright with project root
            ["python", "-m", "pylsp"],  # Python Language Server
            ["python", "-m", "pyright-langserver", "--stdio"],  # Pyright (备用)
            ["python-lsp-server"],  # python-lsp-server
        ],
            "javascript": [
                ["npx", "typescript-language-server", "--stdio"],
                ["npx", "javascript-typescript-langserver", "--stdio"],
            ],
            "typescript": [
                ["npx", "typescript-language-server", "--stdio"],
            ],
            "go": [
                ["gopls"],
            ],
            "rust": [
                ["rust-analyzer"],
            ],
            "java": [
                [
                    "java",
                    "-jar",
                    "eclipse.jdt.ls/plugins/org.eclipse.equinox.launcher_*.jar",
                ],
            ],
            "cpp": [
                ["clangd"],
            ],
            "c": [
                ["clangd"],
            ],
            "html": [
                ["npx", "vscode-html-languageserver-bin", "--stdio"],
            ],
            "css": [
                ["npx", "vscode-css-languageserver-bin", "--stdio"],
            ],
            "json": [
                ["npx", "vscode-json-languageserver-bin", "--stdio"],
            ],
            "yaml": [
                ["npx", "yaml-language-server", "--stdio"],
            ],
            "markdown": [
                ["npx", "markdown-language-server", "--stdio"],
            ],
        }

        commands = server_commands.get(language, [])
        for command in commands:
            if self._is_command_available(command):
                return command

        return None

    def _is_command_available(self, command: list[str]) -> bool:
        """Check if a command is available in the system."""
        # First check if the main command exists
        if shutil.which(command[0]) is None:
            return False

        # For pyright-langserver and pylsp, also test if they can start
        if command[0] == "pyright-langserver" or (len(command) > 2 and command[1] == "-m" and command[2] in ["pylsp", "pyright-langserver"]):
            try:
                result = subprocess.run(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5,
                )
                # If it starts without error, it's available
                return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False

        return True

    def get_file_uri(self, file_path: str) -> str:
        """Convert file path to URI."""
        abs_path = os.path.abspath(file_path)
        return f"file://{abs_path}"

    def get_relative_path(self, base_path: str, file_path: str) -> str:
        """Get relative path from base path to file path."""
        try:
            return os.path.relpath(file_path, base_path)
        except ValueError:
            return file_path

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages."""
        return list(set(self.language_extensions.values()))
