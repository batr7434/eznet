#!/usr/bin/env python3
"""
EZNet CLI - Main entry point for the network testing tool.

This module provides the command-line interface using Click and orchestrates
all network tests asynchronously.
"""

import asyncio
import json
import sys
import datetime
from typing import Dict, Any, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from .dns_check import DNSChecker
from .tcp_check import TCPChecker
from .http_check import HTTPChecker
from .icmp_check import ICMPChecker
from .ssl_check import SSLChecker
from .utils import format_duration, is_valid_ip, is_valid_hostname, parse_ports, get_common_ports, get_port_description


console = Console()


class EZNetResult:
    """Container for all network probe results."""
    
    def __init__(self, host: str, ports: Optional[list] = None):
        self.host = host
        self.ports = ports or []
        self.dns_results = {}
        self.tcp_results = {}  # Changed to dict for multiple ports
        self.http_results = {}  # Changed to dict for multiple ports
        self.ssl_results = {}   # New for SSL checks
        self.icmp_result = {}
        self.start_time = None
        self.end_time = None
    
    @property
    def port(self):
        """Backward compatibility - return first port if single port"""
        return self.ports[0] if len(self.ports) == 1 else None
    
    @property 
    def tcp_result(self):
        """Backward compatibility - return first TCP result"""
        if len(self.ports) == 1:
            return self.tcp_results.get(self.ports[0], {})
        return {}
    
    @property
    def http_result(self):
        """Backward compatibility - return first HTTP result"""
        if len(self.ports) == 1:
            return self.http_results.get(self.ports[0], {})
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for JSON output."""
        result = {
            "host": self.host,
            "ports": self.ports,
            "dns": self.dns_results,
            "icmp": self.icmp_result,
            "duration_ms": format_duration(self.start_time, self.end_time) if self.start_time and self.end_time else None
        }
        
        # Add port-specific results
        if self.tcp_results:
            result["tcp"] = self.tcp_results
        if self.http_results:
            result["http"] = self.http_results
        if self.ssl_results:
            result["ssl"] = self.ssl_results
        
        # Backward compatibility for single port
        if len(self.ports) == 1:
            port = self.ports[0]
            result["port"] = port
            if port in self.tcp_results:
                result["tcp_single"] = self.tcp_results[port]
            if port in self.http_results:
                result["http_single"] = self.http_results[port]
            if port in self.ssl_results:
                result["ssl_single"] = self.ssl_results[port]
        
        return result


async def run_port_scan(host: str, ports: list, timeout: int, ssl_check: bool, max_concurrent: int = 50) -> EZNetResult:
    """Run port scanning tests on multiple ports."""
    result = EZNetResult(host, ports)
    result.start_time = asyncio.get_event_loop().time()
    
    # Initialize checkers
    dns_checker = DNSChecker(timeout=timeout)
    tcp_checker = TCPChecker(timeout=timeout)
    http_checker = HTTPChecker(timeout=timeout)
    icmp_checker = ICMPChecker(timeout=timeout)
    ssl_checker = SSLChecker(timeout=timeout) if ssl_check else None
    
    # Run DNS and ICMP once (not port-specific)
    dns_task = dns_checker.check(host)
    icmp_task = icmp_checker.check(host)
    
    # Run port-specific checks concurrently
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_port_with_semaphore(port):
        async with semaphore:
            tasks = [tcp_checker.check(host, port)]
            
            # Add HTTP check for web ports
            if port in [80, 443, 8080, 8443]:
                tasks.append(http_checker.check(host, port))
            
            # Add SSL check for HTTPS ports
            if ssl_check and port in [443, 8443, 993, 995, 465, 587, 636]:
                tasks.append(ssl_checker.check(host, port))
            
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    # Execute all tasks
    dns_result, icmp_result = await asyncio.gather(dns_task, icmp_task, return_exceptions=True)
    port_results = await asyncio.gather(*[check_port_with_semaphore(port) for port in ports], return_exceptions=True)
    
    # Process results
    result.dns_results = dns_result if not isinstance(dns_result, Exception) else {"error": str(dns_result)}
    result.icmp_result = icmp_result if not isinstance(icmp_result, Exception) else {"error": str(icmp_result)}
    
    # Process port-specific results
    for i, port_result_list in enumerate(port_results):
        port = ports[i]
        
        if isinstance(port_result_list, Exception):
            result.tcp_results[port] = {"error": str(port_result_list)}
            continue
        
        # TCP result is always first
        if len(port_result_list) > 0 and not isinstance(port_result_list[0], Exception):
            result.tcp_results[port] = port_result_list[0]
        
        # HTTP result (if requested)
        if len(port_result_list) > 1 and not isinstance(port_result_list[1], Exception):
            result.http_results[port] = port_result_list[1]
        
        # SSL result (if requested)
        if len(port_result_list) > 2 and not isinstance(port_result_list[2], Exception):
            result.ssl_results[port] = port_result_list[2]
    
    result.end_time = asyncio.get_event_loop().time()
    return result


def display_port_scan_results(result: EZNetResult) -> None:
    """Display results for port scanning."""
    
    # Create main title
    ports_desc = f"{len(result.ports)} ports" if len(result.ports) > 1 else f"port {result.ports[0]}"
    title = f"EZNet Port Scan Results for {result.host} ({ports_desc})"
    
    console.print(Panel(title, style="bold blue"))
    
    # DNS Results (same as before)
    if result.dns_results:
        dns_table = Table(title="🌐 DNS Resolution", box=box.ROUNDED)
        dns_table.add_column("Record Type", style="cyan")
        dns_table.add_column("Status", style="green")
        dns_table.add_column("Result", style="white")
        
        dns_data = result.dns_results
        if "ipv4" in dns_data:
            status = "✅ Success" if dns_data["ipv4"]["success"] else "❌ Failed"
            addresses = ", ".join(dns_data["ipv4"].get("addresses", [])) if dns_data["ipv4"]["success"] else dns_data["ipv4"].get("error", "")
            dns_table.add_row("IPv4 (A)", status, addresses)
        
        if "ipv6" in dns_data:
            status = "✅ Success" if dns_data["ipv6"]["success"] else "❌ Failed"
            addresses = ", ".join(dns_data["ipv6"].get("addresses", [])) if dns_data["ipv6"]["success"] else dns_data["ipv6"].get("error", "")
            dns_table.add_row("IPv6 (AAAA)", status, addresses)
        
        console.print(dns_table)
        console.print()
    
    # Port Scan Results
    if result.tcp_results:
        port_table = Table(title="🔍 Port Scan Results", box=box.ROUNDED)
        port_table.add_column("Port", style="cyan")
        port_table.add_column("Service", style="yellow")
        port_table.add_column("Status", style="green")
        port_table.add_column("Response Time", style="white")
        
        # Sort ports for better display
        sorted_ports = sorted(result.ports)
        open_ports = []
        
        for port in sorted_ports:
            tcp_data = result.tcp_results.get(port, {})
            service = get_port_description(port)
            
            if tcp_data.get("success"):
                status = "✅ Open"
                response_time = f"{tcp_data.get('response_time_ms', 0):.1f} ms"
                open_ports.append(port)
            else:
                status = "❌ Closed"
                response_time = tcp_data.get("error", "Connection failed")
            
            port_table.add_row(str(port), service, status, response_time)
        
        console.print(port_table)
        
        # Summary
        total_ports = len(result.ports)
        open_count = len(open_ports)
        console.print(f"\n[bold]Summary:[/bold] {open_count}/{total_ports} ports open")
        if open_ports:
            console.print(f"[green]Open ports:[/green] {', '.join(map(str, open_ports))}")
        console.print()
    
    # HTTP Results for open web ports
    web_ports = [p for p in result.ports if p in result.http_results and result.http_results[p].get("success")]
    if web_ports:
        http_table = Table(title="🌍 HTTP Services", box=box.ROUNDED)
        http_table.add_column("Port", style="cyan")
        http_table.add_column("Status", style="green")
        http_table.add_column("Server", style="white")
        http_table.add_column("Response Time", style="white")
        
        for port in sorted(web_ports):
            http_data = result.http_results[port]
            status = f"{http_data.get('status_code')} {http_data.get('reason_phrase', '')}"
            server = http_data.get('server', 'Unknown')
            response_time = f"{http_data.get('response_time_ms', 0):.1f} ms"
            
            http_table.add_row(str(port), status, server, response_time)
        
        console.print(http_table)
        console.print()
    
    # SSL Results
    ssl_ports = [p for p in result.ports if p in result.ssl_results and isinstance(result.ssl_results[p], dict) and result.ssl_results[p].get("success")]
    if ssl_ports:
        ssl_table = Table(title="🔒 SSL/TLS Certificates", box=box.ROUNDED)
        ssl_table.add_column("Port", style="cyan")
        ssl_table.add_column("Grade", style="green")
        ssl_table.add_column("Valid Until", style="white")
        ssl_table.add_column("Issuer", style="white")
        
        for port in sorted(ssl_ports):
            ssl_data = result.ssl_results[port]
            cert = ssl_data.get("certificate", {})
            security = ssl_data.get("security_score", {})
            
            grade = security.get("grade", "?")
            grade_color = "green" if grade.startswith("A") else "yellow" if grade in ["B", "C"] else "red"
            
            valid_until = cert.get("not_after", "Unknown")
            if valid_until != "Unknown" and "GMT" in valid_until:
                try:
                    # Parse the date string format from SSL certificate
                    date_obj = datetime.datetime.strptime(valid_until, "%b %d %H:%M:%S %Y GMT")
                    valid_until = date_obj.strftime("%Y-%m-%d")
                except:
                    pass
            
            # Extract issuer organization name
            issuer_info = cert.get("issuer", "Unknown")
            if isinstance(issuer_info, str) and "CN=" in issuer_info:
                # Extract just the CN part
                issuer_parts = issuer_info.split(",")
                for part in issuer_parts:
                    if "CN=" in part:
                        issuer_org = part.strip().replace("CN=", "")
                        break
                else:
                    issuer_org = "Unknown"
            else:
                issuer_org = "Unknown"
            
            ssl_table.add_row(
                str(port), 
                f"[{grade_color}]{grade}[/{grade_color}]", 
                valid_until, 
                issuer_org
            )
        
        console.print(ssl_table)
        console.print()
    
    # ICMP Results
    if result.icmp_result:
        icmp_table = Table(title="🏓 ICMP Ping", box=box.ROUNDED)
        icmp_table.add_column("Target", style="cyan")
        icmp_table.add_column("Status", style="green")
        icmp_table.add_column("Response Time", style="white")
        
        icmp_data = result.icmp_result
        status = "✅ Reachable" if icmp_data.get("success") else "❌ Unreachable"
        response_time = f"{icmp_data.get('response_time_ms', 0):.1f} ms" if icmp_data.get("success") else icmp_data.get("error", "")
        icmp_table.add_row(result.host, status, response_time)
        
        console.print(icmp_table)
        console.print()
    
    # Summary
    if result.start_time and result.end_time:
        duration = format_duration(result.start_time, result.end_time)
        console.print(f"[dim]Total scan time: {duration:.1f} ms[/dim]")


async def run_multi_host_checks(hosts: list, port: Optional[int], timeout: int, max_concurrent: int = 50, ssl_check: bool = False) -> dict:
    """Run network checks for multiple hosts concurrently."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_host_with_semaphore(host):
        async with semaphore:
            return await run_all_checks(host, port, timeout, ssl_check)
    
    start_time = asyncio.get_event_loop().time()
    
    # Run all checks concurrently
    tasks = [check_host_with_semaphore(host) for host in hosts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = asyncio.get_event_loop().time()
    
    # Process results
    host_results = {}
    successful_hosts = 0
    
    for i, result in enumerate(results):
        host = hosts[i]
        if isinstance(result, Exception):
            host_results[host] = {
                "success": False,
                "error": str(result),
                "host": host,
                "port": port
            }
        else:
            host_results[host] = result.to_dict()
            if result.dns_results.get("ipv4", {}).get("success") or result.icmp_result.get("success"):
                successful_hosts += 1
    
    return {
        "scan_timestamp": start_time,
        "total_hosts": len(hosts),
        "successful_hosts": successful_hosts,
        "total_duration_ms": format_duration(start_time, end_time),
        "results": host_results
    }


def display_multi_host_results(results: dict, hosts: list) -> None:
    """Display results for multiple hosts."""
    
    # Summary header
    total_hosts = results["total_hosts"]
    successful_hosts = results["successful_hosts"]
    duration = results["total_duration_ms"]
    
    console.print(Panel(
        f"Multi-Host Scan Results: {successful_hosts}/{total_hosts} hosts reachable ({duration:.1f} ms total)",
        style="bold blue"
    ))
    
    # Create summary table
    summary_table = Table(title="📊 Host Summary", box=box.ROUNDED)
    summary_table.add_column("Host", style="cyan")
    summary_table.add_column("DNS", style="white")
    summary_table.add_column("TCP", style="white")
    summary_table.add_column("HTTP", style="white")
    summary_table.add_column("ICMP", style="white")
    summary_table.add_column("Status", style="green")
    
    for host in hosts:
        result = results["results"].get(host, {})
        
        # Status indicators
        dns_status = "✅" if result.get("dns", {}).get("ipv4", {}).get("success") else "❌"
        tcp_status = "✅" if result.get("tcp", {}).get("success") else "❌" if result.get("tcp") else "⊝"
        http_status = "✅" if result.get("http", {}).get("success") else "❌" if result.get("http") else "⊝"
        icmp_status = "✅" if result.get("icmp", {}).get("success") else "❌"
        
        # Overall status
        if result.get("error"):
            overall_status = f"❌ Error: {result['error']}"
        elif dns_status == "✅" or icmp_status == "✅":
            overall_status = "✅ Reachable"
        else:
            overall_status = "❌ Unreachable"
        
        summary_table.add_row(
            host,
            dns_status,
            tcp_status,
            http_status,
            icmp_status,
            overall_status
        )
    
    console.print(summary_table)
    console.print()
    
    # Show detailed results for failed hosts
    failed_hosts = [host for host in hosts if not results["results"].get(host, {}).get("dns", {}).get("ipv4", {}).get("success")]
    if failed_hosts and len(failed_hosts) < len(hosts):
        console.print("[yellow]Detailed results for failed hosts:[/yellow]")
        for host in failed_hosts[:3]:  # Show max 3 detailed failures
            result_obj = type('Result', (), {
                'host': host,
                'port': results["results"].get(host, {}).get("port"),
                'dns_results': results["results"].get(host, {}).get("dns", {}),
                'tcp_result': results["results"].get(host, {}).get("tcp", {}),
                'http_result': results["results"].get(host, {}).get("http", {}),
                'icmp_result': results["results"].get(host, {}).get("icmp", {}),
                'start_time': None,
                'end_time': None
            })()
            display_results(result_obj)


async def run_all_checks(host: str, port: Optional[int], timeout: int, ssl_check: bool = False) -> EZNetResult:
    """Run all network checks asynchronously."""
    ports = [port] if port else []
    result = EZNetResult(host, ports)
    result.start_time = asyncio.get_event_loop().time()
    
    # Initialize checkers
    dns_checker = DNSChecker(timeout=timeout)
    tcp_checker = TCPChecker(timeout=timeout)
    http_checker = HTTPChecker(timeout=timeout)
    icmp_checker = ICMPChecker(timeout=timeout)
    ssl_checker = SSLChecker(timeout=timeout) if ssl_check else None
    
    # Run checks concurrently
    tasks = [
        dns_checker.check(host),
        icmp_checker.check(host)
    ]
    
    # Add TCP check if port is specified
    if port:
        tasks.append(tcp_checker.check(host, port))
        
        # Add HTTP check for common web ports
        if port in [80, 443, 8080, 8443]:
            tasks.append(http_checker.check(host, port))
        
        # Add SSL check for HTTPS ports
        if ssl_check and port in [443, 8443, 993, 995, 465, 587, 636]:
            tasks.append(ssl_checker.check(host, port))
    
    # Execute all tasks
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    result.dns_results = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
    result.icmp_result = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}
    
    if port:
        # TCP result
        if len(results) > 2:
            result.tcp_results[port] = results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])}
        
        # HTTP result
        if len(results) > 3:
            result.http_results[port] = results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])}
        
        # SSL result (ensure it's a dictionary)
        if len(results) > 4:
            ssl_result = results[4] if not isinstance(results[4], Exception) else {"error": str(results[4])}
            if isinstance(ssl_result, dict):
                result.ssl_results[port] = ssl_result
    
    result.end_time = asyncio.get_event_loop().time()
    return result


