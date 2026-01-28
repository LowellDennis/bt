#!/usr/bin/env python3
"""
Version Bump Script for BIOS Tool

Updates version numbers across all project files consistently.

Usage:
    python scripts/bump-version.py 1.1.0
    python scripts/bump-version.py 1.1.0 --dry-run
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Version format: Major.Minor.Patch
VERSION_PATTERN = r'\d+\.\d+\.\d+'

# Files to update with their version patterns
VERSION_FILES = [
    {
        'file': 'README.md',
        'patterns': [
            (r'\*\*Current Version:\*\* V\d+\.\d+', r'**Current Version:** V{}'),
            (r'\| \*\*V\d+\.\d+\*\* \|', r'| **V{}** |'),
        ]
    },
    {
        'file': 'installers/windows/biostool.iss',
        'patterns': [
            (r'#define MyAppVersion "\d+\.\d+\.\d+"', r'#define MyAppVersion "{}"'),
        ]
    },
    {
        'file': 'installers/linux/debian/changelog',
        'patterns': [
            (r'^biostool \(\d+\.\d+\.\d+-1\)', r'biostool ({}-1)'),
        ]
    },
    {
        'file': '.vscode-extension/package.json',
        'patterns': [
            (r'"version": "\d+\.\d+\.\d+"', r'"version": "{}"'),
        ]
    },
    {
        'file': 'installers/README.md',
        'patterns': [
            (r'BIOSTool-\d+\.\d+\.\d+-Setup\.exe', r'BIOSTool-{}-Setup.exe'),
            (r'biostool_\d+\.\d+\.\d+-1_all\.deb', r'biostool_{}-1_all.deb'),
            (r'\*\*Current Version:\*\* V\d+\.\d+', r'**Current Version:** V{}'),
        ]
    },
]


def validate_version(version: str) -> bool:
    """Validate version format (Major.Minor.Patch)"""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))


def get_current_version() -> str:
    """Extract current version from README.md"""
    readme_path = PROJECT_ROOT / 'README.md'
    content = readme_path.read_text(encoding='utf-8')
    match = re.search(r'\*\*Current Version:\*\* V(\d+\.\d+)', content)
    if match:
        return match.group(1) + '.0'  # Assuming patch version
    return 'unknown'


def update_file(file_info: dict, new_version: str, dry_run: bool = False) -> List[str]:
    """Update version in a single file"""
    file_path = PROJECT_ROOT / file_info['file']
    
    if not file_path.exists():
        return [f"⚠️  File not found: {file_info['file']}"]
    
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    changes = []
    
    # Apply each pattern replacement
    for pattern, replacement in file_info['patterns']:
        # Format replacement string with new version
        # Handle both full version (1.0.0) and short version (1.0)
        if '{}' in replacement:
            short_version = '.'.join(new_version.split('.')[:2])  # Major.Minor
            
            # Determine which version format to use based on the original pattern
            if 'V' in pattern and not '.' in pattern.split('V')[1].split(r'\d')[0]:
                # Pattern like V\d+\.\d+ (short version)
                repl = replacement.format(short_version)
            else:
                # Full version
                repl = replacement.format(new_version)
            
            matches = list(re.finditer(pattern, content))
            if matches:
                content = re.sub(pattern, repl, content)
                changes.append(f"  ✓ Updated: {pattern[:40]}...")
    
    # Write changes if not dry run
    if content != original_content:
        if not dry_run:
            file_path.write_text(content, encoding='utf-8')
            return [f"✓ {file_info['file']}: {len(changes)} change(s)"] + changes
        else:
            return [f"[DRY RUN] {file_info['file']}: {len(changes)} change(s)"] + changes
    
    return [f"- {file_info['file']}: No changes needed"]


def main():
    """Main entry point"""
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python bump-version.py <new-version> [--dry-run]")
        print("Example: python bump-version.py 1.1.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    # Validate version format
    if not validate_version(new_version):
        print(f"❌ Invalid version format: {new_version}")
        print("Expected format: Major.Minor.Patch (e.g., 1.0.0)")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    
    print("=" * 60)
    print("BIOS Tool Version Bump")
    print("=" * 60)
    print(f"Current version: {current_version}")
    print(f"New version:     {new_version}")
    if dry_run:
        print("Mode:            DRY RUN (no files will be modified)")
    print("=" * 60)
    print()
    
    # Update each file
    all_results = []
    for file_info in VERSION_FILES:
        results = update_file(file_info, new_version, dry_run)
        all_results.extend(results)
        for result in results:
            print(result)
        print()
    
    # Summary
    print("=" * 60)
    if dry_run:
        print("Dry run complete. Use without --dry-run to apply changes.")
    else:
        print("✓ Version bump complete!")
        print()
        print("Next steps:")
        print("1. Review the changes: git diff")
        print("2. Update CHANGELOG.md with release notes")
        print("3. Commit: git commit -am 'Bump version to {}'".format(new_version))
        print("4. Tag: git tag -a V{} -m 'Version {}'".format(
            '.'.join(new_version.split('.')[:2]), 
            '.'.join(new_version.split('.')[:2])
        ))
        print("5. Build installers")
        print("6. Push: git push && git push --tags")
    print("=" * 60)


if __name__ == '__main__':
    main()
