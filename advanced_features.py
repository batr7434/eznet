"""
Advanced features for EZNet - Implementation ideas and prototypes.

This file contains prototypes for advanced features that could be added to EZNet.
"""

import asyncio
import csv
import time
from typing import List, Dict, Any
from pathlib import Path
import yaml


class MultiHostScanner:
    """Scanner for multiple hosts simultaneously."""
    
    def __init__(self, max_concurrent: int = 50):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def scan_hosts(self, hosts: List[str], port: int = None) -> Dict[str, Any]:
        """Scan multiple hosts concurrently."""
        async def scan_with_semaphore(host):
            async with self.semaphore:
                from eznet.cli import run_all_checks
                return await run_all_checks(host, port, 5)
        
        tasks = [scan_with_semaphore(host) for host in hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "scan_timestamp": time.time(),
            "total_hosts": len(hosts),
            "results": dict(zip(hosts, results))
        }


class PortRangeScanner:
    """Scanner for port ranges."""
    
    async def scan_port_range(self, host: str, start_port: int, end_port: int) -> Dict[str, Any]:
        """Scan a range of ports on a single host."""
        from eznet.tcp_check import TCPChecker
        
        tcp_checker = TCPChecker(timeout=3)
        ports = list(range(start_port, end_port + 1))
        
        result = await tcp_checker.scan_ports(host, ports, max_concurrent=50)
        return result
    
    def get_common_ports(self) -> List[int]:
        """Get list of commonly used ports."""
        return [
            21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995,
            587, 465, 993, 995, 1433, 3306, 3389, 5432, 6379,
            8080, 8443, 9200, 27017
        ]


class ContinuousMonitor:
    """Continuous monitoring functionality."""
    
    def __init__(self, interval: int = 30):
        self.interval = interval
        self.running = False
        self.results_history = []
    
    async def monitor(self, host: str, port: int = None):
        """Monitor a host continuously."""
        from eznet.cli import run_all_checks
        
        self.running = True
        iteration = 0
        
        print(f"🔄 Starting continuous monitoring of {host}" + (f":{port}" if port else ""))
        print(f"📊 Checking every {self.interval} seconds (Ctrl+C to stop)")
        print("-" * 60)
        
        try:
            while self.running:
                iteration += 1
                start_time = time.time()
                
                result = await run_all_checks(host, port, 5)
                end_time = time.time()
                
                # Store result
                self.results_history.append({
                    "timestamp": start_time,
                    "iteration": iteration,
                    "result": result.to_dict(),
                    "response_time": end_time - start_time
                })
                
                # Display summary
                status = "🟢 UP" if self._is_healthy(result) else "🔴 DOWN"
                print(f"[{time.strftime('%H:%M:%S')}] #{iteration:03d} - {status} - {(end_time-start_time)*1000:.1f}ms")
                
                # Wait for next iteration
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n⏹️  Monitoring stopped after {iteration} iterations")
            self._generate_report()
    
    def _is_healthy(self, result) -> bool:
        """Determine if the result indicates a healthy service."""
        # Simple health check - customize as needed
        if result.tcp_result.get("success"):
            return True
        if result.icmp_result.get("success"):
            return True
        return False
    
    def _generate_report(self):
        """Generate a summary report."""
        if not self.results_history:
            return
        
        total_checks = len(self.results_history)
        successful_checks = sum(1 for r in self.results_history if self._is_healthy_dict(r["result"]))
        uptime_percentage = (successful_checks / total_checks) * 100
        
        print("\n📊 Monitoring Report:")
        print(f"   Total checks: {total_checks}")
        print(f"   Successful: {successful_checks}")
        print(f"   Uptime: {uptime_percentage:.1f}%")
    
    def _is_healthy_dict(self, result_dict: Dict) -> bool:
        """Check health from dictionary result."""
        return (result_dict.get("tcp", {}).get("success", False) or 
                result_dict.get("icmp", {}).get("success", False))


