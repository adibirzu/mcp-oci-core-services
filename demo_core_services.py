#!/usr/bin/env python3
"""
Demo script showing LLM-friendly JSON output from OCI Core Services server

Copyright 2025

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from oci_core_services_server import core_manager

async def demo_llm_responses():
    """Demonstrate LLM-friendly responses"""
    print("🎯 OCI Core Services Server - LLM-Friendly Demo")
    print("=" * 60)
    
    compartment_id = core_manager.get_compartment_id()
    
    # Simulate the actual MCP tool responses
    print("\n1️⃣ list_compute_instances Response:")
    print("-" * 40)
    
    try:
        instances = await core_manager.list_instances_sdk(compartment_id, "RUNNING")
        
        # This is exactly what the MCP tool would return
        response = {
            "success": True,
            "summary": f"Found {len(instances)} running compute instances in {core_manager.config.get('region', 'unknown')}",
            "count": len(instances),
            "method": "OCI Python SDK",
            "filters": {
                "compartment_id": compartment_id,
                "lifecycle_state": "RUNNING"
            },
            "instances": [
                {
                    "id": inst["id"],
                    "name": inst["name"],
                    "shape": inst["shape"],
                    "state": inst["state"],
                    "region": inst["region"]
                } for inst in instances[:3]  # Show first 3 for demo
            ],
            "retrieved_at": "2025-07-30T12:00:00Z"
        }
        
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("\n2️⃣ list_instances_with_network Response:")
    print("-" * 40)
    
    try:
        # Get one instance with network info for demo
        if instances:
            first_instance = instances[0]
            network_info = await core_manager.get_instance_network_info_sdk(
                first_instance['id'], compartment_id
            )
            
            primary_nic = next((nic for nic in network_info if nic['is_primary']), 
                             network_info[0] if network_info else None)
            
            # Enhanced instance data with network
            enhanced_instance = {
                **first_instance,
                "network_interfaces": network_info,
                "primary_private_ip": primary_nic['private_ip'] if primary_nic else None,
                "primary_public_ip": primary_nic['public_ip'] if primary_nic else None,
                "hostname": primary_nic['hostname'] if primary_nic else None
            }
            
            network_response = {
                "success": True,
                "summary": f"Found 1 running compute instance with network information",
                "count": 1,
                "method": "OCI Python SDK",
                "network_info_included": True,
                "instances": [enhanced_instance],
                "retrieved_at": "2025-07-30T12:00:00Z"
            }
            
            print(json.dumps(network_response, indent=2))
    
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("\n✅ Demo completed! This shows the exact JSON format that will be")
    print("   returned to Claude/LLMs for easy parsing and understanding.")

if __name__ == "__main__":
    os.environ['OCI_COMPARTMENT_ID'] = 'ocid1.compartment.oc1..aaaaaaaagy3yddkkampnhj3cqm5ar7w2p7tuq5twbojyycvol6wugfav3ckq'
    asyncio.run(demo_llm_responses())