# Claude Desktop Setup - OCI Core Services

## ✅ Server Successfully Moved and Configured

The OCI Core Services MCP Server has been moved to its own dedicated folder and configured for Claude Desktop integration.

### 📁 New Location
```
/Users/abirzu/dev/mcp-oci-core-services/
├── oci_core_services_server.py      # Main FastMCP server
├── run_core_services_server.sh      # Launcher script
├── requirements.txt                 # Python dependencies
├── README.md                        # Complete documentation
├── INSTALLATION.md                  # Installation guide
├── test_core_services.py           # Test functionality
├── demo_core_services.py           # LLM response demo
├── setup.sh                        # Automated setup
└── package.json                    # Project metadata
```

### 🔧 Claude Desktop Configuration Added

Your Claude Desktop config has been updated with:

```json
"oci-core-services": {
  "command": "/Users/abirzu/.pyenv/versions/3.11.9/bin/python",
  "args": [
    "/Users/abirzu/dev/mcp-oci-core-services/oci_core_services_server.py"
  ],
  "env": {
    "OCI_COMPARTMENT_ID": "ocid1.compartment.oc1..aaaaaaaagy3yddkkampnhj3cqm5ar7w2p7tuq5twbojyycvol6wugfav3ckq",
    "SUPPRESS_LABEL_WARNING": "True"
  }
}
```

### 🧪 Test Results
- ✅ **Server starts correctly** in new location
- ✅ **OCI SDK initialized** successfully  
- ✅ **13 instances discovered** in Frankfurt region
- ✅ **Network information** fully functional
- ✅ **LLM-friendly JSON** format working

### 🎯 Available Tools in Claude

Once you restart Claude Desktop, you'll have access to:

| Tool | Description |
|------|-------------|
| `list_compute_instances` | List running instances with basic details |
| `get_instance_details` | Get comprehensive instance information |
| `list_instances_with_network` | List instances with IP addresses and network info |
| `test_core_services_connection` | Test OCI connectivity and permissions |

### 💬 Example Claude Queries

After restarting Claude Desktop, you can ask:

- **"List my running compute instances in Frankfurt"**
- **"Show me the network details for my instances"** 
- **"What are the IP addresses of my running instances?"**
- **"Get details about the ArkimeGOAD instance"**

### 📊 Expected Response Format

Claude will receive well-structured JSON responses like:

```json
{
  "success": true,
  "summary": "Found 13 running compute instances in eu-frankfurt-1",
  "count": 13,
  "method": "OCI Python SDK",
  "instances": [
    {
      "name": "ArkimeGOAD",
      "shape": "VM.Standard.E5.Flex", 
      "state": "RUNNING",
      "primary_private_ip": "192.168.56.132",
      "region": "eu-frankfurt-1"
    }
  ]
}
```

### 🔄 Next Steps

1. **Restart Claude Desktop** to load the new server configuration
2. **Test the integration** by asking Claude about your instances
3. **Verify functionality** with sample queries above

The server is now properly separated from the metrics server and optimized for LLM consumption with clear, structured responses that Claude can easily parse and understand.

## 🚀 Your Frankfurt Instances Ready for Query

Your 13 running instances are now accessible via Claude:
- **Security Tools**: ArkimeGOAD, Caldera, Ludus, Suricata, TPOT
- **Game of Thrones Servers**: braavos, castelblack, meereen, winterfell  
- **Test Instances**: Victim1, victim2, test-Delete
- **Utility**: instance-20250612-2041

All with complete network information, shapes, states, and metadata available through natural language queries to Claude!