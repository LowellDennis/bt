#!/usr/bin/env python

# Standard python modules
import os
import time

class ProgressTracker:
  """Tracks build progress and displays progress bar"""
  
  # Constructor
  # dir:   Directory for cache files
  # name:  Platform name
  # btype: Build type (DEBUG or RELEASE)
  # width: Width of progress bar in characters
  # returns nothing
  def __init__(self, dir=None, name=None, btype=None, width=30):
    self.name = name
    self.btype = btype
    self.modulesBuilt = 0  # Just a counter for display, not used for progress
    self.linesProcessed = 0
    self.totalLines = 35000   # Default estimate
    self.progressWidth = width
    self.progressStr = ''
    self.startTime = time.time()
    self.lastUpdateTime = self.startTime
    
    # Detect Unicode support for partial block characters
    self.usePartialBlocks = self._detectUnicodeSupport()
    
    # Load or estimate line count for progress tracking
    if dir and name:
      loaded = self.LoadLineCount(dir, name)
      if loaded > 0:
        self.totalLines = loaded
  
  # Increment module count (for display only)
  # returns nothing
  def IncrementModule(self):
    self.modulesBuilt += 1
  
  # Detect if terminal supports Unicode partial blocks
  # returns True if supported, False otherwise
  def _detectUnicodeSupport(self):
    try:
      import sys
      # Check if stdout encoding supports UTF-8
      encoding = sys.stdout.encoding or ''
      # Accept utf-8, utf-16, or cp65001 (Windows UTF-8), or try encoding anyway
      if 'utf' in encoding.lower() or 'cp65001' in encoding.lower():
        return True
      # For other encodings (like cp1252), try to encode the partial blocks
      # VS Code and modern terminals often support them even if encoding suggests otherwise
      try:
        test_chars = '▏▎▍▌▋▊▉█'
        test_chars.encode(encoding)
        return True
      except (UnicodeEncodeError, LookupError):
        return False
    except (AttributeError, Exception):
      # When in doubt, try using partial blocks (works in most modern terminals)
      return True
  
  # Update progress bar string
  # returns nothing
  def UpdateProgress(self):
    if self.totalLines == 0:
      self.progressStr = ''
      return
    
    # Calculate percentage based on line count (covers entire build)
    percentage = int((self.linesProcessed / self.totalLines) * 100)
    percentage = min(100, percentage)
    
    if self.usePartialBlocks:
      # Use 8 partial block characters for finer granularity
      blocks = ['░', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']
      progress = (self.linesProcessed / self.totalLines) * self.progressWidth
      full_blocks = int(progress)
      partial = progress - full_blocks
      partial_index = int(partial * 8)
      
      bar = '█' * full_blocks
      if full_blocks < self.progressWidth and partial_index > 0:
        bar += blocks[partial_index]
        bar += '░' * (self.progressWidth - full_blocks - 1)
      else:
        bar += '░' * (self.progressWidth - full_blocks)
    else:
      # Fallback to simple full blocks only
      filled = int((self.linesProcessed / self.totalLines) * self.progressWidth)
      filled = min(filled, self.progressWidth)
      empty = max(0, self.progressWidth - filled)
      bar = '█' * filled + '░' * empty
    
    # Store progress string in format: bar##% (no brackets)
    self.progressStr = f'{bar}{percentage}%'
  
  # Get progress string (or default if not started)
  # returns progress string
  def GetProgressString(self):
    if self.progressStr:
      return self.progressStr
    # Default empty progress bar showing 0% (no brackets)
    return ('\u2591' * self.progressWidth) + '0%'
  
  # Format elapsed time as MM:SS (total minutes)
  # returns formatted time string
  def GetElapsedTime(self):
    elapsed = int(time.time() - self.startTime)
    minutes = elapsed // 60
    seconds = elapsed % 60
    return f'{minutes:02d}:{seconds:02d}'
  
  # Check if enough time has passed to force an update
  # returns True if update should be forced
  def ShouldForceUpdate(self):
    current_time = time.time()
    if current_time - self.lastUpdateTime >= 1.0:
      self.lastUpdateTime = current_time
      return True
    return False
  
  # Loads line count from cache
  # dir:  Directory for cache files
  # name: Platform name
  # returns line count or 0 if not found
  def LoadLineCount(self, dir, name):
    try:
      cache_dir = os.path.join(os.path.expanduser('~'), '.bt')
      cache_file = os.path.join(cache_dir, name)
      
      if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
          count = int(f.read().strip())
          return count
    except Exception:
      pass
    return 0
  
  # Saves actual line count to cache (only on successful builds)
  # dir:   Directory for cache files
  # name:  Platform name
  # count: Actual line count
  # returns nothing
  def SaveLineCount(self, dir, name, count):
    try:
      if not name:
        return
      cache_dir = os.path.join(os.path.expanduser('~'), '.bt')
      cache_file = os.path.join(cache_dir, name)
      
      # Create cache directory if it doesn't exist
      os.makedirs(cache_dir, exist_ok=True)
      
      # Write the actual count
      with open(cache_file, 'w') as f:
        f.write(str(count))
    except Exception as e:
      # Log error for debugging
      import sys
      print(f'\nWarning: Failed to save line count cache: {e}', file=sys.stderr)
  
  # Estimates line count for first build
  # dir: Base directory of BIOS tree
  # returns estimated line count
  def EstimateLineCount(self, dir):
    # Use a reasonable default estimate for UEFI builds
    # The actual count will be cached after the first build
    DEFAULT_ESTIMATE = 50000
    return DEFAULT_ESTIMATE
  
  # Loads line count from cache
  # dir:  Directory for cache files
  # name: Platform name
  # returns line count or 0 if not found
  def LoadLineCount(self, dir, name):
    try:
      cache_dir = os.path.join(os.path.expanduser('~'), '.bt')
      cache_file = os.path.join(cache_dir, name + '_lines')
      
      if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
          count = int(f.read().strip())
          return count
    except Exception:
      pass
    return 0
  
  # Saves actual line count to cache
  # dir:   Directory for cache files
  # name:  Platform name
  # count: Actual line count
  # returns nothing
  def SaveLineCount(self, dir, name, count):
    try:
      if not name:
        return
      cache_dir = os.path.join(os.path.expanduser('~'), '.bt')
      cache_file = os.path.join(cache_dir, name + '_lines')
      
      # Create cache directory if it doesn't exist
      os.makedirs(cache_dir, exist_ok=True)
      
      # Write the actual count
      with open(cache_file, 'w') as f:
        f.write(str(count))
      
      # Print confirmation for debugging
      print(f'\nSaved line count: {count} to {cache_file}')
    except Exception as e:
      # Log error for debugging
      import sys
      print(f'\nWarning: Failed to save line count cache: {e}', file=sys.stderr)
  
  # Estimates line count for first build
  # dir: Base directory of BIOS tree
  # returns estimated line count
  def EstimateLineCount(self, dir):
    # Use a reasonable default estimate for UEFI builds
    # The actual count will be cached after the first build
    DEFAULT_ESTIMATE = 50000
    return DEFAULT_ESTIMATE
