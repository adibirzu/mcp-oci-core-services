#!/bin/bash
#
# Run the OCI Core Services FastMCP Server
# This script starts the dedicated Core Services server for compute instance management
#

# Set environment variables
export OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaagy3yddkkampnhj3cqm5ar7w2p7tuq5twbojyycvol6wugfav3ckq
export SUPPRESS_LABEL_WARNING=True

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use the correct Python path with OCI and FastMCP installed
~/.pyenv/versions/3.11.9/bin/python "$SCRIPT_DIR/oci_core_services_server.py" "$@"