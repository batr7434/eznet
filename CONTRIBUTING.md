# Contributing to EZNet

Thank you for your interest in contributing to EZNet! We welcome contributions from everyone.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Git

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/eznet.git
   cd eznet
   ```

3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Making Changes

### Development Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards
3. Write or update tests for your changes
4. Run the test suite to ensure everything works:
   ```bash
   pytest
   ```

5. Run code quality checks:
   ```bash
   # Format code
   black src/ tests/
   isort src/ tests/
   
   # Lint code
   flake8 src/ tests/
   mypy src/
   
   # Or run all checks at once
   pre-commit run --all-files
   ```

6. Commit your changes with a descriptive message:
   ```bash
   git commit -m "feat: add port range scanning feature"
   ```

7. Push to your fork and submit a pull request

### Coding Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions and methods
- Write docstrings for all public functions, classes, and modules
- Keep functions small and focused
- Use descriptive variable and function names
- Add comments for complex logic

### Commit Message Format

We follow the [Conventional Commits](https://conventionalcommits.org/) specification:

- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `style:` formatting changes that don't affect functionality
- `refactor:` code changes that neither fix bugs nor add features
- `test:` adding or updating tests
- `chore:` maintenance tasks

Examples:
- `feat: add SSL certificate validation`
- `fix: handle timeout errors in TCP checker`
- `docs: update README with new examples`

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use the issue template when available
3. Provide clear reproduction steps
4. Include system information (OS, Python version)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/eznet.git
   cd eznet
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Quality Checks**
   ```bash
   # Format code
   black src/ tests/
   isort src/ tests/
   
   # Lint code
   flake8 src/ tests/
   mypy src/
   
   # Run tests
   pytest tests/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

### Python Code Style

- **Formatter**: Black (line length: 100)
- **Import Sorting**: isort
- **Linting**: flake8
- **Type Checking**: mypy

### Code Organization

- Keep functions focused and small
- Use type hints for all public APIs
- Write comprehensive docstrings
- Follow Google docstring style

### Example Function

```python
async def check_connection(host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
    """
    Check TCP connection to a host and port.
    
    Args:
        host: Target hostname or IP address
        port: Target port number
        timeout: Connection timeout in seconds
        
    Returns:
        Dictionary containing connection results
        
    Raises:
        ValueError: If port is invalid
        
    Example:
        >>> result = await check_connection("google.com", 80)
        >>> print(result["success"])
        True
    """
    if not is_valid_port(port):
        raise ValueError(f"Invalid port: {port}")
    
    # Implementation here...
```

## Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── test_basic.py          # Unit tests
├── test_integration.py    # Integration tests
├── test_performance.py    # Performance tests
└── conftest.py           # Pytest fixtures
```

### Writing Tests

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Test performance characteristics

### Test Categories

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_dns_validation():
    """Unit test for DNS validation."""
    pass

@pytest.mark.integration
async def test_full_network_check():
    """Integration test for complete network check."""
    pass

@pytest.mark.slow
async def test_timeout_behavior():
    """Slow test for timeout behavior."""
    pass
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# With coverage
pytest --cov=eznet --cov-report=html

# Parallel execution
pytest -n auto
```

## Documentation

### Code Documentation

- All public functions/classes need docstrings
- Use Google docstring format
- Include examples in docstrings when helpful
- Document complex algorithms

### README Updates

- Update README.md for new features
- Add usage examples
- Update installation instructions if needed

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

Examples:
```
feat(dns): add IPv6 support for DNS resolution
fix(tcp): handle connection timeout correctly
docs: update installation instructions
```

## Architecture Guidelines

### Module Structure

```
src/eznet/
├── __init__.py           # Package initialization
├── cli.py               # CLI interface
├── dns_check.py         # DNS functionality
├── tcp_check.py         # TCP functionality
├── http_check.py        # HTTP functionality
├── icmp_check.py        # ICMP functionality
└── utils.py             # Utility functions
```

### Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Async First**: Use asyncio for all I/O operations
3. **Error Handling**: Graceful error handling with informative messages
4. **Testability**: Design for easy unit testing
5. **Extensibility**: Make it easy to add new check types

### Adding New Features

When adding new network checks:

1. Create a new module (e.g., `ssl_check.py`)
2. Follow existing patterns for async operation
3. Add comprehensive tests
4. Update CLI integration
5. Add documentation

## Performance Considerations

- Use asyncio for concurrent operations
- Implement proper timeout handling
- Consider memory usage for large scans
- Profile performance-critical code

## Security Considerations

- Validate all user inputs
- Handle network errors gracefully
- Don't expose sensitive information
- Consider privilege requirements (e.g., ICMP)

## Getting Help

- Create an issue for questions
- Join discussions for ideas
- Check existing documentation first
- Provide context when asking for help

Thank you for contributing to EZNet! 🌐✨