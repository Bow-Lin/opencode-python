#!/usr/bin/env python3
"""
Enhanced CLI with SimpleToolAgent integration
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import typer

from agents import AgentInput, SimpleToolAgent
from providers import create_default_manager
from tool_registry.registry import list_tools_with_info
from tools.file_tools import create_dir, list_dir, read_file, write_file
from tools.math_tools import add, divide, multiply, subtract

app = typer.Typer()


@dataclass
class AgentChatContext:
    """Context for agent chat commands"""

    manager: Any
    agent: SimpleToolAgent
    available_providers: list
    current_system_prompt: Optional[str] = None


class AgentCommandHandler:
    """Enhanced command handler with agent integration"""

    def __init__(self, context: AgentChatContext):
        self.context = context
        self.commands: Dict[str, Callable] = {
            "/quit": self._handle_quit,
            "/exit": self._handle_quit,
            "/bye": self._handle_quit,
            "/help": self._handle_help,
            "/switch": self._handle_switch,
            "/info": self._handle_info,
            "/system": self._handle_system,
            "/clear": self._handle_clear,
            "/tools": self._handle_tools,
            "/agent": self._handle_agent,
            "/math": self._handle_math,
            "/file": self._handle_file,
        }

    def handle_command(self, user_input: str) -> bool:
        """Handle user command, return True if should continue, False to quit"""
        command = user_input.split()
        cmd = command[0].lower()

        if cmd in self.commands:
            return self.commands[cmd](command)
        else:
            typer.echo("Unknown command. Type /help for available commands.")
            return True

    def _handle_quit(self, command: list) -> bool:
        """Handle quit commands"""
        typer.echo("Goodbye!")
        return False

    def _handle_help(self, command: list) -> bool:
        """Handle help command"""
        typer.echo("Commands:")
        typer.echo("  /help - Show this help")
        typer.echo("  /switch <provider> - Switch to another provider")
        typer.echo("  /info - Show current provider info")
        typer.echo("  /system <prompt> - Set system prompt")
        typer.echo("  /clear - Clear system prompt")
        typer.echo("  /tools - List available tools")
        typer.echo("  /agent <query> - Use agent to handle query with tools")
        typer.echo("  /math <operation> <args> - Execute math operation")
        typer.echo("  /file <operation> <args> - Execute file operation")
        typer.echo("  /quit, /exit, /bye - Exit chat")
        return True

    def _handle_switch(self, command: list) -> bool:
        """Handle switch provider command"""
        if len(command) <= 1:
            typer.echo("Usage: /switch <provider>")
            return True

        new_provider = command[1]
        if new_provider in self.context.available_providers:
            self.context.manager.set_default_provider(new_provider)
            current_provider = self.context.manager.get_provider()
            provider_info = current_provider.get_model_info()
            typer.echo(f"Switched to provider: {new_provider}")
            typer.echo(f"Model: {provider_info.get('model', 'Unknown')}")
        else:
            typer.echo(f"Provider '{new_provider}' not available.")
            typer.echo(f"Available: {', '.join(self.context.available_providers)}")
        return True

    def _handle_info(self, command: list) -> bool:
        """Handle info command"""
        current_provider = self.context.manager.get_provider()
        provider_info = current_provider.get_model_info()
        typer.echo(f"Current provider: {self.context.manager.default_provider}")
        typer.echo(f"Model: {provider_info.get('model', 'Unknown')}")
        if self.context.current_system_prompt:
            typer.echo(f"System prompt: {self.context.current_system_prompt}")
        return True

    def _handle_system(self, command: list) -> bool:
        """Handle system prompt command"""
        if len(command) <= 1:
            typer.echo("Usage: /system <prompt>")
            return True

        prompt = " ".join(command[1:])
        self.context.current_system_prompt = prompt
        typer.echo(f"System prompt set: {prompt}")
        return True

    def _handle_clear(self, command: list) -> bool:
        """Handle clear system prompt command"""
        self.context.current_system_prompt = None
        typer.echo("System prompt cleared.")
        return True

    def _handle_tools(self, command: list) -> bool:
        """Handle tools command"""
        tools_info = list_tools_with_info()
        typer.echo("Available tools:")
        for tool_info in tools_info:
            desc = tool_info.description or "No description"
            typer.echo(f"  {tool_info.name}: {desc}")
        return True

    def _handle_agent(self, command: list) -> bool:
        """Handle agent command"""
        if len(command) <= 1:
            typer.echo("Usage: /agent <query>")
            return True

        query = " ".join(command[1:])
        try:
            typer.echo("Agent processing...")

            # Create agent input
            input_data = AgentInput(query=query)

            # Use agent to plan and execute
            plan_result = self.context.agent.plan(input_data)
            output = self.context.agent.run(plan_result)

            # Display results
            typer.echo(f"Agent: {output.result}")

        except Exception as e:
            typer.echo(f"Agent error: {e}")
            # Fallback to regular provider
            try:
                response = self.context.manager.generate(
                    user_query=query, prompt=self.context.current_system_prompt
                )
                typer.echo(f"Assistant (fallback): {response}")
            except Exception as fallback_error:
                typer.echo(f"Error generating response: {fallback_error}")
        return True

    def _handle_math(self, command: list) -> bool:
        """Handle math command"""
        if len(command) < 3:
            typer.echo("Usage: /math <operation> <arg1> [arg2]")
            typer.echo("Operations: add, subtract, multiply, divide")
            return True

        operation = command[1].lower()
        try:
            arg1 = float(command[2])
            arg2 = float(command[3]) if len(command) > 3 else 0

            if operation == "add":
                result = add(arg1, arg2)
            elif operation == "subtract":
                result = subtract(arg1, arg2)
            elif operation == "multiply":
                result = multiply(arg1, arg2)
            elif operation == "divide":
                if arg2 == 0:
                    typer.echo("Error: Division by zero")
                    return True
                result = divide(arg1, arg2)
            else:
                typer.echo(f"Unknown operation: {operation}")
                return True

            typer.echo(f"Result: {result}")
        except ValueError:
            typer.echo("Error: Invalid number format")
        except Exception as e:
            typer.echo(f"Error: {e}")
        return True

    def _handle_file(self, command: list) -> bool:
        """Handle file command"""
        if len(command) < 3:
            typer.echo("Usage: /file <operation> <path> [content]")
            typer.echo("Operations: read, write, list, create")
            return True

        operation = command[1].lower()
        path = command[2]

        try:
            if operation == "read":
                content = read_file(path)
                typer.echo(f"File content:\n{content}")
            elif operation == "write":
                if len(command) < 4:
                    typer.echo("Usage: /file write <path> <content>")
                    return True
                content = " ".join(command[3:])
                write_file(path, content)
                typer.echo(f"File written: {path}")
            elif operation == "list":
                items = list_dir(path)
                typer.echo(f"Directory contents:\n{items}")
            elif operation == "create":
                create_dir(path)
                typer.echo(f"Directory created: {path}")
            else:
                typer.echo(f"Unknown operation: {operation}")
        except Exception as e:
            typer.echo(f"Error: {e}")
        return True


def start_chat(
    provider: str = typer.Option(
        None, "--provider", "-p", help="Specify provider to use"
    ),
    system_prompt: str = typer.Option(
        None, "--system-prompt", "-s", help="Set system prompt"
    ),
    agent_mode: bool = typer.Option(
        True, "--agent", "-a", help="Enable agent mode for tool usage"
    ),
):
    """Start the enhanced chat interface with agent support."""
    typer.echo("Welcome to OpenCode Agent (Python version)!")

    # Initialize provider manager
    manager = create_default_manager()
    available_providers = manager.get_available_providers()

    if not available_providers:
        typer.echo("No model providers are available.")
        typer.echo("Please ensure you have either:")
        typer.echo("- Ollama running locally")
        typer.echo("- OpenAI API key set in OPENAI_API_KEY environment variable")
        typer.echo("- DashScope API key set in DASHSCOPE_API_KEY environment variable")
        return

    typer.echo(f"Available providers: {', '.join(available_providers)}")

    # Set provider
    if provider:
        if provider not in available_providers:
            typer.echo(f"Provider '{provider}' is not available.")
            typer.echo(f"Available providers: {', '.join(available_providers)}")
            return
        manager.set_default_provider(provider)
    else:
        manager.set_default_provider(available_providers[0])

    current_provider = manager.get_provider()
    provider_info = current_provider.get_model_info()

    typer.echo(f"Using provider: {manager.default_provider}")
    typer.echo(f"Model: {provider_info.get('model', 'Unknown')}")
    if system_prompt:
        typer.echo(f"System prompt: {system_prompt}")

    # Initialize agent
    agent = SimpleToolAgent()
    typer.echo(f"Agent initialized: {type(agent).__name__}")

    typer.echo("\nCommands:")
    typer.echo("  /help - Show this help")
    typer.echo("  /switch <provider> - Switch to another provider")
    typer.echo("  /info - Show current provider info")
    typer.echo("  /system <prompt> - Set system prompt")
    typer.echo("  /clear - Clear system prompt")
    typer.echo("  /tools - List available tools")
    typer.echo("  /agent <query> - Use agent to handle query with tools")
    typer.echo("  /math <operation> <args> - Execute math operation")
    typer.echo("  /file <operation> <args> - Execute file operation")
    typer.echo("  /quit, /exit, /bye - Exit chat")
    typer.echo()
    typer.echo("Agent mode: Type natural language queries and the agent will")
    typer.echo("automatically determine which tools to use!")
    typer.echo()

    # Initialize chat context and command handler
    context = AgentChatContext(
        manager=manager,
        agent=agent,
        available_providers=available_providers,
        current_system_prompt=system_prompt,
    )
    command_handler = AgentCommandHandler(context)

    # Chat loop
    while True:
        try:
            user_input = typer.prompt("You")

            # Handle commands
            if user_input.startswith("/"):
                should_continue = command_handler.handle_command(user_input)
                if not should_continue:
                    break
                continue

            # Agent mode: Use agent to handle natural language queries
            if agent_mode:
                try:
                    typer.echo("Agent processing...")

                    # Create agent input
                    input_data = AgentInput(query=user_input)

                    # Use agent to plan and execute
                    plan_result = agent.plan(input_data)
                    output = agent.run(plan_result)

                    # Display results
                    typer.echo(f"Assistant: {output.result}")

                except Exception as e:
                    typer.echo(f"Agent error: {e}")
                    # Fallback to regular provider
                    try:
                        response = manager.generate(
                            user_query=user_input, prompt=context.current_system_prompt
                        )
                        typer.echo(f"Assistant (fallback): {response}")
                    except Exception as fallback_error:
                        typer.echo(f"Error generating response: {fallback_error}")
            else:
                # Regular mode: Use provider directly
                try:
                    response = manager.generate(
                        user_query=user_input, prompt=context.current_system_prompt
                    )
                    typer.echo(f"Assistant: {response}")
                except Exception as e:
                    typer.echo(f"Error generating response: {e}")

        except KeyboardInterrupt:
            typer.echo("\nGoodbye!")
            break
        except Exception as e:
            typer.echo(f"Error: {e}")


@app.command()
def start(
    provider: str = typer.Option(
        None, "--provider", "-p", help="Specify provider to use"
    ),
    system_prompt: str = typer.Option(
        None, "--system-prompt", "-s", help="Set system prompt"
    ),
    agent_mode: bool = typer.Option(
        True, "--agent", "-a", help="Enable agent mode for tool usage"
    ),
):
    """Start the enhanced chat interface with agent support."""
    start_chat(provider=provider, system_prompt=system_prompt, agent_mode=agent_mode)


# Default command when no subcommand is provided
@app.callback()
def main(
    provider: str = typer.Option(
        None, "--provider", "-p", help="Specify provider to use"
    ),
    system_prompt: str = typer.Option(
        None, "--system-prompt", "-s", help="Set system prompt"
    ),
    agent_mode: bool = typer.Option(
        True, "--agent", "-a", help="Enable agent mode for tool usage"
    ),
):
    """Enhanced CLI with SimpleToolAgent integration"""
    start_chat(provider=provider, system_prompt=system_prompt, agent_mode=agent_mode)


if __name__ == "__main__":
    app()
