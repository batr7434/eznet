#!/usr/bin/env python3
"""
n9s - EZNet TUI Command Entry Point  
Interactive terminal user interface for network testing (k9s style)
"""

import sys
import argparse
from typing import List, Optional

def main():
    """Main entry point for n9s command"""
    parser = argparse.ArgumentParser(
        description='EZNet TUI - Interactive network testing dashboard (k9s style)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  n9s                                    # Start empty (k9s style)
  n9s google.com github.com              # Start with specific hosts
  n9s --config hosts.txt                 # Load hosts from file
  n9s --live --interval 5                # Live monitoring every 5 seconds
  n9s --help                             # Show this help

Keyboard shortcuts in TUI:
  r         - Refresh all hosts
  s         - SSL certificate details
  p         - Port scanner view  
  m         - Toggle monitoring
  a         - Add host
  d         - Delete host
  q         - Quit
  ?         - Help

Like k9s for network testing! 🚀
        """
    )
    
    parser.add_argument(
        'hosts',
        nargs='*',
        help='Hostnames or IP addresses to monitor (default: google.com, github.com, stackoverflow.com)'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Configuration file with list of hosts (one per line)'
    )
    
    parser.add_argument(
        '--live', '-l',
        action='store_true',
        help='Start in live monitoring mode'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=float,
        default=5.0,
        help='Refresh interval in seconds for live mode (default: 5.0)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=443,
        help='Default port to test (default: 443)'
    )
    
    parser.add_argument(
        '--timeout', '-t',  
        type=int,
        default=5,
        help='Connection timeout in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Determine hosts to monitor
    hosts: List[str] = []
    
    if args.config:
        # Load hosts from config file
        try:
            with open(args.config, 'r') as f:
                hosts = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"❌ Config file not found: {args.config}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading config file: {e}")
            sys.exit(1)
    elif args.hosts:
        # Use hosts from command line
        hosts = args.hosts
    else:
        # Start empty like k9s - hosts will be added via command mode
        hosts = []
    
    # Allow starting with no hosts (k9s style)
    # if not hosts:
    #     print("❌ No hosts specified. Use --help for usage information.")
    #     sys.exit(1)
    
    # Check if textual is available
    try:
        from .tui import run_tui
    except ImportError:
        print("❌ Textual library not found. Installing...")
        print("Run: pip install textual")
        print("\nAlternatively, use regular eznet command for CLI mode:")
        print("  eznet google.com --ssl-check")
        sys.exit(1)
    
    # Validate hosts (allow empty for k9s style)
    valid_hosts = []
    for host in hosts:
        if host and len(host) > 0:
            valid_hosts.append(host)
    
    # Show startup info
    print(f"🚀 Starting EZNet TUI...")
    if valid_hosts:
        print(f"📊 Monitoring {len(valid_hosts)} hosts: {', '.join(valid_hosts[:3])}{' ...' if len(valid_hosts) > 3 else ''}")
    else:
        print("📊 Starting empty - use : to add hosts (k9s style)")
    print(f"⏰ Refresh interval: {args.interval}s")
    print(f"🔌 Default port: {args.port}")
    print()
    print("💡 Press : to add hosts, ? for help, q to quit")
    print("=" * 50)
    
    try:
        # Start the TUI (pass None if empty list to match expected behavior)
        run_tui(hosts=valid_hosts if valid_hosts else None)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()