#!/usr/bin/env python

# Standard python modules
import re
import sys

# Local modules
import data
from   error import ErrorMessage
from   run   import RunCommand

ipv4 = re.compile('^(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')

# Fixup a string
# item:   String to be fixed
# returns Fixed-up string
def FixStr(item):
  if sys.version_info > (3, 0):
    return str(item, 'utf-8')
  return item

# Fixup a path string for proper OS support
# path: Path String to be fixed
# returns Fixed-up string
def FixPath(path):
  if data.gbl.platform == 'Windows':
    path = path.replace('/', '\\')          # Replace slashes with backslashes
  return path

# Return the build type indicated by the local setting releae
# returns one of 'DEBUG' or 'RELEASE'
def GetBuildType():
  release  = data.lcl.GetItem('release')    # Release does not have to be set
  if not release:
    release = 'off'
  return 'RELEASE' if release.lower() == 'on' else 'DEBUG'

# Return the setting indicated by the local setting warnings
# returns True if warnings is set to TRUE, False otherwise
def GetWarnings():
  warning = data.lcl.GetItem('warnings')    # Warnings does not have to be set
  if warning == None: warning == 'FALSE'
  return True if warning.upper() == 'TRUE' else False

# Return the setting indicated by the local setting alert
# returns True if alert is set to TRUE, False otherwise
def GetAlert():
  alert = data.lcl.GetItem('alert')       # Alert does not have to be set
  if alert == None: alert == 'OFF'
  return True if alert.upper() == 'ON' else False

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

# Get the current branch
# returns the current branch or None if none found
def GetCurrentBranch(worktree):
  rc, info = RunCommand('git branch', worktree)
  if rc == 0:
    for line in FixStr(info).split('\n'):
      if line[0] == '*':
        return line[2:]
  return None
