"""
EZNet TUI - Advanced Application with k9s-style features.

This module implements a more complete TUI application with advanced features.
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual.widgets import Header, Footer, DataTable, Static, Input, Button
from textual.screen import ModalScreen
from textual.binding import Binding
from textual import work, on
from textual.message import Message

from ..cli import run_all_checks, run_port_scan, EZNetResult
from ..utils import is_valid_hostname, is_valid_ip, parse_ports, get_common_ports
from .results import ResultsScreen
from .k9s_theme import K9S_THEME


@dataclass
class HostEntry:
    """Represents a host entry in the TUI."""
    hostname: str
    ports: List[int]
    status: str = "pending"  # pending, running, completed, error
    last_scan: Optional[datetime] = None
    results: Optional[EZNetResult] = None
    error: Optional[str] = None


class RefreshDisplay(Message):
    """Message to refresh the display after a scan completes."""
    
    def __init__(self, host: HostEntry) -> None:
        super().__init__()
        self.host = host


class AddHostModal(ModalScreen):
    """Modal screen for adding a new host."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel", show=True),
        Binding("tab", "focus_next", "Next Field", show=False),
        Binding("shift+tab", "focus_previous", "Previous Field", show=False),
    ]
    
    CSS = """
    AddHostModal {
        align: center middle;
    }
    
    #add-host-dialog {
        background: $surface;
        border: solid $accent;
        width: 65;
        height: 21;
        padding: 2;
    }
    
    .dialog-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .input-label {
        margin-bottom: 1;
        color: $text;
    }
    
    #host-input {
        border: solid $accent;
        background: $surface;
        color: $text;
        margin-bottom: 1;
    }
    
    #host-input:focus {
        border: solid $primary;
    }
    
    .example {
        color: $text-muted;
        margin-left: 2;
    }
    
    #button-container {
        align: center middle;
        margin-top: 1;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None
    
    def compose(self) -> ComposeResult:
        """Compose the add host modal."""
        with Container(id="add-host-dialog"):
            yield Static("📡 Add New Host", classes="dialog-title")
            
            with Vertical():
                yield Static("Host (hostname:port or hostname:port1,port2):", classes="input-label")
                yield Input(placeholder="e.g., google.com:443 or google.com:80-90", id="host-input")
                yield Static("")  # Spacer
                yield Static("[dim]Examples:[/dim]", classes="input-label")
                yield Static("[dim]• google.com (uses port 443 for SSL)[/dim]", classes="example")
                yield Static("[dim]• google.com:80 (single port)[/dim]", classes="example") 
                yield Static("[dim]• google.com:80,443 (multiple ports)[/dim]", classes="example")
                yield Static("[dim]• google.com:80-90 (port range)[/dim]", classes="example")
                yield Static("")  # Spacer
                
                with Horizontal(id="button-container"):
                    yield Button("Add", variant="primary", id="add-button")
                    yield Button("Cancel", variant="default", id="cancel-button")
    
    def on_mount(self) -> None:
        """Focus the host input when mounted."""
        self.query_one("#host-input", Input).focus()
    
    @on(Button.Pressed, "#add-button")
    @on(Input.Submitted, "#host-input")
    async def handle_add(self, event) -> None:
        """Handle adding the host."""
        host_input = self.query_one("#host-input", Input)
        host_value = host_input.value.strip()
        
        if not host_value:
            return
        
        # Parse host:port or host:port1,port2 syntax
        hostname, ports = self.parse_host_input(host_value)
        
        if not hostname:
            return
        
        if not (is_valid_hostname(hostname) or is_valid_ip(hostname)):
            # Could show error message here
            return
        
        self.result = {"hostname": hostname, "ports": ports}
        self.dismiss(self.result)
    
    def parse_host_input(self, host_input: str) -> tuple[str, list]:
        """Parse host input in the format hostname:port or hostname:port1,port2."""
        if ':' in host_input:
            # Split host and ports
            hostname, ports_str = host_input.rsplit(':', 1)
            try:
                ports = parse_ports(ports_str)
            except ValueError:
                # If port parsing fails, use default SSL port
                ports = [443]
        else:
            # No port specified, use default SSL port for certificate checks
            hostname = host_input
            ports = [443]
            
        return hostname.strip(), ports
    
    @on(Button.Pressed, "#cancel-button")
    async def handle_cancel(self, event) -> None:
        """Handle canceling the add operation."""
        self.dismiss(None)
    
    def action_focus_next(self) -> None:
        """Focus next input field."""
        self.focus_next()
    
    def action_focus_previous(self) -> None:
        """Focus previous input field."""
        self.focus_previous()


class EZNetAdvancedApp(App):
    """Advanced EZNet TUI Application with k9s-style features."""
    
    TITLE = "e9s - Network Testing Tool"
    CSS = K9S_THEME
    
    BINDINGS = [
        # k9s-style navigation
        Binding("a", "add_host", "Add Host", show=True),
        Binding("d", "delete_host", "Delete", show=True),
        Binding("ctrl+d", "delete_host", "Delete", show=False),
        Binding("r", "refresh_selected", "Refresh Selected", show=True),
        Binding("ctrl+r", "refresh_all", "Refresh All", show=False),
        Binding("s", "scan_all", "Scan All", show=True),
        Binding("enter", "view_results", "View Results", show=True),
        Binding("space", "view_results", "View Results", show=False),
        
        # k9s-style shortcuts
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "cursor_top", "Top", show=False),
        Binding("shift+g", "cursor_bottom", "Bottom", show=False),
        
        # Application control
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
        
        # Help
        Binding("?", "help", "Help", show=True),
        Binding("h", "help", "Help", show=False),
    ]
    

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hosts: List[HostEntry] = []
        self.selected_host_index = 0
        self.dark = True
        self.current_context = "hosts"
    
    def compose(self) -> ComposeResult:
        """Compose the advanced application layout."""
        yield Header()
        
        with Vertical():
            yield Static("e9s > hosts", id="breadcrumbs")
            
            with Horizontal():
                with Vertical(id="host-container"):
                    yield Static("📡 Hosts", classes="panel-title")
                    yield DataTable(id="host-table")
                
                with Vertical(id="info-panel"):
                    yield Static("ℹ️  Host Information", classes="panel-title")
                    with ScrollableContainer(id="info-scroll"):
                        yield Static(self.get_help_text(), id="host-info")
            
            yield Static(self.get_menu_text(), id="menu-bar")
            yield Static("Ready - Press 'a' to add host, 's' to scan, '?' for help", id="status-bar")
        
        yield Footer()
    
    def get_help_text(self) -> str:
        """Get help text for the info panel."""
        return """Welcome to e9s!

