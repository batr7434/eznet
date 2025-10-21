#!/bin/bash
# EZNet Launcher Script

# Change to the eznet directory
cd "$(dirname "$0")"

# Use the virtual environment's Python to run eznet
.venv/bin/python -m eznet.cli "$@"