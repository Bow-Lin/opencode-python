"""
Simple test file for CodeAgent with Qwen model.
Just fill in your query and run the file.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add the project root to Python path to avoid import conflicts
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.code_agent import CodeAgent
from agents.base import AgentInput
from providers.qwen import QwenProvider
from providers.manager import ProviderManager


class SimpleCodeAgentTester:
    """Simple tester for CodeAgent with Qwen model."""
            
    def setup_method(self):
        # Initialize CodeAgent
        self.agent = CodeAgent("TestCodeAgent")
        
    async def run_query(self, user_query: str):
        """Run a single query with the agent."""
        if not self.agent:
            raise RuntimeError("Agent not setup. Call setup() first.")
            
        print(f"\n Your query: {user_query}")
        print("-" * 50)
        
        # Create agent input
        agent_input = AgentInput(query=user_query)
        
        # Plan phase
        print("Planning phase...")
        plan_result = self.agent.plan(agent_input)
        print(f"Plan: {plan_result.plan}")
        print(f"Tools to use: {plan_result.tools_to_use}")
        print(f"Parameters: {plan_result.parameters}")

        
        # Execute phase
        print("\n Execution phase...")
        output = await self.agent.run(plan_result)
        print(f"Result: {output.result}")
        print(f"Tools used: {output.tools_used}")


async def main():
    print(f"api_key: {os.getenv('DASHSCOPE_API_KEY')}")
    """Main function - just fill in your query below."""
    
    # ===========================================
    # FILL IN YOUR QUERY HERE (just one sentence)
    # ===========================================
    your_query = "Please help me diagnose the code in the file /mnt/d/work/opencode_reproduce/opencode_python/agents/runner.py"
    # ===========================================
    
    # Initialize and setup agent
    tester = SimpleCodeAgentTester()
    tester.setup_method()
    
    # Run your query
    await tester.run_query(your_query)


if __name__ == "__main__":
    asyncio.run(main())
