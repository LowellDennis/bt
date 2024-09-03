#!/usr/bin/env python

# Standard python modules
import os
import re
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from abbrev   import UniqueAbbreviation
from error    import ErrorMessage, UsageError

rePath = re.compile('([a-z]:)?', re.IGNORECASE)

# Display the value of an BIOSTool setting
# item:  Setting to be displayed
# local: True if it is a local setting, False if it is a global setting
def DisplayItem(item, local):
  extra = []
  if local: value = data.lcl.GetItem(item)
  else:
    value = data.gbl.GetItem(item)
    if item == 'repositories':
      items = value.split(';')
      value = items[0]
      extra = items[1:]
    elif item == 'worktrees':
      extra = value[1:]
      value = value[0]
  # Display it
  print('  {0}.{1:<15}  = "{2}"'.format('local' if local else 'global', item, value))
  if extra:
    for val in extra:
      print('                            "{0}"'.format(val.strip()))


# Validates a file path
# path:   Path to validate
# returns Path if it is to be used, '' otherwise
# Note: This function allows the user to enter paths that may be currently
#       unavailable (as in network paths when network is not available).
def ValidatePath(path):
  pos  = 0
  size = len(path)
  # Look for <drive>:
  if size >= 2 and path[0].isalpha() and path[1] == ':':
    pos += 2
  # Look for \\share
  elif size >= 4 and path[0:2] == r'\\' and (path[2].isalnum() or path[2] in '_.'):
    pos += 3
  # Look for ///share
  elif size >= 5 and path[0:3] == r'///' and (path[3].isalnum() or path[3] in '_.'):
    pos += 4
  # Validate rest of path
  valid = True
  for i in range(pos, size):
    val = path[i]
    # Character can be alpha numeric or a space, period, underscore, slash or backlash
    if val.isalnum(): continue
    if val in '_. \/\\\(\)':  continue
    # Found invalid character
    valid = False
    break
  # Return the result
  return valid

# Validates a IP address
# ip: IP address to validate
# returns True if IP address is valid, False otherwise
def ValidIP(ip):
  retval = False
  if  ip == '':
    retval = True
  else:
    # Split into parts
    parts = ip.split('.')
    # Must have 4 parts
    if len(parts) == 4:
      # Check each part
      for part in parts:
        try:
          # Must be between - and 255
          val = int(part)
          if val < 0 or val > 255: break
        except ValueError:
          break
      else:
        retval = True
  return retval

# Displays values for all BIOSTool settings 
def DisplayAll():
    # Display current values for all configurable global settings
    print('  Global Configurable Items\n  -------------------------')
    for item in data.gbl.items:
      DisplayItem(item, False)

    # Display current values for all read-only global settings
    print('\n  Global Read-Only Items\n  -------------------------')
    for item in data.gbl.readonly:
      DisplayItem(item, False)

    if data.lcl:
      # Display current values for all configurable local settings
      print('\n  Local Configurable Items\n  -------------------------')
      for item in data.lcl.items:
        DisplayItem(item, True)

      # Display current values for all read-only local settings
      print('\n  Local Read-Only Items\n  -------------------------')
      for item in data.lcl.readonly:
        DisplayItem(item, True)

# Sets a BIOSTool settings
# returns Nothing on success, DOES NOT RETURN otherwise 
def SetItem(item, local, readonly, value):
  # Can't change a readonly setting
  if readonly:
    prompt = data.lcl.prompt[item] if local else data.gbl.prompt[item]
    if prompt:
      prompt = ' (use {0} to change)'.format(prompt.format(data.gbl.progrm))
    ErrorMessage('{0}.{1} is read-only{2} '.format('local' if local else 'global', item, prompt))
    # DOES NOT RETURN

  else:

    # Validate on/off items
    if item in ('alert', 'release', 'warnings'):
      if   value in ['', 'off', 'disabled', 'false', 'no', 'none']:
        value = 'off'
      elif value in ['on', 'enabled', 'true', 'yes']:
        value = 'on'
      else:
        ErrorMessage('Unsupported setting for local.{0}: {1}'.format(item, value))
        # DOES NOT RETURN

    # Validate path items
  #  elif item in ('compare', 'editor', 'hdt', 'lauterbach', 'tagger'):
  #    if not value == '' and not ValidatePath(value):
  #      ErrorMessage('Unsupported setting for local.{0}: {1}'.format(item, value))
  #      # DOES NOT RETURN

    # Validate BMC items
    elif item == 'bmc':
      values = value.split(',')
      # Get the BMC type
      bmc    = values[0].strip().lower()
      if not bmc.lower() in ['ilo', 'openbmc']:
        ErrorMessage('BMC type not supported: {0}'.format(values[0]))
        # DOES NOT RETURN

      # Get IP address
      ip = None
      if len(values) > 1:
        ip     = values[1].strip().upper()
        if not ValidIP(ip):
          ErrorMessage('Unsupported setting for local.ip: {0}'.format(values[1]))
          # DOES NOT RETURN

      # Get usernamne and password (if supplied)
      user   = None if len(values) < 3 else values[2].strip()
      pswd   = None if len(values) < 4 else values[3].strip()
  
      # Put it all back together
      value = bmc
      if ip:
        value += ',' + ip
      if user:
        value += ',' + user
      if pswd:
        value += ',' + pswd

  # Set the item
  hndlr = data.lcl.SetItem if local else data.gbl.SetItem
  hndlr(item, value)
  DisplayItem(item, local)

def GetItemInfo(item):
  try:
    # Start with empty lists
    normalSettings   = []
    readonlySettings = []
    globalSettings   = []
    allSettings      = []
    
    # Add global items
    normalSettings   += data.gbl.items
    readonlySettings += data.gbl.readonly
    globalSettings   += data.gbl.items + data.gbl.readonly
    allSettings      += globalSettings

    # Add local items (if any)
    if data.lcl:
      normalSettings   += data.lcl.items
      readonlySettings += data.lcl.readonly
      allSettings      += data.lcl.items + data.lcl.readonly

    # Create abbreviation dictionary
    abbreviate = UniqueAbbreviation(allSettings)

    # Determine configurable item name,
    item = abbreviate[item]

    # Determine global status
    isLocal = not item in globalSettings

    # Determine readonly status
    isReadonly = item in readonlySettings

    # Return resuls
    return (item, isLocal, isReadonly)

  except KeyError:
    UsageError('Unsupported setting: {0}'.format(item))

# Config command handler
# returns 0 on success, DOES NOT RETURN otherwise
def config():
  # Get command line information
  prms, opts = ParseCommandLine({'default': False}, 2)
  # DOES NOT RETURN if invalid options or parameters are found

  # Determine operation
  argc = len(prms)
  if argc == 0:
    # Handle DisplayAll operation - /default makes no sense here
    if opts['default']:
      UsageError('/default not valid when no setting name is given')
      # DOES NOT RETURN
    DisplayAll()

  else:
    # Get info for setting item of interest
    item, local, readonly = GetItemInfo(prms[0])

    # Get value for configurable item (if given)
    value = '' if (argc < 2) else prms[1]
    if value:

      # Handle SetItem opertion - /default makes no sense here
      if opts['default']:
        UsageError('/default not valid when setting name and value are given')
        # DOES NOT RETURN
      SetItem(item, local, readonly, value)

    else:
      # Handle SetDefault operation
      if opts['default']:
        SetItem(item, local, readonly, '')

      # Handle DisplayItem operation
      else:
        DisplayItem(item, local)

  return 0
