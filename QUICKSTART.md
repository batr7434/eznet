# EZNet - Quick Start Guide

Welcome to EZNet! This guide will get you up and running in just a few minutes.

## 🚀 Installation & Setup

### Method 1: Direct Installation (Recommended)
```bash
# Install directly from GitHub
curl -fsSL https://raw.githubusercontent.com/batr7434/eznet/main/install.sh | bash
```

### Method 2: From Source
```bash
# Clone the repository
git clone https://github.com/batr7434/eznet.git
cd eznet

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install EZNet
pip install -e .
```

### Method 3: Using pip (when available)
```bash
pip install eznet
```

### Verify Installation
```bash
eznet --version
eznet --help
```

## 📚 Quick Usage Examples

### Basic Website Check
```bash
# Test a website - performs all available checks
eznet -H google.com
```

### Specific Port Testing
```bash
# Test HTTP service
eznet -H example.com -p 80

# Test HTTPS service
eznet -H github.com -p 443

# Test SSH service
eznet -H your-server.com -p 22
```

### Port Range Scanning
```bash
# Scan a range of ports
eznet -H example.com -p 80-90

# Scan common ports (115+ ports)
eznet -H target-server.com --common-ports
```

### SSL/TLS Certificate Analysis
```bash
# Analyze SSL certificate security
eznet -H github.com -p 443 --ssl-check
```

### Advanced Options
```bash
# JSON output for scripting
eznet -H api.example.com -p 443 --json

# Verbose output with detailed information
eznet -H example.com -p 80 --verbose

# Custom timeout
eznet -H slow-server.com --timeout 10
```

### Multiple Hosts
```bash
# Test multiple hosts at once
eznet -H google.com,github.com,stackoverflow.com -p 443

# Test hosts from a file
eznet --hosts-file servers.txt -p 22
```

## 🧪 Testing Your Installation

### Quick Test
```bash
# Test against a reliable service
eznet -H 8.8.8.8 -p 53

# Test HTTPS with SSL analysis
eznet -H github.com -p 443 --ssl-check
```

### Run Unit Tests (for developers)
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=eznet --cov-report=html
```

## 🎯 What EZNet Does

EZNet is a comprehensive network testing tool that automatically performs:

1. **🌐 DNS Resolution** - Resolves IPv4 and IPv6 addresses for hostnames
2. **🔌 TCP Connection** - Tests connectivity to specific ports
3. **🌍 HTTP/HTTPS Check** - Retrieves headers, status codes, and response times
4. **🏓 ICMP Ping** - Tests basic network reachability
5. **🔒 SSL/TLS Analysis** - Certificate validation and security assessment
6. **🔍 Port Scanning** - Single ports, ranges, or common port sets

### Key Features
- **No Command Memorization** - Forget `ping`, `telnet`, `curl`, `nc` - EZNet does it all
- **Smart Detection** - Automatically determines which tests to run
- **Beautiful Output** - Rich, colored terminal output with organized tables
- **Fast Performance** - Async operations for quick results
- **Cross-Platform** - Works on Linux, macOS, and Windows

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

## 🔧 Contributing & Development

Want to contribute? Great! Here's how to set up a development environment:

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/batr7434/eznet.git
cd eznet

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
mypy src/

# Run all quality checks
pre-commit run --all-files
```

### Testing
```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_basic.py -v

# Run with coverage
pytest --cov=eznet --cov-report=html
```

## 🌟 Why Choose EZNet?

✅ **All-in-One Tool** - Replace multiple network utilities with one command  
✅ **Beginner Friendly** - No need to remember complex command syntax  
✅ **Professional Output** - Beautiful, organized results perfect for documentation  
✅ **Fast & Efficient** - Async operations test multiple targets simultaneously  
✅ **JSON Export** - Perfect for automation and scripting  
✅ **Cross-Platform** - Works identically on Linux, macOS, and Windows  
✅ **Open Source** - Free, transparent, and community-driven  
✅ **Actively Maintained** - Regular updates and improvements

## 📝 Notes

- ICMP ping requires root privileges for raw sockets (falls back to system ping)
- HTTP checks are performed for ports 80, 443, 8080, 8443 automatically
- DNS resolution supports both IPv4 and IPv6
- All operations have configurable timeouts
- Failed tests are gracefully handled and reported

## 🆘 Troubleshooting

### "eznet: command not found"
**Solution 1:** Reinstall using the install script:
```bash
curl -fsSL https://raw.githubusercontent.com/batr7434/eznet/main/install.sh | bash
```

**Solution 2:** If installed from source, activate the virtual environment:
```bash
cd eznet
source .venv/bin/activate
```

### Permission Issues with ICMP Ping
This is normal! EZNet automatically falls back to system ping when raw sockets aren't available. You'll still get ping results, just using a different method.

### Slow Performance
- Use `--timeout` to adjust timeout values
- Consider using `--max-concurrent` to limit parallel connections
- Some networks/firewalls may cause delays

### SSL Certificate Errors
- Certificate validation errors are reported, not program bugs
- Use `--ssl-check` only on HTTPS ports (443, 8443, etc.)

## 📚 More Resources

- **Full Documentation:** [README.md](README.md)
- **Contributing Guide:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Issue Tracker:** [GitHub Issues](https://github.com/batr7434/eznet/issues)
- **Latest Releases:** [GitHub Releases](https://github.com/batr7434/eznet/releases)

## 💬 Community & Support

- 🐛 **Found a bug?** [Open an issue](https://github.com/batr7434/eznet/issues/new)
- 💡 **Have an idea?** [Start a discussion](https://github.com/batr7434/eznet/discussions)
- 🤝 **Want to contribute?** Check out [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Happy network testing!** 🌐✨

*EZNet - Making network diagnostics simple and beautiful.*