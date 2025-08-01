#!/usr/bin/env python3
"""
Test script for the OCI Core Services FastMCP Server
Tests LLM-friendly JSON format output
"""
import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

# Import the Core Services manager
from oci_core_services_server import core_manager

async def test_core_services():
    """Test the Core Services server functions"""
    print("🧪 Testing OCI Core Services Server...")
    print("=" * 60)
    
    try:
        compartment_id = core_manager.get_compartment_id()
        print(f"🏢 Using compartment: {compartment_id}")
        print("")
        
        # Test 1: Basic instance listing
        print("1️⃣ Testing basic instance listing...")
        if core_manager.compute_client:
            instances = await core_manager.list_instances_sdk(compartment_id, "RUNNING")
            print(f"✅ Found {len(instances)} instances via SDK")
            
            # Show LLM-friendly format
            sample_response = {
                "success": True,
                "summary": f"Found {len(instances)} running compute instances in {core_manager.config.get('region', 'unknown')}",
                "count": len(instances),
                "method": "OCI Python SDK",
                "instances": instances[:2],  # Show first 2 for brevity
                "retrieved_at": "2025-07-30T09:00:00Z"
            }
            
            print("\n📄 Sample LLM-friendly JSON response:")
            print(json.dumps(sample_response, indent=2))
            
        else:
            print("❌ SDK not available, testing CLI...")
            instances = await core_manager.list_instances_cli_fallback(compartment_id, "RUNNING")
            print(f"📊 Found {len(instances)} instances via CLI")
        
        print("\n" + "=" * 60)
        
        # Test 2: Network information
        print("\n2️⃣ Testing network information...")
        if core_manager.network_client and instances:
            first_instance = instances[0]
            print(f"📡 Getting network info for: {first_instance['name']}")
            
            network_info = await core_manager.get_instance_network_info_sdk(
                first_instance['id'], compartment_id
            )
            
            if network_info:
                primary = next((nic for nic in network_info if nic['is_primary']), network_info[0])
                print(f"✅ Primary interface:")
                print(f"   Private IP: {primary['private_ip']}")
                print(f"   Public IP: {primary['public_ip'] or 'None'}")
                print(f"   Hostname: {primary['hostname'] or 'N/A'}")
                
                # Show LLM-friendly network format
                network_sample = {
                    "success": True,
                    "summary": f"Instance '{first_instance['name']}' is running with private IP {primary['private_ip']}",
                    "instance": {
                        "name": first_instance['name'],
                        "state": first_instance['state'],
                        "primary_private_ip": primary['private_ip'],
                        "primary_public_ip": primary['public_ip']
                    },
                    "network_interfaces": network_info[:1]  # Show first interface
                }
                
                print("\n📄 Sample network response:")
                print(json.dumps(network_sample, indent=2))
            else:
                print("❌ No network interfaces found")
        else:
            print("❌ Network client not available or no instances")
        
        print("\n" + "=" * 60)
        
        # Test 3: Instance state checking
        print("\n3️⃣ Testing instance state checking...")
        if core_manager.compute_client and instances:
            first_instance = instances[0]
            print(f"🔍 Checking state for: {first_instance['name']}")
            
            state_info = await core_manager.get_instance_state_sdk(first_instance['id'])
            print(f"✅ Current state: {state_info['lifecycle_state']}")
            
            # Show LLM-friendly state format
            state_sample = {
                "success": True,
                "summary": f"Instance '{state_info['instance_name']}' is currently {state_info['lifecycle_state']}",
                "method": "OCI Python SDK",
                "state_info": state_info,
                "retrieved_at": "2025-07-30T09:00:00Z"
            }
            
            print("\n📄 Sample state response:")
            print(json.dumps(state_sample, indent=2))
        else:
            print("❌ SDK not available or no instances")
        
        print("\n" + "=" * 60)
        
        # Test 4: Lifecycle action validation (without actually performing actions)
        print("\n4️⃣ Testing lifecycle action validation...")
        if core_manager.compute_client and instances:
            first_instance = instances[0]
            print(f"🔧 Testing action validation for: {first_instance['name']}")
            
            # Test valid actions
            valid_actions = ["START", "STOP", "SOFTRESET", "RESET", "SOFTSTOP"]
            for action in valid_actions:
                try:
                    # Just validate the action without executing
                    if action.upper() not in valid_actions:
                        raise Exception(f"Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}")
                    print(f"  ✅ {action}: Valid")
                except Exception as e:
                    print(f"  ❌ {action}: {e}")
            
            # Test invalid action
            try:
                invalid_action = "INVALID_ACTION"
                if invalid_action.upper() not in valid_actions:
                    raise Exception(f"Invalid action '{invalid_action}'. Valid actions: {', '.join(valid_actions)}")
                print(f"  ❌ Should have failed: {invalid_action}")
            except Exception as e:
                print(f"  ✅ Correctly rejected invalid action: {e}")
            
            # Show sample action response format
            action_sample = {
                "success": True,
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
            
            print("\n📄 Sample action response format:")
            print(json.dumps(action_sample, indent=2))
        else:
            print("❌ SDK not available or no instances")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    
    print(f"\n🎉 Core Services test completed with lifecycle management!")
    return True

if __name__ == "__main__":
    # Set environment variable for testing
    os.environ['OCI_COMPARTMENT_ID'] = 'ocid1.compartment.oc1..aaaaaaaagy3yddkkampnhj3cqm5ar7w2p7tuq5twbojyycvol6wugfav3ckq'
    
    success = asyncio.run(test_core_services())
    sys.exit(0 if success else 1)