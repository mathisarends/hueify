# hueify/cli.py
import typer

app = typer.Typer()

@app.callback()
def callback():
    """Hueify CLI tool."""
    pass

@app.command()
def init():
    """Erstellt eine Beispiel-Konfigurationsdatei."""
    typer.echo("Konfiguration wurde erstellt.")

def main():
    app()

if __name__ == "__main__":
    main()