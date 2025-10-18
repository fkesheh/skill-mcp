#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "rich>=13.0.0",
# ]
# ///
"""
Example script demonstrating uv inline dependencies (PEP 723).

This script fetches data from an API and displays it beautifully.
Dependencies are automatically installed by uv when the script runs.
"""

import requests
from rich.console import Console
from rich.table import Table

console = Console()

def fetch_users():
    """Fetch sample user data from JSONPlaceholder API."""
    console.print("[bold blue]Fetching user data...[/bold blue]")
    
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    response.raise_for_status()
    
    users = response.json()
    
    # Create a nice table
    table = Table(title="User Data")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Email", style="yellow")
    table.add_column("City", style="magenta")
    
    for user in users[:5]:  # Show first 5 users
        table.add_row(
            str(user["id"]),
            user["name"],
            user["email"],
            user["address"]["city"]
        )
    
    console.print(table)
    console.print(f"\n[bold green]✓[/bold green] Successfully fetched {len(users)} users")

if __name__ == "__main__":
    try:
        fetch_users()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        exit(1)

