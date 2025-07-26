"""
Planner abstraction for tool selection
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .base import AgentInput, PlanResult


class BasePlanner(ABC):
    """Abstract base class for all planners"""

    @abstractmethod
    def plan(self, input_data: AgentInput, available_tools: List[Any]) -> PlanResult:
        """
        Plan tool execution based on input and available tools

        Args:
            input_data: Agent input containing query and context
            available_tools: List of available tools

        Returns:
            PlanResult with execution plan and tool requirements
        """
        pass


class OpenAIPlanner(BasePlanner):
    """OpenAI-style function calling planner"""

    def __init__(self, provider):
        self.provider = provider

    def plan(self, input_data: AgentInput, available_tools: List[Any]) -> PlanResult:
        """
        Use OpenAI-style function calling to plan tool execution

        Args:
            input_data: Agent input containing query and context
            available_tools: List of available tools

        Returns:
            PlanResult with model-decided tools and parameters
        """
        query = input_data.query
        tools = input_data.tools if input_data.tools else []

        # Filter tools if specified
        if tools:
            available_tools = [tool for tool in available_tools if tool.name in tools]

        # Generate function schema
        functions_schema = self._build_functions_schema(available_tools)

        # Build system prompt
        system_prompt = self._build_system_prompt(available_tools)

        # Get model response
        model_response = self.provider.generate(
            user_query=query,
            prompt=system_prompt,
            functions=functions_schema,
            function_call="auto",
        )

        # Parse response
        tool_calls = self._parse_model_response(model_response)

        # Build plan
        tool_names = [call["tool"] for call in tool_calls]
        plan = f"OpenAI planner decided to call tools: {tool_names}"

        return PlanResult(
            plan=plan,
            tools_to_use=[call["tool"] for call in tool_calls],
            parameters={call["tool"]: call["args"] for call in tool_calls},
            metadata={
                "planner_type": "OpenAIPlanner",
                "model_response": model_response,
                "tool_calls": tool_calls,
            },
        )

    def _build_functions_schema(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """Build OpenAI-style functions schema"""
        import inspect

        functions = []

        for tool in tools:
            # Get function signature
            sig = inspect.signature(tool.func)
            parameters = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                param_info = {
                    "type": self._get_type_name(param.annotation),
                    "description": f"Parameter {param_name}",
                }

                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default
                else:
                    required.append(param_name)

                parameters[param_name] = param_info

            if required:
                parameters["required"] = required

            function_schema = {
                "name": tool.name,
                "description": tool.description or f"Tool: {tool.name}",
                "parameters": {"type": "object", "properties": parameters},
            }

            functions.append(function_schema)

        return functions

    def _get_type_name(self, annotation: Any) -> str:
        """Convert Python type annotation to JSON schema type"""
        if annotation == str:
            return "string"
        elif annotation == int:
            return "integer"
        elif annotation == float:
            return "number"
        elif annotation == bool:
            return "boolean"
        elif annotation == list:
            return "array"
        elif annotation == dict:
            return "object"
        else:
            return "string"

    def _build_system_prompt(self, tools: List[Any]) -> str:
        """Build system prompt for tool selection"""
        tool_descriptions = []
        for tool in tools:
            desc = f"- {tool.name}: {tool.description or 'No description'}"
            if tool.tags:
                desc += f" (tags: {', '.join(tool.tags)})"
            tool_descriptions.append(desc)

        prompt = f"""You are a helpful AI assistant that can use tools to help users.

Available tools:
{chr(10).join(tool_descriptions)}

Instructions:
1. Analyze the user's request carefully
2. Determine if any tools are needed to fulfill the request
3. If tools are needed, call the appropriate tool(s) with correct parameters
4. If no tools are needed, respond directly to the user
5. You can call multiple tools if necessary
6. Always provide the exact parameter names and values as expected by the tools

