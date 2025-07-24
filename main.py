import typer
from cli import chat

app = typer.Typer()
app.add_typer(chat.app, name="chat")

if __name__ == "__main__":
    app()
