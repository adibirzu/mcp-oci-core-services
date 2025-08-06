# OCI Core Services MCP Server - Installation Guide

> **Production-Ready Server**: 15 specialized tools for OCI compute, database, and network management with LLM-optimized responses

## 📋 Prerequisites

### 1. Python Environment
- Python 3.8+ installed
- pip or pip3 available

### 2. OCI CLI Setup
```bash
# Install OCI CLI
curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh | bash

# Configure OCI CLI (creates ~/.oci/config)
oci setup config
```

### 3. OCI Permissions
Ensure your OCI user has the following IAM permissions for full functionality:

**Compute Operations:**
```
ALLOW group <your-group> TO MANAGE instances IN compartment <your-compartment>
ALLOW group <your-group> TO READ instance-configurations IN compartment <your-compartment>
ALLOW group <your-group> TO READ instance-pools IN compartment <your-compartment>
```

**Database Operations:**
```
ALLOW group <your-group> TO MANAGE database-systems IN compartment <your-compartment>
ALLOW group <your-group> TO MANAGE autonomous-databases IN compartment <your-compartment>
```

**Network Operations:**
```
ALLOW group <your-group> TO READ vnics IN compartment <your-compartment>
ALLOW group <your-group> TO READ vnic-attachments IN compartment <your-compartment>
ALLOW group <your-group> TO READ subnets IN compartment <your-compartment>
ALLOW group <your-group> TO READ network-security-groups IN compartment <your-compartment>
```

**Work Request Tracking:**
```
ALLOW group <your-group> TO READ work-requests IN compartment <your-compartment>
```

## 🚀 Quick Setup

### Option 1: Automated Setup
```bash
git clone <repository-url>
cd mcp-oci-core-services
./setup.sh
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip3 install -r requirements.txt

# Test the installation
export OCI_COMPARTMENT_ID="your-compartment-ocid"
python3 test_core_services.py
```

## 🔧 Claude Desktop Integration

### 1. Add to Configuration
Add this to your `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "oci-core-services": {
      "command": "/path/to/python3",
      "args": [
        "/path/to/mcp-oci-core-services/oci_core_services_server.py"
      ],
      "env": {
        "OCI_COMPARTMENT_ID": "ocid1.compartment.oc1..your-compartment-id",
        "SUPPRESS_LABEL_WARNING": "True"
      }
    }
  }
}
```

### 2. Find Your Python Path
```bash
which python3
# Example output: /Users/username/.pyenv/versions/3.11.9/bin/python
```

### 3. Get Your Compartment ID
```bash
# List compartments
oci iam compartment list

# Or use your tenancy OCID as compartment ID
oci iam compartment list --compartment-id-in-subtree=true
```

## 🧪 Testing

### Test Server Functionality
```bash
python3 test_core_services.py
```

### Test Claude Integration
1. Restart Claude Desktop
2. In Claude, ask: "List my running compute instances"
3. You should see a response with your OCI instances

## 📊 Available Tools

Once configured, Claude will have access to 15 comprehensive OCI management tools:

**Instance Information & Discovery:**
- **`list_compute_instances`** - List instances with filtering by state and compartment
- **`get_instance_details`** - Get comprehensive instance information with network details
- **`list_instances_with_network`** - List instances with complete network information
- **`get_compute_instance_state`** - Get current lifecycle state of specific instance

**Instance Lifecycle Management:**
- **`start_compute_instance`** - Start stopped instances with work request tracking
- **`stop_compute_instance`** - Stop running instances (graceful/forced)
- **`restart_compute_instance`** - Restart instances (graceful/forced)

**Database Management:**
- **`list_database_systems`** - List traditional database systems
- **`start_database_system`** / **`stop_database_system`** - Database lifecycle control