When calling tools, ensure all required parameters are provided and "
            "values are of the correct type."""

        return prompt

    def _parse_model_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse model response to extract tool calls"""
        import json

        tool_calls = []

        # Try to parse as JSON first
        try:
            # Try to parse the entire response as JSON
            parsed = json.loads(response.strip())

            # Handle single tool call
            if isinstance(parsed, dict):
                if "tool" in parsed and "args" in parsed:
                    tool_calls.append(parsed)
                elif "function_call" in parsed:
                    func_call = parsed["function_call"]
                    tool_calls.append(
                        {
                            "tool": func_call["name"],
                            "args": func_call.get("arguments", {}),
                        }
                    )

            # Handle multiple tool calls
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "tool" in item and "args" in item:
                        tool_calls.append(item)
        except (json.JSONDecodeError, KeyError):
            # If direct parsing fails, try to extract JSON from the response
            try:
                # Look for JSON in the response
                start = response.find("{")
                end = response.rfind("}") + 1

                if start != -1 and end > start:
                    json_str = response[start:end]
                    parsed = json.loads(json_str)

                    # Handle single tool call
                    if isinstance(parsed, dict):
                        if "tool" in parsed and "args" in parsed:
                            tool_calls.append(parsed)
                        elif "function_call" in parsed:
                            func_call = parsed["function_call"]
                            tool_calls.append(
                                {
                                    "tool": func_call["name"],
                                    "args": func_call.get("arguments", {}),
                                }
                            )

                    # Handle multiple tool calls
                    elif isinstance(parsed, list):
                        for item in parsed:
                            if (
                                isinstance(item, dict)
                                and "tool" in item
                                and "args" in item
                            ):
                                tool_calls.append(item)
            except (json.JSONDecodeError, KeyError):
                pass

        # If no JSON found, try to extract tool calls from text
        if not tool_calls:
            tool_calls = self._extract_tool_calls_from_text(response)

        return tool_calls

    def _extract_tool_calls_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract tool calls from text response"""
        tool_calls = []

        # Simple pattern matching for tool calls
        lines = text.split("\n")
        current_tool = None
        current_args = {}

        for line in lines:
            line = line.strip()

            # Look for tool name patterns
            if line.startswith("Tool:") or line.startswith("Function:"):
                if current_tool:
                    tool_calls.append({"tool": current_tool, "args": current_args})

                current_tool = line.split(":", 1)[1].strip()
                current_args = {}

            # Look for parameter patterns
            elif "=" in line and current_tool:
                try:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Try to parse value as appropriate type
                    if value.lower() in ("true", "false"):
                        current_args[key] = value.lower() == "true"
                    elif value.isdigit():
                        current_args[key] = int(value)
                    elif value.replace(".", "").isdigit():
                        current_args[key] = float(value)
                    else:
                        current_args[key] = value
                except Exception:
                    pass

        # Add the last tool call
        if current_tool:
            tool_calls.append({"tool": current_tool, "args": current_args})

        return tool_calls


class QwenPlanner(BasePlanner):
    """Qwen-style function calling planner"""

    def __init__(self, provider):
        self.provider = provider

    def plan(self, input_data: AgentInput, available_tools: List[Any]) -> PlanResult:
        """
        Use Qwen-style function calling to plan tool execution

        Args:
            input_data: Agent input containing query and context
            available_tools: List of available tools

        Returns:
            PlanResult with model-decided tools and parameters
        """
        # Similar to OpenAIPlanner but with Qwen-specific adaptations
        # This is a placeholder implementation
        query = input_data.query
        tools = input_data.tools if input_data.tools else []

        # Filter tools if specified
        if tools:
            available_tools = [tool for tool in available_tools if tool.name in tools]

        # For now, use simple keyword matching as fallback
        tool_calls = self._simple_keyword_matching(query, available_tools)

        tool_names = [call["tool"] for call in tool_calls]
        plan = f"Qwen planner decided to call tools: {tool_names}"

        return PlanResult(
            plan=plan,
            tools_to_use=[call["tool"] for call in tool_calls],
            parameters={call["tool"]: call["args"] for call in tool_calls},
            metadata={"planner_type": "QwenPlanner", "tool_calls": tool_calls},
        )

    def _simple_keyword_matching(
        self, query: str, tools: List[Any]
    ) -> List[Dict[str, Any]]:
        """Simple keyword-based tool matching as fallback"""
        tool_calls = []
        query_lower = query.lower()

        # Score each tool based on how well it matches the query
        tool_scores = []

        for tool in tools:
            tool_name_lower = tool.name.lower()
            tool_name_clean = tool_name_lower.replace("_", " ")
            tool_parts = tool_name_clean.split()

            # Calculate match score
            score = 0
            matched_parts = 0

            for part in tool_parts:
                if part in query_lower:
                    score += len(part)  # Longer matches get higher scores
                    matched_parts += 1

            # Bonus for exact tool name match
            if tool_name_lower in query_lower:
                score += 100

            # Only consider tools with at least one meaningful match
            if matched_parts > 0:
                tool_scores.append((tool, score))

        # Sort by score (highest first) and take the best match
        if tool_scores:
            tool_scores.sort(key=lambda x: x[1], reverse=True)
            best_tool, best_score = tool_scores[0]

            # Only add if the score is reasonable (at least 3 characters matched)
            if best_score >= 3:
                tool_calls.append({"tool": best_tool.name, "args": {}})

        return tool_calls


class RuleBasedPlanner(BasePlanner):
    """Rule-based planner using predefined patterns"""

    def __init__(self, rules: Dict[str, Dict[str, Any]] = None):
        self.rules = rules or {}

    def plan(self, input_data: AgentInput, available_tools: List[Any]) -> PlanResult:
        """
        Use rule-based matching to plan tool execution

        Args:
            input_data: Agent input containing query and context
            available_tools: List of available tools

        Returns:
            PlanResult with rule-matched tools and parameters
        """
        query = input_data.query.lower()
        tool_calls = []

        # Apply rules
        for pattern, rule in self.rules.items():
            if pattern in query:
                tool_name = rule.get("tool")
                args = rule.get("args", {})

                # Check if tool is available
                if any(tool.name == tool_name for tool in available_tools):
                    tool_calls.append({"tool": tool_name, "args": args})

        plan = (
            f"Rule-based planner matched tools: {[call['tool'] for call in tool_calls]}"
        )

        return PlanResult(
            plan=plan,
            tools_to_use=[call["tool"] for call in tool_calls],
            parameters={call["tool"]: call["args"] for call in tool_calls},
            metadata={"planner_type": "RuleBasedPlanner", "tool_calls": tool_calls},
        )
