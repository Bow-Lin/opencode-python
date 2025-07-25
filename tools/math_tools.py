"""
Math tools module providing basic mathematical operations
"""
from typing import Union

from tool_registry.registry import register_tool


@register_tool(
    name="add",
    description="Add two or more numbers together",
    tags=["math", "arithmetic", "addition"],
    version="1.0.0",
    author="OpenCode",
    parameters=["numbers: List of numbers to add"],
    return_annotation="float",
)
def add(*numbers: Union[int, float]) -> float:
    """
    Add two or more numbers together

    Args:
        *numbers: Variable number of numbers to add

    Returns:
        Sum of all numbers

    Raises:
        ValueError: If no numbers are provided
    """
    if not numbers:
        raise ValueError("At least one number must be provided")

    return sum(numbers)


@register_tool(
    name="subtract",
    description="Subtract numbers from the first number",
    tags=["math", "arithmetic", "subtraction"],
    version="1.0.0",
    author="OpenCode",
    parameters=["numbers: List of numbers to subtract"],
    return_annotation="float",
)
def subtract(*numbers: Union[int, float]) -> float:
    """
    Subtract numbers from the first number

    Args:
        *numbers: First number is the base, subsequent numbers are subtracted

    Returns:
        Result of subtraction

    Raises:
        ValueError: If no numbers are provided
    """
    if not numbers:
        raise ValueError("At least one number must be provided")

    if len(numbers) == 1:
        return numbers[0]

    result = numbers[0]
    for num in numbers[1:]:
        result -= num

    return result


@register_tool(
    name="multiply",
    description="Multiply two or more numbers together",
    tags=["math", "arithmetic", "multiplication"],
    version="1.0.0",
    author="OpenCode",
    parameters=["numbers: List of numbers to multiply"],
    return_annotation="float",
)
def multiply(*numbers: Union[int, float]) -> float:
    """
    Multiply two or more numbers together

    Args:
        *numbers: Variable number of numbers to multiply

    Returns:
        Product of all numbers

    Raises:
        ValueError: If no numbers are provided
    """
    if not numbers:
        raise ValueError("At least one number must be provided")

    result = 1
    for num in numbers:
        result *= num

    return result


@register_tool(
    name="divide",
    description="Divide the first number by subsequent numbers",
    tags=["math", "arithmetic", "division"],
    version="1.0.0",
    author="OpenCode",
    parameters=["numbers: List of numbers to divide"],
    return_annotation="float",
)
def divide(*numbers: Union[int, float]) -> float:
    """
    Divide the first number by subsequent numbers

    Args:
        *numbers: First number is the dividend, subsequent numbers are divisors

    Returns:
        Result of division

    Raises:
        ValueError: If no numbers are provided
        ZeroDivisionError: If any divisor is zero
    """
    if not numbers:
        raise ValueError("At least one number must be provided")

    if len(numbers) == 1:
        return numbers[0]

    result = numbers[0]
    for num in numbers[1:]:
        if num == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        result /= num

    return result
