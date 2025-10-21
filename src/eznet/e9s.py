#!/usr/bin/env python3
"""
e9s - EZNet Terminal User Interface

A k9s-inspired network testing TUI for comprehensive network analysis.
Named e9s as an homage to k9s - the popular Kubernetes TUI.
"""

import sys
import click
from rich.console import Console

console = Console()


@click.command()
@click.version_option(version="0.2.0", prog_name="e9s")
@click.option(
    "--theme", 
    default="k9s", 
    help="UI theme (currently only 'k9s' available)",
    type=click.Choice(["k9s"])
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode for development"
)
def main(theme: str, debug: bool) -> None:
    """
    e9s - EZNet Network Testing TUI
    
    A terminal user interface for comprehensive network testing inspired by k9s.
    Provides interactive host management, real-time network scanning, and 
    detailed SSL certificate analysis.
    
    Features:
    • Interactive host management with k9s-style navigation  
    • Real-time DNS, TCP, HTTP, and ICMP testing
    • SSL/TLS certificate analysis with security grading
    • Concurrent scanning with progress indicators
    • Detailed results view with tabbed interface
    
    Navigation:
    • j/k or ↑/↓  - Navigate hosts
    • a           - Add new host  
    • d           - Delete host
    • r           - Refresh selected host
    • s           - Scan all hosts
    • Enter       - View detailed results
    • q           - Quit
    
    Examples:
    
        e9s                    # Start TUI
        
        e9s --debug           # Start with debug mode
    """
    try:
        from .tui.advanced_app import run_tui
        
        if debug:
            console.print("[yellow]Starting e9s in debug mode...[/yellow]")
            
        console.print("[cyan]🚀 Starting e9s - EZNet Network Testing TUI[/cyan]")
        console.print("[dim]Loading interface...[/dim]")
        run_tui()
        
    except ImportError as e:
        console.print("[red]Error: TUI dependencies not available.[/red]")
        console.print("[yellow]Install with: pip install textual>=0.45.0[/yellow]")
        if debug:
            console.print(f"[dim]Import error details: {e}[/dim]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]e9s interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error starting e9s: {e}[/red]")
        if debug:
            import traceback
            console.print("[dim]Traceback:[/dim]")
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()