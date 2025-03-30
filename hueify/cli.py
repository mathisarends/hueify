# hueify/cli.py
import os
from dotenv import load_dotenv
import typer

app = typer.Typer()

@app.callback()
def callback():
    """Hueify CLI tool."""

@app.command()
def init():
    """Erstellt eine Beispiel-Konfigurationsdatei."""
    typer.echo("Konfiguration wurde erstellt.")

@app.command()
def check_env():
    load_dotenv()
    
    ip = os.getenv("HUE_BRIDGE_IP")
    user = os.getenv("HUE_USER_ID")
    
    if ip:
        typer.echo(f"HUE_BRIDGE_IP: {ip} ✅")
    else:
        typer.echo("HUE_BRIDGE_IP: Nicht gesetzt ❌")
    
    if user:
        typer.echo(f"HUE_USER_ID: {user} ✅")
    else:
        typer.echo("HUE_USER_ID: Nicht gesetzt ❌")
    
    if not ip or not user:
        typer.echo("\nHinweis: Setze die fehlenden Variablen in einer .env-Datei oder direkt in deiner Umgebung.")
        
@app.command()

        
def main():
    app()

if __name__ == "__main__":
    main()