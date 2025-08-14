"""Code Agent - Specialized agent for code operations using multiple tools."""

import json
import re
from typing import List, Optional

from agents.base import BaseAgent, AgentInput, AgentOutput, PlanResult
from providers.manager import create_default_manager
from tools import GrepTool, LSTool, DiagnoseTool
from tools.patch_tool import PatchTool


class CodeAgent(BaseAgent):
    """Agent for code search, diagnostics and modifications."""

    def __init__(self, name: str = "CodeAgent"):
        super().__init__(name)
        self.patch_tool = PatchTool()
        self.grep_tool = GrepTool()
        self.ls_tool = LSTool()
        self.diagnose_tool = DiagnoseTool()
        self.provider_manager = create_default_manager()
        available_providers = self.provider_manager.get_available_providers()
        if available_providers:
            self.provider = self.provider_manager.get_provider(available_providers[0])
        else:
            self.provider = None

    def plan(self, input_data: AgentInput) -> PlanResult:
        """Plan execution based on user intent."""
        query = input_data.query.lower()
        params = input_data.parameters or {}
        print(f"provider: {self.provider}")
        if self.provider:
            return self._ai_plan(input_data)
        # Check for patch diff first
        diff = params.get("diff") or self._extract_diff_from_query(input_data.query)
        if diff:
            parameters = {
                "diff": diff,
                "root": params.get("root", "."),
                "strip": params.get("strip", 1),
                "reverse": params.get("reverse", False),
                "dry_run": params.get("dry_run", False),
                "encoding": params.get("encoding", "utf-8"),
            }
            return PlanResult(
                plan="Apply code patch to repository",
                tools_to_use=["patch"],
                parameters=parameters,
            )

        # Diagnose intent
        diagnose_patterns = [r"\b(diagnose|lint|analy[sz]e|check)\b"]
        if any(re.search(p, query) for p in diagnose_patterns):
            return PlanResult(
                plan="Run diagnostics on a file",
                tools_to_use=["diagnose"],
                parameters={"path": params.get("path", ".")},
            )

        # Grep intent
        grep_patterns = [
            r"\b(search|find|grep)\b.*\b(text|pattern|string|code)\b",
        ]
        if "grep" in query or any(re.search(p, query) for p in grep_patterns):
            pattern = self._extract_pattern_from_query(input_data.query)
            return PlanResult(
                plan="Use grep tool to search code",
                tools_to_use=["grep"],
                parameters={
                    "pattern": pattern,
                    "path": params.get("path", "."),
                    "include": params.get("include"),
                    "literal_text": params.get("literal_text", False),
                },
            )

        # LS intent
        ls_patterns = [
            r"\b(list|show|display|explore|browse|view)\b.*\b(files?|directory|folders?|contents?)\b",
            r"\b(ls|dir)\b",
        ]
        if "ls" in query or any(re.search(p, query) for p in ls_patterns):
            return PlanResult(
                plan="Use ls tool to list directory contents",
                tools_to_use=["ls"],
                parameters={"path": params.get("path", "."), "ignore": params.get("ignore")},
            )



        return PlanResult(plan="No action determined", tools_to_use=[], parameters={})

    def _ai_plan(self, input_data: AgentInput) -> PlanResult:
        """Use provider to determine tool and parameters when not explicit."""

        system_prompt = """You are a code assistant. Choose the best tool for the user's request.
        Available tools: ls, grep, patch, diagnose.Return ONLY a JSON object with this structure:
        {
          "plan": "description",
          "tools": ["ls"|"grep"|"patch"|"diagnose"],
          "parameters": { ... }
        }
        for example:
        {
          "plan": "Run diagnostics on a file",
          "tools": ["diagnose"],
          "parameters": {"path": "."}
        }
        """
        try:
            response = self.provider.generate(
                user_query=input_data.query,
                prompt=system_prompt,
                temperature=0.1,
            )
            print(f"qwen response: {response}")
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group())
                tools = config.get("tools") or config.get("tool")
                if isinstance(tools, str):
                    tools = [tools]
                return PlanResult(
                    plan=config.get("plan", "Execute code operation"),
                    tools_to_use=tools or [],
                    parameters=config.get("parameters", {}),
                )
        except Exception:
            pass

        return PlanResult(plan="No action determined", tools_to_use=[], parameters={})

    async def run(self, plan_result: PlanResult) -> AgentOutput:
        """Execute the plan using appropriate tools."""
        tools_used: List[str] = []
        results: List[str] = []

        for tool_name in plan_result.tools_to_use:
            try:
                if tool_name == "patch":
                    response = await self.patch_tool.execute(**plan_result.parameters)
                elif tool_name == "grep":
                    response = await self.grep_tool.execute(**plan_result.parameters)
                elif tool_name == "ls":
                    response = await self.ls_tool.execute(**plan_result.parameters)
                elif tool_name == "diagnose":
                    response = await self.diagnose_tool.execute(**plan_result.parameters)
                else:
                    continue
                tools_used.append(tool_name)
                results.append(response.content)
            except Exception as e:
                results.append(f"Error executing {tool_name}: {str(e)}")

        return AgentOutput(
            result="\n\n".join(results),
            plan=plan_result.plan,
            tools_used=tools_used,
            metadata={"parameters": plan_result.parameters},
        )

    def _extract_diff_from_query(self, query: str) -> Optional[str]:
        """Extract unified diff text from the query if present."""
        diff_match = re.search(r"diff --git.*", query, re.DOTALL)
        if diff_match:
            return diff_match.group(0)

        diff_match = re.search(r"--- .*\n\+\+\+ .*\n@@.*", query, re.DOTALL)
        if diff_match:
            return diff_match.group(0)

        return None

    def _extract_pattern_from_query(self, query: str) -> Optional[str]:
        """Extract search pattern from quoted text in the query."""
        match = re.search(r'"([^"]+)"', query)
        if match:
            return match.group(1)
        match = re.search(r"`([^`]+)`", query)
        if match:
            return match.group(1)
        return None