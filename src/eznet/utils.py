"""
Utility functions for EZNet.

This module contains helper functions for validation, formatting, and common operations.
"""

import re
import ipaddress
import time
from typing import Union, Optional


def is_valid_ip(ip_string: str) -> bool:
    """
    Check if a string is a valid IP address (IPv4 or IPv6).
    
    Args:
        ip_string: String to validate
        
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def is_valid_hostname(hostname: str) -> bool:
    """
    Check if a string is a valid hostname according to RFC standards.
    
    Args:
        hostname: String to validate
        
    Returns:
        True if valid hostname, False otherwise
    """
    if not hostname or len(hostname) > 253:
        return False
    
    # Check if it's an IP address
    if is_valid_ip(hostname):
        return True
    
    # Remove trailing dot if present
    if hostname.endswith('.'):
        hostname = hostname[:-1]
    
    # Check each label in the hostname
    labels = hostname.split('.')
    for label in labels:
        if not label or len(label) > 63:
            return False
        # Label must start and end with alphanumeric, can contain hyphens in middle
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', label):
            return False
    
    return True


def is_valid_port(port: Union[int, str]) -> bool:
    """
    Check if a port number is valid (1-65535).
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid port, False otherwise
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


def format_duration(start_time: float, end_time: Optional[float] = None) -> float:
    """
    Calculate duration in milliseconds between two timestamps.
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp (current time if None)
        
    Returns:
        Duration in milliseconds
    """
    if end_time is None:
        end_time = time.time()
    
    return (end_time - start_time) * 1000


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes count in human-readable format.
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.2 KB", "3.4 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def parse_host_port(host_port: str) -> tuple[str, Optional[int]]:
    """
    Parse host:port string into separate components.
    
    Args:
        host_port: String in format "host:port" or just "host"
        
    Returns:
        Tuple of (host, port) where port is None if not specified
    """
    # Handle IPv6 addresses in brackets
    if host_port.startswith('['):
        # IPv6 format: [::1]:8080
        bracket_end = host_port.find(']')
        if bracket_end == -1:
            raise ValueError("Invalid IPv6 format: missing closing bracket")
        
        host = host_port[1:bracket_end]
        remainder = host_port[bracket_end + 1:]
        
        if remainder.startswith(':'):
            try:
                port = int(remainder[1:])
                return host, port
            except ValueError:
                raise ValueError("Invalid port number")
        elif remainder == '':
            return host, None
        else:
            raise ValueError("Invalid format after IPv6 address")
    
    # Handle IPv4 or hostname
    parts = host_port.rsplit(':', 1)
    if len(parts) == 2:
        host, port_str = parts
        try:
            port = int(port_str)
            return host, port
        except ValueError:
            # If port parsing fails, treat entire string as hostname
            return host_port, None
    else:
        return host_port, None


def parse_ports(port_string: str) -> list[int]:
    """
    Parse port specification into list of ports.
    
    Supports:
    - Single port: "80"
    - Port range: "80-90" 
    - Comma-separated: "80,443,8080"
    - Mixed: "80,443,8000-8010"
    
    Args:
        port_string: Port specification string
        
    Returns:
        List of port numbers
        
    Raises:
        ValueError: If port specification is invalid
    """
    if not port_string:
        return []
    
    ports = []
    parts = port_string.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            # Handle port range
            try:
                start_str, end_str = part.split('-', 1)
                start_port = int(start_str.strip())
                end_port = int(end_str.strip())
                
                if start_port > end_port:
                    raise ValueError(f"Invalid port range: {part} (start > end)")
                
                if end_port - start_port > 1000:
                    raise ValueError(f"Port range too large: {part} (max 1000 ports)")
                
                for p in range(start_port, end_port + 1):
                    if is_valid_port(p):
                        ports.append(p)
                    else:
                        raise ValueError(f"Invalid port in range: {p}")
                        
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid port range format: {part}")
                raise
        else:
            # Handle single port
            try:
                single_port = int(part)
                if is_valid_port(single_port):
                    ports.append(single_port)
                else:
                    raise ValueError(f"Invalid port: {single_port}")
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid port number: {part}")
                raise
    
    return sorted(list(set(ports)))  # Remove duplicates and sort


def get_common_ports() -> list[int]:
    """
    Get list of commonly scanned ports.
    
    Returns:
        List of common port numbers (top 100)
    """
    return [
        # Web services
        80, 443, 8080, 8443, 8000, 8008, 8888, 9000, 9080, 9443,
        
        # SSH and remote access
        22, 23, 3389, 5900, 5901, 5902,
        
        # Mail services
        25, 587, 465, 110, 995, 143, 993,
        
        # DNS
        53,
        
        # FTP
        21, 990,
        
        # Database services
        1433, 1521, 3306, 5432, 6379, 27017, 27018, 27019,
        
        # Application servers
        8080, 8443, 9000, 9001, 9002, 9080, 9090, 9443, 9999,
        
        # Network services
        135, 139, 445, 161, 162, 389, 636, 873,
        
        # Development/Debug
        3000, 4000, 5000, 8000, 8080, 9000,
        
        # Game servers
        25565, 7777, 27015,
        
        # Monitoring/Management
        9200, 9300, 5601, 3000, 8086, 9090, 9093,
        
        # Media services
        554, 1935, 8554,
        
        # VPN
        1194, 1723, 4500, 500,
        
        # Other common services
        79, 111, 119, 194, 465, 563, 993, 995, 1080, 1433, 1521,
        2049, 2121, 2375, 2376, 3268, 3269, 5060, 5061, 5432, 5984,
        6000, 6001, 6667, 7001, 8001, 8009, 8081, 8090, 8181, 8888,
        9001, 9002, 9003, 9090, 9091, 9200, 9300, 9999, 10000, 50000
    ]


