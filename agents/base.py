"""
Base Agent implementation
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field
from providers.manager import create_default_manager


class AgentMode(str, Enum):
    """Agent mode enumeration"""
    SUBAGENT = "subagent"
    PRIMARY = "primary"
    ALL = "all"


class ModelInfo(BaseModel):
    """Model information structure"""
    model_id: str = Field(..., description="Model identifier")
    provider_id: str = Field(..., description="Provider identifier")


class AgentInfo(BaseModel):
    """Agent information structure equivalent to TypeScript Agent.Info"""
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    mode: AgentMode = Field(..., description="Agent mode")
    top_p: Optional[float] = Field(None, description="Top-p parameter")
    temperature: Optional[float] = Field(None, description="Temperature parameter")
    model: Optional[ModelInfo] = Field(None, description="Model configuration")
    prompt: Optional[str] = Field(None, description="Custom prompt")
    tools: Dict[str, bool] = Field(default_factory=dict, description="Available tools")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional options")


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


class AgentGenerateInput(BaseModel):
    """Input for agent generation"""
    description: str = Field(..., description="Description of the agent to generate")


class AgentGenerateOutput(BaseModel):
    """Output from agent generation"""
    identifier: str = Field(..., description="Generated agent identifier")
    when_to_use: str = Field(..., description="When to use this agent")
    system_prompt: str = Field(..., description="System prompt for the agent")


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
    async def run(self, plan_result: PlanResult) -> AgentOutput:
        """
        Execute the plan and return results

        Args:
            plan_result: Result from the planning phase

        Returns:
            AgentOutput with execution results
        """
        pass

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Complete execution flow: plan then run

        Args:
            input_data: Agent input data

        Returns:
            AgentOutput with final results
        """
        plan_result = self.plan(input_data)
        return await self.run(plan_result)


# State management for agents (equivalent to TypeScript App.state)
class AgentState:
    """State management for agents"""
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize agent state with default configurations"""
        if self._initialized:
            return
            
        # Default agent configurations (equivalent to TypeScript defaults)
        self._agents = {
            "general": AgentInfo(
                name="general",
                description="General-purpose agent for researching complex questions, searching for code, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you.",
                tools={
                    "todoread": False,
                    "todowrite": False,
                },
                options={},
                mode=AgentMode.SUBAGENT,
            ),
            "build": AgentInfo(
                name="build",
                tools={},
                options={},
                mode=AgentMode.PRIMARY,
            ),
            "plan": AgentInfo(
                name="plan",
                options={},
                tools={
                    "write": False,
                    "edit": False,
                    "patch": False,
                },
                mode=AgentMode.PRIMARY,
            ),
        }
        
        # TODO: Load configuration from config file and merge with defaults
        # This would be equivalent to the TypeScript config loading logic
        
        self._initialized = True
    
    async def get_agents(self) -> Dict[str, AgentInfo]:
        """Get all agents"""
        await self.initialize()
        return self._agents.copy()
    
    async def get_agent(self, name: str) -> Optional[AgentInfo]:
        """Get specific agent by name"""
        await self.initialize()
        return self._agents.get(name)
    
    async def add_agent(self, name: str, agent_info: AgentInfo):
        """Add or update an agent"""
        await self.initialize()
        self._agents[name] = agent_info


# Global agent state instance
_agent_state = AgentState()


# Module-level functions (equivalent to TypeScript Agent namespace)
async def get_agent(agent_name: str) -> Optional[AgentInfo]:
    """
    Get agent by name
    
    Args:
        agent_name: Name of the agent to retrieve
        
    Returns:
        AgentInfo if found, None otherwise
    """
    return await _agent_state.get_agent(agent_name)


async def list_agents() -> List[AgentInfo]:
    """
    List all available agents
    
    Returns:
        List of all agent information
    """
    agents = await _agent_state.get_agents()
    return list(agents.values())


async def generate_agent(input_data: AgentGenerateInput) -> AgentGenerateOutput:
    """
    Generate a new agent configuration based on description
    
    Args:
        input_data: Input containing description for agent generation
        
    Returns:
        Generated agent configuration
    """
    # Get default model
    provider_manager = create_default_manager()
    available_providers = provider_manager.get_available_providers()
    
    if not available_providers:
        raise RuntimeError("No model providers available for agent generation")
    
    # Use first available provider as default
    default_provider = available_providers[0]
    provider = provider_manager.get_provider(default_provider)
    
    # Get existing agents to avoid name conflicts
    existing_agents = await list_agents()
    existing_names = [agent.name for agent in existing_agents]
    
    # Generate system prompt for agent creation
    system_prompt = f"""You are an AI assistant that creates agent configurations.
    
    Create an agent configuration based on the user's request.
    
    IMPORTANT: The following identifiers already exist and must NOT be used: {', '.join(existing_names)}
    
    Return ONLY a JSON object with the following structure:
    {{
        "identifier": "unique_agent_name",
        "when_to_use": "description of when to use this agent",
        "system_prompt": "system prompt for the agent"
    }}
    
    Do not include any other text or formatting."""
    
    # Generate the agent configuration using the provider
    try:
        response = provider.generate(
            user_query=f"Create an agent configuration based on this request: \"{input_data.description}\"",
            prompt=system_prompt,
            temperature=0.3
        )
        
        # Parse the response (this is a simplified implementation)
        # In a real implementation, you'd want more robust JSON parsing
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            config_data = json.loads(json_match.group())
            return AgentGenerateOutput(
                identifier=config_data["identifier"],
                when_to_use=config_data["when_to_use"],
                system_prompt=config_data["system_prompt"]
            )
        else:
            raise ValueError("Could not parse JSON response from model")
            
    except Exception as e:
        raise RuntimeError(f"Failed to generate agent: {str(e)}")
