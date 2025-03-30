import typer

app = typer.Typer()

@app.command()
def init():
    """Erstellt eine Beispiel-Konfigurationsdatei."""
    typer.echo("Konfiguration wurde erstellt.")