#!/usr/bin/env python3
"""
EZNet TUI Test Script - Tests the scanning functionality.
"""

import sys
import os
import asyncio

# Add src to path to import eznet
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_scanning():
    """Test the scanning functionality directly."""
    from eznet.cli import run_all_checks
    
    print("🧪 Testing network scanning functionality...")
    
    try:
        # Test a simple scan
        print("📡 Testing google.com:80...")
        result = await run_all_checks("google.com", 80, timeout=5, ssl_check=False)
        
        print(f"✅ DNS Success: {result.dns_results.get('ipv4', {}).get('success', False)}")
        print(f"✅ TCP Success: {result.tcp_results.get(80, {}).get('success', False)}")
        print(f"✅ ICMP Success: {result.icmp_result.get('success', False)}")
        
        if result.tcp_results.get(80, {}).get('success'):
            response_time = result.tcp_results[80].get('response_time_ms', 0)
            print(f"📊 TCP Response Time: {response_time:.1f}ms")
        
        if result.dns_results.get('ipv4', {}).get('success'):
            addresses = result.dns_results['ipv4'].get('addresses', [])
            print(f"🌐 DNS Addresses: {', '.join(addresses[:3])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 EZNet TUI Scan Test")
    print("=" * 50)
    
    success = asyncio.run(test_scanning())
    
    if success:
        print("\n✅ Scanning functionality works correctly!")
        print("The TUI should now update properly when you press 's' to scan.")
    else:
        print("\n❌ Scanning functionality has issues.")
        print("This might explain why the TUI display doesn't update.")
    
    print("\n💡 To test the TUI manually:")
    print("1. Run: eznet --tui")
    print("2. Press 's' to scan all hosts")
    print("3. Wait a few seconds for scans to complete")
    print("4. Status should change from 'pending' to 'completed' or 'error'")