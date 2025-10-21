"""
EZNet TUI - Simplified Main Application.

This module implements a simple TUI application similar to k9s structure.
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, Static
from textual.binding import Binding
from textual import work

from ..cli import run_all_checks, EZNetResult
from ..utils import is_valid_hostname, is_valid_ip
from .results import ResultsScreen


@dataclass
class HostEntry:
    """Represents a host entry in the TUI."""
    hostname: str
    ports: List[int]
    status: str = "pending"  # pending, running, completed, error
    last_scan: Optional[datetime] = None
    results: Optional[EZNetResult] = None
    error: Optional[str] = None


class EZNetApp(App):
    """Main EZNet TUI Application similar to k9s."""
    
    TITLE = "EZNet - Network Testing Tool"
    
    BINDINGS = [
        Binding("a", "add_host", "Add Host", show=True),
        Binding("d", "delete_host", "Delete", show=True),  
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "scan_all", "Scan All", show=True),
        Binding("enter", "view_results", "View Results", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #header {
        background: $primary;
        color: $text;
        height: 3;
        text-align: center;
    }
    
    #host-table {
        border: solid $accent;
        height: 1fr;
    }
    
    #info-panel {
        border: solid $accent;  
        width: 30%;
        padding: 1;
    }
    
    #status {
        background: $accent;
        color: $text;
        height: 1;
        text-align: center;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        background: $primary;
        color: $text;
        height: 1;
        margin: 0 0 1 0;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hosts: List[HostEntry] = []
        self.selected_host_index = 0
        self.dark = True  # k9s-style dark theme
    
    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        
        with Vertical():
            yield Static("🚀 EZNet - Network Testing Tool", classes="title", id="header")
            
            with Horizontal():
                with Vertical():
                    yield Static("📡 Hosts", classes="title")
                    yield DataTable(id="host-table")
                
                with Vertical(id="info-panel"):
                    yield Static("ℹ️  Host Information", classes="title")
                    yield Static("Select a host to view details", id="host-info")
            
            yield Static("Press 'a' to add host, 's' to scan, 'Enter' to view results, 'q' to quit", id="status")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Set up the host table when screen is mounted."""
        table = self.query_one("#host-table", DataTable)
        table.add_columns("Host", "Ports", "Status", "Last Scan", "Results")
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Start with empty host list - users can add hosts with 'a' key
    
    def add_host_entry(self, hostname: str, ports: List[int]):
        """Add a new host entry."""
        host_entry = HostEntry(hostname=hostname, ports=ports)
        self.hosts.append(host_entry)
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the host table display."""
        table = self.query_one("#host-table", DataTable)
        table.clear()
        
        for host in self.hosts:
            ports_str = ",".join(map(str, host.ports)) if host.ports else "all"
            status_emoji = {
                "pending": "⏳",
                "running": "🔄", 
                "completed": "✅",
                "error": "❌"
            }.get(host.status, "⏳")
            
            last_scan = host.last_scan.strftime("%H:%M:%S") if host.last_scan else "-"
            
            results_summary = ""
            if host.results:
                # Show brief results summary
                dns_ok = host.results.dns_results.get("ipv4", {}).get("success", False)
                tcp_count = sum(1 for r in host.results.tcp_results.values() if r.get("success"))
                results_summary = f"DNS:{'✅' if dns_ok else '❌'} TCP:{tcp_count}/{len(host.results.tcp_results)}"
            
            table.add_row(
                host.hostname,
                ports_str,
                f"{status_emoji} {host.status}",
                last_scan,
                results_summary
            )
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the host table."""
        row_index = event.cursor_row
        if row_index < len(self.hosts):
            self.selected_host_index = row_index
            host = self.hosts[row_index]
            self.update_host_info(host)
    
    def update_host_info(self, host: HostEntry):
        """Update the host information panel."""
        info_panel = self.query_one("#host-info", Static)
        
        info_text = f"""[bold]{host.hostname}[/bold]

[cyan]Ports:[/cyan] {', '.join(map(str, host.ports)) if host.ports else 'all common ports'}
[cyan]Status:[/cyan] {host.status}
[cyan]Last Scan:[/cyan] {host.last_scan.strftime('%Y-%m-%d %H:%M:%S') if host.last_scan else 'Never'}

"""
        
        if host.error:
            info_text += f"[red]Error:[/red] {host.error}\n"
        
        if host.results:
            # Show summary of results
            dns_results = host.results.dns_results
            if dns_results.get("ipv4", {}).get("success"):
                addresses = ", ".join(dns_results["ipv4"]["addresses"])
                info_text += f"[green]DNS IPv4:[/green] {addresses}\n"
            
            tcp_successful = [p for p, r in host.results.tcp_results.items() if r.get("success")]
            if tcp_successful:
                info_text += f"[green]Open Ports:[/green] {', '.join(map(str, tcp_successful))}\n"
        
        info_panel.update(info_text)
    
    async def action_add_host(self) -> None:
        """Add a new host (simplified)."""
        # For demo purposes, add a random host
        import random
        demo_hosts = ["stackoverflow.com", "reddit.com", "amazon.com", "microsoft.com"]
        hostname = random.choice(demo_hosts)
        self.add_host_entry(hostname, [80, 443])
        
        status = self.query_one("#status", Static)
        status.update(f"Added host: {hostname}")
    
    async def action_delete_host(self) -> None:
        """Delete the selected host."""
        if 0 <= self.selected_host_index < len(self.hosts):
            host = self.hosts[self.selected_host_index]
            self.hosts.pop(self.selected_host_index)
            self.refresh_table()
            
            status = self.query_one("#status", Static)
            status.update(f"Deleted host: {host.hostname}")
            
            # Clear info panel
            info_panel = self.query_one("#host-info", Static)
            info_panel.update("Select a host to view details")
    
    async def action_refresh(self) -> None:
        """Refresh the current view."""
        self.refresh_table()
        status = self.query_one("#status", Static)
        status.update("Refreshed host list")
    
    @work(exclusive=True)
    async def action_scan_all(self) -> None:
        """Scan all hosts."""
        status = self.query_one("#status", Static)
        status.update("Scanning all hosts...")
        
        # Run scans for all hosts concurrently
        tasks = []
        for host in self.hosts:
            if host.status != "running":
                host.status = "running"
                host.last_scan = datetime.now()
                tasks.append(self.scan_host(host))
        
        self.refresh_table()
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            status.update(f"Completed scanning {len(tasks)} hosts")
        else:
            status.update("No hosts to scan")
    
    async def scan_host(self, host: HostEntry) -> None:
        """Scan a single host."""
        try:
            # For now, just scan first port or no port
            port = host.ports[0] if host.ports else None
            result = await run_all_checks(host.hostname, port, timeout=5, ssl_check=False)
            
            host.results = result
            host.status = "completed"
            host.error = None
            
        except Exception as e:
            host.status = "error"
            host.error = str(e)
            host.results = None
        
        # Update display on main thread
        self.call_from_thread(self.refresh_table)
        if self.selected_host_index < len(self.hosts) and self.hosts[self.selected_host_index] == host:
            self.call_from_thread(self.update_host_info, host)
    
    async def action_view_results(self) -> None:
        """View detailed results for the selected host."""
        if 0 <= self.selected_host_index < len(self.hosts):
            host = self.hosts[self.selected_host_index]
            if host.results:
                self.push_screen(ResultsScreen(host.results, host.hostname))
            else:
                status = self.query_one("#status", Static)
                status.update("No results available - run a scan first")
    
    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui():
    """Run the TUI application."""
    app = EZNetApp()
    app.run()