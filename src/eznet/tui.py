#!/usr/bin/env python3
"""
EZNet TUI - Terminal User Interface for network testing.

A k9s-inspired interactive dashboard for network monitoring and testing.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, DataTable, Static, Label, TabbedContent, 
    TabPane, ProgressBar, Log, Tree, Input
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual.reactive import reactive, var
from textual import on, work
from textual.timer import Timer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

from .dns_check import DNSChecker
from .tcp_check import TCPChecker
from .http_check import HTTPChecker
from .ssl_check import SSLChecker
from .icmp_check import ICMPChecker

@dataclass
class HostResult:
    """Represents the result of host monitoring."""
    host: str
    port: int = 443
    status: str = "⏳ CHECKING"
    dns_status: str = "⏳"
    tcp_status: str = "⏳"
    http_status: str = "⏳"
    ssl_status: str = "⏳"
    ssl_grade: str = ""
    response_time: int = 0
    last_check: Optional[datetime] = None
    uptime: float = 100.0
    total_checks: int = 0
    successful_checks: int = 0
    errors: List[str] = field(default_factory=list)
    
    # Detailed results for inspection
    dns_result: Optional[Dict] = None
    tcp_result: Optional[Dict] = None
    http_result: Optional[Dict] = None
    ssl_result: Optional[Dict] = None
    icmp_result: Optional[Dict] = None


class SSLDetailScreen(ModalScreen[str]):
    """Modal screen showing SSL certificate details (like 'd' in k9s)."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Close"),
        Binding("q", "cancel", "Close"),
    ]
    
    def __init__(self, host_result: HostResult) -> None:
        super().__init__()
        self.host_result = host_result
    
    def compose(self) -> ComposeResult:
        with Container(id="ssl-detail-container"):
            yield Static(f"SSL Certificate Details: {self.host_result.host}:{self.host_result.port}", 
                        classes="ssl-detail-title")
            
            if self.host_result.ssl_result and self.host_result.ssl_result.get('success'):
                ssl_data = self.host_result.ssl_result
                
                # Create detailed SSL info display
                ssl_info = []
                ssl_info.append(f"Subject: {ssl_data.get('subject', 'Unknown')}")
                ssl_info.append(f"Issuer: {ssl_data.get('issuer', 'Unknown')}")
                ssl_info.append(f"Valid Until: {ssl_data.get('valid_until', 'Unknown')}")
                ssl_info.append(f"Security Grade: {ssl_data.get('security_grade', 'Unknown')}")
                ssl_info.append(f"Days Until Expiry: {ssl_data.get('days_until_expiry', 'Unknown')}")
                
                if ssl_data.get('detailed_certificate'):
                    cert = ssl_data['detailed_certificate']
                    ssl_info.append("\n--- Certificate Details ---")
                    ssl_info.append(f"Version: {cert.get('version', 'Unknown')}")
                    ssl_info.append(f"Serial Number: {cert.get('serial_number', 'Unknown')}")
                    ssl_info.append(f"Signature Algorithm: {cert.get('signature_algorithm', 'Unknown')}")
                
                yield Static("\n".join(ssl_info), classes="ssl-detail-content")
            else:
                yield Static("SSL check failed or no SSL data available", classes="ssl-detail-error")
            
            yield Static("\n[ESC] Close | [Q] Quit", classes="ssl-detail-help")
    
    def action_cancel(self) -> None:
        self.dismiss("closed")


