"""
Simple Tool Agent implementation with ToolPlanner and ToolRunner
"""
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from tool_registry.registry import list_tools_with_info

from .base import AgentInput, AgentOutput, BaseAgent, PlanResult
from .planner import BasePlanner, OpenAIPlanner, QwenPlanner
from .runner import ToolExecutor, run_multiple_tools


class SimpleToolAgent(BaseAgent):
    """Simple agent that uses ToolPlanner and ToolRunner for tool execution"""

    def __init__(
        self,
        planner: Optional[BasePlanner] = None,
        executor: Optional[ToolExecutor] = None,
        name: str = "SimpleToolAgent",
    ):
        super().__init__(name)

        # Initialize planner (default to QwenPlanner with mock provider)
        if planner is None:
            mock_provider = MagicMock()
            self.planner = QwenPlanner(mock_provider)
        else:
            self.planner = planner

        # Initialize executor
        self.executor = executor or ToolExecutor()

    def plan(self, input_data: AgentInput) -> PlanResult:
        """
        Use ToolPlanner to determine if tools are needed and which ones to use

        Args:
            input_data: Agent input containing query and context

        Returns:
            PlanResult with execution plan
        """
        # Get available tools
        available_tools = list_tools_with_info()

        # Use planner to determine tool usage
        plan_result = self.planner.plan(input_data, available_tools)

        return plan_result

    def run(self, plan_result: PlanResult) -> AgentOutput:
        """
        Execute the plan using ToolRunner and generate final response

        Args:
            plan_result: Result from the planning phase

        Returns:
            AgentOutput with execution results and final response
        """
        tools_to_use = plan_result.tools_to_use
        parameters = plan_result.parameters
        results = []
        tools_used = []

        # Execute tools if any are needed
        if tools_to_use:
            # Convert plan result to tool calls format
            tool_calls = [
                {"tool": tool_name, "args": args}
                for tool_name, args in parameters.items()
            ]

            # Execute tools using ToolRunner
            execution_results = run_multiple_tools(tool_calls)

            # Process execution results
            for i, exec_result in enumerate(execution_results):
                tool_name = tools_to_use[i] if i < len(tools_to_use) else "unknown"

                if exec_result.success:
                    results.append(
                        {
                            "tool": tool_name,
                            "result": exec_result.result,
                            "execution_time": exec_result.execution_time,
                        }
                    )
                    tools_used.append(tool_name)
                else:
                    results.append(
                        {
                            "tool": tool_name,
                            "error": exec_result.error,
                            "execution_time": exec_result.execution_time,
                        }
                    )

        # Generate final response based on tool results
        final_response = self._generate_final_response(
            plan_result.plan, results, tools_used
        )

        return AgentOutput(
            result=final_response,
            plan=plan_result.plan,
            tools_used=tools_used,
            metadata={
                "agent_type": "SimpleToolAgent",
                "total_tools": len(tools_to_use),
                "successful_tools": len(tools_used),
                "execution_results": results,
                "planner_type": type(self.planner).__name__,
            },
        )

    def _generate_final_response(
        self, plan: str, tool_results: List[Dict[str, Any]], tools_used: List[str]
    ) -> str:
        """
        Generate final response based on tool execution results

        Args:
            plan: Original execution plan
            tool_results: Results from tool executions
            tools_used: List of successfully used tools

        Returns:
            Final response string
        """
        if not tool_results:
            return "No tools were executed."

        response_parts = []
        response_parts.append(f"Plan: {plan}")
        response_parts.append(f"Executed {len(tools_used)} tools successfully.")

        for result in tool_results:
            tool_name = result["tool"]
            if "error" in result:
                response_parts.append(f"Tool '{tool_name}' failed: {result['error']}")
            else:
                response_parts.append(
                    f"Tool '{tool_name}' returned: {result['result']}"
                )

        return "\n".join(response_parts)

    def run_with_provider(self, input_data: AgentInput, provider) -> AgentOutput:
        """
        Run agent with a specific provider for enhanced planning

        Args:
            input_data: Agent input
            provider: LLM provider for planning

        Returns:
            AgentOutput with results
        """
        # Create planner with the provided provider
        if isinstance(self.planner, OpenAIPlanner):
            planner = OpenAIPlanner(provider)
        elif isinstance(self.planner, QwenPlanner):
            planner = QwenPlanner(provider)
        else:
            # Use current planner if not OpenAI/Qwen type
            planner = self.planner

        # Create temporary agent with new planner
        temp_agent = SimpleToolAgent(planner=planner, executor=self.executor)

        # Plan and execute
        plan_result = temp_agent.plan(input_data)
        return temp_agent.run(plan_result)
