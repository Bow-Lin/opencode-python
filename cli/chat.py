import typer

from providers import create_default_manager

app = typer.Typer()


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

    # Chat loop
    current_system_prompt = system_prompt

    while True:
        try:
            user_input = typer.prompt("You")

            # Handle commands
            if user_input.startswith("/"):
                command = user_input.split()
                cmd = command[0].lower()

                if cmd in ["/quit", "/exit", "/bye"]:
                    typer.echo("Goodbye!")
                    break
                elif cmd == "/help":
                    typer.echo("Commands:")
                    typer.echo("  /help - Show this help")
                    typer.echo("  /switch <provider> - Switch to another provider")
                    typer.echo("  /info - Show current provider info")
                    typer.echo("  /system <prompt> - Set system prompt")
                    typer.echo("  /clear - Clear system prompt")
                    typer.echo("  /quit, /exit, /bye - Exit chat")
                elif cmd == "/switch" and len(command) > 1:
                    new_provider = command[1]
                    if new_provider in available_providers:
                        manager.set_default_provider(new_provider)
                        current_provider = manager.get_provider()
                        provider_info = current_provider.get_model_info()
                        typer.echo(f"Switched to provider: {new_provider}")
                        typer.echo(f"Model: {provider_info.get('model', 'Unknown')}")
                    else:
                        typer.echo(f"Provider '{new_provider}' not available.")
                        typer.echo(f"Available: {', '.join(available_providers)}")
                elif cmd == "/info":
                    current_provider = manager.get_provider()
                    provider_info = current_provider.get_model_info()
                    typer.echo(f"Current provider: {manager.default_provider}")
                    typer.echo(f"Model: {provider_info.get('model', 'Unknown')}")
                    if "base_url" in provider_info:
                        typer.echo(f"Base URL: {provider_info['base_url']}")
                    if current_system_prompt:
                        typer.echo(f"System prompt: {current_system_prompt}")
                elif cmd == "/system" and len(command) > 1:
                    current_system_prompt = " ".join(command[1:])
                    typer.echo(f"System prompt set: {current_system_prompt}")
                elif cmd == "/clear":
                    current_system_prompt = None
                    typer.echo("System prompt cleared")
                else:
                    typer.echo("Unknown command. Type /help for available commands.")
                continue

            # Generate response using provider
            try:
                response = manager.generate(user_input, prompt=current_system_prompt)
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
    prompt: str = typer.Option("Hello, how are you?", "--prompt", "-p"),
    provider: str = typer.Option(None, "--provider", "-P"),
    system_prompt: str = typer.Option(None, "--system-prompt", "-s"),
):
    """Test a model provider with a prompt."""
    manager = create_default_manager()

    try:
        response = manager.generate(
            prompt, prompt=system_prompt, provider_name=provider
        )
        typer.echo(f"Response: {response}")
    except Exception as e:
        typer.echo(f"Error: {e}")


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Input prompt"),
    provider: str = typer.Option(None, "--provider", "-P", help="Specify provider"),
    system_prompt: str = typer.Option(
        None, "--system-prompt", "-s", help="System prompt"
    ),
):
    """Generate a single response using the specified provider."""
    manager = create_default_manager()

    try:
        response = manager.generate(
            prompt, prompt=system_prompt, provider_name=provider
        )
        typer.echo(response)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
