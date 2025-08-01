# OCI Core Services FastMCP Server

A dedicated FastMCP server for Oracle Cloud Infrastructure (OCI) Core Services, specifically designed for compute instance management and network operations.

## 🚀 Features

### ✅ **Dedicated Core Services Focus**
- **Compute Instance Management**: List, query, and manage compute instances
- **Instance Lifecycle Control**: Start, stop, and restart compute instances with graceful/forced options
- **Network Information**: Complete VNIC details including IP addresses, hostnames, and MAC addresses
- **Instance Details**: Comprehensive instance configuration and metadata
- **LLM-Friendly Output**: Structured JSON responses optimized for AI/LLM consumption

### ✅ **Official OCI Python SDK Integration**
- **Primary SDK Access**: Direct API calls using `oci>=2.157.0` Python SDK
- **CLI Fallback**: Automatic fallback to OCI CLI for maximum compatibility
- **Authenticated Access**: Uses standard OCI configuration files
- **Regional Support**: Multi-region support with automatic region detection

### ✅ **FastMCP Framework**
- **Modern Architecture**: Built on FastMCP 2.10.6 for optimal performance
- **Type Safety**: Complete Python typing for reliable operations
- **Async Operations**: Non-blocking async/await patterns
- **Error Handling**: Comprehensive error handling with graceful fallbacks

## 📋 Available Tools

### 📊 Instance Information Tools

#### 1. `list_compute_instances`
Lists all compute instances in the compartment with basic details.

**Parameters:**
- `compartment_id` (optional): OCI compartment ID
- `lifecycle_state` (optional): Filter by state (RUNNING, STOPPED, etc.)

**Returns:**
```json
{
  "success": true,
  "summary": "Found 13 running compute instances in eu-frankfurt-1",
  "count": 13,
  "method": "OCI Python SDK",
  "instances": [
    {
      "id": "ocid1.instance.oc1...",
      "name": "ArkimeGOAD",
      "shape": "VM.Standard.E5.Flex",
      "state": "RUNNING",
      "availability_domain": "NoEK:EU-FRANKFURT-1-AD-1",
      "region": "eu-frankfurt-1",
      "created_time": "2025-02-25T17:22:25.782000+00:00"
    }
  ],
  "retrieved_at": "2025-07-30T09:42:30Z"
}
```

#### 2. `get_instance_details`
Get comprehensive details about a specific compute instance.

**Parameters:**
- `instance_id` (required): OCI instance OCID
- `compartment_id` (optional): OCI compartment ID
- `include_network` (optional): Include network interface details

**Returns:**
```json
{
  "success": true,
  "summary": "Instance 'ArkimeGOAD' (VM.Standard.E5.Flex) is running with private IP 192.168.56.132",
  "method": "OCI Python SDK",
  "instance": {
    "id": "ocid1.instance.oc1...",
    "name": "ArkimeGOAD",
    "configuration": {
      "launch_options": {},
      "agent_config": {}
    }
  },
  "network_interfaces": [],
  "network_info_included": true
}
```

#### 3. `list_instances_with_network`
List compute instances with complete network information.

**Parameters:**
- `compartment_id` (optional): OCI compartment ID
- `lifecycle_state` (optional): Filter by state

**Returns:**
```json
{
  "success": true,
  "summary": "Found 13 running compute instances with network information",
  "count": 13,
  "network_info_included": true,
  "instances": [
    {
      "name": "ArkimeGOAD",
      "primary_private_ip": "192.168.56.132",
      "primary_public_ip": null,
      "hostname": "arkimegoad",
      "network_interfaces": [
        {
          "is_primary": true,
          "private_ip": "192.168.56.132",
          "public_ip": null,
          "mac_address": "02:00:17:10:ED:9F"
        }
      ]
    }
  ]
}
```

#### 4. `get_compute_instance_state`
Get the current lifecycle state of a specific compute instance.

**Parameters:**
- `instance_id` (required): OCI instance OCID

**Returns:**
```json
{
  "success": true,
  "summary": "Instance 'ArkimeGOAD' is currently RUNNING",
  "method": "OCI Python SDK",
  "state_info": {
    "instance_id": "ocid1.instance.oc1...",
    "instance_name": "ArkimeGOAD",
    "lifecycle_state": "RUNNING",
    "shape": "VM.Standard.E5.Flex",
    "availability_domain": "NoEK:EU-FRANKFURT-1-AD-1",
    "compartment_id": "ocid1.compartment.oc1...",
    "time_created": "2025-02-25T17:22:25.782000+00:00"
  },
  "retrieved_at": "2025-07-30T09:42:30Z"
}
```

### ⚡ Instance Lifecycle Management Tools

