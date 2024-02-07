import re
import os

rePath = re.compile('^((((\\\\)|(\/\/\/))[a-z0-9_\-\.\s]+)|([a-fA-F]:))?([a-z0-9_\-\.\s\\\/]*)', re.IGNORECASE)

#         Good? Path string
paths = [(True,  'C:\\this is\\a test\\test.1'),          # Fully quaified path
         (False, 'C:\\+this is\\a test\\test.1'),         # Erroneous fully quaified path
         (True,  'C:this is\\a test\\test.1'),            # Path relative to drive
         (False, 'C:this is\\a t|est\\test.1'),           # Erroneous path relative to drive
         (True,  '\\\\drive\\this is\\a test\\test.1'),   # Unmapped network path
         (False, '\\\\drive\\this is\\a test\\te|st.1'),  # Erroneous unmapped network path
         (True,  '\\\\drive'),                            # Just network share
         (False, '\\\\dr|ive'),                           # Just network share
         (True,  '\\\\drive\\'),                          # Network share top
         (False, '\\\\dr|ive\\'),                         # Erroneous etwork share top
         (True,  'file.txt'),                             # Just filename and extension
         (False, 'fi|le.txt'),                            # Erroneous just filename and extension
         (True,  'file'),                                 # Just filename
         (False, 'fi|le'),                                # Erroneous just filename
         (True,  '.ext'),                                 # Just extension
         (False, '.ext|'),                                # Erroneous just extension
        ]

# Validates a file path
# path:   Path to validate
# returns Path if it is to be used, '' otherwise
# Note: This function allows the user to enter paths that may be currently
#       unavailable (as in network paths when network is not available).
def CheckPath(path):
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
    if val in '_. \/\\':  continue
    # Found invalid character
    valid = False
    break
  # Return the result
  return valid

for valid, path in paths:
  result = CheckPath(path)
  print('{0} - {1:5} => {2}'.format('PASSED' if result == valid else 'FAILED', str(result), path))
pass