class OutputFormatter:
    """Advanced output formatting."""
    
    @staticmethod
    def to_csv(results: List[Dict[str, Any]], filepath: str):
        """Export results to CSV format."""
        if not results:
            return
        
        with open(filepath, 'w', newline='') as csvfile:
            # Flatten the nested structure for CSV
            flattened = []
            for result in results:
                flat = {
                    'host': result.get('host'),
                    'port': result.get('port'),
                    'dns_ipv4_success': result.get('dns', {}).get('ipv4', {}).get('success'),
                    'dns_ipv6_success': result.get('dns', {}).get('ipv6', {}).get('success'),
                    'tcp_success': result.get('tcp', {}).get('success'),
                    'tcp_response_time_ms': result.get('tcp', {}).get('response_time_ms'),
                    'http_success': result.get('http', {}).get('success'),
                    'http_status_code': result.get('http', {}).get('status_code'),
                    'icmp_success': result.get('icmp', {}).get('success'),
                    'icmp_response_time_ms': result.get('icmp', {}).get('response_time_ms'),
                    'total_duration_ms': result.get('duration_ms')
                }
                flattened.append(flat)
            
            if flattened:
                writer = csv.DictWriter(csvfile, fieldnames=flattened[0].keys())
                writer.writeheader()
                writer.writerows(flattened)
    
    @staticmethod
    def to_prometheus(results: Dict[str, Any]) -> str:
        """Export results in Prometheus metrics format."""
        metrics = []
        timestamp = int(time.time() * 1000)
        
        result = results.get('results', results)  # Handle both single and multi-host
        
        # DNS metrics
        if 'dns' in result:
            dns = result['dns']
            if 'ipv4' in dns:
                metrics.append(f'eznet_dns_ipv4_success{{host="{result["host"]}"}} {int(dns["ipv4"]["success"])} {timestamp}')
            if 'ipv6' in dns:
                metrics.append(f'eznet_dns_ipv6_success{{host="{result["host"]}"}} {int(dns["ipv6"]["success"])} {timestamp}')
        
        # TCP metrics
        if 'tcp' in result and result['tcp']:
            tcp = result['tcp']
            metrics.append(f'eznet_tcp_success{{host="{result["host"]}",port="{result.get("port", "")}"}} {int(tcp.get("success", False))} {timestamp}')
            if 'response_time_ms' in tcp:
                metrics.append(f'eznet_tcp_response_time_ms{{host="{result["host"]}",port="{result.get("port", "")}"}} {tcp["response_time_ms"]} {timestamp}')
        
        # HTTP metrics
        if 'http' in result and result['http']:
            http = result['http']
            metrics.append(f'eznet_http_success{{host="{result["host"]}",port="{result.get("port", "")}"}} {int(http.get("success", False))} {timestamp}')
            if 'status_code' in http:
                metrics.append(f'eznet_http_status_code{{host="{result["host"]}",port="{result.get("port", "")}"}} {http["status_code"]} {timestamp}')
        
        # ICMP metrics
        if 'icmp' in result and result['icmp']:
            icmp = result['icmp']
            metrics.append(f'eznet_icmp_success{{host="{result["host"]}"}} {int(icmp.get("success", False))} {timestamp}')
            if 'response_time_ms' in icmp:
                metrics.append(f'eznet_icmp_response_time_ms{{host="{result["host"]}"}} {icmp["response_time_ms"]} {timestamp}')
        
        return '\n'.join(metrics)


class ConfigManager:
    """Configuration file management."""
    
    @staticmethod
    def load_hosts_file(filepath: str) -> List[str]:
        """Load hosts from a text file (one per line)."""
        with open(filepath, 'r') as f:
            hosts = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return hosts
    
    @staticmethod
    def load_config_file(filepath: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def create_sample_config(filepath: str):
        """Create a sample configuration file."""
        sample_config = {
            'default_timeout': 5,
            'max_concurrent': 50,
            'output_format': 'table',
            'monitoring': {
                'interval': 30,
                'retries': 3
            },
            'targets': [
                {
                    'name': 'Google DNS',
                    'host': '8.8.8.8',
                    'port': 53
                },
                {
                    'name': 'Cloudflare DNS',
                    'host': '1.1.1.1',
                    'port': 53
                }
            ]
        }
        
        with open(filepath, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)


# Example usage functions
async def demo_multi_host():
    """Demonstrate multi-host scanning."""
    scanner = MultiHostScanner(max_concurrent=10)
    hosts = ['google.com', 'github.com', 'stackoverflow.com']
    results = await scanner.scan_hosts(hosts, 80)
    print("Multi-host scan results:", results)


async def demo_port_range():
    """Demonstrate port range scanning."""
    scanner = PortRangeScanner()
    results = await scanner.scan_port_range('scanme.nmap.org', 20, 25)
    print("Port range scan results:", results)


if __name__ == "__main__":
    print("EZNet Advanced Features Demo")
    print("This file contains prototypes for future EZNet features.")
    
    # You can run individual demos here
    # asyncio.run(demo_multi_host())
    # asyncio.run(demo_port_range())