#### 5. `start_compute_instance`
Start a stopped compute instance.

**Parameters:**
- `instance_id` (required): OCI instance OCID
- `compartment_id` (optional): OCI compartment ID

**Returns:**
```json
{
  "success": true,
  "summary": "Start action initiated for instance 'WebServer' (was STOPPED) - Work Request: ocid1.workrequest.oc1...",
  "method": "OCI Python SDK",
  "action_details": {
    "instance_id": "ocid1.instance.oc1...",
    "instance_name": "WebServer",
    "action": "START",
    "previous_state": "STOPPED",
    "work_request_id": "ocid1.workrequest.oc1...",
    "request_id": "unique-request-id",
    "initiated_at": "2025-07-30T09:42:30Z"
  },
  "initiated_at": "2025-07-30T09:42:30Z"
}
```

#### 6. `stop_compute_instance`
Stop a running compute instance with graceful or forced shutdown.

**Parameters:**
- `instance_id` (required): OCI instance OCID
- `compartment_id` (optional): OCI compartment ID
- `soft_stop` (optional): Use graceful shutdown (SOFTSTOP) if True, force stop (STOP) if False. Default: True

**Returns:**
```json
{
  "success": true,
  "summary": "Graceful stop action initiated for instance 'WebServer' (was RUNNING)",
  "method": "OCI Python SDK",
  "action_details": {
    "instance_id": "ocid1.instance.oc1...",
    "instance_name": "WebServer",
    "action": "SOFTSTOP",
    "previous_state": "RUNNING",
    "work_request_id": "ocid1.workrequest.oc1...",
    "initiated_at": "2025-07-30T09:42:30Z"
  }
}
```

#### 7. `restart_compute_instance`
Restart a compute instance with graceful or forced restart.

**Parameters:**
- `instance_id` (required): OCI instance OCID
- `compartment_id` (optional): OCI compartment ID
- `soft_restart` (optional): Use graceful restart (SOFTRESET) if True, force restart (RESET) if False. Default: True

**Returns:**
```json
{
  "success": true,
  "summary": "Graceful restart action initiated for instance 'WebServer' (was RUNNING)",
  "method": "OCI Python SDK",
  "action_details": {
    "instance_id": "ocid1.instance.oc1...",
    "instance_name": "WebServer",
    "action": "SOFTRESET",
    "previous_state": "RUNNING",
    "work_request_id": "ocid1.workrequest.oc1...",
    "initiated_at": "2025-07-30T09:42:30Z"
  }
}
```

### 🔧 Diagnostic Tools

#### 8. `test_core_services_connection`
Test connectivity to OCI Core Services and validate configuration.

**Returns connection status for:**
- OCI SDK configuration
- Compute service access
- Virtual Network service access

## 🛠️ Installation & Setup

### Prerequisites
```bash
# Install Python dependencies
pip install fastmcp>=0.9.0 oci>=2.157.0 python-dotenv

# Ensure OCI CLI is configured
oci setup config
```

### Configuration
The server uses standard OCI configuration:
- **Config file**: `~/.oci/config` (default)
- **Environment**: `OCI_COMPARTMENT_ID` for default compartment
- **Authentication**: OCI config file with API keys

### Running the Server

#### Option 1: Direct execution
```bash
python3 oci_core_services_server.py
```

#### Option 2: Using the launcher script
```bash
./run_core_services_server.sh
```

## 📊 Current Test Results

**✅ Successfully tested with production OCI tenancy:**

### Instance Discovery
- **13 running instances discovered**
- Instance names: ArkimeGOAD, Caldera, Ludus, Suricata, TPOT, Victim1, braavos, etc.
- Shapes: VM.Standard.E4.Flex, VM.Standard.E5.Flex, VM.Standard.E6.Flex
- All with complete OCIDs and lifecycle states

### Network Information  
- **Private IPs**: 192.168.56.x, 192.168.57.x networks
- **Public IPs**: Available where configured
- **Hostnames**: arkimegoad, ludus, etc.
- **MAC addresses**: Complete network interface details
- **Security groups**: NSG associations included

### Performance
- **Primary Method**: OCI Python SDK
- **Response time**: ~500ms for 13 instances with network info
- **Fallback**: CLI method available for compatibility
- **LLM-friendly**: Optimized JSON structure for AI consumption

## 🔄 SDK vs CLI Approach

### Primary: OCI Python SDK
- ✅ **Direct API access** to OCI Core Services
- ✅ **Type-safe** responses with proper data structures  
- ✅ **Better performance** with connection pooling
- ✅ **Rich metadata** including detailed configurations
- ✅ **Network information** via VirtualNetworkClient
- ✅ **Real-time data** with immediate API responses