def display_results(result: EZNetResult) -> None:
    """Display results in a nice formatted table."""
    
    # Create main title
    title = f"EZNet Results for {result.host}"
    if result.port:
        title += f":{result.port}"
    
    console.print(Panel(title, style="bold blue"))
    
    # DNS Results
    if result.dns_results:
        dns_table = Table(title="🌐 DNS Resolution", box=box.ROUNDED)
        dns_table.add_column("Record Type", style="cyan")
        dns_table.add_column("Status", style="green")
        dns_table.add_column("Result", style="white")
        
        dns_data = result.dns_results
        if "ipv4" in dns_data:
            status = "✅ Success" if dns_data["ipv4"]["success"] else "❌ Failed"
            addresses = ", ".join(dns_data["ipv4"].get("addresses", [])) if dns_data["ipv4"]["success"] else dns_data["ipv4"].get("error", "")
            dns_table.add_row("IPv4 (A)", status, addresses)
        
        if "ipv6" in dns_data:
            status = "✅ Success" if dns_data["ipv6"]["success"] else "❌ Failed"
            addresses = ", ".join(dns_data["ipv6"].get("addresses", [])) if dns_data["ipv6"]["success"] else dns_data["ipv6"].get("error", "")
            dns_table.add_row("IPv6 (AAAA)", status, addresses)
        
        console.print(dns_table)
        console.print()
    
    # TCP Results
    if result.tcp_result:
        tcp_table = Table(title="🔌 TCP Connection", box=box.ROUNDED)
        tcp_table.add_column("Target", style="cyan")
        tcp_table.add_column("Status", style="green")
        tcp_table.add_column("Response Time", style="white")
        
        tcp_data = result.tcp_result
        status = "✅ Open" if tcp_data.get("success") else "❌ Closed/Filtered"
        response_time = f"{tcp_data.get('response_time_ms', 0):.1f} ms" if tcp_data.get("success") else tcp_data.get("error", "")
        tcp_table.add_row(f"{result.host}:{result.port}", status, response_time)
        
        console.print(tcp_table)
        console.print()
    
    # HTTP Results
    if result.http_result:
        http_table = Table(title="🌍 HTTP Check", box=box.ROUNDED)
        http_table.add_column("Property", style="cyan")
        http_table.add_column("Value", style="white")
        
        http_data = result.http_result
        if http_data.get("success"):
            http_table.add_row("Status", f"✅ {http_data.get('status_code')} {http_data.get('reason_phrase', '')}")
            http_table.add_row("Response Time", f"{http_data.get('response_time_ms', 0):.1f} ms")
            http_table.add_row("Content Type", http_data.get("content_type", "Unknown"))
            http_table.add_row("Server", http_data.get("server", "Unknown"))
            if http_data.get("redirect_url"):
                http_table.add_row("Redirect", http_data["redirect_url"])
        else:
            http_table.add_row("Status", f"❌ Failed: {http_data.get('error', 'Unknown error')}")
        
        console.print(http_table)
        console.print()
    
    # SSL Results
    if result.ssl_results:
        ssl_ports = [p for p in result.ports if p in result.ssl_results and result.ssl_results[p].get("success")]
        if ssl_ports:
            ssl_table = Table(title="🔒 SSL/TLS Certificate", box=box.ROUNDED)
            ssl_table.add_column("Property", style="cyan")
            ssl_table.add_column("Value", style="white")
            
            port = ssl_ports[0]  # Show first SSL result
            ssl_data = result.ssl_results[port]
            cert = ssl_data.get("certificate", {})
            security = ssl_data.get("security_score", {})
            
            # Security grade with color
            grade = security.get("grade", "?")
            grade_color = "green" if grade.startswith("A") else "yellow" if grade in ["B", "C"] else "red"
            
            ssl_table.add_row("Security Grade", f"[{grade_color}]{grade}[/{grade_color}] ({security.get('score', 0)}/100)")
            ssl_table.add_row("Subject", cert.get("subject", "Unknown"))
            
            # Handle issuer which could be a string or dict
            issuer = cert.get("issuer", "Unknown")
            if isinstance(issuer, str):
                # Extract just the first part or organization name
                if "CN=" in issuer:
                    issuer_display = issuer.split(",")[0].replace("CN=", "").strip()
                else:
                    issuer_display = issuer
            else:
                issuer_display = issuer.get("organizationName", "Unknown") if isinstance(issuer, dict) else "Unknown"
            
            ssl_table.add_row("Issuer", issuer_display)
            
            # Expiry information
            days_until_expiry = cert.get("days_until_expiry", 0)
            if days_until_expiry is None:
                days_until_expiry = 0
            
            if days_until_expiry > 30:
                expiry_color = "green"
            elif days_until_expiry > 7:
                expiry_color = "yellow"
            else:
                expiry_color = "red"
            ssl_table.add_row("Days Until Expiry", f"[{expiry_color}]{days_until_expiry}[/{expiry_color}]")
            
            # Certificate validity dates
            not_after = cert.get("not_after", "Unknown")
            ssl_table.add_row("Valid Until", not_after)
            
            # Security issues
            issues = security.get("issues", [])
            if issues:
                ssl_table.add_row("Security Issues", ", ".join(issues))
            else:
                ssl_table.add_row("Security Issues", "[green]None detected[/green]")
            
            # Issues
            issues = security.get("issues", [])
            if issues:
                ssl_table.add_row("Issues", "; ".join(issues[:3]))  # Show max 3 issues
            
            console.print(ssl_table)
            console.print()
    
    # ICMP Results
    if result.icmp_result:
        icmp_table = Table(title="🏓 ICMP Ping", box=box.ROUNDED)
        icmp_table.add_column("Target", style="cyan")
        icmp_table.add_column("Status", style="green")
        icmp_table.add_column("Response Time", style="white")
        
        icmp_data = result.icmp_result
        status = "✅ Reachable" if icmp_data.get("success") else "❌ Unreachable"
        response_time = f"{icmp_data.get('response_time_ms', 0):.1f} ms" if icmp_data.get("success") else icmp_data.get("error", "")
        icmp_table.add_row(result.host, status, response_time)
        
        console.print(icmp_table)
        console.print()
    
    # Summary
    if result.start_time and result.end_time:
        duration = format_duration(result.start_time, result.end_time)
        console.print(f"[dim]Total scan time: {duration:.1f} ms[/dim]")


