#!/usr/bin/env python

# Standard python modules
# None

# Local modules
# None

# Creates a dictionary of unique abbreviations for a list of strings
# items:  list of strings for which the unique dictionary is to be created
# returns dicionary of allowed abbreviations for this set of items
def UniqueAbbreviation(items):
  # Start with empty unique dictionary
  unique = {}

  # Check for empty list
  if items != None:

    # Loop through each item in the list
    for item in items:
    
      # Loop through characters in item
      for i in range(0, len(item)):

        # Get potential unique abbreviation
        abbrev = item[0:i+1]

        # See if it is in the dictionary
        if abbrev in unique:

          # See if it matches a full item name
          if abbrev in items:
            # It does, set it correctly
            unique[abbrev] = abbrev
          else:
            # Set entry to None so it can be removed later
            unique[abbrev] = None
          

        # If it is not in the dictionary, add it because it is unique so far
        else: unique[abbrev] = item

    # Remove items in dictionary with value of None
    for key in [key for key in unique if unique[key] == None]: del unique[key]

  # Return the dictionary of unique abbreviations
  return unique
