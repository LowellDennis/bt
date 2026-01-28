# Pytest configuration and shared fixtures

import pytest
import os
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def temp_config(temp_dir):
    """Create temporary configuration files."""
    config_dir = Path(temp_dir)
    global_config = config_dir / "global.txt"
    local_config = config_dir / "local.txt"
    
    # Create empty config files
    global_config.touch()
    local_config.touch()
    
    yield {
        'dir': config_dir,
        'global': global_config,
        'local': local_config
    }


@pytest.fixture
def mock_git_repo(temp_dir):
    """Create a mock Git repository for testing."""
    import subprocess
    
    repo_path = Path(temp_dir)
    
    # Initialize git repo
    subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True)
    
    # Create initial commit
    readme = repo_path / 'README.md'
    readme.write_text('# Test Repository')
    subprocess.run(['git', 'add', 'README.md'], cwd=repo_path, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True, capture_output=True)
    
    yield repo_path


@pytest.fixture
def isolated_environment(monkeypatch, temp_dir):
    """Provide an isolated environment for testing."""
    # Change to temp directory
    monkeypatch.chdir(temp_dir)
    
    # Clear environment variables that might affect tests
    env_vars = ['BIOS_SOURCE', 'BUILD_TARGET', 'EDITOR', 'JUMP_SERVER']
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    
    yield temp_dir
