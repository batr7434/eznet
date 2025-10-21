"""
DNS checking functionality for EZNet.

This module provides asynchronous DNS resolution for both IPv4 and IPv6 addresses.
"""

import asyncio
import socket
from typing import Dict, List, Any, Optional

try:
    import aiodns
    HAS_AIODNS = True
except ImportError:
    HAS_AIODNS = False


class DNSChecker:
    """Asynchronous DNS checker for IPv4 and IPv6 resolution."""
    
    def __init__(self, timeout: int = 5):
        """
        Initialize DNS checker.
        
        Args:
            timeout: Timeout in seconds for DNS queries
        """
        self.timeout = timeout
        self.resolver = None
    
    async def check(self, hostname: str) -> Dict[str, Any]:
        """
        Perform DNS checks for both IPv4 and IPv6.
        
        Args:
            hostname: The hostname to resolve
            
        Returns:
            Dictionary containing DNS resolution results
        """
        results = {
            "hostname": hostname,
            "ipv4": await self._resolve_ipv4(hostname),
            "ipv6": await self._resolve_ipv6(hostname)
        }
        return results
    
    async def _resolve_ipv4(self, hostname: str) -> Dict[str, Any]:
        """Resolve IPv4 addresses (A records)."""
        try:
            if HAS_AIODNS:
                # Create resolver lazily in async context
                if self.resolver is None:
                    self.resolver = aiodns.DNSResolver(timeout=self.timeout)
                
                # Use aiodns for async resolution
                records = await self.resolver.query(hostname, 'A')
                addresses = [record.host for record in records]
            else:
                # Fallback to synchronous resolution
                addresses = await asyncio.get_event_loop().run_in_executor(
                    None, self._sync_resolve_ipv4, hostname
                )
            
            return {
                "success": True,
                "addresses": addresses,
                "count": len(addresses)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "addresses": [],
                "count": 0
            }
    
    async def _resolve_ipv6(self, hostname: str) -> Dict[str, Any]:
        """Resolve IPv6 addresses (AAAA records)."""
        try:
            if HAS_AIODNS:
                # Create resolver lazily in async context
                if self.resolver is None:
                    self.resolver = aiodns.DNSResolver(timeout=self.timeout)
                
                # Use aiodns for async resolution
                records = await self.resolver.query(hostname, 'AAAA')
                addresses = [record.host for record in records]
            else:
                # Fallback to synchronous resolution
                addresses = await asyncio.get_event_loop().run_in_executor(
                    None, self._sync_resolve_ipv6, hostname
                )
            
            return {
                "success": True,
                "addresses": addresses,
                "count": len(addresses)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "addresses": [],
                "count": 0
            }
    
    def _sync_resolve_ipv4(self, hostname: str) -> List[str]:
        """Synchronous IPv4 resolution fallback."""
        try:
            result = socket.getaddrinfo(hostname, None, socket.AF_INET)
            return list(set([addr[4][0] for addr in result]))
        except Exception:
            return []
    
    def _sync_resolve_ipv6(self, hostname: str) -> List[str]:
        """Synchronous IPv6 resolution fallback."""
        try:
            result = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            return list(set([addr[4][0] for addr in result]))
        except Exception:
            return []
    
    async def reverse_lookup(self, ip_address: str) -> Dict[str, Any]:
        """
        Perform reverse DNS lookup.
        
        Args:
            ip_address: IP address to reverse lookup
            
        Returns:
            Dictionary containing reverse lookup results
        """
        try:
            if HAS_AIODNS:
                # Create resolver lazily in async context
                if self.resolver is None:
                    self.resolver = aiodns.DNSResolver(timeout=self.timeout)
                
                result = await self.resolver.gethostbyaddr(ip_address)
                hostname = result.name
            else:
                hostname = await asyncio.get_event_loop().run_in_executor(
                    None, socket.gethostbyaddr, ip_address
                )
                hostname = hostname[0]
            
            return {
                "success": True,
                "hostname": hostname,
                "ip_address": ip_address
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ip_address": ip_address
            }