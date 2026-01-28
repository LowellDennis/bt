#!/usr/bin/python2.7

# Standard python modules
import io
import os
import sys
import threading
import queue
from   subprocess import PIPE, Popen, run, STDOUT
from   contextlib import contextmanager

# Wake-lock support (keeps system awake during long operations)
try:
    from wakepy import keep
except ImportError:
    # wakepy not installed - install it automatically
    if sys.platform == 'win32':
        import ctypes
        import subprocess
        
        # Run pip install with visible console
        process = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'install', 'wakepy'],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        process.wait()
        
        if process.returncode == 0:
            ctypes.windll.user32.MessageBoxW(0, 
                "wakepy installed successfully!\n\nPlease restart the command.", 
                "Installation Complete", 
                0x40)
            sys.exit(0)  # Exit so user restarts with wakepy loaded
        else:
            ctypes.windll.user32.MessageBoxW(0, 
                f"Failed to install wakepy.\n\nPlease install manually:\npython -m pip install wakepy", 
                "Installation Failed", 
                0x10)  # MB_ICONERROR
            sys.exit(1)
    else:
        print("Error: wakepy is required but not installed. Install with: pip install wakepy")
        sys.exit(1)

# Local modules
from announce   import Announce

# Default output filter for the commands below
def NoFilter(line):
  if line is None:
    return
  out = line.decode('utf-8') if isinstance(line, bytes) else str(line)
  sys.stdout.write(out)

# Set the directory for command execution
# directory - Directory from which to execute
# returns original directory or None is no change was needed
def SetDirectory(directory):
  retval = None
  if directory:
    retval = os.getcwd()
    os.chdir(directory)
  return retval

# Execute a command, capturing output
# command    - Command to execute
# directory  - Directory from which to run command
# returns a tuple containing the return code of the execuable and its output
def RunCommand(command, directory = None):
  # Move to indicated directory
  saved = SetDirectory(directory)
  # Execute command in another process
  with keep.running():
    process = Popen(command.split(' '), stdout=PIPE, stderr=STDOUT)
    output = process.communicate()[0]
  # Restore original directory
  SetDirectory(saved)
  return (process.returncode, output)

# Run a set of command, capturing output
# executable - Executable to recieve the commands
# commands   - List of commands
# directory  - Directory from which to run commands
# returns a tuple containing the return code of the execuable and its output
def RunCommands(executable, commands, directory = None, log=None):
  # Move to indicated directory
  saved = SetDirectory(directory)
  # Execute commands in another process
  with keep.running():
    process = Popen(executable, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    if (isinstance(commands, list)):
      for cmd in commands:
        process.stdin.write(cmd);
    else:
      process.stdin.write(commands);
    output = process.communicate()[0]
  # Restore original directory
  SetDirectory(saved)
  return (process.returncode, output)

# Execute a command filtering output line-by-line
# command    - Command to execute
# filter     - Routine for processing output one line at a time
# directory  - Directory from which to run command
# log        - File in which to log the output
# returns the return code of the command that was execuated
def FilterCommand(command, filter = NoFilter, directory = None, log=None):
  # Helper function to read lines from process into a queue
  def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
      queue.put(line)
    out.close()
  
  # Move to indicated directory
  saved = SetDirectory(directory)
  # Open log file
  if log: logFile = open(log, 'w')
  # Execute command in another process
  with keep.running():
    process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
    # Create a queue and thread to read output
    q = queue.Queue()
    t = threading.Thread(target=enqueue_output, args=(process.stdout, q))
    t.daemon = True
    t.start()
    
    # Handle command output with timeout for periodic updates
    while True:
      # Try to get a line with a timeout
      try:
        line = q.get(timeout=1.0)  # 1 second timeout
        filter(line)
        if log: logFile.write(line.decode('utf-8') if type(line) is bytes else line)
      except queue.Empty:
        # No output available, check if process is still running
        if process.poll() is not None:
          break
        # Force a status update even with no new output
        # Pass None to signal a timeout update
        filter(None)
    
    returncode = process.poll()
  # Close log file
  if log: logFile.close()
  # Restore original directory
  SetDirectory(saved)
  return returncode

# Execute a command capturing output in real time
# command    - Command to execute
# filter     - Routine for processing output one chunk at a time
# directory  - Directory from which to run command
# log        - File in which to log the output
# returns the return code of the command that was execuated
def FilterCommandAsync(command, filter = NoFilter, directory = None, log=None):
  # Move to indicated directory
  saved = SetDirectory(directory)
  # Open log file
  if log: logFile = open(log, 'w')
  # Execute command in another process
  process = Popen(command.split(), stdout=PIPE, stderr=STDOUT)
  # Open command output
  sout = io.open(process.stdout.fileno(), 'rb', closefd=False)
  # Handle command output
  while True:
    buffer = sout.read1(1024)
    if process.poll() != None: break
    if len(buffer) == 0: continue
    filter(buffer)
    if log: logFile.write(buffer)
  # Close log file
  if log: logFile.close()
  # Restore original directory
  SetDirectory(saved)
  return process.returncode

# Execute a command capturing output in real time
# operation  - String indicating operation being performed
# completion - Completion message
# command    - Command to execute
# directory  - Directory from which to run command
# returns thee return code of the command that was execuated
def DoCommand(operation, completion, command, directory = None):
  try:
    equalLine  = '=' * (58 + len(operation))
    print(equalLine)
    print('=== {0} ... Please be patient this could take a while ... ==='.format(operation))
    print(equalLine)
    print('Command: {0}'.format(command))
    with keep.running():
      result = run(command, cwd=directory).returncode
    print('')
    msg   = completion + ' ' + ('FAILED!' if (result) else 'Passed!')
    Announce(msg, '!' if (result) else '*')
    return result
  except KeyboardInterrupt:
    return 1
