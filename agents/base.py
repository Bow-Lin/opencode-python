"""
Base Agent implementation
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    """Agent input data structure"""

    query: str = Field(..., description="User query or instruction")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context information"
    )
    tools: Optional[List[str]] = Field(
        default=None, description="List of specific tools to use"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool parameters"
    )


class AgentOutput(BaseModel):
    """Agent output data structure"""

    result: Any = Field(..., description="Execution result")
    plan: Optional[str] = Field(default=None, description="Execution plan description")
    tools_used: Optional[List[str]] = Field(
        default=None, description="List of tools that were used"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class PlanResult(BaseModel):
    """Plan execution result structure"""

    plan: str = Field(..., description="Execution plan")
    tools_to_use: List[str] = Field(
        default_factory=list, description="Tools to be used"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class BaseAgent(ABC):
    """Abstract base class for all agents"""

    def __init__(self, name: str = "BaseAgent"):
        self.name = name

    @abstractmethod
    def plan(self, input_data: AgentInput) -> PlanResult:
        """
        Plan the execution based on input

        Args:
            input_data: Agent input containing query and context

        Returns:
            PlanResult with execution plan and tool requirements
        """
        pass

    @abstractmethod
    def run(self, plan_result: PlanResult) -> AgentOutput:
        """
        Execute the plan and return results

        Args:
            plan_result: Result from the planning phase

        Returns:
            AgentOutput with execution results
        """
        pass

    def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Complete execution flow: plan then run

        Args:
            input_data: Agent input data

        Returns:
            AgentOutput with final results
        """
        plan_result = self.plan(input_data)
        return self.run(plan_result)
