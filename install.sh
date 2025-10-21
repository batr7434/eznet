#!/bin/bash
# EZNet Homebrew-style installer

set -e

echo "🚀 Installing EZNet..."

# Create installation directory
INSTALL_DIR="/usr/local/eznet"
BIN_DIR="/usr/local/bin"

# Check if we need sudo
if [[ ! -w "/usr/local" ]]; then
    echo "🔐 Need sudo permissions for installation..."
    SUDO="sudo"
else
    SUDO=""
fi

# Create directories
$SUDO mkdir -p "$INSTALL_DIR"

# Clone or copy the repository
if command -v git >/dev/null 2>&1; then
    echo "📦 Cloning EZNet repository..."
    $SUDO git clone https://github.com/batr7434/eznet.git "$INSTALL_DIR" 2>/dev/null || {
        echo "Updating existing installation..."
        cd "$INSTALL_DIR"
        $SUDO git pull
    }
else
    echo "❌ Git not found. Please install git first."
    exit 1
fi

# Create virtual environment
echo "🐍 Setting up Python environment..."
cd "$INSTALL_DIR"
$SUDO python3 -m venv .venv
$SUDO .venv/bin/pip install -e .

# Create wrapper script
echo "🔗 Creating eznet command..."
$SUDO tee "$BIN_DIR/eznet" > /dev/null <<EOF
#!/bin/bash
cd "$INSTALL_DIR"
.venv/bin/python -m eznet.cli "\$@"
EOF

$SUDO chmod +x "$BIN_DIR/eznet"

echo "✅ EZNet installed successfully!"
echo "💡 Usage: eznet -H google.com"
echo "📖 Help:  eznet --help"