@click.command()
@click.argument("host", required=False)
@click.option("--hosts-file", type=click.Path(exists=True), help="File containing list of hosts (one per line)")
@click.option("--port", "-p", help="Port number to test (can be single port, range like 80-90, or comma-separated)")
@click.option("--common-ports", is_flag=True, help="Scan common ports (top 100)")
@click.option("--ssl-check", is_flag=True, help="Perform SSL/TLS certificate analysis (for HTTPS ports)")
@click.option("--timeout", "-t", default=5, help="Timeout in seconds (default: 5)")
@click.option("--json", "output_json", is_flag=True, help="Output results in JSON format")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--max-concurrent", default=50, help="Maximum concurrent connections (default: 50)")
@click.version_option(version="0.2.0", prog_name="eznet")
def main(host: Optional[str], hosts_file: Optional[str], port: Optional[str], common_ports: bool, ssl_check: bool, timeout: int, output_json: bool, verbose: bool, max_concurrent: int) -> None:
    """
    EZNet - Comprehensive network testing tool.
    
    Automatically performs DNS resolution, TCP connection tests, HTTP checks,
    and ICMP ping tests without requiring you to remember specific commands.
    
    Examples:
    
        eznet google.com
        
        eznet google.com -p 80
        
        eznet google.com -p 80-90
        
        eznet google.com --common-ports
        
        eznet google.com,github.com,stackoverflow.com -p 80
        
        eznet --hosts-file hosts.txt -p 443
        
        eznet google.com -p 443 --ssl-check
        
        eznet 8.8.8.8 -p 53 --json
    """
    # Validate input - either host or hosts-file must be provided
    if not host and not hosts_file:
        console.print("[red]Error: Either HOST or --hosts-file must be provided[/red]")
        console.print("[yellow]Usage: eznet HOST [OPTIONS][/yellow]")
        console.print("[yellow]   or: eznet --hosts-file FILE [OPTIONS][/yellow]")
        sys.exit(1)
    
    if host and hosts_file:
        console.print("[red]Error: Cannot use both HOST and --hosts-file[/red]")
        sys.exit(1)
    
    # Prepare host list
    hosts = []
    if host:
        # Handle comma-separated hosts
        hosts = [h.strip() for h in host.split(',') if h.strip()]
    elif hosts_file:
        # Read hosts from file
        with open(hosts_file, 'r') as f:
            hosts = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Parse ports
    ports = []
    if port:
        try:
            ports = parse_ports(port)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    elif common_ports:
        ports = get_common_ports()
        if verbose:
            console.print(f"[dim]Scanning {len(ports)} common ports[/dim]")
    
    # Validate port count
    if len(ports) > 1000:
        console.print("[red]Error: Too many ports specified (max 1000)[/red]")
        sys.exit(1)
    
    # Validate hosts
    for h in hosts:
        if not is_valid_hostname(h) and not is_valid_ip(h):
            console.print(f"[red]Error: Invalid hostname or IP address: {h}[/red]")
            sys.exit(1)
    
    if verbose:
        hosts_desc = f"{len(hosts)} hosts" if len(hosts) > 1 else hosts[0]
        ports_desc = f"{len(ports)} ports" if len(ports) > 1 else (f"port {ports[0]}" if ports else "no specific port")
        console.print(f"[dim]Starting network probe for {hosts_desc}, {ports_desc} with {timeout}s timeout[/dim]")
        if ssl_check:
            console.print("[dim]SSL certificate analysis enabled[/dim]")
    
    try:
        if len(hosts) == 1 and len(ports) <= 1:
            # Single host, single/no port - use original logic
            single_port = ports[0] if ports else None
            result = asyncio.run(run_all_checks(hosts[0], single_port, timeout, ssl_check))
            
            if output_json:
                print(json.dumps(result.to_dict(), indent=2))
            else:
                display_results(result)
        elif len(hosts) == 1:
            # Single host, multiple ports - port scanning
            result = asyncio.run(run_port_scan(hosts[0], ports, timeout, ssl_check, max_concurrent))
            
            if output_json:
                print(json.dumps(result.to_dict(), indent=2))
            else:
                display_port_scan_results(result)
        else:
            # Multiple hosts - run concurrently
            single_port = ports[0] if len(ports) == 1 else None
            results = asyncio.run(run_multi_host_checks(hosts, single_port, timeout, max_concurrent, ssl_check))
            
            if output_json:
                print(json.dumps(results, indent=2))
            else:
                display_multi_host_results(results, hosts)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()