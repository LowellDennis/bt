#!/bin/bash

# Generate unique session ID based on timestamp and random number
BTID="$(date +%H%M%S%N | cut -c1-10)$RANDOM"
POSTCMD="${TMPDIR:-/tmp}/postbt_${BTID}.sh"

# Delete post executable command file (if it exists)
if [ -f "$POSTCMD" ]; then
    rm -f "$POSTCMD"
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}" .sh)"

# Execute the BIOS tool with session ID
python3 "${SCRIPT_DIR}/${SCRIPT_NAME}.py" --btid="$BTID" "$@"

# See if there is a post executable command file
if [ -f "$POSTCMD" ]; then
    # Execute post command file
    source "$POSTCMD"
    # Clean up post command file
    rm -f "$POSTCMD" 2>/dev/null
fi
