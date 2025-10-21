"""
TCP connection checking functionality for EZNet.

This module provides asynchronous TCP connection testing.
"""

import asyncio
import socket
import time
from typing import Dict, Any


class TCPChecker:
    """Asynchronous TCP connection checker."""
    
    def __init__(self, timeout: int = 5):
        """
        Initialize TCP checker.
        
        Args:
            timeout: Timeout in seconds for TCP connections
        """
        self.timeout = timeout
    
    async def check(self, host: str, port: int) -> Dict[str, Any]:
        """
        Test TCP connection to host:port.
        
        Args:
            host: Target hostname or IP address
            port: Target port number
            
        Returns:
            Dictionary containing TCP connection results
        """
        start_time = time.time()
        
        try:
            # Create connection with timeout
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=self.timeout)
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            # Clean up connection
            writer.close()
            await writer.wait_closed()
            
            return {
                "success": True,
                "host": host,
                "port": port,
                "response_time_ms": response_time,
                "status": "open"
            }
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "port": port,
                "response_time_ms": response_time,
                "status": "timeout",
                "error": f"Connection timeout after {self.timeout}s"
            }
            
        except ConnectionRefusedError:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "port": port,
                "response_time_ms": response_time,
                "status": "refused",
                "error": "Connection refused"
            }
            
        except socket.gaierror as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "port": port,
                "response_time_ms": response_time,
                "status": "dns_error",
                "error": f"DNS resolution failed: {e}"
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "port": port,
                "response_time_ms": response_time,
                "status": "error",
                "error": str(e)
            }
    
    async def scan_ports(self, host: str, ports: list, max_concurrent: int = 50) -> Dict[str, Any]:
        """
        Scan multiple ports concurrently.
        
        Args:
            host: Target hostname or IP address
            ports: List of port numbers to scan
            max_concurrent: Maximum number of concurrent connections
            
        Returns:
            Dictionary containing results for all ports
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_with_semaphore(port):
            async with semaphore:
                return await self.check(host, port)
        
        # Create tasks for all ports
        tasks = [check_with_semaphore(port) for port in ports]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        port_results = {}
        for i, result in enumerate(results):
            port = ports[i]
            if isinstance(result, Exception):
                port_results[port] = {
                    "success": False,
                    "host": host,
                    "port": port,
                    "error": str(result)
                }
            else:
                port_results[port] = result
        
        return {
            "host": host,
            "total_ports": len(ports),
            "open_ports": [port for port, result in port_results.items() if result.get("success")],
            "results": port_results
        }
    
    def get_service_name(self, port: int) -> str:
        """
        Get common service name for a port.
        
        Args:
            port: Port number
            
        Returns:
            Service name or "unknown"
        """
        common_ports = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            3389: "RDP",
            5432: "PostgreSQL",
            3306: "MySQL",
            6379: "Redis",
            27017: "MongoDB",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt"
        }
        
        return common_ports.get(port, "unknown")