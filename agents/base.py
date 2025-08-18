"""
Base Agent implementation
"""
import warnings
import copy
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


class _ConditionalTransition:
    """Helper class for conditional transitions"""
    def __init__(self, src: 'BaseAgent', action: str):
        self.src = src
        self.action = action
    
    def __rshift__(self, target: 'BaseAgent') -> 'BaseAgent':
        return self.src.next(target, self.action)


class BaseAgent(ABC):
    """Abstract base class for all agents with flow control capabilities"""

    def __init__(self, name: str = "BaseAgent"):
        self.name = name
        self.successors: Dict[str, 'BaseAgent'] = {}
        self.params: Dict[str, Any] = {}

    def set_params(self, params: Dict[str, Any]) -> None:
        """Set parameters for the agent"""
        self.params = params

    def next(self, node: 'BaseAgent', action: str = "default") -> 'BaseAgent':
        """Set the next node in the flow"""
        if action in self.successors:
            warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action] = node
        return node

    def get_next_node(self, action: Optional[str] = None) -> Optional['BaseAgent']:
        """Get the next node based on action"""
        next_node = self.successors.get(action or "default")
        if not next_node and self.successors:
            warnings.warn(f"Flow ends: '{action}' not found in {list(self.successors.keys())}")
        return next_node

    def __rshift__(self, other: 'BaseAgent') -> 'BaseAgent':
        """Operator for setting default successor"""
        return self.next(other)

    def __sub__(self, action: str) -> _ConditionalTransition:
        """Operator for creating conditional transitions"""
        if isinstance(action, str):
            return _ConditionalTransition(self, action)
        raise TypeError("Action must be a string")

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

    async def post(self, context: Any, plan_result: PlanResult, exec_result: AgentOutput) -> AgentOutput:
        """
        Post-processing after execution
        
        Args:
            context: Context store or shared data
            plan_result: Result from planning phase
            exec_result: Result from execution phase
            
        Returns:
            Processed AgentOutput
        """
        return exec_result

    async def _run_async(self, context: Any, input_data: AgentInput) -> AgentOutput:
        """
        Internal async execution method (equivalent to BaseNode._run)
        
        Args:
            context: Context store or shared data
            input_data: Agent input data
            
        Returns:
            AgentOutput with execution results
        """
        plan_result = self.plan(input_data)
        exec_result = await self.run(plan_result)
        return await self.post(context, plan_result, exec_result)

    async def run_async(self, context: Any, input_data: AgentInput) -> AgentOutput:
        """
        Async execution method for single node (equivalent to BaseNode.run_async)
        
        Args:
            context: Context store or shared data
            input_data: Agent input data
            
        Returns:
            AgentOutput with execution results
        """
        if self.successors:
            warnings.warn("Node won't run successors. Use AsyncFlow.")
        return await self._run_async(context, input_data)

    # Backward compatibility methods
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Complete execution flow: plan then run (backward compatibility)

        Args:
            input_data: Agent input data

        Returns:
            AgentOutput with final results
        """
        plan_result = self.plan(input_data)
        return await self.run(plan_result)


class AsyncFlow(BaseAgent):
    """Flow control for orchestrating multiple agents"""

    def __init__(self, name: str = "AsyncFlow", start_node: Optional[BaseAgent] = None):
        super().__init__(name)
        self.start_node = start_node

    def start(self, start_node: BaseAgent) -> BaseAgent:
        """Set the start node of the flow"""
        self.start_node = start_node
        return start_node

    async def _orch_async(self, context: Any, input_data: AgentInput, params: Optional[Dict[str, Any]] = None) -> AgentOutput:
        """
        Orchestrate the flow execution (equivalent to AsyncFlow._orch_async)
        
        Args:
            context: Context store or shared data
            input_data: Agent input data
            params: Additional parameters
            
        Returns:
            Final AgentOutput from the flow
        """
        if not self.start_node:
            raise RuntimeError("No start node set for flow")
            
        current = copy.copy(self.start_node)
        current_params = params or {**self.params}
        last_action = None
        
        # Set flow parameters in context if it's a ContextStore
        if hasattr(context, 'set_flow_params'):
            context.set_flow_params(current_params)
        
        while current:
            current.set_params(current_params)
            result = await current._run_async(context, input_data)
            
            # Record flow step in context if it's a ContextStore
            if hasattr(context, 'record_flow_step'):
                context.record_flow_step(
                    agent_name=current.name,
                    action=last_action or "default",
                    result=result,
                    metadata=result.metadata
                )
            
            # Determine next action based on result
            # This is a simple implementation - you might want to customize this logic
            if hasattr(result, 'metadata') and result.metadata and 'action' in result.metadata:
                last_action = result.metadata['action']
            else:
                last_action = "default"
            
            current = copy.copy(current.get_next_node(last_action))
        
        return result

    async def _run_async(self, context: Any, input_data: AgentInput) -> AgentOutput:
        """
        Internal async execution method for flow
        
        Args:
            context: Context store or shared data
            input_data: Agent input data
            
        Returns:
            AgentOutput with execution results
        """
        plan_result = self.plan(input_data)
        exec_result = await self._orch_async(context, input_data)
        return await self.post(context, plan_result, exec_result)

    async def post(self, context: Any, plan_result: PlanResult, exec_result: AgentOutput) -> AgentOutput:
        """Post-processing for flow execution"""
        return exec_result

    # Implement abstract methods for flow
    def plan(self, input_data: AgentInput) -> PlanResult:
        """Plan for flow execution"""
        return PlanResult(
            plan=f"Execute flow starting with {self.start_node.name if self.start_node else 'undefined'}",
            tools_to_use=[],
            parameters={},
            metadata={"flow": True, "start_node": self.start_node.name if self.start_node else None}
        )

    async def run(self, plan_result: PlanResult) -> AgentOutput:
        """Run the flow (this is handled by _orch_async)"""
        # This method is not used in flow execution, but required by abstract base
        raise RuntimeError("Use run_async for flow execution")


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
