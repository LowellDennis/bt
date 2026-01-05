#!/usr/bin/env python

# Standard python modules
import os
import sys

# Add parent directory to path for dsc_parser import
import_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, import_dir)
from dsc_parser import estimate_module_count, MINIMUM_ESTIMATE

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
    self.modulesBuilt = 0
    self.totalModules = 0
    self.progressWidth = width
    self.progressStr = ''
    
    # Load or estimate module count for progress tracking
    if dir and name:
      self.totalModules = self.LoadModuleCount(dir, name)
      if self.totalModules == 0:
        self.totalModules = self.EstimateModuleCount(dir)
  
  # Increment module count and update progress
  # returns nothing
  def IncrementModule(self):
    self.modulesBuilt += 1
    # If actual count exceeds estimate, increase estimate to prevent overflow display
    if self.modulesBuilt > self.totalModules:
      self.totalModules = self.modulesBuilt + int(self.modulesBuilt * 0.1)  # Add 10% buffer
    self.UpdateProgress()
  
  # Update progress bar string
  # returns nothing
  def UpdateProgress(self):
    if self.totalModules == 0:
      self.progressStr = ''
      return
    
    # Calculate percentage (0% at start, maximum 100%)
    percentage = int((self.modulesBuilt / self.totalModules) * 100)
    percentage = min(100, percentage)
    
    # Calculate filled portion of progress bar (cap at max width)
    filled = int((self.modulesBuilt / self.totalModules) * self.progressWidth)
    filled = min(filled, self.progressWidth)
    empty = max(0, self.progressWidth - filled)
    bar = '█' * filled + '░' * empty
    
    # Store progress string in format: [bar]##%
    self.progressStr = f'[{bar}]{percentage}%'
  
  # Get progress string (or default if not started)
  # returns progress string
  def GetProgressString(self):
    if self.progressStr:
      return self.progressStr
    # Default empty progress bar showing 0%
    return '[' + ('░' * self.progressWidth) + ']0%'
  
  # Loads module count from cache
  # dir:  Directory for cache files
  # name: Platform name
  # returns module count or 0 if not found
  def LoadModuleCount(self, dir, name):
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
  
  # Saves actual module count to cache
  # dir:   Directory for cache files
  # name:  Platform name
  # count: Actual module count
  # returns nothing
  def SaveModuleCount(self, dir, name, count):
    try:
      cache_dir = os.path.join(os.path.expanduser('~'), '.bt')
      cache_file = os.path.join(cache_dir, name)
      
      # Create cache directory if it doesn't exist
      os.makedirs(cache_dir, exist_ok=True)
      
      # Write the actual count
      with open(cache_file, 'w') as f:
        f.write(str(count))
    except Exception:
      pass
  
  # Estimates module count by parsing DSC files
  # dir: Base directory of BIOS tree
  # returns estimated module count
  def EstimateModuleCount(self, dir):
    try:
      # Look for platform package directory containing PlatformPkg.dsc
      # Search pattern: find directory with platform name that contains PlatformPkg.dsc
      platform_dir = None
      if self.name:
        for root, dirs, files in os.walk(dir):
          # Check if current directory name contains platform name and has PlatformPkg.dsc
          if self.name.lower() in os.path.basename(root).lower() and 'PlatformPkg.dsc' in files:
            platform_dir = root
            break
      
      if platform_dir:
        estimated, unique, total = estimate_module_count(dir, platform_dir)
        # Estimate already includes 2x buffer
        return estimated
    except Exception:
      pass
    
    # Default fallback estimate
    return MINIMUM_ESTIMATE
