"""
ICMP ping functionality for EZNet.

This module provides ICMP ping testing with fallback to system ping command.
"""

import asyncio
import subprocess
import time
import os
import platform
from typing import Dict, Any


class ICMPChecker:
    """ICMP ping checker with multiple implementations."""
    
    def __init__(self, timeout: int = 5):
        """
        Initialize ICMP checker.
        
        Args:
            timeout: Timeout in seconds for ping
        """
        self.timeout = timeout
        self.system = platform.system().lower()
    
    async def check(self, host: str) -> Dict[str, Any]:
        """
        Perform ICMP ping test.
        
        Args:
            host: Target hostname or IP address
            
        Returns:
            Dictionary containing ping results
        """
        # Try different ping methods in order of preference
        methods = [
            self._ping_with_system_command,
            self._ping_with_raw_socket  # Requires root privileges
        ]
        
        last_error = None
        for method in methods:
            try:
                result = await method(host)
                if result.get("success"):
                    return result
                last_error = result.get("error", "Unknown error")
            except Exception as e:
                last_error = str(e)
                continue
        
        return {
            "success": False,
            "host": host,
            "error": last_error or "All ping methods failed",
            "method": "none"
        }
    
    async def _ping_with_system_command(self, host: str) -> Dict[str, Any]:
        """
        Use system ping command.
        
        Args:
            host: Target hostname or IP address
            
        Returns:
            Dictionary containing ping results
        """
        start_time = time.time()
        
        try:
            # Determine ping command based on OS
            if self.system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(self.timeout * 1000), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(self.timeout), host]
            
            # Execute ping command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout + 2
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "host": host,
                    "error": f"Ping timeout after {self.timeout}s",
                    "method": "system_command"
                }
            
            response_time = (time.time() - start_time) * 1000
            
            # Parse output
            output = stdout.decode('utf-8', errors='ignore')
            
            if process.returncode == 0:
                # Extract timing information from output
                parsed_time = self._parse_ping_time(output)
                if parsed_time is not None:
                    response_time = parsed_time
                
                return {
                    "success": True,
                    "host": host,
                    "response_time_ms": response_time,
                    "method": "system_command",
                    "raw_output": output.strip()
                }
            else:
                error_output = stderr.decode('utf-8', errors='ignore')
                return {
                    "success": False,
                    "host": host,
                    "error": error_output.strip() or "Ping failed",
                    "method": "system_command",
                    "response_time_ms": response_time
                }
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "error": str(e),
                "method": "system_command",
                "response_time_ms": response_time
            }
    
    async def _ping_with_raw_socket(self, host: str) -> Dict[str, Any]:
        """
        Use raw socket for ICMP ping (requires root privileges).
        
        Args:
            host: Target hostname or IP address
            
        Returns:
            Dictionary containing ping results
        """
        # Check if running as root
        if os.geteuid() != 0:
            return {
                "success": False,
                "host": host,
                "error": "Raw socket ping requires root privileges",
                "method": "raw_socket"
            }
        
        try:
            # Import required modules for raw socket ping
            import socket
            import struct
            import select
            
            # Create raw socket
            icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            icmp_socket.settimeout(self.timeout)
            
            # Resolve hostname
            dest_addr = socket.gethostbyname(host)
            
            # Create ICMP packet
            packet_id = os.getpid() & 0xFFFF
            packet = self._create_icmp_packet(packet_id, 1)
            
            start_time = time.time()
            
            # Send packet
            icmp_socket.sendto(packet, (dest_addr, 1))
            
            # Wait for reply
            ready = select.select([icmp_socket], [], [], self.timeout)
            if ready[0]:
                recv_packet, addr = icmp_socket.recvfrom(1024)
                response_time = (time.time() - start_time) * 1000
                
                # Parse ICMP reply
                if self._parse_icmp_reply(recv_packet, packet_id):
                    icmp_socket.close()
                    return {
                        "success": True,
                        "host": host,
                        "response_time_ms": response_time,
                        "method": "raw_socket",
                        "dest_addr": dest_addr
                    }
            
            icmp_socket.close()
            return {
                "success": False,
                "host": host,
                "error": "No ICMP reply received",
                "method": "raw_socket"
            }
            
        except Exception as e:
            return {
                "success": False,
                "host": host,
                "error": f"Raw socket ping failed: {e}",
                "method": "raw_socket"
            }
    
    def _create_icmp_packet(self, packet_id: int, sequence: int) -> bytes:
        """Create ICMP echo request packet."""
        import struct
        
        # ICMP header: type (8), code (0), checksum (0), id, sequence
        header = struct.pack("bbHHh", 8, 0, 0, packet_id, sequence)
        data = b"EZNet ICMP Test"
        
        # Calculate checksum
        checksum = self._calculate_checksum(header + data)
        
        # Pack header with checksum
        header = struct.pack("bbHHh", 8, 0, checksum, packet_id, sequence)
        
        return header + data
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate ICMP checksum."""
        import struct
        
        checksum = 0
        
        # Make 16-bit words out of every two adjacent bytes
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = (data[i] << 8) + data[i + 1]
            else:
                word = data[i] << 8
            checksum += word
        
        # Add high 16 bits to low 16 bits
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += (checksum >> 16)
        
        # One's complement
        return (~checksum) & 0xFFFF
    
    def _parse_icmp_reply(self, packet: bytes, expected_id: int) -> bool:
        """Parse ICMP reply packet."""
        import struct
        
        try:
            # Skip IP header (usually 20 bytes)
            icmp_header = packet[20:28]
            type_code, code, checksum, packet_id, sequence = struct.unpack("bbHHh", icmp_header)
            
            # Check if it's an echo reply (type 0) with our packet ID
            return type_code == 0 and packet_id == expected_id
        except:
            return False
    
    def _parse_ping_time(self, output: str) -> float:
        """
        Extract ping time from system ping output.
        
        Args:
            output: Raw ping command output
            
        Returns:
            Response time in milliseconds or None if not found
        """
        import re
        
        # Common patterns for different ping outputs
        patterns = [
            r'time[<=](\d+\.?\d*)\s*ms',  # Linux/Unix: time=1.234 ms
            r'Zeit[<=](\d+\.?\d*)\s*ms',  # German Windows: Zeit=1ms
            r'time[<=](\d+\.?\d*)',       # Without ms suffix
            r'(\d+\.?\d*)\s*ms',          # Just number with ms
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    async def continuous_ping(self, host: str, count: int = 4, interval: float = 1.0) -> Dict[str, Any]:
        """
        Perform continuous ping test.
        
        Args:
            host: Target hostname or IP address
            count: Number of ping packets to send
            interval: Interval between pings in seconds
            
        Returns:
            Dictionary containing continuous ping results
        """
        results = []
        successful_pings = 0
        total_time = 0.0
        
        for i in range(count):
            result = await self.check(host)
            results.append(result)
            
            if result.get("success"):
                successful_pings += 1
                total_time += result.get("response_time_ms", 0)
            
            # Wait before next ping (except for last one)
            if i < count - 1:
                await asyncio.sleep(interval)
        
        # Calculate statistics
        packet_loss = ((count - successful_pings) / count) * 100
        avg_time = total_time / successful_pings if successful_pings > 0 else 0
        
        # Calculate min, max times
        successful_times = [r.get("response_time_ms", 0) for r in results if r.get("success")]
        min_time = min(successful_times) if successful_times else 0
        max_time = max(successful_times) if successful_times else 0
        
        return {
            "host": host,
            "packets_sent": count,
            "packets_received": successful_pings,
            "packet_loss_percent": packet_loss,
            "response_times": {
                "min_ms": min_time,
                "max_ms": max_time,
                "avg_ms": avg_time
            },
            "individual_results": results
        }