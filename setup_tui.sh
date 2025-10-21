#!/bin/bash

# EZNet TUI Installation und Test Script

echo "🚀 EZNet TUI Setup"
echo "=================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the eznet root directory"
    exit 1
fi

echo "📦 Installing dependencies..."

# Install package in development mode
pip install -e .

# Install textual for TUI
pip install textual

echo "✅ Installation complete!"
echo ""
echo "🎯 Testing TUI functionality..."

# Test if TUI can be imported
python -c "
try:
    from src.eznet.tui.advanced_app import run_tui
    print('✅ TUI modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "🔧 Available commands:"
echo "• eznet --tui                 # Start interactive TUI"
echo "• python demo_tui.py          # Run TUI demo"
echo "• eznet google.com --tui      # Start TUI (ignores host argument)"
echo ""
echo "📚 TUI Shortcuts:"
echo "• a - Add host"
echo "• d - Delete host"
echo "• s - Scan all hosts"
echo "• Enter - View detailed results"
echo "• j/k - Navigate up/down (vim-style)"
echo "• g/G - Go to top/bottom"
echo "• ? - Show help"
echo "• q - Quit"
echo ""
echo "🎉 Ready to use EZNet TUI!"
echo "Try: eznet --tui"