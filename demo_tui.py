#!/usr/bin/env python3
"""
EZNet TUI Demo Script.

This script demonstrates the TUI functionality.
"""

import sys
import os

# Add src to path to import eznet
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from eznet.tui.advanced_app import run_tui
    
    if __name__ == "__main__":
        print("🚀 Starting EZNet TUI Demo...")
        print("This is a k9s-style terminal interface for network testing.")
        print("Use the following keys:")
        print("• a - Add host")
        print("• d - Delete host") 
        print("• s - Scan all hosts")
        print("• Enter - View detailed results")
        print("• ? - Help")
        print("• q - Quit")
        print()
        print("Starting TUI now...")
        
        run_tui()
        
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Please install textual: pip install textual")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n👋 Demo interrupted by user")
    sys.exit(0)