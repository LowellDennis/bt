#!/usr/bin/env python 

# Standard python modules
# None

# Local modules
# None

# Make a message more easy to see on the screen
# message:   message to be displayed
# character: character to surround it
# returns    nothing
def Announce(message, character = '*'):
  length = len(message)

  # Display header line
  print(character * (length + 8))

  # Display message line
  print((character * 3) + ' ' + message + ' ' + (character * 3))
  
  # Display footer line
  print(character * (length + 8))
