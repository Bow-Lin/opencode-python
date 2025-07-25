from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import typer

from providers import create_default_manager

app = typer.Typer()


@dataclass
class ChatContext:
    """Context for chat commands"""

    manager: Any
    available_providers: list
    current_system_prompt: Optional[str] = None


class CommandHandler:
    """Command handler using Command pattern"""

    def __init__(self, context: ChatContext):
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
        if "base_url" in provider_info:
            typer.echo(f"Base URL: {provider_info['base_url']}")
        if self.context.current_system_prompt:
            typer.echo(f"System prompt: {self.context.current_system_prompt}")
        return True

    def _handle_system(self, command: list) -> bool:
        """Handle system prompt command"""
        if len(command) <= 1:
            typer.echo("Usage: /system <prompt>")
            return True

        self.context.current_system_prompt = " ".join(command[1:])
        typer.echo(f"System prompt set: {self.context.current_system_prompt}")
        return True

    def _handle_clear(self, command: list) -> bool:
        """Handle clear system prompt command"""
        self.context.current_system_prompt = None
        typer.echo("System prompt cleared")
        return True


@app.command()
def start(
    provider: str = typer.Option(
        None, "--provider", "-p", help="Specify provider to use"
    ),
    system_prompt: str = typer.Option(
        None, "--system-prompt", "-s", help="Set system prompt"
    ),
):
    """Start the chat interface."""
    typer.echo("Welcome to OpenCode (Python version)!")

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

    typer.echo("\nCommands:")
    typer.echo("  /help - Show this help")
    typer.echo("  /switch <provider> - Switch to another provider")
    typer.echo("  /info - Show current provider info")
    typer.echo("  /system <prompt> - Set system prompt")
    typer.echo("  /clear - Clear system prompt")
    typer.echo("  /quit, /exit, /bye - Exit chat")
    typer.echo()

    # Initialize chat context and command handler
    context = ChatContext(
        manager=manager,
        available_providers=available_providers,
        current_system_prompt=system_prompt,
    )
    command_handler = CommandHandler(context)

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

            # Generate response using provider
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
def providers():
    """List available model providers."""
    manager = create_default_manager()

    typer.echo("Registered providers:")
    for provider_name in manager.list_providers():
        provider = manager.get_provider(provider_name)
        status = "✓ Available" if provider.is_available() else "✗ Not available"
        typer.echo(f"  {provider_name}: {status}")

        if provider.is_available():
            info = provider.get_model_info()
            typer.echo(f"    Model: {info.get('model', 'Unknown')}")
            if "base_url" in info:
                typer.echo(f"    Base URL: {info['base_url']}")


@app.command()
def test(
    user_query: str = typer.Option("Hello, how are you?", "--user-query", "-q"),
    provider: str = typer.Option(None, "--provider", "-P"),
    system_prompt: str = typer.Option(None, "--system-prompt", "-s"),
):
    """Test a model provider with a user query."""
    manager = create_default_manager()

    try:
        # Get provider info for display
        if provider:
            current_provider = manager.get_provider(provider)
            provider_info = current_provider.get_model_info()
            typer.echo(f"Testing provider: {provider}")
            typer.echo(f"Model: {provider_info.get('model', 'Unknown')}")
        else:
            typer.echo(f"Testing default provider: {manager.default_provider}")

        if system_prompt:
            typer.echo(f"System prompt: {system_prompt}")

        typer.echo(f"User query: {user_query}")
        typer.echo("---")

        response = manager.generate(
            user_query=user_query, prompt=system_prompt, provider_name=provider
        )
        typer.echo(response)
    except Exception as e:
        typer.echo(f"Error: {e}")


@app.command()
def generate(
    user_query: str = typer.Argument(..., help="Input user query"),
    provider: str = typer.Option(None, "--provider", "-P", help="Specify provider"),
    system_prompt: str = typer.Option(
        None, "--system-prompt", "-s", help="System prompt"
    ),
):
    """Generate a single response using the specified provider."""
    manager = create_default_manager()

    try:
        response = manager.generate(
            user_query=user_query, prompt=system_prompt, provider_name=provider
        )
        typer.echo(response)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