### Fallback: OCI CLI
- ✅ **Universal compatibility** where SDK isn't available
- ✅ **Same data format** for seamless switching
- ⚠️ **Limited network info** (requires additional calls)
- ⚠️ **JSON parsing overhead**

## 🎯 LLM-Friendly JSON Format

### Key Design Principles:
1. **Human-readable summaries**: Every response includes a `summary` field
2. **Consistent structure**: All responses follow the same pattern
3. **Clear success indicators**: `success` boolean for easy parsing
4. **Comprehensive data**: Both summary and detailed data included
5. **ISO timestamps**: Standardized time format
6. **Error handling**: Consistent error response format

### Response Structure:
```json
{
  "success": true|false,
  "summary": "Human-readable description",
  "count": 13,
  "method": "OCI Python SDK|OCI CLI",
  "data_field": [...],
  "retrieved_at": "2025-07-30T09:42:30Z",
  "error": "Error message if failed"
}
```

## 🔧 Technical Architecture

### FastMCP Integration
```python
from fastmcp import FastMCP
mcp = FastMCP("OCI Core Services Server")

@mcp.tool()
async def list_compute_instances(...) -> Dict[str, Any]:
    # Tool implementation
```

### OCI SDK Integration
```python
from oci.core import ComputeClient, VirtualNetworkClient

# Initialize clients with automatic auth
self.compute_client = ComputeClient(self.config)
self.network_client = VirtualNetworkClient(self.config)
```

### Error Handling & Fallbacks
```python
try:
    instances = await self.list_instances_sdk(compartment_id)
    method = "OCI Python SDK"
except Exception as sdk_error:
    logger.warning(f"SDK failed, trying CLI: {sdk_error}")
    instances = await self.list_instances_cli_fallback(compartment_id)
    method = "OCI CLI"
```

## 📈 Usage Examples

### Basic Instance Listing
```json
{
  "name": "list_compute_instances",
  "arguments": {
    "lifecycle_state": "RUNNING"
  }
}
```

### Instance Details with Network
```json
{
  "name": "get_instance_details",
  "arguments": {
    "instance_id": "ocid1.instance.oc1.eu-frankfurt-1...",
    "include_network": true
  }
}
```

### Complete Network Inventory
```json
{
  "name": "list_instances_with_network",
  "arguments": {
    "compartment_id": "ocid1.compartment.oc1...",
    "lifecycle_state": "RUNNING"
  }
}
```

### Start a Stopped Instance
```json
{
  "name": "start_compute_instance",
  "arguments": {
    "instance_id": "ocid1.instance.oc1.eu-frankfurt-1..."
  }
}
```

### Graceful Stop Instance
```json
{
  "name": "stop_compute_instance",
  "arguments": {
    "instance_id": "ocid1.instance.oc1.eu-frankfurt-1...",
    "soft_stop": true
  }
}
```

### Force Restart Instance
```json
{
  "name": "restart_compute_instance",
  "arguments": {
    "instance_id": "ocid1.instance.oc1.eu-frankfurt-1...",
    "soft_restart": false
  }
}
```

### Check Instance State
```json
{
  "name": "get_compute_instance_state",
  "arguments": {
    "instance_id": "ocid1.instance.oc1.eu-frankfurt-1..."
  }
}
```

## 🌐 Integration Notes

### With Other MCP Servers
- **Metrics Server**: Complements OCI monitoring/metrics server
- **Logan MCP**: Compatible timestamp and data formats
- **Security Analysis**: Network data perfect for security correlation

### Claude/LLM Integration
- **Optimized responses**: Designed for AI consumption
- **Clear summaries**: Human-readable context for LLMs
- **Structured data**: Detailed data for programmatic access
- **Error resilience**: Graceful handling of failures

## 🎯 Benefits Over Generic Solutions

### Specialized Focus
- ✅ **Core Services Only**: Dedicated to compute and network operations with lifecycle management
- ✅ **Complete Instance Control**: Start, stop, restart with graceful/forced options
- ✅ **Optimized Performance**: Targeted for specific use cases
- ✅ **Clean Architecture**: No mixing of concerns with monitoring/metrics
- ✅ **LLM-First Design**: Built specifically for AI assistant consumption

### Production Ready
- ✅ **Tested**: Verified with 13 running instances in production
- ✅ **Reliable**: SDK primary with CLI fallback ensures availability
- ✅ **Scalable**: Efficient async operations for multiple instances
- ✅ **Maintainable**: Clean separation of concerns

---

**This OCI Core Services FastMCP Server provides dedicated compute instance management with LLM-optimized responses, perfect for AI assistants needing OCI infrastructure data.**