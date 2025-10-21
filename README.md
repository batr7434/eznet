# EZNet 🌐

A comprehensive network testing CLI tool that automatically performs various network tests without requiring users to remember specific commands like `ping`, `nc`, `curl`, or `telnet`.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Features ✨

EZNet automatically performs the following tests:

- **DNS Resolution**: IPv4 & IPv6 address resolution
- **TCP Connection**: Test connectivity to specific ports
- **HTTP/HTTPS Check**: Retrieve headers and response information
- **ICMP Ping**: Test basic connectivity (when possible)
- **Port Range Scanning**: Scan multiple ports in a range (e.g., 80-90)
- **Common Ports Scanning**: Scan 115+ frequently used ports
- **SSL/TLS Certificate Analysis**: Comprehensive certificate security assessment
- **Rich Output**: Beautiful, colored terminal output
- **JSON Export**: Machine-readable output format
- **Async Operations**: Fast parallel testing
- **Smart Detection**: Automatically determines appropriate tests

## Installation 📦

### From Source

```bash
git clone https://github.com/batr7434/eznet.git
cd eznet
pip install -e .
```

### Using Homebrew

```bash
# Add tap and install
brew tap batr7434/eznet
brew install eznet

# Or one-liner
brew install batr7434/eznet/eznet
```

### Using pip (once published)

```bash
pip install eznet
```

## Usage 🚀

### Basic Examples

```bash
# Test a website
eznet google.com

# Test specific port
eznet google.com -p 80

# Test HTTPS
eznet google.com -p 443

# Test with custom timeout
eznet example.com --timeout 10

# JSON output
eznet google.com -p 80 --json

# Verbose output
eznet google.com -v
```

### Port Scanning Examples

```bash
# Scan a range of ports
eznet example.com -p 80-90

# Scan common ports (115+ ports including HTTP, HTTPS, SSH, FTP, etc.)
eznet example.com --common-ports

# Combine with other options
eznet example.com --common-ports --json
```

### SSL/TLS Certificate Analysis

```bash
# Analyze SSL certificate
eznet github.com -p 443 --ssl-check

# SSL analysis with verbose output
eznet github.com -p 443 --ssl-check --verbose
```

### Advanced Examples

```bash
# Test DNS server
eznet 8.8.8.8 -p 53

# Test SSH connection
eznet myserver.com -p 22

# Test database connection
eznet db.example.com -p 5432

# Comprehensive HTTPS analysis
eznet api.example.com -p 443 --ssl-check --json
```

## Sample Output 🎨

### Standard Output

```
╭─────────────────────────────────────────────────────────────╮
│                     EZNet Results for github.com:443       │
╰─────────────────────────────────────────────────────────────╯

┌─────────────────────── 🌐 DNS Resolution ───────────────────────┐
│ Record Type │ Status     │ Result                               │
├─────────────┼────────────┼──────────────────────────────────────┤
│ IPv4 (A)    │ ✅ Success │ 140.82.121.4                        │
│ IPv6 (AAAA) │ ❌ Failed  │ (1, 'DNS server returned answer...) │
└─────────────┴────────────┴──────────────────────────────────────┘

┌─────────────────────── 🔌 TCP Connection ──────────────────────┐
│ Target           │ Status  │ Response Time │
├──────────────────┼─────────┼───────────────┤
│ github.com:443   │ ✅ Open │ 69.1 ms       │
└──────────────────┴─────────┴───────────────┘

┌─────────────────────── 🌍 HTTP Check ──────────────────────────┐
│ Property      │ Value                     │
├───────────────┼───────────────────────────┤
│ Status        │ ✅ 200 OK                │
│ Response Time │ 97.3 ms                  │
│ Content Type  │ text/html; charset=utf-8 │
│ Server        │ github.com               │
└───────────────┴───────────────────────────┘

┌─────────────────────── 🔒 SSL/TLS Certificate ──────────────────────┐
│ Property          │ Value                                      │
├───────────────────┼────────────────────────────────────────────┤
│ Security Grade    │ A+ (100/100)                               │
│ Subject           │ CN=github.com                              │
│ Issuer            │ Sectigo ECC Domain Validation Secure Serv │
│ Days Until Expiry │ 107                                        │
│ Valid Until       │ Feb  5 23:59:59 2026 GMT                   │
│ Security Issues   │ None detected                              │
└───────────────────┴────────────────────────────────────────────┘

┌─────────────────────── 🏓 ICMP Ping ──────────────────────────┐
│ Target      │ Status        │ Response Time │
├─────────────┼───────────────┼───────────────┤
│ github.com  │ ✅ Reachable  │ 0.0 ms        │
└─────────────┴───────────────┴───────────────┘

Total scan time: 104.5 ms
```

### Port Range Scanning Output

