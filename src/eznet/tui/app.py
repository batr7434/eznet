"""
EZNet TUI - Main Application.

This module implements the main TUI application similar to k9s structure.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header, Footer, DataTable, Static, Button, 
    Input, TabbedContent, TabPane, Label
)
from textual.screen import Screen
from textual.binding import Binding
from textual import work

from ..cli import run_all_checks, run_port_scan, EZNetResult
from ..utils import is_valid_hostname, is_valid_ip


@dataclass
class HostEntry:
    """Represents a host entry in the TUI."""
    hostname: str
    ports: List[int]
    status: str = "pending"  # pending, running, completed, error
    last_scan: Optional[datetime] = None
    results: Optional[EZNetResult] = None
    error: Optional[str] = None


class StatusBar(Static):
    """Status bar widget similar to k9s."""
    
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $accent;
        color: $text;
        text-align: center;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_status("Ready")
    
    def update_status(self, message: str):
        """Update the status message."""
        self.update(f"[bold]{message}[/bold]")


class BreadcrumbBar(Static):
    """Breadcrumb navigation bar similar to k9s crumbs."""
    
    DEFAULT_CSS = """
    BreadcrumbBar {
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.breadcrumbs = ["eznet"]
        self.update_display()
    
    def push(self, name: str):
        """Push a new breadcrumb."""
        self.breadcrumbs.append(name)
        self.update_display()
    
    def pop(self):
        """Pop the last breadcrumb."""
        if len(self.breadcrumbs) > 1:
            self.breadcrumbs.pop()
            self.update_display()
    
    def update_display(self):
        """Update the breadcrumb display."""
        crumb_text = " > ".join(self.breadcrumbs)
        self.update(f"[dim]{crumb_text}[/dim]")


class MenuBar(Static):
    """Menu bar showing keyboard shortcuts."""
    
    DEFAULT_CSS = """
    MenuBar {
        height: 1;
        background: $panel;
        color: $text;
        text-align: left;
        padding: 0 1;
    }
    """
    
    def __init__(self, shortcuts: Dict[str, str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shortcuts = shortcuts
        self.update_display()
    
    def update_shortcuts(self, shortcuts: Dict[str, str]):
        """Update the shortcuts display."""
        self.shortcuts = shortcuts
        self.update_display()
    
    def update_display(self):
        """Update the menu display."""
        menu_items = []
        for key, description in self.shortcuts.items():
            menu_items.append(f"[bold]{key}[/bold] {description}")
        
        menu_text = " | ".join(menu_items)
        self.update(menu_text)


class HostListScreen(Screen):
    """Main screen showing the list of hosts similar to k9s resource view."""
    
    BINDINGS = [
        Binding("a", "add_host", "Add Host", show=True),
        Binding("d", "delete_host", "Delete", show=True),  
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "scan_all", "Scan All", show=True),
        Binding("enter", "view_results", "View Results", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "app.pop_screen", "Back", show=False),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hosts: List[HostEntry] = []
        self.selected_host_index = 0
        
    def compose(self) -> ComposeResult:
        """Compose the host list screen."""
        with Vertical():
            yield BreadcrumbBar(id="breadcrumbs")
            
            with Horizontal(id="main-container"):
                with Vertical(id="host-panel"):
                    yield Static("📡 Hosts", id="host-title")
                    yield DataTable(id="host-table")
                
                with Vertical(id="info-panel"):
                    yield Static("ℹ️  Host Information", id="info-title")
                    yield Static("Select a host to view details", id="host-info")
            
            yield MenuBar({
                "a": "Add Host",
                "d": "Delete", 
                "r": "Refresh",
                "s": "Scan All",
                "Enter": "View Results"
            }, id="menu")
            yield StatusBar(id="status")
    
    def on_mount(self) -> None:
        """Set up the host table when screen is mounted."""
        table = self.query_one("#host-table", DataTable)
        table.add_columns("Host", "Ports", "Status", "Last Scan", "Results")
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Load some example hosts
        self.add_host_entry("google.com", [80, 443])
        self.add_host_entry("github.com", [22, 80, 443])
        self.add_host_entry("8.8.8.8", [53])
    
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
    
    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
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
        """Show add host dialog."""
        def handle_add_host(hostname: str) -> None:
            if hostname and (is_valid_hostname(hostname) or is_valid_ip(hostname)):
                # Default to common ports
                common_ports = [22, 53, 80, 443, 993, 995]
                self.add_host_entry(hostname, common_ports)
                status_bar = self.query_one("#status", StatusBar)
                status_bar.update_status(f"Added host: {hostname}")
            else:
                status_bar = self.query_one("#status", StatusBar)  
                status_bar.update_status("Invalid hostname or IP address")
        
        # Simple text input for now - in a full implementation, this would be a modal dialog
        self.app.push_screen("add_host", handle_add_host)
    
    async def action_delete_host(self) -> None:
        """Delete the selected host."""
        if 0 <= self.selected_host_index < len(self.hosts):
            host = self.hosts[self.selected_host_index]
            self.hosts.pop(self.selected_host_index)
            self.refresh_table()
            
            status_bar = self.query_one("#status", StatusBar)
            status_bar.update_status(f"Deleted host: {host.hostname}")
            
            # Clear info panel
            info_panel = self.query_one("#host-info", Static)
            info_panel.update("Select a host to view details")
    
    async def action_refresh(self) -> None:
        """Refresh the current view."""
        self.refresh_table()
        status_bar = self.query_one("#status", StatusBar)
        status_bar.update_status("Refreshed host list")
    
    @work(exclusive=True)
    async def action_scan_all(self) -> None:
        """Scan all hosts."""
        status_bar = self.query_one("#status", StatusBar)
        status_bar.update_status("Scanning all hosts...")
        
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
            status_bar.update_status(f"Completed scanning {len(tasks)} hosts")
        else:
            status_bar.update_status("No hosts to scan")
    
    async def scan_host(self, host: HostEntry) -> None:
        """Scan a single host."""
        try:
            if len(host.ports) <= 1:
                # Single host, single/no port
                port = host.ports[0] if host.ports else None
                result = await run_all_checks(host.hostname, port, timeout=5, ssl_check=False)
            else:
                # Multi-port scan
                result = await run_port_scan(host.hostname, host.ports, timeout=5, ssl_check=False)
            
            host.results = result
            host.status = "completed"
            host.error = None
            
        except Exception as e:
            host.status = "error"
            host.error = str(e)
            host.results = None
        
        # Update display
        self.call_from_thread(self.refresh_table)
        if self.selected_host_index < len(self.hosts) and self.hosts[self.selected_host_index] == host:
            self.call_from_thread(self.update_host_info, host)
    
    async def action_view_results(self) -> None:
        """View detailed results for the selected host."""
        if 0 <= self.selected_host_index < len(self.hosts):
            host = self.hosts[self.selected_host_index]
            if host.results:
                self.app.push_screen("results", host.results, host.hostname)
            else:
                status_bar = self.query_one("#status", StatusBar)
                status_bar.update_status("No results available - run a scan first")


class AddHostScreen(Screen):
    """Screen for adding a new host."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel", show=True),
        Binding("ctrl+c", "app.pop_screen", "Cancel", show=False),
    ]
    
    def __init__(self, callback: Callable[[str], None], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        """Compose the add host screen."""
        with Vertical(id="add-host-container"):
            yield Static("Add New Host", id="add-host-title")
            yield Label("Enter hostname or IP address:")
            yield Input(placeholder="e.g., google.com or 8.8.8.8", id="hostname-input")
            
            with Horizontal(id="button-container"):
                yield Button("Add", variant="primary", id="add-button")
                yield Button("Cancel", variant="default", id="cancel-button")
    
    def on_mount(self) -> None:
        """Focus the input when screen is mounted."""
        input_widget = self.query_one("#hostname-input", Input)
        input_widget.focus()
    
    @on(Button.Pressed, "#add-button")
    @on(Input.Submitted, "#hostname-input")
    async def handle_add(self, event) -> None:
        """Handle adding the host."""
        input_widget = self.query_one("#hostname-input", Input)
        hostname = input_widget.value.strip()
        
        if hostname:
            self.callback(hostname)
        
        self.app.pop_screen()
    
    @on(Button.Pressed, "#cancel-button")
    async def handle_cancel(self, event) -> None:
        """Handle canceling the add operation."""
        self.app.pop_screen()


class EZNetApp(App):
    """Main EZNet TUI Application."""
    
    TITLE = "EZNet - Network Testing Tool"
    CSS_PATH = None  # We'll use inline CSS for now
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dark = True  # k9s-style dark theme
    
    def on_mount(self) -> None:
        """Set up the application when mounted."""
        self.push_screen(HostListScreen())
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    # Screen management
    SCREENS = {
        "hosts": HostListScreen,
        "add_host": AddHostScreen,
    }
    
    def push_screen(self, screen_name: str, *args, **kwargs):
        """Push a screen onto the screen stack."""
        if screen_name == "add_host":
            # Special handling for add_host screen
            callback = args[0] if args else lambda x: None
            screen = AddHostScreen(callback)
            super().push_screen(screen)
        elif screen_name == "results":
            # Results screen would be implemented separately
            # For now, just show a placeholder
            super().push_screen(ResultsScreen(*args, **kwargs))
        else:
            super().push_screen(screen_name)


class ResultsScreen(Screen):
    """Screen showing detailed scan results for a host."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("ctrl+c", "app.pop_screen", "Back", show=False),
    ]
    
    def __init__(self, results: EZNetResult, hostname: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = results
        self.hostname = hostname
    
    def compose(self) -> ComposeResult:
        """Compose the results screen."""
        with Vertical():
            breadcrumbs = BreadcrumbBar()
            breadcrumbs.push(f"results:{self.hostname}")
            yield breadcrumbs
            
            with TabbedContent():
                with TabPane("DNS", id="dns-tab"):
                    yield self.create_dns_table()
                
                with TabPane("Ports", id="ports-tab"):
                    yield self.create_ports_table()
                
                with TabPane("HTTP", id="http-tab"):
                    yield self.create_http_table()
                
                with TabPane("SSL", id="ssl-tab"):
                    yield self.create_ssl_table()
                
                with TabPane("ICMP", id="icmp-tab"):
                    yield self.create_icmp_table()
            
            yield MenuBar({
                "Esc": "Back",
                "r": "Refresh"
            })
            yield StatusBar()
    
    def create_dns_table(self) -> DataTable:
        """Create DNS results table."""
        table = DataTable()
        table.add_columns("Record Type", "Status", "Result")
        
        dns_data = self.results.dns_results
        if "ipv4" in dns_data:
            status = "✅ Success" if dns_data["ipv4"]["success"] else "❌ Failed"
            addresses = ", ".join(dns_data["ipv4"].get("addresses", [])) if dns_data["ipv4"]["success"] else dns_data["ipv4"].get("error", "")
            table.add_row("IPv4 (A)", status, addresses)
        
        if "ipv6" in dns_data:
            status = "✅ Success" if dns_data["ipv6"]["success"] else "❌ Failed"
            addresses = ", ".join(dns_data["ipv6"].get("addresses", [])) if dns_data["ipv6"]["success"] else dns_data["ipv6"].get("error", "")
            table.add_row("IPv6 (AAAA)", status, addresses)
        
        return table
    
    def create_ports_table(self) -> DataTable:
        """Create ports scan results table."""
        table = DataTable()
        table.add_columns("Port", "Status", "Response Time", "Service")
        
        for port, result in self.results.tcp_results.items():
            status = "✅ Open" if result.get("success") else "❌ Closed"
            response_time = f"{result.get('response_time_ms', 0):.1f} ms" if result.get("success") else result.get("error", "")
            service = self.get_service_name(port)
            table.add_row(str(port), status, response_time, service)
        
        return table
    
    def create_http_table(self) -> DataTable:
        """Create HTTP results table."""
        table = DataTable()
        table.add_columns("Port", "Status Code", "Server", "Response Time")
        
        for port, result in self.results.http_results.items():
            if result.get("success"):
                status = f"{result.get('status_code')} {result.get('reason_phrase', '')}"
                server = result.get("server", "Unknown")
                response_time = f"{result.get('response_time_ms', 0):.1f} ms"
                table.add_row(str(port), status, server, response_time)
        
        return table
    
    def create_ssl_table(self) -> DataTable:
        """Create SSL results table."""
        table = DataTable()
        table.add_columns("Port", "Grade", "Valid Until", "Issuer")
        
        for port, result in self.results.ssl_results.items():
            if isinstance(result, dict) and result.get("success"):
                cert = result.get("certificate", {})
                security = result.get("security_score", {})
                
                grade = security.get("grade", "?")
                valid_until = cert.get("not_after", "Unknown")
                issuer = cert.get("issuer", "Unknown")
                
                table.add_row(str(port), grade, valid_until, str(issuer))
        
        return table
    
    def create_icmp_table(self) -> DataTable:
        """Create ICMP results table."""
        table = DataTable()
        table.add_columns("Target", "Status", "Response Time")
        
        icmp_data = self.results.icmp_result
        status = "✅ Reachable" if icmp_data.get("success") else "❌ Unreachable"
        response_time = f"{icmp_data.get('response_time_ms', 0):.1f} ms" if icmp_data.get("success") else icmp_data.get("error", "")
        
        table.add_row(self.hostname, status, response_time)
        
        return table
    
    def get_service_name(self, port: int) -> str:
        """Get service name for a port."""
        service_map = {
            22: "SSH",
            53: "DNS", 
            80: "HTTP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S"
        }
        return service_map.get(port, "Unknown")
    
    async def action_refresh(self) -> None:
        """Refresh the results (re-run scan)."""
        status_bar = self.query_one(StatusBar)
        status_bar.update_status("Refreshing results...")
        # Implementation for re-running the scan would go here