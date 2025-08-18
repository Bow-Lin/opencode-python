# Agent Flow Control

This document describes the new flow control functionality that allows you to orchestrate multiple agents in a workflow-like manner.

## Overview

The flow control system is inspired by the BaseNode pattern and provides:

- **Single Agent Execution**: Backward compatible with existing agents
- **Multi-Agent Flows**: Orchestrate multiple agents in sequence
- **Conditional Branching**: Route execution based on agent results
- **Context Tracking**: Maintain state across flow execution
- **Async Support**: Full asynchronous execution support

## Core Concepts

### BaseAgent Enhancements

The `BaseAgent` class has been enhanced with flow control capabilities:

```python
class BaseAgent(ABC):
    def __init__(self, name: str = "BaseAgent"):
        self.name = name
        self.successors: Dict[str, 'BaseAgent'] = {}  # Flow control
        self.params: Dict[str, Any] = {}              # Parameters
    
    # Flow control methods
    def next(self, node: 'BaseAgent', action: str = "default") -> 'BaseAgent'
    def get_next_node(self, action: Optional[str] = None) -> Optional['BaseAgent']
    
    # Operator overloads for fluent API
    def __rshift__(self, other: 'BaseAgent') -> 'BaseAgent'  # Default successor
    def __sub__(self, action: str) -> _ConditionalTransition  # Conditional successor
```

### AsyncFlow

The `AsyncFlow` class orchestrates multiple agents:

```python
class AsyncFlow(BaseAgent):
    def __init__(self, name: str = "AsyncFlow", start_node: Optional[BaseAgent] = None):
        super().__init__(name)
        self.start_node = start_node
    
    def start(self, start_node: BaseAgent) -> BaseAgent
    async def run_async(self, context: Any, input_data: AgentInput) -> AgentOutput
```

### ContextStore Enhancements

The `ContextStore` has been enhanced to track flow execution:

```python
@dataclass
class ContextStore:
    # Existing fields...
    
    # New flow-related fields
    current_agent: Optional[str] = None
    flow_history: List[FlowRecord] = field(default_factory=list)
    branch_decisions: List[str] = field(default_factory=list)
    flow_params: Dict[str, Any] = field(default_factory=dict)
    
    # New methods
    def record_flow_step(self, agent_name: str, action: str, result: Any, metadata: Optional[Dict[str, Any]] = None)
    def get_flow_summary(self) -> Dict[str, Any]
    def reset_flow(self) -> None
```

## Usage Examples

### Single Agent (Backward Compatible)

```python
from agents.base import BaseAgent, AgentInput
from agents.context import ContextStore

class MyAgent(BaseAgent):
    def plan(self, input_data: AgentInput) -> PlanResult:
        # Your planning logic
        pass
    
    async def run(self, plan_result: PlanResult) -> AgentOutput:
        # Your execution logic
        pass

# Use existing API
agent = MyAgent("MyAgent")
input_data = AgentInput(query="Hello world")
result = await agent.execute(input_data)
```

### Simple Flow

```python
from agents.base import AsyncFlow, AgentInput
from agents.context import ContextStore

# Create agents
agent1 = MyAgent("Agent1")
agent2 = MyAgent("Agent2")
agent3 = MyAgent("Agent3")

# Create flow
flow = AsyncFlow("MyFlow")
flow.start(agent1)

# Define flow: agent1 -> agent2 -> agent3
agent1 >> agent2 >> agent3

# Execute flow
context = ContextStore()
input_data = AgentInput(query="Process this")
result = await flow.run_async(context, input_data)
```

### Conditional Flow

```python
# Create agents
analysis_agent = AnalysisAgent("Analysis")
simple_agent = SimpleAgent("Simple")
report_agent = ReportAgent("Report")

# Create flow
flow = AsyncFlow("ConditionalFlow")
flow.start(analysis_agent)

# Define conditional paths
analysis_agent >> simple_agent                    # Default path
analysis_agent - "complex" >> report_agent        # Complex analysis path
analysis_agent - "simple" >> simple_agent         # Simple analysis path

# Execute flow
context = ContextStore()
input_data = AgentInput(query="This is a complex analysis")
result = await flow.run_async(context, input_data)
```