[cyan]📋 Navigation Commands:[/cyan]
• ↑/↓ or j/k    - Navigate up/down through hosts
• g             - Jump to first host (top)
• G             - Jump to last host (bottom)  
• Enter/Space   - View detailed results for selected host

[cyan]🔧 Host Management:[/cyan]
• a             - Add new host (opens dialog)
• d / Ctrl+d    - Delete currently selected host
• r             - Rescan currently selected host
• Ctrl+r        - Rescan all hosts

[cyan]🚀 Network Testing:[/cyan]
• s             - Start scanning all hosts concurrently
                  (Tests DNS, TCP, HTTP, ICMP for each host)

[cyan]ℹ️  Information & Help:[/cyan]
• ?             - Toggle this help information
• h             - Alternative help shortcut
• Esc           - Cancel current action or return to host info

[cyan]🚪 Application Control:[/cyan]
• q             - Quit EZNet TUI
• Ctrl+c        - Force quit

[dim]💡 Tips:[/dim]
• [dim]Select a host from the left panel to view detailed information here[/dim]
• [dim]Add hosts with specific ports (e.g., 80,443 or 80-90)[/dim]
• [dim]Leave ports empty when adding hosts to use common ports[/dim]
• [dim]Scanning runs asynchronously - watch the status column for updates[/dim]

