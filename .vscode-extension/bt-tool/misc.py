#!/usr/bin/env python

# Standard python modules
import re
import sys

# Local modules
import data
from   error import ErrorMessage
from   run   import RunCommand

ipv4 = re.compile('^(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
# Normalize a setting value to on/off and return appropriate result
# value:     Value to check (can be None or empty string)
# onResult:  Value to return if setting is "on"
# offResult: Value to return if setting is "off"
# returns:   onResult or offResult based on normalized value
def NormalizeSetting(value, onResult, offResult):
  if not value:
    return offResult
  lower_value = value.lower()
  if lower_value in ['on', 'enabled', 'true', 'yes', '1']:
    return onResult
  else:
    return offResult
# Fixup a string
# item:   String to be fixed
# returns Fixed-up string
def FixStr(item):
  if sys.version_info > (3, 0):
    return str(item, 'utf-8')
  return item

# Fixup a path string (in case wrong slashes are used)
# path: Path String to be fixed
# forceWindows: If True, force Windows style path
# returns Fixed-up string
def FixPath(path, forceWindows=False):
  if data.gbl.platform == 'Windows' or forceWindows:
    path = path.replace('/', '\\')          # Replace slashes with backslashes on Windows
  else:
    path = path.replace('\\', '/')          # Replace backslashes with slashes on Linux/Mac
  return path

# Fixup a branch string (in case wrong slashes are used)
# path: Path String to be fixed
# returns Fixed-up string
def FixBranch(path):
  path = path.replace('\\', '/')          # Replace backslashes with slashes in branch names
  return path

# Return the build type indicated by the local setting releae
# returns one of 'DEBUG' or 'RELEASE'
def GetBuildType():
  release = data.lcl.GetItem('release')    # Release does not have to be set
  return NormalizeSetting(release, 'RELEASE', 'DEBUG')

# Return the setting indicated by the local setting warnings
# returns True if warnings is set to on, False otherwise
def GetWarnings():
  warning = data.lcl.GetItem('warnings')    # Warnings does not have to be set
  return NormalizeSetting(warning, True, False)

# Return the setting indicated by the local setting alert
# returns True if alert is set to on, False otherwise
def GetAlert():
  alert = data.lcl.GetItem('alert')       # Alert does not have to be set
  return NormalizeSetting(alert, True, False)

# Return the setting indicated by the local setting itp
# returns True if itp is set to ON, False otherwise
def GetITP():
  itp = data.lcl.GetItem('itp')           # ITP does not have to be set
  return NormalizeSetting(itp, True, False)

# Validate an IP address
# returns IP address if OK, does not return otherwise
def ValidateIP(ip):
  global ipv4
  if ipv4.match(ip): return ip
  ErrorMessage('Invalid IP address: {0}'.format(ip))

# Return BMC info indicated by the local setting bmc
# The bmc config entry is of the format ilo|openbmc;<ip-address>;[<username>;<password>]
# For openmbc the username and password will default to root/0penBmc
# There is no default username and password for ilo
# retunrns None if bmc is not set, otherwise returns parsed BMC information as a dictionary
#   {bmc: ilo | openbmc, ip: <ip-address>, user: <username>, pswd: <password> }
def GetBmcInfo():
  info = None                               # Assume bmc is not set
  bmc = data.lcl.GetItem('bmc')             # Bmc does not have to be set
  # Parse info?
  if bmc:
    bmc    = bmc.split(';')
    length = len(bmc)
    if bmc[0].lower() == 'ilo':
      # Indicate iLO (no other defaults)
      info = { 'bmc': 'iLO' }
    elif bmc[0].lower() == 'openbmc':
      # Indicate OpenBMC (with default user and password)
      info = { 'bmc': 'OpenBMC', 'user': 'root', 'password': '0penBmc' }
    else:
      ErrorMessage('Unrecognized BMC name: {0}'.format(bmc[0]))
      # DOES NOT RETURN
    if length < 2:
      ErrorMessage('IP address required for {0}'.format(info['bmc']))
    info['ip'] = ValidateIP(bmc[1])
    if length > 2: info['user'] = bmc[2]
    if length > 3: info['pswd'] = bmc[3]
  return info

# Return Jump Station info indicated by the local setting jump
# The jump config entry is just the destination path
# Returns None if jump is not set, otherwise returns a dictionary with {dest: <destination-path>}
def GetJumpStationInfo():
  info = None
  jump = data.lcl.GetItem('jump')
  if jump:
    info = {'dest': jump}
  return info

# Get the current branch
# returns the current branch or None if none found
def GetCurrentBranch(worktree):
  rc, info = RunCommand('git branch', worktree)
  if rc == 0:
    for line in FixStr(info).split('\n'):
      if line[0] == '*':
        return line[2:]
  return None
