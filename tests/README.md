# BT Test Suite

This directory contains automated tests for the BIOS Tool (BT) project.

## Test Structure

```
tests/
  unit/           # Unit tests for individual modules
  integration/    # Integration tests for command workflows
  fixtures/       # Test data and fixtures
  conftest.py     # Pytest configuration and shared fixtures
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test categories:
```bash
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
```

### Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file:
```bash
pytest tests/unit/test_data.py
```

## Writing Tests

### Test Naming Convention
- Test files: `test_<module>.py`
- Test functions: `test_<functionality>()`
- Test classes: `Test<Component>`

### Example Test Structure
```python
import pytest
from data import get, set

def test_config_get_existing_key():
    """Test retrieving an existing configuration key."""
    # Arrange
    set('TEST_KEY', 'test_value')
    
    # Act
    result = get('TEST_KEY')
    
    # Assert
    assert result == 'test_value'

def test_config_get_missing_key():
    """Test retrieving a non-existent key."""
    # Act
    result = get('NONEXISTENT_KEY')
    
    # Assert
    assert result is None
```

### Fixtures
Use `conftest.py` for shared fixtures:
- Mock Git repositories
- Temporary configuration files
- Isolated test environments

### Mocking VCS Operations
When testing commands that use Git:
```python
from unittest.mock import patch

@patch('vcs.is_repository')
def test_command_needs_vcs(mock_is_repo):
    mock_is_repo.return_value = True
    # Test logic here
```

## Test Coverage Goals

- **Core modules** (run.py, data.py, vcs.py): 80%+ coverage
- **Commands**: 70%+ coverage
- **Critical paths**: 90%+ coverage

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Release tags

See `.github/workflows/test.yml` for CI configuration.
