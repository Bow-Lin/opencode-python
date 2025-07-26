"""
Tool Runner - Execute registered tools with error handling
"""
import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from tool_registry.registry import get_tool_func


class ToolExecutionResult(BaseModel):
    """Result of tool execution"""

    success: bool = Field(..., description="Whether the execution was successful")
    result: Optional[Any] = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: Optional[float] = Field(
        None, description="Execution time in seconds"
    )
    tool_name: str = Field(..., description="Name of the executed tool")
    args: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments passed to the tool"
    )

    class Config:
        arbitrary_types_allowed = True


class ToolExecutor:
    """Execute registered tools with error handling and async support"""

    def __init__(self):
        self._execution_history: List[ToolExecutionResult] = []

    def run(self, tool_name: str, args: Dict[str, Any]) -> ToolExecutionResult:
        """
        Execute a tool synchronously

        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool

        Returns:
            ToolExecutionResult with execution details
        """
        import time

        start_time = time.time()

        try:
            # Get tool function
            tool_func = get_tool_func(tool_name)
            if tool_func is None:
                execution_result = ToolExecutionResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found",
                    tool_name=tool_name,
                    args=args,
                )
                # Store in history
                self._execution_history.append(execution_result)
                return execution_result

            # Validate arguments
            validation_result = self._validate_arguments(tool_func, args)
            if not validation_result["valid"]:
                execution_result = ToolExecutionResult(
                    success=False,
                    error=f"Invalid arguments: {validation_result['error']}",
                    tool_name=tool_name,
                    args=args,
                )
                # Store in history
                self._execution_history.append(execution_result)
                return execution_result

            # Execute tool
            result = tool_func(**args)

            execution_time = time.time() - start_time

            # Create success result
            execution_result = ToolExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=tool_name,
                args=args,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution failed: {str(e)}"

            # Create error result
            execution_result = ToolExecutionResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                tool_name=tool_name,
                args=args,
            )

        # Store in history
        self._execution_history.append(execution_result)

        return execution_result

    async def run_async(
        self, tool_name: str, args: Dict[str, Any]
    ) -> ToolExecutionResult:
        """
        Execute a tool asynchronously (if supported)

        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool

        Returns:
            ToolExecutionResult with execution details
        """
        import time

        start_time = time.time()

        try:
            # Get tool function
            tool_func = get_tool_func(tool_name)
            if tool_func is None:
                execution_result = ToolExecutionResult(
                    success=False,
                    error=f"Tool '{tool_name}' not found",
                    tool_name=tool_name,
                    args=args,
                )
                # Store in history
                self._execution_history.append(execution_result)
                return execution_result

            # Validate arguments
            validation_result = self._validate_arguments(tool_func, args)
            if not validation_result["valid"]:
                execution_result = ToolExecutionResult(
                    success=False,
                    error=f"Invalid arguments: {validation_result['error']}",
                    tool_name=tool_name,
                    args=args,
                )
                # Store in history
                self._execution_history.append(execution_result)
                return execution_result

            # Check if function is async
            if asyncio.iscoroutinefunction(tool_func):
                # Execute async tool
                result = await tool_func(**args)
            else:
                # Execute sync tool in thread pool
                loop = asyncio.get_event_loop()

                # Create a wrapper function to handle keyword arguments
                def run_sync_tool():
                    return tool_func(**args)

                result = await loop.run_in_executor(None, run_sync_tool)

            execution_time = time.time() - start_time

            # Create success result
            execution_result = ToolExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=tool_name,
                args=args,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution failed: {str(e)}"

            # Create error result
            execution_result = ToolExecutionResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                tool_name=tool_name,
                args=args,
            )

        # Store in history
        self._execution_history.append(execution_result)

        return execution_result

    def run_multiple(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """
        Execute multiple tools sequentially

        Args:
            tool_calls: List of tool calls with 'tool' and 'args' keys

        Returns:
            List of ToolExecutionResult objects
        """
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})

            if tool_name:
                result = self.run(tool_name, args)
                results.append(result)
            else:
                # Invalid tool call
                result = ToolExecutionResult(
                    success=False,
                    error="Invalid tool call: missing 'tool' key",
                    tool_name="unknown",
                    args=tool_call,
                )
                results.append(result)

        return results

    async def run_multiple_async(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecutionResult]:
        """
        Execute multiple tools asynchronously

        Args:
            tool_calls: List of tool calls with 'tool' and 'args' keys

        Returns:
            List of ToolExecutionResult objects
        """
        tasks = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})

            if tool_name:
                task = self.run_async(tool_name, args)
                tasks.append(task)
            else:
                # Invalid tool call
                result = ToolExecutionResult(
                    success=False,
                    error="Invalid tool call: missing 'tool' key",
                    tool_name="unknown",
                    args=tool_call,
                )

                # Create a task that immediately returns the result
                async def return_result():
                    return result

                tasks.append(return_result())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions from gather
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(
                    ToolExecutionResult(
                        success=False,
                        error=f"Async execution failed: {str(result)}",
                        tool_name="unknown",
                        args={},
                    )
                )
            else:
                final_results.append(result)

        return final_results

    def _validate_arguments(
        self, tool_func: Callable, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate arguments against tool function signature

        Args:
            tool_func: Function to validate arguments against
            args: Arguments to validate

        Returns:
            Dict with 'valid' boolean and optional 'error' string
        """
        try:
            sig = inspect.signature(tool_func)

            # Check for required parameters
            required_params = []
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                if param.default == inspect.Parameter.empty:
                    required_params.append(param_name)

            # Check if all required parameters are provided
            missing_params = [param for param in required_params if param not in args]
            if missing_params:
                return {
                    "valid": False,
                    "error": f"Missing required parameters: {missing_params}",
                }

            # Check for unexpected parameters
            expected_params = [
                name for name, param in sig.parameters.items() if name != "self"
            ]
            unexpected_params = [
                param for param in args.keys() if param not in expected_params
            ]
            if unexpected_params:
                return {
                    "valid": False,
                    "error": f"Unexpected parameters: {unexpected_params}",
                }

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"Argument validation failed: {str(e)}"}

    def get_execution_history(self) -> List[ToolExecutionResult]:
        """
        Get execution history

        Returns:
            List of ToolExecutionResult objects
        """
        return self._execution_history.copy()

    def clear_history(self):
        """Clear execution history"""
        self._execution_history.clear()

    def get_successful_executions(self) -> List[ToolExecutionResult]:
        """
        Get only successful executions from history

        Returns:
            List of successful ToolExecutionResult objects
        """
        return [result for result in self._execution_history if result.success]

    def get_failed_executions(self) -> List[ToolExecutionResult]:
        """
        Get only failed executions from history

        Returns:
            List of failed ToolExecutionResult objects
        """
        return [result for result in self._execution_history if not result.success]

    def get_tool_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics

        Returns:
            Dict with execution statistics
        """
        if not self._execution_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0,
                "tool_usage": {},
            }

        total = len(self._execution_history)
        successful = len(self.get_successful_executions())
        failed = len(self.get_failed_executions())

        # Calculate average execution time
        execution_times = [
            result.execution_time
            for result in self._execution_history
            if result.execution_time is not None
        ]
        avg_time = (
            sum(execution_times) / len(execution_times) if execution_times else 0.0
        )

        # Calculate tool usage
        tool_usage = {}
        for result in self._execution_history:
            tool_name = result.tool_name
            if tool_name not in tool_usage:
                tool_usage[tool_name] = {"total": 0, "successful": 0, "failed": 0}

            tool_usage[tool_name]["total"] += 1
            if result.success:
                tool_usage[tool_name]["successful"] += 1
            else:
                tool_usage[tool_name]["failed"] += 1

        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": (successful / total) * 100 if total > 0 else 0.0,
            "average_execution_time": avg_time,
            "tool_usage": tool_usage,
        }


