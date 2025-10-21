"""
EZNet TUI - Terminal User Interface components.

This package provides a k9s-style terminal interface for network testing.
"""

try:
    from .advanced_app import EZNetAdvancedApp, run_tui
    from .simple_app import EZNetApp
    from .results import ResultsScreen
    
    __all__ = ["EZNetAdvancedApp", "EZNetApp", "ResultsScreen", "run_tui"]
except ImportError:
    # Handle case when textual is not installed
    __all__ = []