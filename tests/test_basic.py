"""
Basic tests for EZNet functionality.

This module contains unit and integration tests for the core EZNet features.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Import modules to test
from eznet.utils import (
    is_valid_ip, 
    is_valid_hostname, 
    is_valid_port, 
    format_duration,
    parse_host_port,
    get_port_description
)
from eznet.dns_check import DNSChecker
from eznet.tcp_check import TCPChecker
from eznet.http_check import HTTPChecker
from eznet.icmp_check import ICMPChecker


class TestUtils:
    """Test utility functions."""
    
    def test_is_valid_ip(self):
        """Test IP address validation."""
        # Valid IPv4
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("8.8.8.8") is True
        assert is_valid_ip("127.0.0.1") is True
        
        # Valid IPv6
        assert is_valid_ip("::1") is True
        assert is_valid_ip("2001:db8::1") is True
        
        # Invalid IPs
        assert is_valid_ip("256.256.256.256") is False
        assert is_valid_ip("192.168.1") is False
        assert is_valid_ip("not.an.ip") is False
        assert is_valid_ip("") is False
    
    def test_is_valid_hostname(self):
        """Test hostname validation."""
        # Valid hostnames
        assert is_valid_hostname("google.com") is True
        assert is_valid_hostname("sub.domain.example.org") is True
        assert is_valid_hostname("localhost") is True
        assert is_valid_hostname("test-server") is True
        
        # Valid IPs should also pass
        assert is_valid_hostname("192.168.1.1") is True
        
        # Invalid hostnames
        assert is_valid_hostname("") is False
        assert is_valid_hostname("-invalid") is False
        assert is_valid_hostname("invalid-") is False
        assert is_valid_hostname("a" * 254) is False  # Too long
    
    def test_is_valid_port(self):
        """Test port validation."""
        # Valid ports
        assert is_valid_port(80) is True
        assert is_valid_port(443) is True
        assert is_valid_port(1) is True
        assert is_valid_port(65535) is True
        assert is_valid_port("8080") is True
        
        # Invalid ports
        assert is_valid_port(0) is False
        assert is_valid_port(65536) is False
        assert is_valid_port(-1) is False
        assert is_valid_port("not_a_port") is False
    
    def test_format_duration(self):
        """Test duration formatting."""
        start_time = 1000.0
        end_time = 1001.5
        
        duration = format_duration(start_time, end_time)
        assert duration == 1500.0  # 1.5 seconds = 1500ms
    
    def test_parse_host_port(self):
        """Test host:port parsing."""
        # Host only
        host, port = parse_host_port("google.com")
        assert host == "google.com"
        assert port is None
        
        # Host with port
        host, port = parse_host_port("google.com:80")
        assert host == "google.com"
        assert port == 80
        
        # IPv4 with port
        host, port = parse_host_port("192.168.1.1:8080")
        assert host == "192.168.1.1"
        assert port == 8080
        
        # IPv6 with brackets
        host, port = parse_host_port("[::1]:8080")
        assert host == "::1"
        assert port == 8080
        
        # IPv6 without port
        host, port = parse_host_port("[::1]")
        assert host == "::1"
        assert port is None
    
    def test_get_port_description(self):
        """Test port description lookup."""
        assert get_port_description(80) == "HTTP"
        assert get_port_description(443) == "HTTPS"
        assert get_port_description(22) == "SSH"
        assert get_port_description(99999) == "Unknown"


class TestDNSChecker:
    """Test DNS checking functionality."""
    
    @pytest.fixture
    def dns_checker(self):
        """Create DNS checker instance."""
        return DNSChecker(timeout=5)
    
    @pytest.mark.asyncio
    async def test_dns_check_valid_domain(self, dns_checker):
        """Test DNS resolution for valid domain."""
        result = await dns_checker.check("google.com")
        
        assert result["hostname"] == "google.com"
        assert "ipv4" in result
        assert "ipv6" in result
        
        # At least IPv4 should work for google.com
        assert result["ipv4"]["success"] is True
        assert len(result["ipv4"]["addresses"]) > 0
    
    @pytest.mark.asyncio
    async def test_dns_check_invalid_domain(self, dns_checker):
        """Test DNS resolution for invalid domain."""
        result = await dns_checker.check("nonexistent.invalid.domain.test")
        
        assert result["hostname"] == "nonexistent.invalid.domain.test"
        assert result["ipv4"]["success"] is False
        assert result["ipv6"]["success"] is False


class TestTCPChecker:
    """Test TCP connection checking."""
    
    @pytest.fixture
    def tcp_checker(self):
        """Create TCP checker instance."""
        return TCPChecker(timeout=5)
    
    @pytest.mark.asyncio
    async def test_tcp_check_open_port(self, tcp_checker):
        """Test TCP connection to known open port."""
        # Google DNS should be accessible
        result = await tcp_checker.check("8.8.8.8", 53)
        
        assert result["host"] == "8.8.8.8"
        assert result["port"] == 53
        assert result["success"] is True
        assert result["status"] == "open"
        assert result["response_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_tcp_check_closed_port(self, tcp_checker):
        """Test TCP connection to likely closed port."""
        # Port 1 on localhost should be closed
        result = await tcp_checker.check("127.0.0.1", 1)
        
        assert result["host"] == "127.0.0.1"
        assert result["port"] == 1
        assert result["success"] is False
        assert result["status"] in ["refused", "timeout"]
    
    def test_get_service_name(self, tcp_checker):
        """Test service name lookup."""
        assert tcp_checker.get_service_name(80) == "HTTP"
        assert tcp_checker.get_service_name(443) == "HTTPS"
        assert tcp_checker.get_service_name(22) == "SSH"
        assert tcp_checker.get_service_name(99999) == "unknown"


class TestHTTPChecker:
    """Test HTTP checking functionality."""
    
    @pytest.fixture
    def http_checker(self):
        """Create HTTP checker instance."""
        return HTTPChecker(timeout=10)
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default to avoid external dependencies
        reason="Requires external network access"
    )
    async def test_http_check_valid_site(self, http_checker):
        """Test HTTP check for valid website."""
        result = await http_checker.check("httpbin.org", 80)
        
        assert result["host"] == "httpbin.org"
        assert result["port"] == 80
        assert result["protocol"] == "http"
        
        if result["success"]:
            assert result["status_code"] in [200, 301, 302]  # Allow redirects
            assert result["response_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_http_check_invalid_host(self, http_checker):
        """Test HTTP check for invalid host."""
        result = await http_checker.check("nonexistent.invalid.domain.test", 80)
        
        assert result["host"] == "nonexistent.invalid.domain.test"
        assert result["port"] == 80
        assert result["success"] is False
        assert "error" in result


class TestICMPChecker:
    """Test ICMP ping functionality."""
    
    @pytest.fixture
    def icmp_checker(self):
        """Create ICMP checker instance."""
        return ICMPChecker(timeout=5)
    
    @pytest.mark.asyncio
    async def test_ping_localhost(self, icmp_checker):
        """Test ping to localhost."""
        result = await icmp_checker.check("127.0.0.1")
        
        assert result["host"] == "127.0.0.1"
        
        # Localhost should be reachable
        if result["success"]:
            assert result["response_time_ms"] >= 0
            assert result["method"] in ["system_command", "raw_socket"]
    
    def test_parse_ping_time(self, icmp_checker):
        """Test ping time parsing from output."""
        # Linux ping output
        linux_output = "64 bytes from 8.8.8.8: icmp_seq=1 ttl=119 time=23.4 ms"
        time_ms = icmp_checker._parse_ping_time(linux_output)
        assert time_ms == 23.4
        
        # Windows ping output (German)
        windows_output = "Antwort von 8.8.8.8: Bytes=32 Zeit=15ms TTL=119"
        time_ms = icmp_checker._parse_ping_time(windows_output)
        assert time_ms == 15.0
        
        # No time found
        no_time_output = "Request timeout"
        time_ms = icmp_checker._parse_ping_time(no_time_output)
        assert time_ms is None


class TestIntegration:
    """Integration tests for full EZNet functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_check_localhost(self):
        """Test full check against localhost."""
        from eznet.cli import run_all_checks
        
        result = await run_all_checks("127.0.0.1", None, 5)
        
        assert result.host == "127.0.0.1"
        assert result.port is None
        assert result.dns_results is not None
        assert result.icmp_result is not None
        assert result.start_time is not None
        assert result.end_time is not None
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_check_with_port(self):
        """Test full check with specific port."""
        from eznet.cli import run_all_checks
        
        # Use a commonly available service (DNS on 8.8.8.8:53)
        result = await run_all_checks("8.8.8.8", 53, 5)
        
        assert result.host == "8.8.8.8"
        assert result.port == 53
        assert result.dns_results is not None
        assert result.tcp_result is not None
        assert result.icmp_result is not None


# Pytest configuration for running tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])