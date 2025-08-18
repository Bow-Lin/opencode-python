from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os


@dataclass
class InteractionRecord:
    """Record of a single agent interaction."""

    query: str
    plan: str
    tools_used: List[str]
    tool_results: List[Dict[str, Any]]


@dataclass
class FlowRecord:
    """Record of a flow execution step."""

    agent_name: str
    action: str
    result: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ContextStore:
    """In-memory context store for agent sessions with flow control support."""

    cwd: str = field(default_factory=os.getcwd)
    path_history: List[str] = field(default_factory=lambda: [os.getcwd()])
    interactions: List[InteractionRecord] = field(default_factory=list)
    
    # Flow control related fields
    current_agent: Optional[str] = field(default=None)
    flow_history: List[FlowRecord] = field(default_factory=list)
    branch_decisions: List[str] = field(default_factory=list)
    flow_params: Dict[str, Any] = field(default_factory=dict)

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

    def record_flow_step(
        self, 
        agent_name: str, 
        action: str, 
        result: Any, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a step in flow execution."""
        self.current_agent = agent_name
        self.flow_history.append(
            FlowRecord(
                agent_name=agent_name,
                action=action,
                result=result,
                metadata=metadata
            )
        )
        self.branch_decisions.append(action)

    def set_flow_params(self, params: Dict[str, Any]) -> None:
        """Set parameters for flow execution."""
        self.flow_params.update(params)

    def get_flow_params(self) -> Dict[str, Any]:
        """Get current flow parameters."""
        return self.flow_params.copy()

    def get_last_flow_step(self) -> Optional[FlowRecord]:
        """Get the last executed flow step."""
        return self.flow_history[-1] if self.flow_history else None

    def get_flow_summary(self) -> Dict[str, Any]:
        """Get a summary of the flow execution."""
        return {
            "total_steps": len(self.flow_history),
            "current_agent": self.current_agent,
            "branch_decisions": self.branch_decisions,
            "flow_params": self.flow_params,
            "steps": [
                {
                    "agent": step.agent_name,
                    "action": step.action,
                    "metadata": step.metadata
                }
                for step in self.flow_history
            ]
        }

    def reset(self) -> None:
        """Clear interaction and path history."""
        self.interactions.clear()
        self.path_history = [self.cwd]
        self.flow_history.clear()
        self.branch_decisions.clear()
        self.flow_params.clear()
        self.current_agent = None

    def reset_flow(self) -> None:
        """Clear only flow-related data."""
        self.flow_history.clear()
        self.branch_decisions.clear()
        self.flow_params.clear()
        self.current_agent = None