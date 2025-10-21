"""
HTTP/HTTPS checking functionality for EZNet.

This module provides asynchronous HTTP/HTTPS testing using httpx.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class HTTPChecker:
    """Asynchronous HTTP/HTTPS checker."""
    
    def __init__(self, timeout: int = 5):
        """
        Initialize HTTP checker.
        
        Args:
            timeout: Timeout in seconds for HTTP requests
        """
        self.timeout = timeout
        self.user_agent = "EZNet/0.1.0 (Network Testing Tool)"
    
    async def check(self, host: str, port: int) -> Dict[str, Any]:
        """
        Perform HTTP/HTTPS check.
        
        Args:
            host: Target hostname or IP address
            port: Target port number
            
        Returns:
            Dictionary containing HTTP check results
        """
        if not HAS_HTTPX:
            return {
                "success": False,
                "error": "httpx library not available",
                "host": host,
                "port": port
            }
        
        # Determine protocol
        protocol = "https" if port in [443, 8443] else "http"
        url = f"{protocol}://{host}:{port}/"
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                verify=False,  # Don't verify SSL certificates for testing
                follow_redirects=True
            ) as client:
                
                response = await client.head(
                    url,
                    headers={"User-Agent": self.user_agent}
                )
                
                response_time = (time.time() - start_time) * 1000
                
                result = {
                    "success": True,
                    "host": host,
                    "port": port,
                    "url": str(response.url),
                    "protocol": protocol,
                    "status_code": response.status_code,
                    "reason_phrase": response.reason_phrase,
                    "response_time_ms": response_time,
                    "headers": dict(response.headers),
                    "server": response.headers.get("server", "Unknown"),
                    "content_type": response.headers.get("content-type", "Unknown"),
                    "content_length": response.headers.get("content-length"),
                    "is_redirect": 300 <= response.status_code < 400
                }
                
                # Check for redirects
                if result["is_redirect"]:
                    result["redirect_url"] = response.headers.get("location")
                
                # Additional security headers check
                result["security_headers"] = self._check_security_headers(response.headers)
                
                return result
                
        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "port": port,
                "url": url,
                "protocol": protocol,
                "response_time_ms": response_time,
                "error": f"HTTP timeout after {self.timeout}s"
            }
            
        except httpx.ConnectError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "port": port,
                "url": url,
                "protocol": protocol,
                "response_time_ms": response_time,
                "error": f"Connection failed: {e}"
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "port": port,
                "url": url,
                "protocol": protocol,
                "response_time_ms": response_time,
                "error": str(e)
            }
    
    async def get_full_response(self, host: str, port: int, path: str = "/") -> Dict[str, Any]:
        """
        Get full HTTP response including body.
        
        Args:
            host: Target hostname or IP address
            port: Target port number
            path: URL path to request
            
        Returns:
            Dictionary containing full HTTP response
        """
        if not HAS_HTTPX:
            return {
                "success": False,
                "error": "httpx library not available"
            }
        
        protocol = "https" if port in [443, 8443] else "http"
        url = f"{protocol}://{host}:{port}{path}"
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                verify=False,
                follow_redirects=True
            ) as client:
                
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent}
                )
                
                response_time = (time.time() - start_time) * 1000
                
                return {
                    "success": True,
                    "host": host,
                    "port": port,
                    "url": str(response.url),
                    "protocol": protocol,
                    "status_code": response.status_code,
                    "reason_phrase": response.reason_phrase,
                    "response_time_ms": response_time,
                    "headers": dict(response.headers),
                    "content": response.text[:1000],  # First 1000 chars
                    "content_length": len(response.content),
                    "encoding": response.encoding
                }
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "host": host,
                "port": port,
                "url": url,
                "protocol": protocol,
                "response_time_ms": response_time,
                "error": str(e)
            }
    
    def _check_security_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Check for common security headers.
        
        Args:
            headers: HTTP response headers
            
        Returns:
            Dictionary with security header analysis
        """
        security_headers = {
            "strict-transport-security": headers.get("strict-transport-security"),
            "x-frame-options": headers.get("x-frame-options"),
            "x-content-type-options": headers.get("x-content-type-options"),
            "x-xss-protection": headers.get("x-xss-protection"),
            "content-security-policy": headers.get("content-security-policy"),
            "referrer-policy": headers.get("referrer-policy")
        }
        
        # Count present security headers
        present_headers = sum(1 for value in security_headers.values() if value is not None)
        
        return {
            "headers": security_headers,
            "score": f"{present_headers}/6",
            "present_count": present_headers,
            "missing_count": 6 - present_headers
        }
    
    def parse_url(self, url: str) -> Dict[str, Any]:
        """
        Parse URL and extract components.
        
        Args:
            url: URL to parse
            
        Returns:
            Dictionary with URL components
        """
        try:
            parsed = urlparse(url)
            return {
                "success": True,
                "scheme": parsed.scheme,
                "hostname": parsed.hostname,
                "port": parsed.port,
                "path": parsed.path,
                "query": parsed.query,
                "fragment": parsed.fragment
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }