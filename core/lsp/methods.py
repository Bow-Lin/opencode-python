"""
LSP methods implementation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from .protocol import Position, Range, CompletionItem, Diagnostic, Location
from .transport import Transport

import time


class LSPMethods:
    """LSP methods implementation."""

    def __init__(self, transport: Transport):
        self.transport = transport

    def initialize(self, root_path: str, process_id: Optional[int] = None) -> bool:
        """Initialize the language server."""
        params = {
            "processId": process_id,
            "rootPath": root_path,
            "capabilities": {
                "textDocument": {
                    "completion": {"completionItem": {"snippetSupport": True}},
                    "hover": {},
                    "definition": {},
                    "diagnostic": {},
                    "implementation": {},
                    "references": {},
                    "documentSymbol": {},
                    "formatting": {},
                    "rangeFormatting": {},
                    "typeDefinition": {},
                    "codeAction": {},
                    "codeLens": {},
                    "documentLink": {},
                    "rename": {},
                    "prepareRename": {},
                    "foldingRange": {},
                    "selectionRange": {},
                    "signatureHelp": {},
                    "documentHighlight": {},
                    "semanticTokens": {},
                    "inlayHint": {},
                    "inlineCompletion": {},
                },
                "workspace": {
                    "symbol": {},
                    "executeCommand": {},
                    "applyEdit": {},
                    "configuration": {},
                    "didChangeConfiguration": {},
                    "didChangeWatchedFiles": {},
                    "didCreateFiles": {},
                    "didRenameFiles": {},
                    "didDeleteFiles": {},
                },
                "window": {
                    "showMessage": {},
                    "logMessage": {},
                    "showDocument": {},
                    "workDoneProgress": {},
                },
            },
        }
        response = self.transport.send_request("initialize", params)
        if response:
            self.transport.send_notification("initialized", {})
            return True
        return False

    def shutdown(self) -> bool:
        """Shutdown the language server."""
        response = self.transport.send_request("shutdown")
        return response is not None

    def exit(self):
        """Exit the language server."""
        self.transport.send_notification("exit")

    def text_document_completion(
        self,
        file_path: str,
        position: Position,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[CompletionItem]:
        """Get completion items at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
            "context": context or {"triggerKind": 1},
        }
        response = self.transport.send_request("textDocument/completion", params)
        if response and "result" in response:
            return [CompletionItem(**item) for item in response["result"]]
        return []

    def text_document_did_open(
        self,
        file_path: str,
        content: str,
        language_id: str = "python",
        version: int = 1,
    ):
        """Notify that a text document was opened."""
        params = {
            "textDocument": {
                "uri": f"file://{file_path}",
                "languageId": language_id,
                "version": version,
                "text": content,
            }
        }
        self.transport.send_notification("textDocument/didOpen", params)

    def text_document_did_change(self, file_path: str, content: str, version: int = 1):
        """Notify that a text document was changed."""
        params = {
            "textDocument": {"uri": f"file://{file_path}", "version": version},
            "contentChanges": [{"text": content}],
        }
        self.transport.send_notification("textDocument/didChange", params)

    def text_document_did_close(self, file_path: str):
        """Notify that a text document was closed."""
        params = {"textDocument": {"uri": f"file://{file_path}"}}
        self.transport.send_notification("textDocument/didClose", params)

    def text_document_did_save(self, file_path: str, content: Optional[str] = None):
        """Notify that a text document was saved."""
        params = {"textDocument": {"uri": f"file://{file_path}"}}
        if content is not None:
            params["text"] = content
        self.transport.send_notification("textDocument/didSave", params)

    def text_document_definition(
        self, file_path: str, position: Position
    ) -> Optional[Location]:
        """Get the definition location for the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
        }
        response = self.transport.send_request("textDocument/definition", params)
        if response and "result" in response:
            return Location(**response["result"])
        return None

    def text_document_type_definition(
        self, file_path: str, position: Position
    ) -> Optional[Location]:
        """Get the type definition location for the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
        }
        response = self.transport.send_request("textDocument/typeDefinition", params)
        if response and "result" in response:
            return Location(**response["result"])
        return None

    def text_document_implementation(
        self, file_path: str, position: Position
    ) -> List[Location]:
        """Get the implementation locations for the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
        }
        response = self.transport.send_request("textDocument/implementation", params)
        if response and "result" in response:
            return [Location(**impl) for impl in response["result"]]
        return []

    def text_document_hover(
        self, file_path: str, position: Position
    ) -> Optional[Dict[str, Any]]:
        """Get hover information for the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
        }
        response = self.transport.send_request("textDocument/hover", params)
        return response.get("result") if response else None

    def text_document_signature_help(
        self, file_path: str, position: Position
    ) -> Optional[Dict[str, Any]]:
        """Get signature help for the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
        }
        response = self.transport.send_request("textDocument/signatureHelp", params)
        return response.get("result") if response else None

    def text_document_references(
        self,
        file_path: str,
        position: Position,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Location]:
        """Get references for the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
            "context": context or {"includeDeclaration": True},
        }
        response = self.transport.send_request("textDocument/references", params)
        if response and "result" in response:
            return [Location(**ref) for ref in response["result"]]
        return []

    def text_document_document_highlight(
        self, file_path: str, position: Position
    ) -> List[Dict[str, Any]]:
        """Get document highlights for the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
        }
        response = self.transport.send_request("textDocument/documentHighlight", params)
        return response.get("result", []) if response else []

    def text_document_document_symbol(self, file_path: str) -> List[Dict[str, Any]]:
        """Get document symbols."""
        params = {"textDocument": {"uri": f"file://{file_path}"}}
        response = self.transport.send_request("textDocument/documentSymbol", params)
        return response.get("result", []) if response else []

    def text_document_code_action(
        self, file_path: str, range: Range, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get code actions for the given range."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "range": range.model_dump(),
            "context": context,
        }
        response = self.transport.send_request("textDocument/codeAction", params)
        return response.get("result", []) if response else []

    def text_document_code_lens(self, file_path: str) -> List[Dict[str, Any]]:
        """Get code lenses for the document."""
        params = {"textDocument": {"uri": f"file://{file_path}"}}
        response = self.transport.send_request("textDocument/codeLens", params)
        return response.get("result", []) if response else []

    def text_document_document_link(self, file_path: str) -> List[Dict[str, Any]]:
        """Get document links."""
        params = {"textDocument": {"uri": f"file://{file_path}"}}
        response = self.transport.send_request("textDocument/documentLink", params)
        return response.get("result", []) if response else []

    def text_document_rename(
        self, file_path: str, position: Position, new_name: str
    ) -> Optional[Dict[str, Any]]:
        """Rename the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
            "newName": new_name,
        }
        response = self.transport.send_request("textDocument/rename", params)
        return response.get("result") if response else None

    def text_document_prepare_rename(
        self, file_path: str, position: Position
    ) -> Optional[Dict[str, Any]]:
        """Prepare rename for the symbol at the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
        }
        response = self.transport.send_request("textDocument/prepareRename", params)
        return response.get("result") if response else None

    def text_document_folding_range(self, file_path: str) -> List[Dict[str, Any]]:
        """Get folding ranges for the document."""
        params = {"textDocument": {"uri": f"file://{file_path}"}}
        response = self.transport.send_request("textDocument/foldingRange", params)
        return response.get("result", []) if response else []

    def text_document_selection_range(
        self, file_path: str, positions: List[Position]
    ) -> List[Dict[str, Any]]:
        """Get selection ranges for the given positions."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "positions": [pos.model_dump() for pos in positions],
        }
        response = self.transport.send_request("textDocument/selectionRange", params)
        return response.get("result", []) if response else []

    def text_document_semantic_tokens_full(
        self, file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Get full semantic tokens for the document."""
        params = {"textDocument": {"uri": f"file://{file_path}"}}
        response = self.transport.send_request(
            "textDocument/semanticTokens/full", params
        )
        return response.get("result") if response else None

    def text_document_semantic_tokens_range(
        self, file_path: str, range: Range
    ) -> Optional[Dict[str, Any]]:
        """Get semantic tokens for the given range."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "range": range.model_dump(),
        }
        response = self.transport.send_request(
            "textDocument/semanticTokens/range", params
        )
        return response.get("result") if response else None

    def text_document_inlay_hint(
        self, file_path: str, range: Range
    ) -> List[Dict[str, Any]]:
        """Get inlay hints for the given range."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "range": range.model_dump(),
        }
        response = self.transport.send_request("textDocument/inlayHint", params)
        return response.get("result", []) if response else []

    def text_document_inline_completion(
        self, file_path: str, position: Position, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get inline completion for the given position."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
            "context": context,
        }
        response = self.transport.send_request("textDocument/inlineCompletion", params)
        return response.get("result") if response else None



    def text_document_diagnostic(self, file_path: str) -> List[Diagnostic]:
        """Get diagnostics for the document."""
        try:
            content = Path(file_path).read_text(encoding='utf-8')

            # === 先完成一次握手（只处理 workspace/configuration） ===
            handshake_deadline = time.time() + 2.0
            while time.time() < handshake_deadline:
                msg = self.transport._read_response(timeout=0.2)
                if not msg:
                    continue
                if msg.get("method") == "workspace/configuration":
                    items = msg.get("params", {}).get("items", [])
                    results = []
                    for it in items:
                        sec = it.get("section")
                        if sec == "python":
                            results.append({})
                        elif sec == "python.analysis":
                            results.append({
                                "typeCheckingMode": "basic",
                                "diagnosticMode": "workspace"
                            })
                        elif sec == "pyright":
                            results.append({})
                        else:
                            results.append(None)
                    self.transport.send_response({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "result": results
                    })
                elif msg.get("method") == "window/logMessage":
                    print("LSP log:", msg.get("params", {}).get("message"))

            # === 握手完成后再 didOpen ===
            self.text_document_did_open(file_path, content, "python")

            diagnostics = None
            max_attempts = 30

            for attempt in range(max_attempts):
                msg = self.transport._read_response(timeout=0.3)
                if not msg:
                    if attempt < max_attempts - 1:
                        time.sleep(0.2)
                    continue
                if msg.get("method") == "workspace/configuration":
                    # 握手之后还有迟到的 config 请求，也要回
                    items = msg.get("params", {}).get("items", [])
                    results = []
                    for it in items:
                        sec = it.get("section")
                        if sec == "python":
                            results.append({})
                        elif sec == "python.analysis":
                            results.append({
                                "typeCheckingMode": "basic",
                                "diagnosticMode": "workspace"
                            })
                        elif sec == "pyright":
                            results.append({})
                        else:
                            results.append(None)
                    self.transport.send_response({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "result": results
                    })
                    continue

                if msg.get("method") == "textDocument/publishDiagnostics":
                    params = msg.get("params", {})

                    if params.get("uri") == Path(file_path).resolve().as_uri():
                        if diagnostics is None or diagnostics == []:
                            diagnostics = [Diagnostic(**d) for d in params.get("diagnostics", [])]
                            if diagnostics:
                                return diagnostics

                elif msg.get("method") == "window/logMessage":
                    log_msg = msg.get('params', {}).get('message', '')
                    print(f"LSP log: {log_msg}")

            return diagnostics or []

        except Exception as e:
            print(f"Error getting diagnostics: {e}")
            return []


    def text_document_formatting(
        self, file_path: str, options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format the entire document."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "options": options or {},
        }
        response = self.transport.send_request("textDocument/formatting", params)
        return response.get("result", []) if response else []

    def text_document_range_formatting(
        self, file_path: str, range: Range, options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Format a range in the document."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "range": range.model_dump(),
            "options": options or {},
        }
        response = self.transport.send_request("textDocument/rangeFormatting", params)
        return response.get("result", []) if response else []

    def text_document_on_type_formatting(
        self,
        file_path: str,
        position: Position,
        ch: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Format on type."""
        params = {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": position.model_dump(),
            "ch": ch,
            "options": options or {},
        }
        response = self.transport.send_request("textDocument/onTypeFormatting", params)
        return response.get("result", []) if response else []

    def workspace_symbol(self, query: str) -> List[Dict[str, Any]]:
        """Search for symbols in the workspace."""
        params = {"query": query}
        response = self.transport.send_request("workspace/symbol", params)
        return response.get("result", []) if response else []

    def workspace_execute_command(
        self, command: str, arguments: Optional[List[Any]] = None
    ) -> Any:
        """Execute a workspace command."""
        params = {"command": command, "arguments": arguments or []}
        response = self.transport.send_request("workspace/executeCommand", params)
        return response.get("result") if response else None

    def workspace_apply_edit(self, label: str, edit: Dict[str, Any]) -> bool:
        """Apply a workspace edit."""
        params = {
            "label": label,
            "edit": edit,
        }
        response = self.transport.send_request("workspace/applyEdit", params)
        return response.get("result", {}).get("applied", False) if response else False

    def workspace_configuration(self, items: List[Dict[str, Any]]) -> List[Any]:
        """Get workspace configuration."""
        params = {"items": items}
        response = self.transport.send_request("workspace/configuration", params)
        return response.get("result", []) if response else []

    def workspace_did_change_configuration(self, settings: Dict[str, Any]):
        """Notify that workspace configuration has changed."""
        params = {"settings": settings}
        self.transport.send_notification("workspace/didChangeConfiguration", params)

    def workspace_did_change_watched_files(self, changes: List[Dict[str, Any]]):
        """Notify that watched files have changed."""
        params = {"changes": changes}
        self.transport.send_notification("workspace/didChangeWatchedFiles", params)

    def workspace_did_create_files(self, files: List[Dict[str, Any]]):
        """Notify that files have been created."""
        params = {"files": files}
        self.transport.send_notification("workspace/didCreateFiles", params)

    def workspace_did_rename_files(self, files: List[Dict[str, Any]]):
        """Notify that files have been renamed."""
        params = {"files": files}
        self.transport.send_notification("workspace/didRenameFiles", params)

    def workspace_did_delete_files(self, files: List[Dict[str, Any]]):
        """Notify that files have been deleted."""
        params = {"files": files}
        self.transport.send_notification("workspace/didDeleteFiles", params)

    def window_show_message(self, type: int, message: str):
        """Show a message in the client."""
        params = {"type": type, "message": message}
        self.transport.send_notification("window/showMessage", params)

    def window_log_message(self, type: int, message: str):
        """Log a message in the client."""
        params = {"type": type, "message": message}
        self.transport.send_notification("window/logMessage", params)

    def window_show_document(
        self,
        uri: str,
        external: bool = False,
        take_focus: bool = True,
        selection: Optional[Range] = None,
    ) -> bool:
        """Show a document in the client."""
        params = {
            "uri": uri,
            "external": external,
            "takeFocus": take_focus,
        }
        if selection:
            params["selection"] = selection.model_dump()

        response = self.transport.send_request("window/showDocument", params)
        return response.get("result", {}).get("success", False) if response else False

    def window_work_done_progress_create(self, token: str) -> bool:
        """Create a work done progress."""
        params = {"token": token}
        response = self.transport.send_request("window/workDoneProgress/create", params)
        return response is not None

    def window_work_done_progress_cancel(self, token: str):
        """Cancel a work done progress."""
        params = {"token": token}
        self.transport.send_notification("window/workDoneProgress/cancel", params)
