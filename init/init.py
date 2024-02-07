#!/usr/bin/env python 

# Standard python modules
import json
import os
import re
import sys

# Local modules
import data
from   error    import ErrorMessage, UsageError
from   cmdline  import ParseCommandLine
from   misc     import FixPath

PRODUCT_PATHS = [
  'HpeProductLine/Volume/HpPlatforms',    # Gen 11
  'HpeProductLine/HPC/HpPlatforms',       # Gen 11
  'HpeProductLine/Synergy/HpPlatforms',   # Gen 11
  'HpeProductLine/Alabama/HpPlatforms',   # Gen 11
  'Volume/HpPlatforms',                   # Gen 10+
  'HPC/HpPlatforms',                      # Gen 10+
  'Synergy/HpPlatforms',                  # Gen 10+
  'Alabama/HpPlatforms',                  # Gen 10+
  'HpPlatforms',                          # Gen 10/9
]

# Find the platform package
# top:      top of tree
# platform: platform name
# returns path to platform package or None if no found
def FindPlatformPackage(top, platform):
  global PRODUCT_PATHS
  # Find platform package directory
  target = platform.lower() + 'pkg'
  for path in PRODUCT_PATHS:
    if data.gbl.platform == 'Windows':
      path = path.replace('/', '\\')  # Fix slashes
    base = os.path.join(top, path)
    for rootdir, dirs, files in os.walk(base):
      for subdir in dirs:
        if subdir.lower() == target: return os.path.join(rootdir, subdir)
  return None

# Determine the type of AMD CPU
# platform: full path to platform package
# returns the AMD CPU name (e.g. milan)
# DOES NOT RETURN IF THERE IS AN ERROR
def GetAmdCpu(platform):
  try:
    with open(os.path.join(platform,"PlatformPkgBuildArgs.txt"),'r') as f:
      lines = f.readlines()
      for line in lines:
        if not line.startswith('-D CPUTARGET='): continue
        return line.replace('-D CPUTARGET=','').strip().lower()
      else:
        ErrorMessage('Unable to autodetect AMD CPU type')
        # DOES NOT RETURN
  except FileNotFoundError:
    ErrorMessage('PlatformPkgBuildArgs.txt not found in platform package directory')
    # DOES NOT RETURN

# Determine the type of Arm CPU
# platform: full path to platform package
# returns the Arm CPU name (e.g. Ampere Pro)
# DOES NOT RETURN IF THERE IS AN ERROR
def GetArmCpu(platform):
  try:
    with open(os.path.join(platform,"PlatformPkgBuildArgs.txt"),'r') as f:
      lines = f.readlines()
      for line in lines:
        if not line.startswith('-D CPUTARGET='): continue
        return line.replace('-D CPUTARGET=','').strip().lower()
      else:
        ErrorMessage('Unable to autodetect Arm CPU type')
        # DOES NOT RETURN
  except FileNotFoundError:
    ErrorMessage('PlatformPkgBuildArgs.txt not found in platform package directory')
    # DOES NOT RETURN

# Determine the type of Intel CPU
# platform: full path to platform package
# returns the Intel CPU name (e.g. eaglestream)
# DOES NOT RETURN IF THERE IS AN ERROR
def GetIntelCpu(platform):
  try:
    with open(os.path.join(platform,'PlatformPkg.dsc'),'r') as f:
      lines = f.readlines()
      for line in lines:
        line = line.strip()
        if not line.startswith('DEFINE'): continue
        items = line.split()
        if   items[1] == 'HP_CHIPSETINFO_PKG':
          return items[3][2:-3].lower()
        elif items[1] == 'HP_SOCKET_PKG':
          return items[3][2:-9].lower()
        else: continue
      else:
        ErrorMessage('Unable to autodetect Intel CPU type')
        # DOES NOT RETURN
  except FileNotFoundError:
    ErrorMessage('PlatformPkg.dsc not found in platform package directory')
    # DOES NOT RETURN

# Autodetect the vendor and cpu
# top:  top of tree
# name: platform name
def AutoDetect(top, name):
  platform = FindPlatformPackage(top, name)
  if not platform:
    ErrorMessage('Unable to autodetect platform package')
    # DOES NOT RETURN
  # See if it is AMD
  if name[0] == 'A':
    vendor = 'amd'
    cpu    = GetAmdCpu(platform)
    # Does not return if CPU cannot be determined
  elif name[0] == 'R':
    vendor = 'arm'
    cpu    = GetArmCpu(platform)
    # Does not return if CPU cannot be determined
  else:
    vendor = 'intel'
    cpu    = GetIntelCpu(platform)
  return (platform, vendor, cpu)

# Init command handler
# returns 0 on success, DOES NOT RETURN otherwise
def init():
  # Make sure the current directory makes sense as a build dreictory
  cwd = os.getcwd()
  # Check for build file file
  script = 'hpbuild.bat' if data.gbl.platform == 'Windows' else 'hpbuild.sh'
  bld = os.path.join(cwd, script)
  if not os.path.isfile(bld):
    ErrorMessage('Current directory is not a platform build directory: {0}'.format(cwd))
    # DOES NOT RETURN

  # Get command line information
  prms, opts = ParseCommandLine(None, 1)
  # Does not return if invalid options or parameters are found

  # Platform must be given
  if len(prms) == 0:
    UsageError('platform name must be provided')
    # DOES NOT RETURN

  # Save platform name
  name = prms[0] if len(prms) > 0 else ''
  data.lcl.SetItem('name', name)
  print('  {0:>6}.{1:<8} = "{2}"'.format('local', 'name', name))

  # Autodetect CPU vendor
  platform, vendor, cpu = AutoDetect(cwd, name)
  # Does not return if autodetect fails

  # Platform path is supposed to be relative to the top of tree
  worktree = data.gbl.GetItem('worktree')
  platform = os.path.relpath(platform, worktree)

  # Save platform and CPU information
  data.lcl.SetItem('platform', platform)
  data.lcl.SetItem('vendor', vendor)
  data.lcl.SetItem('cpu',   cpu)
  print('  {0:>6}.{1:<8} = "{2}"'.format('local', 'platform', platform))
  print('  {0:>6}.{1:<8} = "{2}"'.format('local', 'vendor',   vendor))
  print('  {0:>6}.{1:<8} = "{2}"'.format('local', 'cpu',      cpu))

  # Initialize other items
  data.lcl.SetItem('alert',    "FALSE")
  data.lcl.SetItem('release',  "FALSE")
  data.lcl.SetItem('warnings', "FALSE")
  print('  {0:>6}.{1:<8} = "{2}"'.format('local', 'alert',    "FALSE"))
  print('  {0:>6}.{1:<8} = "{2}"'.format('local', 'release',  "FALSE"))
  print('  {0:>6}.{1:<8} = "{2}"'.format('local', 'warmings', "FALSE"))
