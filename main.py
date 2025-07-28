import typer

from cli import agent_chat, chat, tools

app = typer.Typer()


@app.command()
def agent(
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
    """Start agent chat interface"""
    agent_chat.start_chat(
        provider=provider, system_prompt=system_prompt, agent_mode=agent_mode
    )


# Add other subcommands
app.add_typer(chat.app, name="chat")
app.add_typer(tools.app, name="tools")


if __name__ == "__main__":
    app()
