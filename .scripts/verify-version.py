#!/usr/bin/env python3
"""
Version Verification Script for BIOS Tool

Verifies that version numbers are consistent across all project files.
Useful as a pre-commit hook or CI check.

Usage:
    python scripts/verify-version.py
"""

import sys
import re
from pathlib import Path
from typing import Dict, List

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Version extraction patterns for each file
VERSION_CHECKS = [
    {
        'file': 'README.md',
        'pattern': r'\*\*Current Version:\*\* V(\d+\.\d+)',
        'name': 'README (header)'
    },
    {
        'file': 'installers/windows/biostool.iss',
        'pattern': r'#define MyAppVersion "(\d+\.\d+\.\d+)"',
        'name': 'Windows Installer'
    },
    {
        'file': 'installers/linux/debian/changelog',
        'pattern': r'^biostool \((\d+\.\d+\.\d+)-1\)',
        'name': 'Debian Changelog'
    },
    {
        'file': '.vscode-extension/package.json',
        'pattern': r'"version": "(\d+\.\d+\.\d+)"',
        'name': 'VS Code Extension'
    },
]


def extract_version(file_path: Path, pattern: str) -> str:
    """Extract version from a file using regex pattern"""
    try:
        content = file_path.read_text(encoding='utf-8')
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        return f"ERROR: {e}"


def normalize_version(version: str) -> str:
    """Normalize version to Major.Minor.Patch format"""
    if not version or version.startswith('ERROR'):
        return version
    
    parts = version.split('.')
    if len(parts) == 2:
        # Add .0 for patch version
        return f"{parts[0]}.{parts[1]}.0"
    return version


def main():
    """Main entry point"""
    print("=" * 60)
    print("BIOS Tool Version Verification")
    print("=" * 60)
    print()
    
    versions = {}
    errors = []
    
    # Extract versions from all files
    for check in VERSION_CHECKS:
        file_path = PROJECT_ROOT / check['file']
        
        if not file_path.exists():
            errors.append(f"❌ File not found: {check['file']}")
            continue
        
        version = extract_version(file_path, check['pattern'])
        
        if version is None:
            errors.append(f"❌ Could not find version in {check['file']}")
            continue
        
        if version.startswith('ERROR'):
            errors.append(f"❌ Error reading {check['file']}: {version}")
            continue
        
        normalized = normalize_version(version)
        versions[check['name']] = {
            'raw': version,
            'normalized': normalized,
            'file': check['file']
        }
        
        print(f"✓ {check['name']:25s} : {version}")
    
    print()
    
    # Check for errors
    if errors:
        print("Errors found:")
        for error in errors:
            print(f"  {error}")
        print()
        sys.exit(1)
    
    # Check consistency
    normalized_versions = [v['normalized'] for v in versions.values()]
    unique_versions = set(normalized_versions)
    
    if len(unique_versions) > 1:
        print("❌ VERSION MISMATCH DETECTED!")
        print()
        print("Found different versions:")
        for name, info in versions.items():
            print(f"  {name:25s} : {info['normalized']:10s} ({info['file']})")
        print()
        print("All version numbers must match.")
        print("Use: python scripts/bump-version.py <version>")
        sys.exit(1)
    
    # Success
    current_version = list(unique_versions)[0]
    print("=" * 60)
    print(f"✓ All versions consistent: {current_version}")
    print("=" * 60)
    sys.exit(0)


if __name__ == '__main__':
    main()
