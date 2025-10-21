#!/usr/bin/env python3
"""
EZNet Examples - Demonstration script showing various EZNet usage scenarios.

This script demonstrates different ways to use EZNet for network testing.
"""

import asyncio
import subprocess
import json
import sys
from pathlib import Path

# Add the src directory to the path so we can import eznet
sys.path.insert(0, str(Path(__file__).parent / "src"))

from eznet.cli import run_all_checks, display_results


async def demo_basic_dns_check():
    """Demonstrate basic DNS checking."""
    print("🌐 Basic DNS Check Example")
    print("=" * 50)
    
    result = await run_all_checks("google.com", None, 5)
    display_results(result)
    print("\n")


async def demo_web_service_check():
    """Demonstrate web service checking."""
    print("🌍 Web Service Check Example")
    print("=" * 50)
    
    result = await run_all_checks("httpbin.org", 80, 10)
    display_results(result)
    print("\n")


async def demo_secure_web_check():
    """Demonstrate HTTPS service checking."""
    print("🔒 HTTPS Service Check Example")
    print("=" * 50)
    
    result = await run_all_checks("google.com", 443, 5)
    display_results(result)
    print("\n")


async def demo_dns_server_check():
    """Demonstrate DNS server checking."""
    print("🔍 DNS Server Check Example")
    print("=" * 50)
    
    result = await run_all_checks("1.1.1.1", 53, 5)
    display_results(result)
    print("\n")


async def demo_json_output():
    """Demonstrate JSON output format."""
    print("📄 JSON Output Example")
    print("=" * 50)
    
    result = await run_all_checks("github.com", 22, 5)
    print(json.dumps(result.to_dict(), indent=2))
    print("\n")


def demo_cli_usage():
    """Demonstrate CLI usage with subprocess."""
    print("💻 CLI Usage Examples")
    print("=" * 50)
    
    examples = [
        "eznet -H google.com",
        "eznet -H google.com -p 80",
        "eznet -H 8.8.8.8 -p 53 --json",
        "eznet -H example.com -p 443 --timeout 10 -v"
    ]
    
    for example in examples:
        print(f"$ {example}")
    
    print("\nNote: Run these commands from your terminal after installing EZNet")
    print("\n")


async def main():
    """Run all demonstration examples."""
    print("🚀 EZNet Demonstration Script")
    print("=" * 80)
    print("This script demonstrates various EZNet features and usage patterns.")
    print("=" * 80)
    print("\n")
    
    try:
        # Run async examples
        await demo_basic_dns_check()
        await demo_web_service_check()
        await demo_secure_web_check()
        await demo_dns_server_check()
        await demo_json_output()
        
        # Show CLI examples
        demo_cli_usage()
        
        print("🎉 Demonstration completed successfully!")
        print("=" * 80)
        print("To use EZNet in your own projects:")
        print("1. Install: pip install -e .")
        print("2. Use CLI: eznet -H google.com")
        print("3. Use programmatically: from eznet.cli import run_all_checks")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demonstration stopped by user")
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())