```
╭─────────────────────────────────────────────────────────────────╮
│             EZNet Port Scan Results for example.com (6 ports)   │
╰─────────────────────────────────────────────────────────────────╯

┌─────────────────────── 🔍 Port Scan Results ────────────────────────┐
│ Port │ Service │ Status    │ Response Time               │
├──────┼─────────┼───────────┼─────────────────────────────┤
│ 80   │ HTTP    │ ✅ Open   │ 62.6 ms                     │
│ 81   │ Unknown │ ❌ Closed │ Connection timeout after 5s │
│ 82   │ Unknown │ ❌ Closed │ Connection timeout after 5s │
│ 83   │ Unknown │ ❌ Closed │ Connection timeout after 5s │
│ 84   │ Unknown │ ❌ Closed │ Connection timeout after 5s │
│ 85   │ Unknown │ ❌ Closed │ Connection timeout after 5s │
└──────┴─────────┴───────────┴─────────────────────────────┘

Summary: 1/6 ports open
Open ports: 80
```

### JSON Output

```json
{
  "host": "google.com",
  "port": 80,
  "dns": {
    "hostname": "google.com",
    "ipv4": {
      "success": true,
      "addresses": ["142.250.191.14"],
      "count": 1
    },
    "ipv6": {
      "success": true,
      "addresses": ["2a00:1450:4001:82a::200e"],
      "count": 1
    }
  },
  "tcp": {
    "success": true,
    "host": "google.com",
    "port": 80,
    "response_time_ms": 23.4,
    "status": "open"
  },
  "http": {
    "success": true,
    "host": "google.com",
    "port": 80,
    "url": "http://google.com:80/",
    "protocol": "http",
    "status_code": 200,
    "reason_phrase": "OK",
    "response_time_ms": 45.2,
    "server": "gws",
    "content_type": "text/html; charset=ISO-8859-1"
  },
  "icmp": {
    "success": true,
    "host": "google.com",
    "response_time_ms": 12.8,
    "method": "system_command"
  },
  "duration_ms": 67.3
}
```

## Command Line Options 🛠️

```
Usage: eznet [OPTIONS]

  EZNet - Comprehensive network testing tool.

  Automatically performs DNS resolution, TCP connection tests, HTTP checks,
  and ICMP ping tests without requiring you to remember specific commands.

Options:
  -H, --host TEXT         Hostname or IP address to test  [required]
  -p, --port TEXT         Port number or range to test (e.g., "80", "80-90")
  --common-ports          Scan common ports (115+ ports)
  --ssl-check             Perform SSL/TLS certificate analysis
  -t, --timeout INTEGER   Timeout in seconds (default: 5)
  --json                  Output results in JSON format
  -v, --verbose           Enable verbose output
  --max-concurrent INTEGER
                          Maximum concurrent connections (default: 50)
  --version               Show the version and exit.
  --help                  Show this message and exit.
```

## Dependencies 📋

- **Python 3.12+**
- **click**: Command-line interface
- **rich**: Beautiful terminal output
- **httpx**: HTTP client for async requests
- **aiodns**: Asynchronous DNS resolution (optional, with fallback)

## Development 👨‍💻

### Setup Development Environment

```bash
git clone https://github.com/batr7434/eznet.git
cd eznet

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=eznet

# Run specific test category
pytest -m unit
pytest -m integration
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

## Roadmap 🗺️

**Recently Added Features:**
- ✅ **Port Range Scanning**: Scan multiple ports in ranges (e.g., `80-90`)
- ✅ **Common Ports Scanning**: Scan 115+ frequently used ports
- ✅ **SSL/TLS Certificate Analysis**: Security grading and certificate validation

**Future Features Planned:**
- **Enhanced TLS Analysis**: Cipher suite analysis and protocol version detection
- **Multi-Host Scanning**: Scan multiple hosts from files
- **Service Detection**: Advanced service fingerprinting
- **Performance Monitoring**: Track response times over time
- **Configuration Files**: Save and reuse test configurations
- **Plugin System**: Extend functionality with custom checks
- **Web API**: REST API for programmatic access
- **Docker Support**: Container-based deployment
- **Network Topology Discovery**: Map network infrastructure

## Contributing 🤝

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- Inspired by traditional network tools like `ping`, `telnet`, `nc`, and `curl`
- Built with modern Python async/await patterns
- Uses the excellent `rich` library for beautiful terminal output

## Troubleshooting 🔧

### Homebrew Installation Issues

If `brew install eznet` suggests installing `zeronet` instead, use the full tap name:

```bash
# Correct installation
brew install batr7434/eznet/eznet

# Or add tap first
brew tap batr7434/eznet
brew install eznet
```

### Common Issues

- **"Formula not found"**: Make sure you've added the tap first
- **Permission errors**: Try `brew doctor` to check your Homebrew setup
- **Python version conflicts**: EZNet requires Python 3.12+

## Support 💬

- 📫 Create an issue for bug reports or feature requests
- 💭 Discussions for questions and ideas
- 📖 Check the documentation for detailed usage examples

---

**EZNet** - Making network testing simple and beautiful! 🌐✨