class EZNetTUI(App):
    """
    EZNet TUI - k9s-inspired network testing dashboard.
    
    Navigation:
    - j/k or arrow keys: Navigate hosts
    - d: Show SSL certificate details  
    - r: Refresh current host
    - R: Refresh all hosts
    - m: Toggle monitoring mode
    - :: Command mode (add hosts)
    - q: Quit
    """
    
    TITLE = "EZNet TUI"
    SUB_TITLE = "Network Testing Dashboard"
    CSS_PATH = None
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh_current", "Refresh"),
        Binding("shift+r", "refresh_all", "Refresh All"),
        Binding("d", "show_ssl_details", "SSL Details"),
        Binding("m", "toggle_monitoring", "Monitor"),
        Binding("colon", "command_mode", "Command", show=False),
        Binding("?", "help", "Help"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]
    
    # Reactive variables
    monitoring_active = reactive(False)
    current_host = reactive("")
    refresh_interval = reactive(5.0)
    
    def __init__(self, initial_hosts: Optional[List[str]] = None):
        super().__init__()
        self.hosts: Dict[str, HostResult] = {}
        self.selected_row = 0
        self.monitor_timer: Optional[Timer] = None
        self.command_input: Optional[Input] = None
        self.command_mode_active = False
        
        # Initialize network checkers
        self.dns_checker = DNSChecker()
        self.tcp_checker = TCPChecker()
        self.http_checker = HTTPChecker()
        self.ssl_checker = SSLChecker()
        self.icmp_checker = ICMPChecker()
        
        # Only add initial hosts if provided (for command line usage)
        if initial_hosts:
            for host in initial_hosts:
                host_key = f"{host}:443"
                self.hosts[host_key] = HostResult(host=host, port=443)
    
    def compose(self) -> ComposeResult:
        """Create the main UI layout."""
        yield Header()
        
        with TabbedContent():
            with TabPane("Hosts", id="hosts-tab"):
                yield DataTable(id="hosts-table", cursor_type="row")
                
            with TabPane("SSL Details", id="ssl-tab"):
                yield Static("Select a host and press 'd' to view SSL details", id="ssl-content")
                
            with TabPane("Logs", id="logs-tab"):
                yield Log(id="main-log")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the UI when mounted."""
        # Setup the hosts table
        table = self.query_one("#hosts-table", DataTable)
        table.add_columns(
            "Host", "Port", "Status", "DNS", "TCP", "HTTP", "SSL", "Grade", 
            "Response", "Uptime", "Last Check"
        )
        
        # Add initial rows
        for host_result in self.hosts.values():
            self._add_host_row(table, host_result)
        
        # Initial check
        self.call_after_refresh(self._check_all_hosts)
        
        # Log startup
        log = self.query_one("#main-log", Log)
        log.write_line("🚀 EZNet TUI started")
        log.write_line(f"📊 Monitoring {len(self.hosts)} hosts")
    
    def _add_host_row(self, table: DataTable, host_result: HostResult) -> None:
        """Add a host row to the table."""
        last_check = host_result.last_check.strftime("%H:%M:%S") if host_result.last_check else "Never"
        response_time = f"{host_result.response_time}ms" if host_result.response_time > 0 else "-"
        uptime_str = f"{host_result.uptime:.1f}%"
        
        table.add_row(
            host_result.host,
            str(host_result.port),
            host_result.status,
            host_result.dns_status,
            host_result.tcp_status,
            host_result.http_status,
            host_result.ssl_status,
            host_result.ssl_grade,
            response_time,
            uptime_str,
            last_check,
            key=f"{host_result.host}:{host_result.port}"
        )
    
    def _update_host_row(self, table: DataTable, host_result: HostResult) -> None:
        """Update an existing host row."""
        row_key = f"{host_result.host}:{host_result.port}"
        
        try:
            last_check = host_result.last_check.strftime("%H:%M:%S") if host_result.last_check else "Never"
            response_time = f"{host_result.response_time}ms" if host_result.response_time > 0 else "-"
            uptime_str = f"{host_result.uptime:.1f}%"
            
            # Update the row
            table.update_cell(row_key, "Status", host_result.status)
            table.update_cell(row_key, "DNS", host_result.dns_status)
            table.update_cell(row_key, "TCP", host_result.tcp_status)
            table.update_cell(row_key, "HTTP", host_result.http_status)
            table.update_cell(row_key, "SSL", host_result.ssl_status)
            table.update_cell(row_key, "Grade", host_result.ssl_grade)
            table.update_cell(row_key, "Response", response_time)
            table.update_cell(row_key, "Uptime", uptime_str)
            table.update_cell(row_key, "Last Check", last_check)
            
        except Exception as e:
            # Row might not exist, add it
            self._add_host_row(table, host_result)
    
    async def _check_single_host_internal(self, host_key: str) -> None:
        """Internal method to check a single host and update its status."""
        if host_key not in self.hosts:
            return
        
        host_result = self.hosts[host_key]
        host_result.status = "⏳ CHECKING"
        
        start_time = time.time()
        
        # Log the check
        log = self.query_one("#main-log", Log)
        log.write_line(f"🔍 Checking {host_result.host}:{host_result.port}")
        
        try:
            # Perform all checks concurrently
            tasks = [
                self.dns_checker.check(host_result.host),
                self.tcp_checker.check(host_result.host, host_result.port),
                self.http_checker.check(host_result.host, host_result.port),
                self.ssl_checker.check(host_result.host, host_result.port, detailed=True),
                self.icmp_checker.check(host_result.host)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            dns_result, tcp_result, http_result, ssl_result, icmp_result = results
            
            # Update DNS status
            if not isinstance(dns_result, Exception) and dns_result.get('success'):
                host_result.dns_status = "✅"
                host_result.dns_result = dns_result
            else:
                host_result.dns_status = "❌"
                host_result.errors.append("DNS failed")
            
            # Update TCP status
            if not isinstance(tcp_result, Exception) and tcp_result.get('success'):
                host_result.tcp_status = "✅"
                host_result.tcp_result = tcp_result
            else:
                host_result.tcp_status = "❌"
                host_result.errors.append("TCP failed")
            
            # Update HTTP status
            if not isinstance(http_result, Exception) and http_result.get('success'):
                host_result.http_status = "✅"
                host_result.http_result = http_result
            else:
                host_result.http_status = "❌"
                host_result.errors.append("HTTP failed")
            
            # Update SSL status
            if not isinstance(ssl_result, Exception) and ssl_result.get('success'):
                host_result.ssl_status = "✅"
                host_result.ssl_result = ssl_result
                host_result.ssl_grade = ssl_result.get('security_grade', 'Unknown')
            else:
                host_result.ssl_status = "❌"
                host_result.errors.append("SSL failed")
            
            # Update ICMP result
            if not isinstance(icmp_result, Exception):
                host_result.icmp_result = icmp_result
            
            # Calculate overall status
            if host_result.tcp_status == "✅" and host_result.http_status == "✅":
                host_result.status = "✅ UP"
                host_result.successful_checks += 1
            elif host_result.tcp_status == "✅":
                host_result.status = "⚠️ PARTIAL"
            else:
                host_result.status = "❌ DOWN"
            
            # Update timing and statistics
            host_result.response_time = int((time.time() - start_time) * 1000)
            host_result.last_check = datetime.now()
            host_result.total_checks += 1
            
            # Calculate uptime
            if host_result.total_checks > 0:
                host_result.uptime = (host_result.successful_checks / host_result.total_checks) * 100
            
            # Update the table
            table = self.query_one("#hosts-table", DataTable)
            self._update_host_row(table, host_result)
            
            # Log completion
            log.write_line(f"✅ Completed check for {host_result.host} - {host_result.status} ({host_result.response_time}ms)")
            
        except Exception as e:
            host_result.status = "❌ ERROR"
            host_result.errors.append(str(e))
            host_result.last_check = datetime.now()
            host_result.total_checks += 1
            
            log.write_line(f"❌ Error checking {host_result.host}: {str(e)}")
    
    async def _check_single_host(self, host_key: str) -> None:
        """Check a single host and update its status."""
        await self._check_single_host_internal(host_key)
    
    async def _check_all_hosts(self) -> None:
        """Check all hosts concurrently."""
        log = self.query_one("#main-log", Log)
        log.write_line(f"🔄 Refreshing all {len(self.hosts)} hosts...")
        
        # Check all hosts concurrently using the actual async methods
        tasks = []
        for host_key in self.hosts.keys():
            tasks.append(self._check_single_host_internal(host_key))
        
        await asyncio.gather(*tasks)
        log.write_line("✅ All hosts refreshed")
    
    def action_refresh_current(self) -> None:
        """Refresh the currently selected host."""
        table = self.query_one("#hosts-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.hosts):
            host_keys = list(self.hosts.keys())
            if table.cursor_row < len(host_keys):
                host_key = host_keys[table.cursor_row]
                asyncio.create_task(self._check_single_host(host_key))
    
    def action_refresh_all(self) -> None:
        """Refresh all hosts."""
        asyncio.create_task(self._check_all_hosts())
    
    def action_show_ssl_details(self) -> None:
        """Show SSL certificate details for selected host."""
        table = self.query_one("#hosts-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.hosts):
            host_keys = list(self.hosts.keys())
            if table.cursor_row < len(host_keys):
                host_key = host_keys[table.cursor_row]
                host_result = self.hosts[host_key]
                
                # Show SSL details modal
                def handle_ssl_detail_result(result: Optional[str]) -> None:
                    pass  # Modal closed
                
                self.push_screen(SSLDetailScreen(host_result), handle_ssl_detail_result)
    
    def action_toggle_monitoring(self) -> None:
        """Toggle automatic monitoring mode."""
        self.monitoring_active = not self.monitoring_active
        
        log = self.query_one("#main-log", Log)
        
        if self.monitoring_active:
            # Start monitoring timer
            self.monitor_timer = self.set_interval(self.refresh_interval, self._monitor_callback)
            log.write_line(f"📊 Started monitoring (interval: {self.refresh_interval}s)")
            self.notify("� Monitoring started")
        else:
            # Stop monitoring timer
            if self.monitor_timer:
                self.monitor_timer.stop()
                self.monitor_timer = None
            log.write_line("⏸️ Stopped monitoring")
            self.notify("⏸️ Monitoring stopped")
    
    def _monitor_callback(self) -> None:
        """Callback for monitoring timer."""
        if self.monitoring_active:
            asyncio.create_task(self._check_all_hosts())
    
    def action_command_mode(self) -> None:
        """Enter command mode (like k9s :command)"""
        from textual.screen import ModalScreen
        from textual.widgets import Input
        from textual.containers import Container
        
        def handle_command_result(result: Optional[str]) -> None:
            if result and result.strip():
                # Parse command (for now just add as host)
                host = result.strip()
                if host.startswith(':'):
                    host = host[1:]  # Remove : prefix
                
                # Add default port if not specified
                if ':' not in host:
                    hostname = host
                    host_key = f"{host}:443"
                    port = 443
                else:
                    try:
                        hostname, port_str = host.rsplit(':', 1)
                        port = int(port_str)
                        host_key = host
                    except (ValueError, AttributeError):
                        hostname = host
                        port = 443
                        host_key = f"{host}:443"
                
                # Add new host
                host_result = HostResult(host=hostname, port=port)
                self.hosts[host_key] = host_result
                
                # Add to table
                table = self.query_one("#hosts-table", DataTable)
                self._add_host_row(table, host_result)
                
                # Start monitoring immediately
                asyncio.create_task(self._check_single_host(host_key))
        
        # Create a simple input screen for commands
        class CommandScreen(ModalScreen[str]):
            def compose(self):
                with Container(id="command-container"):
                    yield Input(placeholder="Enter command (e.g., google.com:443)", id="command_input")
            
            def on_mount(self) -> None:
                self.query_one("#command_input", Input).focus()
            
            def on_input_submitted(self, event: Input.Submitted) -> None:
                self.dismiss(event.value)
            
            def on_key(self, event) -> None:
                if event.key == "escape":
                    self.dismiss("")
        
        self.push_screen(CommandScreen(), handle_command_result)
    
    def action_help(self) -> None:
        """Show help information."""
        help_text = """
EZNet TUI - Network Testing Dashboard

Navigation:
  j/k or ↑/↓    Navigate hosts
  :             Command mode (add hosts like :google.com)
  d             Show SSL certificate details
  r             Refresh current host
  R             Refresh all hosts
  m             Toggle monitoring mode
  q             Quit
  ?             Show this help

Like k9s for network testing! 🚀
        """
        self.notify(help_text.strip())
    
    def action_cursor_down(self) -> None:
        """Move cursor down in table."""
        table = self.query_one("#hosts-table", DataTable)
        table.action_cursor_down()
    
    def action_cursor_up(self) -> None:
        """Move cursor up in table."""
        table = self.query_one("#hosts-table", DataTable)
        table.action_cursor_up()


def run_tui(hosts: Optional[List[str]] = None) -> None:
    """Run the EZNet TUI application."""
    try:
        app = EZNetTUI(initial_hosts=hosts)
        app.run()
    except KeyboardInterrupt:
        print("\n👋 EZNet TUI stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error running TUI: {e}")
        print("Try running with: eznet --help")


if __name__ == "__main__":
    run_tui()