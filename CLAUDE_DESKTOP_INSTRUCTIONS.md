# Claude Desktop Setup - OCI Core Services MCP Server

> **Production-Ready**: 15 specialized tools for comprehensive OCI compute, database, and network management

## Quick Setup

1. **Locate your Claude Desktop configuration file**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add the server configuration**:
   ```json
   {
     "mcpServers": {
       "oci-core-services": {
         "command": "/Users/abirzu/.pyenv/versions/3.11.9/bin/python",
         "args": [
           "/Users/abirzu/dev/mcp-oci-core-services/oci_core_services_server.py"
         ],
         "env": {
           "OCI_COMPARTMENT_ID": "your_compartment_ocid_here",
           "SUPPRESS_LABEL_WARNING": "True"
         }
       }
     }
   }
   ```

3. **Update the configuration**:
   - Replace `your_compartment_ocid_here` with your OCI compartment OCID
   - Update the Python path if your Python installation is different
   - Update the script path to match your installation directory

4. **Restart Claude Desktop**

## Available Tools

The server provides 15 comprehensive tools for OCI infrastructure management:

### Instance Management
- `list_compute_instances` - List running instances
- `get_instance_details` - Get detailed instance information
- `list_instances_with_network` - List instances with network details
- `get_compute_instance_state` - Get current instance state

### Instance Lifecycle
- `start_compute_instance` - Start a stopped instance
- `stop_compute_instance` - Stop a running instance (graceful/forced)
- `restart_compute_instance` - Restart an instance (graceful/forced)

### Database Management
- `list_database_systems` - List traditional database systems
- `start_database_system` - Start a stopped database system
- `stop_database_system` - Stop a running database system

### Autonomous Database Management
- `list_autonomous_databases` - List autonomous databases with workload filtering
- `get_autonomous_database_details` - Get detailed autonomous database information
- `start_autonomous_database` - Start a stopped autonomous database
- `stop_autonomous_database` - Stop a running autonomous database
- `restart_autonomous_database` - Restart an autonomous database
- `scale_autonomous_database` - Scale compute (ECPU/OCPU) and storage
- `get_autonomous_database_state` - Get autonomous database state

### Diagnostics
- `test_core_services_connection` - Test OCI connectivity and validate configuration

## Example Queries

Once configured, you can ask Claude:

- "List my running compute instances"
- "What are the IP addresses of my instances?"
- "Start the instance named 'test-server'"
- "Show me details about my database systems"
- "Test my OCI connection"

## Requirements

- OCI CLI installed and configured
- OCI Python SDK installed (`pip install oci`)
- FastMCP installed (`pip install fastmcp`)
- Valid OCI configuration file at `~/.oci/config`

## Troubleshooting

If you encounter issues:

1. **Check Python path**: Ensure the Python path in the config points to a Python installation with the required packages
2. **Verify OCI config**: Run `oci iam compartment list` to test your OCI configuration
3. **Check compartment ID**: Ensure your compartment OCID is correct
4. **View logs**: Check Claude Desktop logs for error messages