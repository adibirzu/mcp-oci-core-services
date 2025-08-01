#!/bin/bash
#
# Setup script for OCI Core Services MCP Server
#

echo "🚀 Setting up OCI Core Services MCP Server..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if OCI CLI is available
if ! command -v oci &> /dev/null; then
    echo "⚠️  OCI CLI not found. Please install and configure OCI CLI first:"
    echo "   curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh | bash"
    echo "   oci setup config"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    python3 -m pip install -r requirements.txt
fi

# Make scripts executable
chmod +x run_core_services_server.sh

# Test the installation
echo "🧪 Testing installation..."
export OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaagy3yddkkampnhj3cqm5ar7w2p7tuq5twbojyycvol6wugfav3ckq
python3 test_core_services.py

if [ $? -eq 0 ]; then
    echo "✅ Setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Add this server to your Claude Desktop configuration:"
    echo "   \"oci-core-services\": {"
    echo "     \"command\": \"$(which python3)\","
    echo "     \"args\": [\"$(pwd)/oci_core_services_server.py\"],"
    echo "     \"env\": {"
    echo "       \"OCI_COMPARTMENT_ID\": \"your-compartment-id\","
    echo "       \"SUPPRESS_LABEL_WARNING\": \"True\""
    echo "     }"
    echo "   }"
    echo ""
    echo "2. Restart Claude Desktop"
    echo "3. Test with: \"List my running compute instances in Frankfurt\""
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi