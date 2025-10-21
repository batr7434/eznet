# EZNet Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-10-21

### Added
- **Port Range Scanning**: Scan multiple ports using range syntax (e.g., `80-90`)
- **Common Ports Scanning**: Scan 115+ frequently used ports with `--common-ports` flag
- **SSL/TLS Certificate Analysis**: Comprehensive certificate validation and security scoring
  - Certificate information display (subject, issuer, validity dates)
  - Security grading system (A+ to F)
  - Days until expiration with color-coded warnings
  - Automatic detection of security issues
- **Enhanced CLI Options**:
  - `--ssl-check`: Enable SSL certificate analysis
  - `--common-ports`: Scan common ports
  - `--max-concurrent`: Control concurrent connection limit
- **Improved Output Formatting**: Better tables and color-coded results
- **Enhanced Error Handling**: More robust error reporting and recovery

### Changed
- **License**: Changed from MIT to Apache License 2.0
- **Version**: Bumped to 0.2.0 to reflect major feature additions
- **Documentation**: Updated README with new features and examples
- **Dependencies**: Enhanced type hints and error handling

### Fixed
- **Hostname Validation**: Improved regex for hostname validation
- **Multi-host Support**: Better handling of multiple hosts
- **JSON Output**: Consistent JSON structure across all features
- **Async Performance**: Optimized concurrent operations

### Security
- **SSL Analysis**: Added comprehensive SSL/TLS security assessment
- **Certificate Validation**: Automated detection of certificate issues
- **Security Scoring**: Professional-grade security evaluation

## [0.1.0] - 2024-12-01

### Added
- **Core Network Testing Features**:
  - DNS resolution (IPv4 and IPv6)
  - TCP connection testing
  - HTTP/HTTPS response checking
  - ICMP ping testing
- **CLI Interface**: User-friendly command-line interface with Click
- **Rich Output**: Beautiful, colored terminal output using Rich library
- **JSON Export**: Machine-readable output format
- **Async Operations**: Fast parallel network testing
- **Smart Detection**: Automatic determination of appropriate tests
- **Timeout Control**: Configurable timeout settings
- **Verbose Mode**: Detailed logging and debugging information

### Technical
- **Python 3.12+ Support**: Modern Python with type hints
- **Async/Await**: Non-blocking network operations
- **Error Handling**: Graceful handling of network failures
- **Cross-Platform**: Works on Windows, macOS, and Linux

---

## Release Notes

### Version 0.2.0 Highlights

This release significantly expands EZNet's capabilities with three major new features:

1. **Advanced Port Scanning**: From simple single-port tests to comprehensive port range and common port scanning
2. **SSL Security Analysis**: Professional-grade certificate validation and security assessment
3. **Enhanced User Experience**: Improved output formatting, better error handling, and more intuitive CLI options

The tool now serves both quick connectivity checks and detailed security analysis needs, making it suitable for DevOps, security professionals, and system administrators.

### Breaking Changes

None in this release. All existing functionality remains backward compatible.

### Migration Guide

No migration needed. All existing commands and options continue to work as before. New features are opt-in through additional flags.

### Performance Improvements

- Optimized concurrent connections for port scanning
- Improved async operations for better performance
- Enhanced error recovery and timeout handling

### Future Roadmap

- Enhanced TLS/SSL analysis with cipher suite detection
- Multi-host batch scanning from files
- Network topology discovery
- Performance monitoring and trending
- Web API for programmatic access