[yellow]Press 'a' to add your first host and get started![/yellow]"""
    
    def get_menu_text(self) -> str:
        """Get menu bar text."""
        return "[bold]a[/bold] Add | [bold]d[/bold] Delete | [bold]s[/bold] Scan | [bold]Enter[/bold] Results | [bold]?[/bold] Help | [bold]q[/bold] Quit"
    
    def on_mount(self) -> None:
        """Set up the application when mounted."""
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
        selected_row = table.cursor_row
        table.clear()
        
        for i, host in enumerate(self.hosts):
            ports_str = ",".join(map(str, host.ports)) if host.ports else "common"
            if len(ports_str) > 15:
                ports_str = ports_str[:12] + "..."
            
            status_emoji = {
                "pending": "⏳",
                "running": "🔄", 
                "completed": "✅",
                "error": "❌"
            }.get(host.status, "⏳")
            
            last_scan = host.last_scan.strftime("%H:%M:%S") if host.last_scan else "-"
            
            results_summary = ""
            if host.results:
                dns_ok = host.results.dns_results.get("ipv4", {}).get("success", False)
                tcp_ok = sum(1 for r in host.results.tcp_results.values() if r.get("success"))
                total_tcp = len(host.results.tcp_results)
                results_summary = f"DNS:{'✓' if dns_ok else '✗'} TCP:{tcp_ok}/{total_tcp}"
            elif host.error:
                results_summary = "Error"
            
            table.add_row(
                host.hostname,
                ports_str,
                f"{status_emoji} {host.status}",
                last_scan,
                results_summary
            )
        
        # Restore cursor position
        if 0 <= selected_row < len(self.hosts):
            table.move_cursor(row=selected_row)
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the host table."""
        row_index = event.cursor_row
        if 0 <= row_index < len(self.hosts):
            self.selected_host_index = row_index
            host = self.hosts[row_index]
            self.update_host_info(host)
    
    def update_host_info(self, host: HostEntry):
        """Update the host information panel."""
        info_panel = self.query_one("#host-info", Static)
        
        if not host.results:
            # Show basic info when no results available
            info_text = f"""[bold]EZNet Results for {host.hostname}[/bold]

[cyan]Configuration:[/cyan]
Ports: {', '.join(map(str, host.ports)) if host.ports else 'Common ports'}
Status: {host.status.title()}
Last Scan: {host.last_scan.strftime('%Y-%m-%d %H:%M:%S') if host.last_scan else 'Never'}

"""
            if host.error:
                info_text += f"[red]Error:[/red] {host.error}\n\n"
            
            info_text += """[yellow]Press 's' to scan this host or 'Enter' for detailed view[/yellow]"""
            info_panel.update(info_text)
            return
        
        # Create CLI-style output similar to eznet google.de --ssl-check
        info_text = f"""[bold]EZNet Results for {host.hostname}[/bold]

"""
        
        # DNS Resolution Table
        dns_results = host.results.dns_results
        info_text += """[bold blue]🌐 DNS Resolution[/bold blue]
┌──────────────┬─────────┬────────────────────────────────────────┐
│ Record Type  │ Status  │ Result                                 │
├──────────────┼─────────┼────────────────────────────────────────┤
"""
        
        if "ipv4" in dns_results:
            status = "✅ Success" if dns_results["ipv4"]["success"] else "❌ Failed"
            addresses = ", ".join(dns_results["ipv4"].get("addresses", [])[:2]) if dns_results["ipv4"]["success"] else dns_results["ipv4"].get("error", "")[:35]
            info_text += f"│ IPv4 (A)     │ {status:<7} │ {addresses:<38} │\n"
        
        if "ipv6" in dns_results:
            status = "✅ Success" if dns_results["ipv6"]["success"] else "❌ Failed"
            addresses = ", ".join(dns_results["ipv6"].get("addresses", [])[:1]) if dns_results["ipv6"]["success"] else "No IPv6"
            info_text += f"│ IPv6 (AAAA)  │ {status:<7} │ {addresses:<38} │\n"
        
        info_text += """└──────────────┴─────────┴────────────────────────────────────────┘

"""
        
        # Port Scan Results Table
        if host.results.tcp_results:
            info_text += """[bold blue]🔍 Port Scan Results[/bold blue]
┌──────┬─────────────────┬─────────┬───────────────┐
│ Port │ Service         │ Status  │ Response Time │
├──────┼─────────────────┼─────────┼───────────────┤
"""
            
            # Sort ports for better display
            sorted_ports = sorted(host.results.tcp_results.keys())
            for port in sorted_ports[:8]:  # Show max 8 ports in table
                tcp_data = host.results.tcp_results[port]
                service = self.get_service_description(port)
                
                if tcp_data.get("success"):
                    status = "✅ Open"
                    response_time = f"{tcp_data.get('response_time_ms', 0):.1f} ms"
                else:
                    status = "❌ Closed"
                    response_time = "Connection failed"[:13]
                
                info_text += f"│ {port:<4} │ {service:<15} │ {status:<7} │ {response_time:<13} │\n"
            
            info_text += """└──────┴─────────────────┴─────────┴───────────────┘

"""
            
            # Summary
            open_ports = [p for p, r in host.results.tcp_results.items() if r.get("success")]
            total_ports = len(host.results.tcp_results)
            info_text += f"[bold]Summary:[/bold] {len(open_ports)}/{total_ports} ports open\n"
            if open_ports:
                info_text += f"[green]Open ports:[/green] {', '.join(map(str, open_ports))}\n"
            info_text += "\n"
        
        # HTTP Services Table
        http_ports = [(p, r) for p, r in host.results.http_results.items() if r.get("success")]
        if http_ports:
            info_text += """[bold blue]🌍 HTTP Services[/bold blue]
┌──────┬─────────┬──────────────────┬───────────────┐
│ Port │ Status  │ Server           │ Response Time │
├──────┼─────────┼──────────────────┼───────────────┤
"""
            
            for port, http_data in http_ports:
                status = f"{http_data.get('status_code')} {http_data.get('reason_phrase', '')}"[:7]
                server = http_data.get('server', 'Unknown')[:16]
                response_time = f"{http_data.get('response_time_ms', 0):.1f} ms"
                
                info_text += f"│ {port:<4} │ {status:<7} │ {server:<16} │ {response_time:<13} │\n"
            
            info_text += """└──────┴─────────┴──────────────────┴───────────────┘

"""
        
        # SSL/TLS Certificates Table
        ssl_ports = [(p, r) for p, r in host.results.ssl_results.items() if isinstance(r, dict) and r.get("success")]
        if ssl_ports:
            info_text += """[bold blue]🔒 SSL/TLS Certificates[/bold blue]
┌──────┬───────┬────────────┬─────────────────────┐
│ Port │ Grade │ Valid Until│ Issuer              │
├──────┼───────┼────────────┼─────────────────────┤
"""
            
            for port, ssl_data in ssl_ports:
                cert = ssl_data.get("certificate", {})
                security = ssl_data.get("security_score", {})
                
                grade = security.get("grade", "?")
                valid_until = cert.get("not_after", "Unknown")[:10]
                
                # Extract issuer info
                issuer_info = cert.get("issuer", "Unknown")
                if isinstance(issuer_info, str) and "CN=" in issuer_info:
                    issuer_parts = issuer_info.split(",")
                    for part in issuer_parts:
                        if "CN=" in part:
                            issuer = part.strip().replace("CN=", "")[:19]
                            break
                    else:
                        issuer = "Unknown"
                else:
                    issuer = "Unknown"
                
                # Color grade
                if grade.startswith("A"):
                    grade_display = f"[green]{grade}[/green]"
                elif grade in ["B", "C"]:
                    grade_display = f"[yellow]{grade}[/yellow]"
                else:
                    grade_display = f"[red]{grade}[/red]"
                
                info_text += f"│ {port:<4} │ {grade:<5} │ {valid_until:<10} │ {issuer:<19} │\n"
            
            info_text += """└──────┴───────┴────────────┴─────────────────────┘

"""
        
        # Add detailed certificate information if available
        if host.results.ssl_results:
            for port, ssl_result in host.results.ssl_results.items():
                if ssl_result and ssl_result.get("success") and ssl_result.get("detailed_certificate"):
                    detailed_cert = ssl_result["detailed_certificate"]
                    cert_data = ssl_result.get("certificate", {})
                    
                    info_text += f"""[bold cyan]📋 Detailed Certificate Information (Port {port})[/bold cyan]
┌───────────────────────────┬────────────────────────────────────┐
│ Version                   │ {detailed_cert.get('version', 'Unknown'):<34} │
│ Serial Number             │ {str(detailed_cert.get('serial_number', 'Unknown'))[:34]:<34} │
│ Signature Algorithm       │ {detailed_cert.get('signature_algorithm', 'Unknown'):<34} │
└───────────────────────────┴────────────────────────────────────┘

"""
                    
                    # Certificate Issuer
                    issuer = detailed_cert.get('issuer', {})
                    info_text += f"""[bold cyan]🏢 Certificate Issuer[/bold cyan]
┌──────────────┬──────────────────────────────────────────────┐
│ Common Name  │ {issuer.get('Common Name', 'Unknown'):<44} │
│ Organization │ {issuer.get('Organization', 'Unknown'):<44} │
│ Country      │ {issuer.get('Country', 'Unknown'):<44} │
└──────────────┴──────────────────────────────────────────────┘

"""
                    
                    # Certificate Subject
                    subject = detailed_cert.get('subject', {})
                    info_text += f"""[bold cyan]🎯 Certificate Subject[/bold cyan]
┌─────────────┬────────────────────────────────────────────────┐
│ Common Name │ {subject.get('Common Name', 'Unknown'):<46} │
│ Organization│ {subject.get('Organization', 'N/A'):<46} │
└─────────────┴────────────────────────────────────────────────┘

"""
                    
                    # Certificate Validity
                    validity = detailed_cert.get('validity', {})
                    info_text += f"""[bold cyan]📅 Certificate Validity[/bold cyan]
┌────────────┬──────────────────────────────────────────────────┐
│ Not Before │ {validity.get('not_before', 'Unknown'):<48} │
│ Not After  │ {validity.get('not_after', 'Unknown'):<48} │
└────────────┴──────────────────────────────────────────────────┘

"""
                    
                    # Public Key Information
                    pubkey_info = detailed_cert.get('subject_public_key_info', {})
                    rsa_info = pubkey_info.get('rsa_public_key', {})
                    info_text += f"""[bold cyan]🔑 Public Key Information[/bold cyan]
┌──────────────┬────────────────────────────────────────────────┐
│ Algorithm    │ {pubkey_info.get('public_key_algorithm', 'Unknown'):<46} │
│ Key Size     │ {rsa_info.get('modulus', 'Unknown'):<46} │
│ Exponent     │ {rsa_info.get('exponent', 'Unknown'):<46} │
└──────────────┴────────────────────────────────────────────────┘

"""
                    
                    # Certificate Extensions
                    extensions = detailed_cert.get('extensions', {})
                    san_list = extensions.get('subject_alternative_name', [])
                    san_str = ', '.join([name[1] if isinstance(name, tuple) else str(name) for name in san_list])[:35]
                    key_usage_str = ', '.join(extensions.get('key_usage', []))[:35]
                    ext_key_usage_str = ', '.join(extensions.get('extended_key_usage', []))[:35]
                    
                    info_text += f"""[bold cyan]🔧 Certificate Extensions[/bold cyan]
┌──────────────────────────┬─────────────────────────────────────┐
│ Subject Alt Names        │ {san_str or 'N/A':<35} │
│ Key Usage                │ {key_usage_str or 'N/A':<35} │
│ Extended Key Usage       │ {ext_key_usage_str or 'N/A':<35} │
│ Basic Constraints        │ {extensions.get('basic_constraints', 'N/A'):<35} │
└──────────────────────────┴─────────────────────────────────────┘

"""
                    break  # Only show details for the first SSL certificate
        
        # ICMP Ping Table
        icmp_data = host.results.icmp_result
        info_text += """[bold blue]🏓 ICMP Ping[/bold blue]
┌─────────────────┬─────────────┬───────────────┐
│ Target          │ Status      │ Response Time │
├─────────────────┼─────────────┼───────────────┤
"""
        
        status = "✅ Reachable" if icmp_data.get("success") else "❌ Unreachable"
        response_time = f"{icmp_data.get('response_time_ms', 0):.1f} ms" if icmp_data.get("success") else icmp_data.get("error", "No response")[:13]
        target = host.hostname[:15]
        
        info_text += f"│ {target:<15} │ {status:<11} │ {response_time:<13} │\n"
        info_text += """└─────────────────┴─────────────┴───────────────┘

"""
        
        # Show hint if ICMP is blocked
        if not icmp_data.get("success") and icmp_data.get("hint"):
            info_text += f"[dim italic]💡 {icmp_data.get('hint')}[/dim italic]\n\n"
        
        # Summary timing
        if host.results.start_time and host.results.end_time:
            from ..utils import format_duration
            duration = format_duration(host.results.start_time, host.results.end_time)
            info_text += f"[dim]Total scan time: {duration:.1f} ms[/dim]\n\n"
        
        info_text += """[bold]Actions:[/bold] [cyan]Enter[/cyan] detailed view • [cyan]s[/cyan] scan • [cyan]d[/cyan] delete"""
        
        info_panel.update(info_text)
    
    def get_service_description(self, port: int) -> str:
        """Get service description for a port."""
        service_map = {
            22: "SSH",
            25: "SMTP", 
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            465: "SMTPS",
            587: "SMTP-Auth",
            993: "IMAPS",
            995: "POP3S",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt"
        }
        return service_map.get(port, "Unknown")
    
    # Navigation actions (k9s-style)
    async def action_cursor_down(self) -> None:
        """Move cursor down."""
        table = self.query_one("#host-table", DataTable)
        table.action_cursor_down()
    
    async def action_cursor_up(self) -> None:
        """Move cursor up."""
        table = self.query_one("#host-table", DataTable)
        table.action_cursor_up()
    
    async def action_cursor_top(self) -> None:
        """Move cursor to top."""
        table = self.query_one("#host-table", DataTable)
        if self.hosts:
            table.move_cursor(row=0)
    
    async def action_cursor_bottom(self) -> None:
        """Move cursor to bottom."""
        table = self.query_one("#host-table", DataTable)
        if self.hosts:
            table.move_cursor(row=len(self.hosts) - 1)
    
    # Main actions
    @work(exclusive=True)
    async def action_add_host(self) -> None:
        """Show add host modal."""
        result = await self.push_screen_wait(AddHostModal())
        if result:
            hostname = result["hostname"]
            ports = result["ports"]
            
            # Add the host
            self.add_host_entry(hostname, ports)
            
            # Select the newly added host
            if self.hosts:
                table = self.query_one("#host-table", DataTable)
                new_host_index = len(self.hosts) - 1
                self.selected_host_index = new_host_index
                table.move_cursor(row=new_host_index)
                self.update_host_info(self.hosts[new_host_index])
            
            status = self.query_one("#status-bar", Static)
            status.update(f"Added host: {hostname} - Starting scan...")
            
            # Automatically start scanning the new host
            if self.hosts:
                new_host = self.hosts[-1]
                new_host.status = "running"
                new_host.last_scan = datetime.now()
                self.refresh_table()
                
                # Start scan in background
                asyncio.create_task(self.scan_host(new_host))
    
    async def action_delete_host(self) -> None:
        """Delete the selected host."""
        if 0 <= self.selected_host_index < len(self.hosts):
            host = self.hosts[self.selected_host_index]
            self.hosts.pop(self.selected_host_index)
            
            # Adjust selection
            if self.selected_host_index >= len(self.hosts) and self.hosts:
                self.selected_host_index = len(self.hosts) - 1
            
            self.refresh_table()
            
            status = self.query_one("#status-bar", Static)
            status.update(f"Deleted host: {host.hostname}")
            
            # Update info panel
            if self.hosts and 0 <= self.selected_host_index < len(self.hosts):
                self.update_host_info(self.hosts[self.selected_host_index])
            else:
                info_panel = self.query_one("#host-info", Static)
                info_panel.update(self.get_help_text())
    
    @work(exclusive=True)
    async def action_refresh_selected(self) -> None:
        """Refresh (rescan) only the currently selected host."""
        if not self.hosts or not (0 <= self.selected_host_index < len(self.hosts)):
            status = self.query_one("#status-bar", Static)
            status.update("No host selected to refresh")
            return
            
        selected_host = self.hosts[self.selected_host_index]
        status = self.query_one("#status-bar", Static)
        status.update(f"Rescanning {selected_host.hostname}...")
        
        # Rescan the selected host
        await self.scan_host(selected_host)
        
        # Update display
        self.refresh_table()
        self.update_host_info(selected_host)
        status.update(f"Refreshed {selected_host.hostname}")

    async def action_refresh_all(self) -> None:
        """Refresh (rescan) all hosts - same as scan_all."""
        self.action_scan_all()
    
    @work(exclusive=True)
    async def action_scan_all(self) -> None:
        """Scan all hosts concurrently."""
        if not self.hosts:
            status = self.query_one("#status-bar", Static)
            status.update("No hosts to scan - add some hosts first")
            return
        
        status = self.query_one("#status-bar", Static)
        status.update(f"Scanning {len(self.hosts)} hosts...")
        
        # Update breadcrumbs
        breadcrumbs = self.query_one("#breadcrumbs", Static)
        breadcrumbs.update("eznet > hosts > scanning...")
        
        # Prepare scan tasks
        tasks = []
        for host in self.hosts:
            if host.status != "running":
                host.status = "running"
                host.last_scan = datetime.now()
                tasks.append(self.scan_host(host))
        
        self.refresh_table()
        
        if tasks:
            # Run scans concurrently with a reasonable limit
            semaphore = asyncio.Semaphore(10)  # Max 10 concurrent scans
            
            async def scan_with_semaphore(scan_task):
                async with semaphore:
                    return await scan_task
            
            await asyncio.gather(*[scan_with_semaphore(task) for task in tasks], return_exceptions=True)
            
            status.update(f"Completed scanning {len(tasks)} hosts")
            breadcrumbs.update("eznet > hosts")
        else:
            status.update("All hosts already scanned")
            breadcrumbs.update("eznet > hosts")
    
    async def scan_host(self, host: HostEntry) -> None:
        """Scan a single host."""
        try:
            if len(host.ports) <= 1:
                # Single port or no specific ports
                port = host.ports[0] if host.ports else None
                result = await run_all_checks(host.hostname, port, timeout=5, ssl_check=True)
            else:
                # Multi-port scan
                result = await run_port_scan(host.hostname, host.ports, timeout=5, ssl_check=True, max_concurrent=5)
            
            host.results = result
            host.status = "completed"
            host.error = None
            
        except Exception as e:
            host.status = "error"
            host.error = str(e)
            host.results = None
        
        # Update display - post message to refresh UI
        self.post_message(RefreshDisplay(host))
    
    async def action_view_results(self) -> None:
        """View detailed results for the selected host."""
        if 0 <= self.selected_host_index < len(self.hosts):
            host = self.hosts[self.selected_host_index]
            if host.results:
                self.push_screen(ResultsScreen(host.results, host.hostname))
            else:
                status = self.query_one("#status-bar", Static)
                status.update("No results available - run a scan first (press 's')")
    
    async def action_help(self) -> None:
        """Show help information."""
        info_panel = self.query_one("#host-info", Static)
        help_text = """[bold]EZNet TUI Help[/bold]

[cyan]Navigation:[/cyan]
• ↑↓ / j k    - Move cursor
• g / G       - Top / Bottom
• Enter       - View results
• Space       - View results

[cyan]Host Management:[/cyan]
• a           - Add host
• d / Ctrl+d  - Delete host
• r / Ctrl+r  - Refresh

[cyan]Scanning:[/cyan]
• s           - Scan all hosts

[cyan]Application:[/cyan]
• ?           - This help
• q           - Quit
• Esc         - Cancel/Back

[cyan]Tips:[/cyan]
• Add hosts with specific ports: 80,443
• Use port ranges: 80-90
• Leave ports empty for common ports

Press any key to return to host info."""
        info_panel.update(help_text)
    
    async def action_cancel(self) -> None:
        """Handle escape key."""
        if self.hosts and 0 <= self.selected_host_index < len(self.hosts):
            self.update_host_info(self.hosts[self.selected_host_index])
        else:
            info_panel = self.query_one("#host-info", Static)
            info_panel.update(self.get_help_text())
    
    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    @on(RefreshDisplay)
    def handle_refresh_display(self, message: RefreshDisplay) -> None:
        """Handle refresh display message from background scan."""
        self.refresh_table()
        if (0 <= self.selected_host_index < len(self.hosts) and 
            self.hosts[self.selected_host_index] == message.host):
            self.update_host_info(message.host)


def run_tui():
    """Run the advanced TUI application."""
    app = EZNetAdvancedApp()
    app.run()