# Global executor instance
executor = ToolExecutor()


# Convenience functions
def run_tool(tool_name: str, args: Dict[str, Any]) -> ToolExecutionResult:
    """
    Execute a tool synchronously

    Args:
        tool_name: Name of the tool to execute
        args: Arguments to pass to the tool

    Returns:
        ToolExecutionResult with execution details
    """
    return executor.run(tool_name, args)


async def run_tool_async(tool_name: str, args: Dict[str, Any]) -> ToolExecutionResult:
    """
    Execute a tool asynchronously

    Args:
        tool_name: Name of the tool to execute
        args: Arguments to pass to the tool

    Returns:
        ToolExecutionResult with execution details
    """
    return await executor.run_async(tool_name, args)


def run_multiple_tools(tool_calls: List[Dict[str, Any]]) -> List[ToolExecutionResult]:
    """
    Execute multiple tools sequentially

    Args:
        tool_calls: List of tool calls with 'tool' and 'args' keys

    Returns:
        List of ToolExecutionResult objects
    """
    return executor.run_multiple(tool_calls)


async def run_multiple_tools_async(
    tool_calls: List[Dict[str, Any]]
) -> List[ToolExecutionResult]:
    """
    Execute multiple tools asynchronously

    Args:
        tool_calls: List of tool calls with 'tool' and 'args' keys

    Returns:
        List of ToolExecutionResult objects
    """
    return await executor.run_multiple_async(tool_calls)
