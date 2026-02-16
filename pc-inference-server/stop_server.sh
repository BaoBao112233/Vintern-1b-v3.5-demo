#!/bin/bash

###############################################################################
#  Stop PC Inference Server
###############################################################################

echo "Stopping llama-server..."

# Find and kill llama-server processes
pkill -f "llama-server" && echo "Server stopped successfully" || echo "No server process found"

# Show remaining processes
ps aux | grep llama-server | grep -v grep || echo "All server processes stopped"
