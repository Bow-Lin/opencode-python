from dataclasses import dataclass, field
from typing import Any, Dict, List
import os


@dataclass
class InteractionRecord:
    """Record of a single agent interaction."""

    query: str
    plan: str
    tools_used: List[str]
    tool_results: List[Dict[str, Any]]


@dataclass
class ContextStore:
    """In-memory context store for agent sessions."""

    cwd: str = field(default_factory=os.getcwd)
    path_history: List[str] = field(default_factory=lambda: [os.getcwd()])
    interactions: List[InteractionRecord] = field(default_factory=list)

    def change_directory(self, path: str) -> None:
        """Change working directory and record the change."""
        abs_path = os.path.abspath(path)
        os.chdir(abs_path)
        self.cwd = abs_path
        self.path_history.append(abs_path)

    def record_interaction(
        self, query: str, plan: str, tools: List[str], results: List[Dict[str, Any]]
    ) -> None:
        """Store details about an agent interaction."""
        self.interactions.append(
            InteractionRecord(
                query=query, plan=plan, tools_used=tools, tool_results=results
            )
        )

    def reset(self) -> None:
        """Clear interaction and path history."""
        self.interactions.clear()
        self.path_history = [self.cwd]