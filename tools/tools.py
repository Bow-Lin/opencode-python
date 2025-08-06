"""
Tools module for Python CLI code agent.

This module provides base classes and structures for tools that can be used
by code agents to read, modify, and generate code files and documentation.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolInfo:
    """Tool information for agent registration and usage."""

    name: str
    description: str
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LLM function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolExecutionResponse:
    """
    Response from tool execution.

    This response contains all information needed by the agent to understand
    the tool execution result and provide feedback to the user.
    """

    success: bool
    content: str
    metadata: Optional[str] = None


class BaseTool(ABC):
    """
    Base class for all code agent tools.

    All tools should inherit from this class and implement the required methods.
    Tools can perform various operations like file reading, code modification,
    documentation processing, etc.
    """

    @abstractmethod
    def get_tool_info(self) -> ToolInfo:
        """
        Get tool information for agent registration.

        Returns:
            ToolInfo containing name, description, and parameters schema
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolExecutionResponse:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool parameters as keyword arguments

        Returns:
            ToolExecutionResponse with execution result
        """
        pass
