#!/usr/bin/env python
"""
DSC file parser for estimating UEFI module build counts.
Handles DEFINE variables, !include directives, and architecture-specific sections.
"""

import os
import re

# Constants for estimation
FUDGE_FACTOR = 2.0  # Multiply DSC count by this factor to account for libraries and variations
MINIMUM_ESTIMATE = 2000  # Minimum estimate to use if DSC parsing yields low results


def build_packages_path(workspace_dir):
    """
    Build list of package search paths from workspace.
    
    Args:
        workspace_dir: Root directory of the workspace
    
    Returns:
        List of absolute paths to search for packages
    """
    packages_path = [workspace_dir]
    
    # Add common required paths
    common_paths = ['HpeServerCore', 'HpeIntel', 'Edk2', 'Edk2-Platforms', 'Intel']
    for common in common_paths:
        common_path = os.path.join(workspace_dir, common)
        if os.path.isdir(common_path):
            packages_path.append(common_path)
    
    # Add paths from GitSubmoduleInfo.txt
    git_submodule_file = os.path.join(workspace_dir, 'GitSubmoduleInfo.txt')
    if os.path.isfile(git_submodule_file):
        try:
            with open(git_submodule_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('['):
                        pkg_path = os.path.join(workspace_dir, line)
                        if os.path.isdir(pkg_path) and pkg_path not in packages_path:
                            packages_path.append(pkg_path)
        except:
            pass
    
    return packages_path


def resolve_variable(value, defines):
    """
    Resolve $(VARIABLE) references in a string.
    
    Args:
        value: String that may contain $(VAR) references
        defines: Dictionary of variable definitions
    
    Returns:
        String with variables resolved
    """
    max_iterations = 10
    iteration = 0
    while iteration < max_iterations:
        match = re.search(r'\$\((\w+)\)', value)
        if not match:
            break
        var_name = match.group(1)
        if var_name in defines:
            value = value.replace(match.group(0), defines[var_name])
        else:
            break
        iteration += 1
    return value


def parse_dsc_for_modules(dsc_file, packages_path, defines, visited):
    """
    Parse DSC file for module references with architecture tracking.
    
    Args:
        dsc_file: Path to DSC file to parse
        packages_path: List of paths to search for included files
        defines: Dictionary of DEFINE variables
        visited: Set of already processed DSC files (to avoid loops)
    
    Returns:
        Dictionary mapping INF paths to sets of architectures
        Example: {'Path/Module.inf': {'IA32', 'X64'}}
    """
    abs_path = os.path.abspath(dsc_file)
    if abs_path in visited:
        return {}
    visited.add(abs_path)
    
    modules = {}
    
    try:
        with open(dsc_file, 'r', encoding='utf-8', errors='ignore') as f:
            in_defines_section = False
            in_components_section = False
            section_arch = None
            
            for line in f:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if '#' in line:
                    line = line.split('#')[0].strip()
                
                # Track sections
                if line.startswith('['):
                    in_defines_section = line.startswith('[Defines]')
                    in_components_section = line.startswith('[Components')
                    
                    # Extract architecture from section header
                    if in_components_section:
                        # Check for specific architecture
                        arch_match = re.search(r'\[Components\.(IA32|X64|ARM|AARCH64)\b', line, re.IGNORECASE)
                        if arch_match:
                            section_arch = arch_match.group(1).upper()
                        # Check for .common or no architecture suffix (both mean all architectures)
                        elif re.search(r'\[Components(\.(common|Common|COMMON))?\]', line):
                            section_arch = 'COMMON'  # Special marker for common sections
                        else:
                            section_arch = None
                    else:
                        section_arch = None
                    continue
                
                # Parse DEFINE statements
                if (in_defines_section or line.startswith('DEFINE ')) and 'DEFINE ' in line:
                    match = re.match(r'DEFINE\s+(\w+)\s*=\s*(.+)', line)
                    if match:
                        key, value = match.groups()
                        defines[key] = value.strip()
                    continue
                
                # Parse !include statements
                if line.startswith('!include '):
                    include_path = line[9:].strip()
                    include_path = resolve_variable(include_path, defines)
                    
                    # Skip if still has unresolved variables
                    if '$(' in include_path:
                        continue
                    
                    # Find the include file
                    include_file = None
                    for pkg_path in packages_path:
                        test_path = os.path.join(pkg_path, include_path.replace('/', os.sep))
                        if os.path.isfile(test_path):
                            include_file = test_path
                            break
                    
                    if include_file:
                        sub_modules = parse_dsc_for_modules(include_file, packages_path, defines.copy(), visited)
                        for inf_path, archs in sub_modules.items():
                            if inf_path not in modules:
                                modules[inf_path] = set()
                            modules[inf_path].update(archs)
                    continue
                
                # Parse component INF references
                if in_components_section and '.inf' in line.lower():
                    match = re.search(r'([^\s|]+\.inf)', line, re.IGNORECASE)
                    if match:
                        inf_path = match.group(1)
                        inf_path = resolve_variable(inf_path, defines)
                        inf_path = inf_path.replace('\\', '/')
                        
                        # Determine architectures for this module
                        if section_arch == 'COMMON':
                            # Common section - both IA32 and X64
                            archs = ['IA32', 'X64']
                        elif section_arch:
                            # Specific architecture
                            archs = [section_arch]
                        else:
                            # No architecture specified (shouldn't happen in well-formed DSC)
                            archs = ['IA32', 'X64']
                        
                        if inf_path not in modules:
                            modules[inf_path] = set()
                        modules[inf_path].update(archs)
    
    except Exception as e:
        pass
    
    return modules


def estimate_module_count(workspace_dir, platform_path):
    """
    Estimate module build count by parsing DSC files.
    
    Args:
        workspace_dir: Root directory of the workspace
        platform_path: Absolute path to platform package directory
    
    Returns:
        Tuple of (estimated_count, unique_modules, total_builds)
        Returns (600, 0, 0) if parsing fails
    """
    try:
        # Find the main DSC file
        dsc_file = os.path.join(platform_path, 'PlatformPkg.dsc')
        if not os.path.isfile(dsc_file):
            return (MINIMUM_ESTIMATE, 0, 0)  # Default estimate
        
        # Build packages path for resolving includes
        packages_path = build_packages_path(workspace_dir)
        
        # Parse DSC with proper path resolution
        defines = {'PLATFORM_DIR': platform_path, 'WORKSPACE': workspace_dir}
        modules = parse_dsc_for_modules(dsc_file, packages_path, defines, set())
        
        # Count total builds (accounting for multiple architectures)
        unique_modules = len(modules)
        total_builds = sum(len(archs) for archs in modules.values())
        
        # If we found very few, DSC parsing likely failed - use default
        if unique_modules < 50:
            return (MINIMUM_ESTIMATE, unique_modules, total_builds)  # Default estimate
        
        # Apply fudge factor to account for library dependencies and variations
        estimated = int(total_builds * FUDGE_FACTOR)
        
        # Ensure estimate meets minimum threshold
        estimated = max(estimated, MINIMUM_ESTIMATE)
        
        return (estimated, unique_modules, total_builds)
    
    except Exception as e:
        return (MINIMUM_ESTIMATE, 0, 0)  # Default estimate on error
