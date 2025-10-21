"""
EZNet TUI - Results Screen.

This module implements the detailed results view similar to k9s resource details.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Static, TabbedContent, TabPane
from textual.screen import ModalScreen
from textual.binding import Binding
from textual import work

from ..cli import EZNetResult


class ResultsScreen(ModalScreen):
    """Screen showing detailed scan results for a host."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]
    
    CSS = """
    ResultsScreen {
        background: $surface;
        border: solid $accent;
        padding: 1;
    }
    
    .results-title {
        text-align: center;
        text-style: bold;
        background: $primary;
        color: $text;
        height: 1;
        margin: 0 0 1 0;
    }
    
    DataTable {
        border: solid $accent;
        margin: 1 0;
    }
    """
    
    def __init__(self, results: EZNetResult, hostname: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = results
        self.hostname = hostname
    
    def compose(self) -> ComposeResult:
        """Compose the results screen."""
        with Vertical():
            yield Static(f"📊 Results for {self.hostname}", classes="results-title")
            
            with TabbedContent():
                with TabPane("DNS", id="dns-tab"):
                    yield self.create_dns_table()
                
                with TabPane("Ports", id="ports-tab"):
                    yield self.create_ports_table()
                
                with TabPane("HTTP", id="http-tab"):
                    yield self.create_http_table()
                
                with TabPane("ICMP", id="icmp-tab"):
                    yield self.create_icmp_table()
            
            yield Static("Press 'Esc' to go back, 'r' to refresh", id="results-status")
    
    def create_dns_table(self) -> DataTable:
        """Create DNS results table."""
        table = DataTable()
        self.populate_dns_table(table)
        return table
    
    def create_ports_table(self) -> DataTable:
        """Create ports scan results table."""
        table = DataTable()
        self.populate_ports_table(table)
        return table
    
    def create_http_table(self) -> DataTable:
        """Create HTTP results table."""
        table = DataTable()
        self.populate_http_table(table)
        return table
    
    def create_icmp_table(self) -> DataTable:
        """Create ICMP results table."""
        table = DataTable()
        self.populate_icmp_table(table)
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
    
    @work(exclusive=True)
    async def action_refresh(self) -> None:
        """Refresh the results by rescanning the host."""
        status = self.query_one("#results-status", Static)
        status.update("Refreshing results...")
        
        try:
            # Import the scan function
            from ..cli import run_port_scan
            
            # Get the ports from current results
            ports = list(self.results.tcp_results.keys()) if self.results.tcp_results else [80, 443]
            
            # Rescan the host
            new_results = await run_port_scan(
                self.hostname, 
                ports, 
                timeout=5, 
                ssl_check=True, 
                max_concurrent=5
            )
            
            # Update the results
            self.results = new_results
            
            # Refresh all tabs by updating their content
            self.update_all_tables()
            
            status.update(f"Results refreshed for {self.hostname}")
            
        except Exception as e:
            status.update(f"Refresh failed: {str(e)}")
    
    def update_all_tables(self) -> None:
        """Update all tables with new results data."""
        try:
            # Update DNS table
            dns_tab = self.query_one("#dns-tab")
            dns_table = dns_tab.query_one(DataTable)
            dns_table.clear()
            self.populate_dns_table(dns_table)
            
            # Update Ports table
            ports_tab = self.query_one("#ports-tab")  
            ports_table = ports_tab.query_one(DataTable)
            ports_table.clear()
            self.populate_ports_table(ports_table)
            
            # Update HTTP table
            http_tab = self.query_one("#http-tab")
            http_table = http_tab.query_one(DataTable)  
            http_table.clear()
            self.populate_http_table(http_table)
            
            # Update ICMP table
            icmp_tab = self.query_one("#icmp-tab")
            icmp_table = icmp_tab.query_one(DataTable)
            icmp_table.clear()
            self.populate_icmp_table(icmp_table)
            
        except Exception as e:
            # If table update fails, just log the error
            pass
    
    def populate_dns_table(self, table: DataTable) -> None:
        """Populate DNS table with data."""
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
    
    def populate_ports_table(self, table: DataTable) -> None:
        """Populate ports table with data."""
        table.add_columns("Port", "Status", "Response Time", "Service")
        
        for port, result in self.results.tcp_results.items():
            status = "✅ Open" if result.get("success") else "❌ Closed"
            response_time = f"{result.get('response_time_ms', 0):.1f} ms" if result.get("success") else result.get("error", "")
            service = self.get_service_name(port)
            table.add_row(str(port), status, response_time, service)
    
    def populate_http_table(self, table: DataTable) -> None:
        """Populate HTTP table with data."""
        table.add_columns("Port", "Status Code", "Server", "Response Time")
        
        for port, result in self.results.http_results.items():
            if result.get("success"):
                status = f"{result.get('status_code')} {result.get('reason_phrase', '')}"
                server = result.get("server", "Unknown")
                response_time = f"{result.get('response_time_ms', 0):.1f} ms"
                table.add_row(str(port), status, server, response_time)
    
    def populate_icmp_table(self, table: DataTable) -> None:
        """Populate ICMP table with data."""
        table.add_columns("Target", "Status", "Response Time")
        
        icmp_data = self.results.icmp_result
        status = "✅ Reachable" if icmp_data.get("success") else "❌ Unreachable"
        response_time = f"{icmp_data.get('response_time_ms', 0):.1f} ms" if icmp_data.get("success") else icmp_data.get("error", "")
        
        table.add_row(self.hostname, status, response_time)