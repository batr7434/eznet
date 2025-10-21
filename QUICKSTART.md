# EZNet - Quick Start Guide

## 🚀 Installation & Setup

### 1. Navigate to the project directory
```bash
cd /Users/bilal.aytar/eznet
```

### 2. Activate virtual environment (if not already active)
```bash
source .venv/bin/activate
```

### 3. Install EZNet in development mode
```bash
pip install -e .
```

### 4. Verify installation
```bash
eznet --version
```

## 📚 Quick Usage Examples

### Basic DNS check
```bash
eznet -H google.com
```

### Check web service
```bash
eznet -H google.com -p 80
```

### Check HTTPS service
```bash
eznet -H google.com -p 443
```

### Check DNS server
```bash
eznet -H 8.8.8.8 -p 53
```

### JSON output format
```bash
eznet -H github.com -p 22 --json
```

### With custom timeout and verbose output
```bash
eznet -H example.com -p 443 --timeout 10 -v
```

## 🧪 Run Tests
```bash
pytest tests/ -v
```

## 🎯 What EZNet Does

EZNet automatically performs these tests:

1. **🌐 DNS Resolution** - Resolves IPv4 and IPv6 addresses
2. **🔌 TCP Connection** - Tests port connectivity
3. **🌍 HTTP/HTTPS Check** - Retrieves headers and status codes
4. **🏓 ICMP Ping** - Tests basic network reachability

## 📁 Project Structure

```
eznet/
├── src/eznet/           # Main source code
│   ├── __init__.py
│   ├── cli.py             # CLI interface
│   ├── dns_check.py       # DNS functionality
│   ├── tcp_check.py       # TCP connectivity
│   ├── http_check.py      # HTTP/HTTPS checks
│   ├── icmp_check.py      # ICMP ping
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
├── .github/workflows/     # CI/CD configuration
├── README.md              # Full documentation
├── requirements.txt       # Dependencies
├── pyproject.toml         # Project configuration
└── examples.py            # Usage examples
```

## 🔧 Development

### Install development dependencies
```bash
pip install -e ".[dev]"
```

### Run code quality checks
```bash
black src/ tests/          # Format code
isort src/ tests/          # Sort imports
flake8 src/ tests/         # Lint code
mypy src/                  # Type checking
```

### Run specific tests
```bash
pytest tests/test_basic.py -v                    # Basic tests
pytest -m "not integration" -v                   # Unit tests only
pytest tests/ --cov=eznet --cov-report=html   # With coverage
```

## 🌟 Features

✅ **Async Operations** - Fast parallel network testing  
✅ **Rich Terminal Output** - Beautiful, colored tables  
✅ **JSON Export** - Machine-readable results  
✅ **Smart Detection** - Automatic test selection  
✅ **Cross-Platform** - Works on Linux, macOS, Windows  
✅ **Comprehensive** - DNS, TCP, HTTP, ICMP in one tool  
✅ **Extensible** - Easy to add new test types  

## 📝 Notes

- ICMP ping requires root privileges for raw sockets (falls back to system ping)
- HTTP checks are performed for ports 80, 443, 8080, 8443 automatically
- DNS resolution supports both IPv4 and IPv6
- All operations have configurable timeouts
- Failed tests are gracefully handled and reported

## 🆘 Troubleshooting

### "eznet: command not found"
Make sure the virtual environment is activated and the package is installed:
```bash
source .venv/bin/activate
pip install -e .
```

### "Permission denied" for ICMP
This is expected for non-root users. EZNet will fall back to system ping.

### Import errors during development
Ensure you're in the project root directory and using the virtual environment.

Happy network testing! 🌐✨