### Flow with Parameters

```python
# Set flow parameters
flow.set_params({"priority": "high", "timeout": 30})

# Set agent-specific parameters
agent1.set_params({"retry_count": 3})
agent2.set_params({"batch_size": 100})

# Execute with context
context = ContextStore()
context.set_flow_params({"user_id": "123"})
result = await flow.run_async(context, input_data)
```

## Action Determination

The flow system determines the next action based on the agent's output metadata:

```python
async def run(self, plan_result: PlanResult) -> AgentOutput:
    # Your execution logic...
    
    return AgentOutput(
        result="Task completed",
        metadata={
            "action": "success",  # This determines the next branch
            "status": "completed"
        }
    )
```

## Context Tracking

The `ContextStore` automatically tracks flow execution:

```python
# After flow execution
summary = context.get_flow_summary()
print(f"Total steps: {summary['total_steps']}")
print(f"Current agent: {summary['current_agent']}")
print(f"Branch decisions: {summary['branch_decisions']}")

# Access individual steps
for step in context.flow_history:
    print(f"{step.agent_name}: {step.action} -> {step.result}")
```

## Best Practices

### 1. Action Naming

Use consistent action names across your agents:

```python
# Recommended action names
"success"    # Successful completion
"failure"    # Failed execution
"retry"      # Need to retry
"continue"   # Continue to next step
"complete"   # Final completion
"error"      # Error condition
```

### 2. Metadata Structure

Structure your agent metadata consistently:

```python
return AgentOutput(
    result="Task result",
    metadata={
        "action": "success",           # Required for flow control
        "status": "completed",         # Status information
        "error_code": None,           # Error information if applicable
        "performance_metrics": {...}   # Additional metrics
    }
)
```

### 3. Error Handling

Implement proper error handling in your agents:

```python
async def run(self, plan_result: PlanResult) -> AgentOutput:
    try:
        # Your execution logic
        result = await self.perform_task()
        return AgentOutput(
            result=result,
            metadata={"action": "success"}
        )
    except Exception as e:
        return AgentOutput(
            result=f"Error: {str(e)}",
            metadata={"action": "failure", "error": str(e)}
        )
```

### 4. Flow Design

Design flows with clear entry and exit points:

```python
# Good: Clear flow structure
flow.start(entry_agent)
entry_agent >> processing_agent >> exit_agent

# Avoid: Complex nested conditions without clear paths
# This can lead to infinite loops or dead ends
```

## Migration Guide

### From Single Agent to Flow

1. **Keep existing code unchanged** - Single agent execution still works
2. **Add flow control gradually** - Start with simple linear flows
3. **Enhance agents with metadata** - Add action metadata to enable branching
4. **Use ContextStore** - Replace simple context with enhanced ContextStore

### Example Migration

```python
# Before: Single agent
agent = MyAgent()
result = await agent.execute(input_data)

# After: Flow with same agent
flow = AsyncFlow()
flow.start(agent)
context = ContextStore()
result = await flow.run_async(context, input_data)
```

## Advanced Features

### Custom Action Logic

You can customize how actions are determined by overriding the flow logic:

```python
class CustomFlow(AsyncFlow):
    async def _orch_async(self, context: Any, input_data: AgentInput, params: Optional[Dict[str, Any]] = None) -> AgentOutput:
        # Custom orchestration logic
        current = copy.copy(self.start_node)
        
        while current:
            result = await current._run_async(context, input_data)
            
            # Custom action determination
            if result.result == "success":
                action = "success"
            elif "error" in str(result.result):
                action = "failure"
            else:
                action = "continue"
            
            current = copy.copy(current.get_next_node(action))
        
        return result
```

### Flow Composition

You can compose flows by using flows as nodes:

```python
# Create sub-flows
sub_flow1 = AsyncFlow("SubFlow1")
sub_flow1.start(agent1) >> agent2

sub_flow2 = AsyncFlow("SubFlow2")
sub_flow2.start(agent3) >> agent4

# Compose main flow
main_flow = AsyncFlow("MainFlow")
main_flow.start(sub_flow1) >> sub_flow2
```

This provides a powerful way to build complex workflows from simpler components.
