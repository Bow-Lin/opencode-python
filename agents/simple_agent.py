"""
Simple Tool Agent implementation
"""
from typing import List

from tool_registry.registry import get_tool_func, list_tools

from .base import AgentInput, AgentOutput, BaseAgent, PlanResult


class SimpleToolAgent(BaseAgent):
    """Simple agent that can directly call registered tools"""

    def __init__(self, name: str = "SimpleToolAgent"):
        super().__init__(name)

    def plan(self, input_data: AgentInput) -> PlanResult:
        """
        Simple planning that identifies tools to use based on input

        Args:
            input_data: Agent input containing query and context

        Returns:
            PlanResult with execution plan
        """
        query = input_data.query
        tools = input_data.tools or []
        parameters = input_data.parameters or {}

        # Simple tool selection logic
        tools_to_use = []
        if tools:
            # Use specified tools if provided
            tools_to_use = tools
        else:
            # Try to infer tools from query (basic implementation)
            available_tools = self._get_available_tools()
            tools_to_use = self._select_tools_by_query(query, available_tools)

        plan = f"Execute tools: {', '.join(tools_to_use)} with query: {query}"

        return PlanResult(
            plan=plan,
            tools_to_use=tools_to_use,
            parameters=parameters,
            metadata={"agent_type": "SimpleToolAgent"},
        )

    def run(self, plan_result: PlanResult) -> AgentOutput:
        """
        Execute the plan by calling the specified tools

        Args:
            plan_result: Result from the planning phase

        Returns:
            AgentOutput with execution results
        """
        tools_to_use = plan_result.tools_to_use
        parameters = plan_result.parameters
        results = []
        tools_used = []

        for tool_name in tools_to_use:
            tool_func = get_tool_func(tool_name)
            if tool_func:
                try:
                    # Execute tool with parameters
                    if parameters and tool_name in parameters:
                        tool_params = parameters[tool_name]
                        if isinstance(tool_params, dict):
                            result = tool_func(**tool_params)
                        else:
                            result = tool_func(tool_params)
                    else:
                        result = tool_func()

                    results.append({"tool": tool_name, "result": result})
                    tools_used.append(tool_name)
                except Exception as e:
                    results.append({"tool": tool_name, "error": str(e)})
            else:
                results.append({"tool": tool_name, "error": "Tool not found"})

        return AgentOutput(
            result=results,
            plan=plan_result.plan,
            tools_used=tools_used,
            metadata={
                "agent_type": "SimpleToolAgent",
                "total_tools": len(tools_to_use),
                "successful_tools": len(tools_used),
            },
        )

    def _get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list_tools()

    def _select_tools_by_query(
        self, query: str, available_tools: List[str]
    ) -> List[str]:
        """
        Simple tool selection based on query keywords

        Args:
            query: User query
            available_tools: List of available tool names

        Returns:
            List of selected tool names
        """
        query_lower = query.lower()
        selected_tools = []

        # Simple keyword-based tool selection
        for tool_name in available_tools:
            tool_name_lower = tool_name.lower()

            # Check if tool name appears in query
            if tool_name_lower in query_lower:
                selected_tools.append(tool_name)
                continue

            # Check for common patterns
            file_keywords = ["file", "read", "write"]
            math_keywords = ["math", "calculate", "compute"]

            if (
                any(keyword in query_lower for keyword in file_keywords)
                and "file" in tool_name_lower
            ):
                selected_tools.append(tool_name)
            elif (
                any(keyword in query_lower for keyword in math_keywords)
                and "math" in tool_name_lower
            ):
                selected_tools.append(tool_name)

        return selected_tools[:3]  # Limit to 3 tools max