def get_port_description(port: int) -> str:
    """
    Get description for a port number.
    
    Args:
        port: Port number
        
    Returns:
        Service description or "Unknown"
    """
    port_descriptions = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        79: "Finger",
        80: "HTTP",
        110: "POP3",
        111: "RPC",
        119: "NNTP",
        135: "RPC",
        139: "NetBIOS",
        143: "IMAP",
        161: "SNMP",
        194: "IRC",
        389: "LDAP",
        443: "HTTPS",
        445: "SMB",
        465: "SMTPS",
        500: "IPSec",
        554: "RTSP",
        563: "NNTPS",
        587: "SMTP-Submit",
        636: "LDAPS",
        873: "rsync",
        993: "IMAPS",
        995: "POP3S",
        1080: "SOCKS",
        1194: "OpenVPN",
        1433: "MSSQL",
        1521: "Oracle",
        1723: "PPTP",
        1935: "RTMP",
        2049: "NFS",
        2121: "FTP-Proxy",
        2375: "Docker",
        2376: "Docker-TLS",
        3000: "Dev-Server",
        3268: "LDAP-GC",
        3269: "LDAP-GC-SSL",
        3306: "MySQL",
        3389: "RDP",
        4000: "Dev-Server",
        4500: "IPSec-NAT",
        5000: "Dev-Server",
        5060: "SIP",
        5061: "SIP-TLS",
        5432: "PostgreSQL",
        5601: "Kibana",
        5900: "VNC",
        5984: "CouchDB",
        6000: "X11",
        6379: "Redis",
        6667: "IRC",
        7001: "Cassandra",
        7777: "Game-Server",
        8000: "HTTP-Alt",
        8001: "HTTP-Alt",
        8008: "HTTP-Alt",
        8009: "HTTP-Alt",
        8080: "HTTP-Proxy",
        8081: "HTTP-Alt",
        8086: "InfluxDB",
        8090: "HTTP-Alt",
        8181: "HTTP-Alt",
        8443: "HTTPS-Alt",
        8554: "RTSP-Alt",
        8888: "HTTP-Alt",
        9000: "App-Server",
        9001: "App-Server",
        9002: "App-Server",
        9003: "App-Server",
        9080: "HTTP-Alt",
        9090: "Prometheus",
        9091: "Pushgateway",
        9093: "Alertmanager",
        9200: "Elasticsearch",
        9300: "Elasticsearch",
        9443: "HTTPS-Alt",
        9999: "App-Server",
        10000: "Webmin",
        25565: "Minecraft",
        27015: "Steam",
        27017: "MongoDB",
        27018: "MongoDB",
        27019: "MongoDB",
        50000: "SAP"
    }
    
    return port_descriptions.get(port, "Unknown")


def sanitize_hostname(hostname: str) -> str:
    """
    Sanitize hostname by removing invalid characters.
    
    Args:
        hostname: Hostname to sanitize
        
    Returns:
        Sanitized hostname
    """
    # Remove leading/trailing whitespace
    hostname = hostname.strip()
    
    # Remove protocol prefixes
    for prefix in ['http://', 'https://', 'ftp://', 'ftps://']:
        if hostname.lower().startswith(prefix):
            hostname = hostname[len(prefix):]
            break
    
    # Remove path and query parameters
    hostname = hostname.split('/')[0]
    hostname = hostname.split('?')[0]
    
    return hostname


def format_response_time(ms: float) -> str:
    """
    Format response time in human-readable format.
    
    Args:
        ms: Response time in milliseconds
        
    Returns:
        Formatted string
    """
    if ms < 1:
        return f"{ms:.2f} ms"
    elif ms < 1000:
        return f"{ms:.1f} ms"
    else:
        seconds = ms / 1000
        return f"{seconds:.1f} s"


def create_summary_stats(results: list) -> dict:
    """
    Create summary statistics from a list of test results.
    
    Args:
        results: List of test result dictionaries
        
    Returns:
        Dictionary with summary statistics
    """
    if not results:
        return {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "success_rate": 0.0
        }
    
    successful = sum(1 for r in results if r.get("success", False))
    failed = len(results) - successful
    success_rate = (successful / len(results)) * 100
    
    return {
        "total_tests": len(results),
        "successful_tests": successful,
        "failed_tests": failed,
        "success_rate": success_rate
    }


def detect_service_from_response(response_text: str, headers: dict) -> str:
    """
    Detect service type from HTTP response.
    
    Args:
        response_text: Response body text
        headers: Response headers dictionary
        
    Returns:
        Detected service name or "Unknown"
    """
    # Check server header
    server = headers.get("server", "").lower()
    
    # Common server signatures
    if "apache" in server:
        return "Apache"
    elif "nginx" in server:
        return "Nginx"
    elif "iis" in server:
        return "IIS"
    elif "cloudflare" in server:
        return "Cloudflare"
    elif "express" in server:
        return "Express.js"
    
    # Check content for service signatures
    content_lower = response_text.lower()
    
    if "wordpress" in content_lower:
        return "WordPress"
    elif "drupal" in content_lower:
        return "Drupal"
    elif "joomla" in content_lower:
        return "Joomla"
    elif "docker" in content_lower:
        return "Docker Registry"
    elif "jenkins" in content_lower:
        return "Jenkins"
    
    return "Unknown"


class Timer:
    """Simple timer context manager for measuring execution time."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix