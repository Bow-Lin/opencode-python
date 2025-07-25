import typer

from cli import chat, tools

app = typer.Typer()
app.add_typer(chat.app, name="chat")
app.add_typer(tools.app, name="tools")

if __name__ == "__main__":
    app()
