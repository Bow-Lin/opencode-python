"""
File Agent - Specialized agent for file operations
"""
import json
import re
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentInput, AgentOutput, PlanResult
from providers.manager import create_default_manager
from tools import LSTool, GrepTool, GlobTool


class FileAgent(BaseAgent):
    """Agent specialized for file operations using ls, grep, and glob tools"""

    def __init__(self, name: str = "FileAgent"):
        super().__init__(name)
        self.ls_tool = LSTool()
        self.grep_tool = GrepTool()
        self.glob_tool = GlobTool()
        self.provider_manager = create_default_manager()

        # Get available provider for intent recognition
        available_providers = self.provider_manager.get_available_providers()
        if available_providers:
            self.provider = self.provider_manager.get_provider(available_providers[0])
        else:
            self.provider = None

    def plan(self, input_data: AgentInput) -> PlanResult:
        """
        Plan the execution based on user query intent

        Args:
            input_data: Agent input containing query and context

        Returns:
            PlanResult with execution plan and tool requirements
        """
        query = input_data.query.lower()

        # Intent recognition patterns
        ls_patterns = [
            r"\b(list|show|display|explore|browse|view)\b.*\b(directory|folder|files?|contents?)\b",
            r"\b(what|what's)\b.*\b(in|inside)\b.*\b(directory|folder)\b",
            r"\b(ls|dir)\b",
            r"\b(structure|organization)\b.*\b(files?|project)\b",
        ]

        grep_patterns = [
            r"\b(search|find|grep)\b.*\b(content|text|pattern|string)\b",
            r"\b(look|look for|find)\b.*\b(in|inside|within)\b.*\b(files?)\b",
            r"\b(contains?|has|with)\b.*\b(text|content|pattern)\b",
            r"\b(search|find)\b.*\b(for|to find)\b",
        ]

        glob_patterns = [
            r"\b(find|search|locate)\b.*\b(files?)\b.*\b(by|with)\b.*\b(name|pattern|extension)\b",
            r"\b(all|every)\b.*\b(\.\w+)\b.*\b(files?)\b",
            r"\b(files?)\b.*\b(ending|with)\b.*\b(\.\w+)\b",
            r"\b(\.\w+)\b.*\b(files?)\b",
        ]

        # Check for explicit tool mentions
        if "ls" in query or any(re.search(pattern, query) for pattern in ls_patterns):
            return PlanResult(
                plan="Use ls tool to list directory contents",
                tools_to_use=["ls"],
                parameters={"path": input_data.parameters.get("path") if input_data.parameters else "."},
            )

        elif "grep" in query or any(re.search(pattern, query) for pattern in grep_patterns):
            # Extract pattern from query
            pattern = self._extract_pattern_from_query(input_data.query)
            return PlanResult(
                plan="Use grep tool to search file contents",
                tools_to_use=["grep"],
                parameters={
                    "pattern": pattern,
                    "path": input_data.parameters.get("path") if input_data.parameters else ".",
                    "include": input_data.parameters.get("include") if input_data.parameters else None,
                    "literal_text": input_data.parameters.get("literal_text", False)
                    if input_data.parameters
                    else False,
                },
            )

        elif "glob" in query or any(re.search(pattern, query) for pattern in glob_patterns):
            # Extract pattern from query
            pattern = self._extract_glob_pattern_from_query(input_data.query)
            return PlanResult(
                plan="Use glob tool to find files by pattern",
                tools_to_use=["glob"],
                parameters={
                    "pattern": pattern,
                    "path": input_data.parameters.get("path") if input_data.parameters else ".",
                },
            )

        # If no clear intent, use AI to determine the best tool
        if self.provider:
            return self._ai_plan(input_data)
        else:
            # Fallback: try ls tool for general exploration
            return PlanResult(
                plan="Use ls tool for general directory exploration",
                tools_to_use=["ls"],
                parameters={"path": input_data.parameters.get("path") if input_data.parameters else "."},
            )

    def _ai_plan(self, input_data: AgentInput) -> PlanResult:
        """Use AI to determine the best tool for the query"""
        system_prompt = """You are a file operation assistant. Based on the user's query, determine which tool to use:

Available tools:
1. ls - List directory contents and structure (use for: listing files, exploring directories)
2. grep - Search for text patterns in file contents (use for: finding text, searching content)
3. glob - Find files by name patterns or extensions (use for: finding files by name, filtering by extension)

Examples:
- "show me files" → {"tool": "ls", "plan": "List directory contents", "parameters": {"path": "."}}
- "find .py files" → {"tool": "glob", "plan": "Find Python files", "parameters": {"pattern": "*.py", "path": "."}}
- "search for error" → {"tool": "grep", "plan": "Search for error messages", "parameters": {"pattern": "error", "path": "."}}

Return ONLY a JSON object with this structure:
{
    "tool": "ls|grep|glob",
    "plan": "brief description of what to do",
    "parameters": {
        "pattern": "search pattern if needed (string)",
        "path": "directory path (string, default: '.')",
        "include": "file filter pattern (string, optional)",
        "literal_text": "use literal text matching (boolean, default: false)"
    }
}"""

        try:
            response = self.provider.generate(
                user_query=input_data.query,
                prompt=system_prompt,
                temperature=0.1,
            )

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group())
                return PlanResult(
                    plan=config.get("plan", "Execute file operation"),
                    tools_to_use=[config.get("tool", "ls")],
                    parameters=config.get("parameters", {}),
                )
        except Exception:
            pass

        # Fallback to ls tool
        return PlanResult(
            plan="Use ls tool for general directory exploration",
            tools_to_use=["ls"],
            parameters={"path": input_data.parameters.get("path") if input_data.parameters else "."},
        )

    async def run(self, plan_result: PlanResult) -> AgentOutput:
        """
        Execute the plan using the appropriate tool

        Args:
            plan_result: Result from the planning phase

        Returns:
            AgentOutput with execution results
        """
        tools_used = []
        results = []

        for tool_name in plan_result.tools_to_use:
            try:
                if tool_name == "ls":
                    response = await self.ls_tool.execute(**plan_result.parameters)
                    tools_used.append("ls")
                    results.append(f"Directory listing:\n{response.content}")

                elif tool_name == "grep":
                    response = await self.grep_tool.execute(**plan_result.parameters)
                    tools_used.append("grep")
                    results.append(f"Content search results:\n{response.content}")

                elif tool_name == "glob":
                    response = await self.glob_tool.execute(**plan_result.parameters)
                    tools_used.append("glob")
                    results.append(f"File pattern matches:\n{response.content}")

            except Exception as e:
                results.append(f"Error executing {tool_name}: {str(e)}")

        return AgentOutput(
            result="\n\n".join(results),
            plan=plan_result.plan,
            tools_used=tools_used,
            metadata={"parameters": plan_result.parameters},
        )

    def _extract_pattern_from_query(self, query: str) -> str:
        """Extract search pattern from user query"""
        # Look for quoted strings
        quoted_match = re.search(r'"([^"]+)"', query)
        if quoted_match:
            return quoted_match.group(1)

        # Look for single quoted strings
        single_quoted_match = re.search(r"'([^']+)'", query)
        if single_quoted_match:
            return single_quoted_match.group(1)

        # Look for common search patterns
        search_patterns = [
            r"\b(search|find|grep)\s+(?:for\s+)?([^\s]+)",
            r"\b(look|look for)\s+(?:for\s+)?([^\s]+)",
            r"\b(contains?|has)\s+([^\s]+)",
        ]

        for pattern in search_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(2)

        # Fallback: extract words that might be search terms
        words = query.split()
        # Skip common words
        skip_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "must",
            "shall",
        }
        search_terms = [word for word in words if word.lower() not in skip_words and len(word) > 2]

        return search_terms[0] if search_terms else ""

    def _extract_glob_pattern_from_query(self, query: str) -> str:
        """Extract glob pattern from user query"""
        # Look for file extensions
        ext_match = re.search(r"\.(\w+)\s+(?:files?)?", query, re.IGNORECASE)
        if ext_match:
            return f"*.{ext_match.group(1)}"

        # Look for quoted patterns
        quoted_match = re.search(r'"([^"]+)"', query)
        if quoted_match:
            return quoted_match.group(1)

        # Look for common file patterns
        if "python" in query.lower() or "py" in query.lower():
            return "*.py"
        elif "javascript" in query.lower() or "js" in query.lower():
            return "*.js"
        elif "typescript" in query.lower() or "ts" in query.lower():
            return "*.{ts,tsx}"
        elif "html" in query.lower():
            return "*.html"
        elif "css" in query.lower():
            return "*.css"
        elif "json" in query.lower():
            return "*.json"
        elif "yaml" in query.lower() or "yml" in query.lower():
            return "*.{yaml,yml}"

        # Fallback to all files
        return "*"

    async def execute(self, input_data: AgentInput, max_iterations: int = 3) -> AgentOutput:
        """Complete agent workflow with optional multi-step reasoning.

        This overrides :meth:`BaseAgent.execute` to introduce an iterative
        planning/execution loop. After each tool run the agent may consult the
        provider to decide whether another action is required. The loop stops
        when no follow-up query is produced or the ``max_iterations`` limit is
        reached.

        Args:
            input_data: Initial user query and parameters.
            max_iterations: Maximum planning/execution iterations.

        Returns:
            Aggregated :class:`AgentOutput` from all executed steps.
        """

        current_input = input_data
        all_results: List[str] = []
        all_tools: List[str] = []

        for _ in range(max_iterations):
            plan_result = self.plan(current_input)
            output = await self.run(plan_result)
            all_results.append(output.result)
            if output.tools_used:
                all_tools.extend(output.tools_used)

            # Determine whether we need another step
            next_query = self._determine_follow_up(current_input.query, output.result)
            if not next_query:
                break
            current_input = AgentInput(query=next_query, parameters=current_input.parameters)

        return AgentOutput(
            result="\n\n".join(all_results),
            plan=plan_result.plan if "plan_result" in locals() else None,
            tools_used=all_tools,
            metadata={"iterations": len(all_results)},
        )

    def _determine_follow_up(self, query: str, last_result: str) -> Optional[str]:
        """Use the provider (if available) to decide next action.

        The provider is expected to return a JSON payload with the structure:
        `{"next_query": "<follow up query or empty>"}`. If the provider is
        unavailable or the response cannot be parsed, `None` is returned which
        stops the execution loop.
        """

        if not self.provider:
            return None

        prompt = (
            "You are coordinating file operations. Given the user's original "
            "query and the latest tool output, decide if another action is "
            "required. Return ONLY a JSON object in the form: {\"next_query\": "
            "string|null}."
        )

        try:
            response = self.provider.generate(
                user_query=f"User query: {query}\nTool output:\n{last_result}",
                prompt=prompt,
                temperature=0.1,
            )

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group())
                return config.get("next_query")
        except Exception:
            return None

        return None
