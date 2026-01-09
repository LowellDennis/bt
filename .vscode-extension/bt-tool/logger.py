#!/usr/bin/env python 

# Standard python modules
import sys
import re

# Local modules
# None

DEBUG = 0

class Logger:

  # Constructor
  # log:    Logfile name
  # task:   Current task
  # warn:   True to enable warnings, False otherwise
  # returns nothing
  def __init__(self, log = '', task = 'Running', warn = False):
    # Save givens
    self.task     = task
    self.warn     = warn
    # Initialize counters
    self.lines    = 0
    self.errors   = 0
    self.warnings = 0
    # Initialize regular expression search patterns
    self.reQuick  = re.compile(r'(^|\b)(error|fail|warn)' if warn else r'(^|\b)(error|fail)',re.IGNORECASE)
    self.reError  = re.compile(r'\b(errors)|(error)|(failures)|(failure)|(failed)|(fail)\b', re.IGNORECASE)
    self.reWarn   = re.compile(r'\b(warnings)|(warning)|(warned)|(warn)\b', re.IGNORECASE)
    # Initialize inline show code (needed because of python V2/V3 differences)
    if (sys.version_info > (3, 0)):
      self.show   = "print(msg, end = '')"
    else:
      self.show   = "print(msg),"
    # Open log file
    self.log      = open(log, 'w') if log else None

  # Indicates if a line is a real error or warning
  # which:  'error' for error, 'warn' otherwise
  # line :  Line to check
  # result: Variable in which to return information (if needed)
  # returns True if real error or warning, False otherwise
  def IsReal(self, which, line, result):
    return True

  # Prints output
  # prefix: Prefix to include in optput
  # line:   Line of output
  # result: Variable in which to return information (if needed)
  # returns nothing
  def Print(self, prefix, line):
    # Remove trailing whitespace from line
    output = line.rstrip()
    # Add spaces enough to cover the last progress line
    length = len(output) + len(prefix) + 2
    if (length < self.length): output += ' ' * (self.length - length)
    # Show the line
    print('\r{0}: {1}'.format(prefix, output))

  # Processes a captured line of output
  # line:   Line of output
  # returns nothing
  def Process(self, line):
    self.lines += 1
    line = line.decode('utf-8')
    if self.log: self.log.write(line.rstrip() + '\n')
    # Do quick and dirty search for failures, errors, and warnings
    quick = self.reQuick.search(line)
    if (quick):
      if (DEBUG): print('\nquick search: {0}'.format(line.rstrip()))
      # Line has not been handled
      handled = False
      # Perform more selective search for errors
      error = self.reError.search(line)
      if (error):
        if (DEBUG): print('error search: {0}'.format(line.rstrip()))
        # Allow for errors to be filtered
        if (self.IsReal('error', line, error)):
          handled     = True
          self.errors += 1
          self.Print('***  ERROR  ***', line)
        elif (DEBUG): print('error filtered!')
      elif (DEBUG): print('error search: no match!')
      if (not handled and self.warn):
        # Perform more selective search for warnings
        warn = self.reWarn.search(line)
        if (warn):
          if (DEBUG): print('warning search: {0}'.format(line.rstrip()))
          # Allow for warnings to be filtered
          if (self.IsReal('warn', line, warn)):
            self.warnings += 1
            self.Print('*** WARNING ***', line)
          elif (DEBUG): print('warning filtered!')
        elif (DEBUG): print('warning search: no match!')
    msg = '\r{0}: Lines {1}, Errors {2}{3}'.format(self.task, self.lines, self.errors, ', Warnings {0}'.format(self.warnings) if self.warn else '')
    self.length = len(msg)
    exec(self.show)
