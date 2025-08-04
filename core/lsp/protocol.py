"""
LSP (Language Server Protocol) protocol definitions.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class Position(BaseModel):
    """Position in a text document."""

    line: int = Field(..., description="Line position (0-based)")
    character: int = Field(..., description="Character offset on the line (0-based)")


class Range(BaseModel):
    """Range in a text document."""

    start: Position = Field(..., description="Start position")
    end: Position = Field(..., description="End position")


class Location(BaseModel):
    """Location in a text document."""

    uri: str = Field(..., description="Document URI")
    range: Range = Field(..., description="Range in the document")


class TextDocumentItem(BaseModel):
    """Text document item."""

    uri: str = Field(..., description="Document URI")
    language_id: str = Field(..., description="Language identifier")
    version: int = Field(..., description="Version number")
    text: str = Field(..., description="Document content")


class TextDocumentIdentifier(BaseModel):
    """Text document identifier."""

    uri: str = Field(..., description="Document URI")


class VersionedTextDocumentIdentifier(TextDocumentIdentifier):
    """Versioned text document identifier."""

    version: int = Field(..., description="Version number")


class TextDocumentContentChangeEvent(BaseModel):
    """Text document content change event."""

    range: Optional[Range] = Field(None, description="Range of the change")
    range_length: Optional[int] = Field(None, description="Length of the range")
    text: str = Field(..., description="New text")


class CompletionItem(BaseModel):
    """Completion item."""

    label: str = Field(..., description="Display text")
    kind: Optional[int] = Field(None, description="Completion item kind")
    detail: Optional[str] = Field(None, description="Additional details")
    documentation: Optional[str] = Field(None, description="Documentation")
    sort_text: Optional[str] = Field(None, description="Sort text")
    insert_text: Optional[str] = Field(None, description="Insert text")


class Diagnostic(BaseModel):
    """Diagnostic information."""

    range: Range = Field(..., description="Range in the document")
    severity: int = Field(..., description="Severity level")
    code: Optional[Union[str, int]] = Field(None, description="Diagnostic code")
    source: Optional[str] = Field(None, description="Source of the diagnostic")
    message: str = Field(..., description="Diagnostic message")


class LSPRequest(BaseModel):
    """LSP request message."""

    jsonrpc: str = Field("2.0", description="JSON-RPC version")
    id: Union[int, str] = Field(..., description="Request ID")
    method: str = Field(..., description="Method name")
    params: Optional[Dict[str, Any]] = Field(None, description="Request parameters")


class LSPResponse(BaseModel):
    """LSP response message."""

    jsonrpc: str = Field("2.0", description="JSON-RPC version")
    id: Union[int, str] = Field(..., description="Request ID")
    result: Optional[Any] = Field(None, description="Response result")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information")


class LSPNotification(BaseModel):
    """LSP notification message."""

    jsonrpc: str = Field("2.0", description="JSON-RPC version")
    method: str = Field(..., description="Method name")
    params: Optional[Dict[str, Any]] = Field(
        None, description="Notification parameters"
    )


# LSP methods
class Methods:
    """LSP method names."""

    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    SHUTDOWN = "shutdown"
    EXIT = "exit"
    TEXT_DOCUMENT_COMPLETION = "textDocument/completion"
    TEXT_DOCUMENT_DID_OPEN = "textDocument/didOpen"
    TEXT_DOCUMENT_DID_CHANGE = "textDocument/didChange"
    TEXT_DOCUMENT_DID_CLOSE = "textDocument/didClose"
    TEXT_DOCUMENT_DID_SAVE = "textDocument/didSave"
    TEXT_DOCUMENT_DEFINITION = "textDocument/definition"
    TEXT_DOCUMENT_HOVER = "textDocument/hover"
    TEXT_DOCUMENT_SIGNATURE_HELP = "textDocument/signatureHelp"
    TEXT_DOCUMENT_REFERENCES = "textDocument/references"
    TEXT_DOCUMENT_DOCUMENT_SYMBOL = "textDocument/documentSymbol"
    TEXT_DOCUMENT_FORMATTING = "textDocument/formatting"
    TEXT_DOCUMENT_RANGE_FORMATTING = "textDocument/rangeFormatting"
    TEXT_DOCUMENT_DIAGNOSTIC = "textDocument/diagnostic"


# Severity levels
class DiagnosticSeverity:
    """Diagnostic severity levels."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


# Completion item kinds
class CompletionItemKind:
    """Completion item kinds."""

    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18
    FOLDER = 19
    ENUM_MEMBER = 20
    CONSTANT = 21
    STRUCT = 22
    EVENT = 23
    OPERATOR = 24
    TYPE_PARAMETER = 25
