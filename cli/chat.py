import typer

app = typer.Typer()


@app.command()
def start():
    typer.echo("Welcome to OpenCode (Python version)!")
