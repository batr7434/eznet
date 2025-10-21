#!/usr/bin/env python3
"""
EZNet TUI - Interactive Terminal User Interface for network testing
Inspired by k9s for Kubernetes
"""

import asyncio
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import Header, Footer, Static, DataTable, Log
    from textual.binding import Binding
    from textual.reactive import reactive
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

from .dns_check import DNSChecker
from .tcp_check import TCPChecker
from .http_check import HTTPChecker
from .ssl_check import SSLChecker
from .icmp_check import ICMPChecker


@dataclass
class HostStatus:
    """Container for host monitoring status"""
    host: str
    port: int = 443
    last_check: Optional[datetime] = None
    dns_status: str = "❓"
    tcp_status: str = "❓"
    http_status: str = "❓"
    ssl_status: str = "❓"
    icmp_status: str = "❓"
    response_time: Optional[float] = None
    ssl_grade: str = "?"
    uptime_percentage: float = 0.0
    error_message: str = ""
    check_count: int = 0
    success_count: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)


class SimpleTUI:
    """Simple TUI implementation using Rich Live Display"""
    
    def __init__(self, hosts: Optional[List[str]] = None):
        self.console = Console()
        self.hosts: Dict[str, HostStatus] = {}
        
        # Initialize hosts
        initial = hosts or ["google.com", "github.com", "stackoverflow.com"]
        for host in initial:
            self.hosts[host] = HostStatus(host=host)
        
        # Network checkers
        self.dns_checker = DNSChecker()
        self.tcp_checker = TCPChecker()
        self.http_checker = HTTPChecker()
        self.ssl_checker = SSLChecker()
        self.icmp_checker = ICMPChecker()
        
        # Monitoring state
        self.monitoring_active = False
        self.refresh_rate = 5.0
        
    def create_layout(self) -> Layout:
        """Create the main layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(
            Panel(
                "[bold blue]EZNet TUI - Network Testing Dashboard[/bold blue]\n"
                f"Monitoring {len(self.hosts)} hosts | Press Ctrl+C to quit",
                style="bold"
            )
        )
        
        # Footer with commands
        layout["footer"].update(
            Panel(
                "[bold]Commands:[/bold] [r]efresh [m]onitor [q]uit | "
                "[bold]Like k9s for network testing![/bold] 🚀",
                style="dim"
            )
        )
        
        return layout
    
    def create_hosts_table(self) -> Table:
        """Create the main hosts table"""
        table = Table(
            title="🌐 Network Hosts Status",
            show_header=True,
            header_style="bold magenta",
            box=None
        )
        
        table.add_column("Host", style="cyan", width=20)
        table.add_column("Port", justify="center", width=6)
        table.add_column("DNS", justify="center", width=5)
        table.add_column("TCP", justify="center", width=5)
        table.add_column("HTTP", justify="center", width=5)
        table.add_column("SSL", justify="center", width=5)
        table.add_column("ICMP", justify="center", width=5)
        table.add_column("Response", justify="right", width=10)
        table.add_column("Uptime", justify="right", width=8)
        table.add_column("Last Check", style="dim", width=10)
        
        for host_status in self.hosts.values():
            last_check = host_status.last_check.strftime("%H:%M:%S") if host_status.last_check else "Never"
            response_time = f"{host_status.response_time:.0f}ms" if host_status.response_time else "-"
            uptime = f"{host_status.uptime_percentage:.1f}%"
            
            # Color coding for uptime
            uptime_style = "green" if host_status.uptime_percentage >= 95 else "yellow" if host_status.uptime_percentage >= 80 else "red"
            
            table.add_row(
                host_status.host,
                str(host_status.port),
                host_status.dns_status,
                host_status.tcp_status,
                host_status.http_status,
                host_status.ssl_status,
                host_status.icmp_status,
                response_time,
                f"[{uptime_style}]{uptime}[/{uptime_style}]",
                last_check
            )
        
        return table
    
    async def check_single_host(self, hostname: str) -> None:
        """Check a single host and update its status"""
        host_status = self.hosts[hostname]
        start_time = time.time()
        
        try:
            # Perform all checks
            dns_result = await self.dns_checker.check(hostname)
            tcp_result = await self.tcp_checker.check(hostname, host_status.port)
            http_result = await self.http_checker.check(hostname, host_status.port)
            ssl_result = await self.ssl_checker.check(hostname, host_status.port, detailed=True)
            icmp_result = await self.icmp_checker.check(hostname)
            
            # Update status
            host_status.dns_status = "✅" if dns_result.get("success") else "❌"
            host_status.tcp_status = "✅" if tcp_result.get("success") else "❌"
            host_status.http_status = "✅" if http_result.get("success") else "❌"
            host_status.ssl_status = "✅" if ssl_result.get("success") else "❌"
            host_status.icmp_status = "✅" if icmp_result.get("success") else "❌"
            
            # Calculate response time
            host_status.response_time = (time.time() - start_time) * 1000
            host_status.last_check = datetime.now()
            
            # Update SSL grade
            if ssl_result.get("success"):
                host_status.ssl_grade = ssl_result.get("security_grade", "?")
            
            # Update statistics
            host_status.check_count += 1
            if dns_result.get("success") and tcp_result.get("success"):
                host_status.success_count += 1
            
            host_status.uptime_percentage = (host_status.success_count / host_status.check_count) * 100 if host_status.check_count > 0 else 0
                
        except Exception as e:
            host_status.error_message = str(e)
            host_status.dns_status = "❌"
            host_status.tcp_status = "❌"
            host_status.http_status = "❌"
            host_status.ssl_status = "❌"
            host_status.icmp_status = "❌"
            host_status.last_check = datetime.now()
    
    async def check_all_hosts(self) -> None:
        """Check all hosts asynchronously"""
        tasks = []
        for host in self.hosts.keys():
            tasks.append(self.check_single_host(host))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def run_live_monitoring(self) -> None:
        """Run the live monitoring dashboard"""
        layout = self.create_layout()
        
        with Live(layout, console=self.console, refresh_per_second=0.5, screen=True) as live:
            self.console.print("\n[bold green]🚀 Starting EZNet TUI...[/bold green]")
            self.console.print("[dim]Performing initial checks...[/dim]\n")
            
            try:
                while True:
                    # Check all hosts
                    await self.check_all_hosts()
                    
                    # Update the main content with hosts table
                    layout["main"].update(self.create_hosts_table())
                    
                    # Update header with current time
                    layout["header"].update(
                        Panel(
                            f"[bold blue]EZNet TUI - Network Testing Dashboard[/bold blue]\n"
                            f"Monitoring {len(self.hosts)} hosts | {datetime.now().strftime('%H:%M:%S')} | Press Ctrl+C to quit",
                            style="bold"
                        )
                    )
                    
                    # Wait for next refresh
                    await asyncio.sleep(self.refresh_rate)
                    
            except KeyboardInterrupt:
                self.console.print("\n[bold yellow]👋 Monitoring stopped. Goodbye![/bold yellow]")


# Textual-based advanced TUI (if available)
if HAS_TEXTUAL:
    class EZNetTUI(App):
        """Advanced EZNet TUI using Textual (if available)"""
        
        TITLE = "EZNet TUI - Network Testing Dashboard"
        SUB_TITLE = "Press ? for help, q to quit"
        
        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("r", "refresh", "Refresh"),
            Binding("m", "monitor", "Monitor"),
            Binding("?", "help", "Help"),
        ]
        
        def __init__(self, initial_hosts: Optional[List[str]] = None):
            super().__init__()
            self.simple_tui = SimpleTUI(hosts=initial_hosts)
        
        def compose(self) -> ComposeResult:
            """Create the UI layout"""
            yield Header()
            yield Static("EZNet TUI - Advanced Mode", classes="title")
            yield Static("Coming soon! Using simple mode for now...", id="content")
            yield Footer()
        
        async def action_refresh(self) -> None:
            """Refresh all hosts"""
            await self.simple_tui.check_all_hosts()
            self.notify("✅ Refreshed all hosts")
        
        async def action_help(self) -> None:
            """Show help"""
            self.notify("Help: Press 'q' to quit, 'r' to refresh, 'm' to monitor")


def run_tui(hosts: Optional[List[str]] = None) -> None:
    """Run the EZNet TUI application"""
    if not HAS_TEXTUAL:
        console = Console()
        console.print("[yellow]⚠️  Textual library not found. Using simple live dashboard mode.[/yellow]")
        console.print("[dim]For full TUI features, install with: pip install textual[/dim]\n")
        
        # Use simple live monitoring
        simple_tui = SimpleTUI(hosts=hosts)
        try:
            asyncio.run(simple_tui.run_live_monitoring())
        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
    else:
        # Use advanced Textual TUI
        app = EZNetTUI(initial_hosts=hosts)
        app.run()


if __name__ == "__main__":
    run_tui()