**Autonomous Database Operations:**
- **`list_autonomous_databases`** - List autonomous databases with workload filtering
- **`get_autonomous_database_details`** - Get comprehensive autonomous database information
- **`start_autonomous_database`** / **`stop_autonomous_database`** / **`restart_autonomous_database`** - Full lifecycle control
- **`scale_autonomous_database`** - Dynamic compute (ECPU/OCPU) and storage scaling
- **`get_autonomous_database_state`** - Get current autonomous database state

**System Diagnostics:**
- **`test_core_services_connection`** - Test OCI connectivity and validate configuration

> **Key Features:** LLM-optimized JSON responses, OCI Python SDK primary with CLI fallback, work request tracking, complete type safety

## 🔍 Troubleshooting

### Common Issues

#### 1. "OCI SDK not installed"
```bash
pip3 install oci>=2.157.0
```

#### 2. "FastMCP not installed"
```bash
pip3 install fastmcp>=0.9.0
```

#### 3. "OCI configuration not found"
```bash
# Check if config exists
ls -la ~/.oci/config

# If missing, run setup
oci setup config
```

#### 4. "Permission denied" errors
```bash
# Make scripts executable
chmod +x run_core_services_server.sh
chmod +x setup.sh
```

#### 5. "Compartment ID is required"
```bash
# Set environment variable
export OCI_COMPARTMENT_ID="your-compartment-ocid"

# Or update Claude Desktop config with correct compartment ID
```

### Debug Mode
```bash
# Run with debug logging
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import oci_core_services_server
"
```

### Verify OCI Access
```bash
# Test OCI CLI access
oci compute instance list --compartment-id "your-compartment-id"

# Test with specific region
oci compute instance list --compartment-id "your-compartment-id" --region eu-frankfurt-1
```

## 📈 Usage Examples

### In Claude Desktop
Once configured, you can ask Claude:

- "List my running compute instances in Frankfurt"
- "Show me the network details for my instances"
- "What instances do I have in compartment X?"
- "Get detailed information about instance Y"

### Expected Response Format
```json
{
  "success": true,
  "summary": "Found 13 running compute instances in eu-frankfurt-1",
  "count": 13,
  "instances": [
    {
      "name": "ArkimeGOAD",
      "shape": "VM.Standard.E5.Flex",
      "state": "RUNNING",
      "primary_private_ip": "192.168.56.132"
    }
  ]
}
```

## 🛠️ Advanced Configuration

### Custom Compartment
```json
{
  "env": {
    "OCI_COMPARTMENT_ID": "ocid1.compartment.oc1..your-specific-compartment",
    "OCI_REGION": "eu-frankfurt-1"
  }
}
```

### Multiple Regions
Create separate server instances for different regions:
```json
{
  "mcpServers": {
    "oci-core-services-frankfurt": {
      "command": "/path/to/python3",
      "args": ["/path/to/oci_core_services_server.py"],
      "env": {
        "OCI_COMPARTMENT_ID": "your-compartment-id",
        "OCI_REGION": "eu-frankfurt-1"
      }
    },
    "oci-core-services-ashburn": {
      "command": "/path/to/python3", 
      "args": ["/path/to/oci_core_services_server.py"],
      "env": {
        "OCI_COMPARTMENT_ID": "your-compartment-id",
        "OCI_REGION": "us-ashburn-1"
      }
    }
  }
}
```

## 🔐 Security Notes

- **Credentials**: Uses OCI config file (~/.oci/config) - no hardcoded credentials
- **Permissions**: Requires only READ permissions for compute and network resources
- **Isolation**: Dedicated server process per Claude Desktop session
- **Logging**: Minimal logging with no sensitive data exposure

## 📚 Additional Resources

- [OCI CLI Documentation](https://docs.oracle.com/iaas/tools/oci-cli/latest/)
- [OCI Python SDK Documentation](https://docs.oracle.com/iaas/tools/python-sdk-examples/latest/)
- [FastMCP Documentation](https://fastmcp.com)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/model-context-protocol)