"""
SSL/TLS Certificate checking functionality for EZNet.

This module provides SSL certificate validation, expiration checking,
and security analysis.
"""

import asyncio
import ssl
import socket
import datetime
from typing import Dict, Any, Optional
import ipaddress


class SSLChecker:
    """SSL/TLS certificate checker."""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize SSL checker.
        
        Args:
            timeout: Timeout in seconds for SSL connections
        """
        self.timeout = timeout
    
    async def check(self, host: str, port: int = 443) -> Dict[str, Any]:
        """
        Perform comprehensive SSL/TLS check.
        
        Args:
            host: Target hostname
            port: Target port (default: 443)
            
        Returns:
            Dictionary containing SSL check results
        """
        try:
            # Get certificate info
            cert_info = await self._get_certificate_info(host, port)
            
            if not cert_info:
                return {
                    "success": False,
                    "error": "Could not retrieve certificate",
                    "host": host,
                    "port": port
                }
            
            # Analyze certificate
            analysis = self._analyze_certificate(cert_info, host)
            
            # Check TLS versions
            tls_support = await self._check_tls_versions(host, port)
            
            # Check cipher suites
            cipher_info = await self._check_cipher_suites(host, port)
            
            return {
                "success": True,
                "host": host,
                "port": port,
                "certificate": analysis,
                "tls_versions": tls_support,
                "cipher_suites": cipher_info,
                "security_score": self._calculate_security_score(analysis, tls_support, cipher_info)
            }
            
        except Exception as e:
            return {
                "success": False,
                "host": host,
                "port": port,
                "error": str(e)
            }
    
    async def _get_certificate_info(self, host: str, port: int) -> Optional[Dict]:
        """Get SSL certificate information."""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=context),
                timeout=self.timeout
            )
            
            # Get peer certificate
            sock = writer.get_extra_info('socket')
            cert_der = sock.getpeercert(binary_form=True)
            cert_dict = sock.getpeercert()
            
            writer.close()
            await writer.wait_closed()
            
            return {
                "der": cert_der,
                "dict": cert_dict,
                "ssl_socket": sock
            }
            
        except Exception as e:
            return None
    
    def _analyze_certificate(self, cert_info: Dict, hostname: str) -> Dict[str, Any]:
        """Analyze SSL certificate."""
        cert_dict = cert_info["dict"]
        
        # Basic certificate info
        subject = dict(x[0] for x in cert_dict.get('subject', []))
        issuer = dict(x[0] for x in cert_dict.get('issuer', []))
        
        # Parse dates
        not_before = datetime.datetime.strptime(cert_dict['notBefore'], '%b %d %H:%M:%S %Y %Z')
        not_after = datetime.datetime.strptime(cert_dict['notAfter'], '%b %d %H:%M:%S %Y %Z')
        now = datetime.datetime.now()
        
        # Calculate validity
        days_until_expiry = (not_after - now).days
        is_expired = now > not_after
        is_valid_time = not_before <= now <= not_after
        
        # Check hostname validation
        san_list = []
        if 'subjectAltName' in cert_dict:
            san_list = [name[1] for name in cert_dict['subjectAltName'] if name[0] == 'DNS']
        
        hostname_valid = self._validate_hostname(hostname, subject.get('commonName'), san_list)
        
        # Certificate chain validation would go here
        # (requires more complex implementation)
        
        return {
            "subject": subject,
            "issuer": issuer,
            "common_name": subject.get('commonName'),
            "organization": subject.get('organizationName'),
            "country": subject.get('countryName'),
            "not_before": not_before.isoformat(),
            "not_after": not_after.isoformat(),
            "days_until_expiry": days_until_expiry,
            "is_expired": is_expired,
            "is_valid_time": is_valid_time,
            "san_list": san_list,
            "hostname_valid": hostname_valid,
            "serial_number": cert_dict.get('serialNumber'),
            "version": cert_dict.get('version'),
            "signature_algorithm": cert_dict.get('signatureAlgorithm')
        }
    
    async def _check_tls_versions(self, host: str, port: int) -> Dict[str, Any]:
        """Check supported TLS versions."""
        tls_versions = {
            "SSLv3": ssl.PROTOCOL_SSLv23,  # Will be rejected by modern servers
            "TLSv1.0": getattr(ssl, 'PROTOCOL_TLSv1', None),
            "TLSv1.1": getattr(ssl, 'PROTOCOL_TLSv1_1', None),
            "TLSv1.2": getattr(ssl, 'PROTOCOL_TLSv1_2', None),
            "TLSv1.3": getattr(ssl, 'PROTOCOL_TLS', None)  # TLS 1.3 uses PROTOCOL_TLS
        }
        
        supported_versions = {}
        
        for version_name, protocol in tls_versions.items():
            if protocol is None:
                supported_versions[version_name] = False
                continue
            
            try:
                context = ssl.SSLContext(protocol)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port, ssl=context),
                    timeout=5
                )
                
                writer.close()
                await writer.wait_closed()
                supported_versions[version_name] = True
                
            except Exception:
                supported_versions[version_name] = False
        
        return {
            "supported": supported_versions,
            "recommended": supported_versions.get("TLSv1.2", False) or supported_versions.get("TLSv1.3", False),
            "insecure": supported_versions.get("SSLv3", False) or supported_versions.get("TLSv1.0", False)
        }
    
    async def _check_cipher_suites(self, host: str, port: int) -> Dict[str, Any]:
        """Check cipher suites (simplified)."""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=context),
                timeout=self.timeout
            )
            
            sock = writer.get_extra_info('socket')
            cipher = sock.cipher()
            
            writer.close()
            await writer.wait_closed()
            
            if cipher:
                return {
                    "success": True,
                    "cipher_name": cipher[0],
                    "tls_version": cipher[1],
                    "cipher_bits": cipher[2],
                    "is_secure": cipher[2] >= 128  # Consider 128+ bit ciphers secure
                }
            
        except Exception as e:
            pass
        
        return {
            "success": False,
            "error": "Could not determine cipher suite"
        }
    
    def _validate_hostname(self, hostname: str, common_name: str, san_list: list) -> bool:
        """Validate hostname against certificate."""
        if not hostname:
            return False
        
        # Check against common name
        if common_name and self._match_hostname(hostname, common_name):
            return True
        
        # Check against SAN list
        for san in san_list:
            if self._match_hostname(hostname, san):
                return True
        
        return False
    
    def _match_hostname(self, hostname: str, cert_hostname: str) -> bool:
        """Match hostname with certificate hostname (supports wildcards)."""
        if hostname.lower() == cert_hostname.lower():
            return True
        
        # Handle wildcards
        if cert_hostname.startswith('*.'):
            # Remove the wildcard part
            cert_domain = cert_hostname[2:]
            # Check if hostname ends with the cert domain
            if hostname.lower().endswith('.' + cert_domain.lower()):
                return True
            # Also check exact match without subdomain
            if hostname.lower() == cert_domain.lower():
                return True
        
        return False
    
    def _calculate_security_score(self, cert_analysis: Dict, tls_support: Dict, cipher_info: Dict) -> Dict[str, Any]:
        """Calculate a security score based on various factors."""
        score = 0
        max_score = 100
        issues = []
        
        # Certificate validity (30 points)
        if cert_analysis.get("is_valid_time"):
            score += 15
        else:
            issues.append("Certificate not valid for current time")
        
        if cert_analysis.get("hostname_valid"):
            score += 15
        else:
            issues.append("Hostname doesn't match certificate")
        
        # Expiry check (20 points)
        days_until_expiry = cert_analysis.get("days_until_expiry", 0)
        if days_until_expiry > 30:
            score += 20
        elif days_until_expiry > 7:
            score += 10
            issues.append("Certificate expires within 30 days")
        else:
            issues.append("Certificate expires within 7 days or is expired")
        
        # TLS version support (30 points)
        if tls_support.get("recommended"):
            score += 20
        else:
            issues.append("No support for TLS 1.2 or 1.3")
        
        if not tls_support.get("insecure"):
            score += 10
        else:
            issues.append("Supports insecure SSL/TLS versions")
        
        # Cipher strength (20 points)
        if cipher_info.get("success") and cipher_info.get("is_secure"):
            score += 20
        elif cipher_info.get("success"):
            score += 10
            issues.append("Weak cipher suite")
        else:
            issues.append("Could not determine cipher strength")
        
        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": score,
            "max_score": max_score,
            "percentage": (score / max_score) * 100,
            "grade": grade,
            "issues": issues
        }