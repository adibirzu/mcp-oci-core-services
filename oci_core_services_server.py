#!/usr/bin/env python3
"""
OCI Core Services FastMCP Server

A dedicated FastMCP server for Oracle Cloud Infrastructure Core Services including:
- Compute instance management and listing
- Network interface (VNIC) information
- Instance lifecycle operations
- Detailed instance configurations

Uses official OCI Python SDK with CLI fallback for maximum compatibility.
Returns LLM-friendly JSON responses with human-readable summaries.

Prerequisites:
- OCI CLI installed and configured
- OCI config file at ~/.oci/config
- OCI Python SDK installed
- Appropriate OCI permissions for core services
"""

import os
import sys
import json
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

try:
    import oci
    from oci.config import from_file, validate_config
    from oci.core import ComputeClient, VirtualNetworkClient
    from oci.core.models import Instance
    from oci.database import DatabaseClient
except ImportError as e:
    print(f"ERROR: OCI Python SDK not installed: {e}")
    print("Install with: pip install oci")
    sys.exit(1)

try:
    from fastmcp import FastMCP
except ImportError as e:
    print(f"ERROR: FastMCP not installed: {e}")
    print("Install with: pip install fastmcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("OCI Core Services Server")

class OCICoreServicesManager:
    """Manages OCI Core Services clients with fallback to CLI"""
    
    def __init__(self):
        self.config = None
        self.compute_client = None
        self.network_client = None
        self.database_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize OCI SDK clients"""
        try:
            # Load OCI config from default location
            self.config = from_file()
            validate_config(self.config)
            
            # Initialize clients
            self.compute_client = ComputeClient(self.config)
            self.network_client = VirtualNetworkClient(self.config)
            self.database_client = DatabaseClient(self.config)
            
            logger.info("✅ OCI Core Services clients initialized successfully")
            logger.info(f"Region: {self.config.get('region', 'Not specified')}")
            logger.info(f"Tenancy: {self.config.get('tenancy', 'Not specified')[:20]}...")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OCI SDK clients: {e}")
            logger.warning("Will fall back to CLI commands")
            self.config = None
            self.compute_client = None
            self.network_client = None
            self.database_client = None
    
    def get_compartment_id(self) -> str:
        """Get compartment ID from environment or config"""
        compartment_id = os.environ.get('OCI_COMPARTMENT_ID')
        if not compartment_id and self.config:
            # Use tenancy as default compartment if no specific compartment set
            compartment_id = self.config.get('tenancy')
        return compartment_id
    
    async def list_instances_sdk(self, compartment_id: str, lifecycle_state: str = "RUNNING") -> List[Dict]:
        """List instances using OCI Python SDK"""
        if not self.compute_client:
            raise Exception("OCI SDK not available")
        
        try:
            logger.info(f"Listing instances with SDK - Compartment: {compartment_id}, State: {lifecycle_state}")
            
            # List instances using SDK
            response = self.compute_client.list_instances(
                compartment_id=compartment_id,
                lifecycle_state=lifecycle_state
            )
            
            instances = []
            for instance in response.data:
                instance_data = {
                    'id': instance.id,
                    'name': instance.display_name,
                    'shape': instance.shape,
                    'state': instance.lifecycle_state,
                    'availability_domain': instance.availability_domain,
                    'compartment_id': instance.compartment_id,
                    'created_time': instance.time_created.isoformat() if instance.time_created else None,
                    'region': self.config.get('region', 'unknown'),
                    'image_id': instance.image_id,
                    'fault_domain': instance.fault_domain,
                    'metadata': instance.metadata or {},
                    'tags': {
                        'freeform': instance.freeform_tags or {},
                        'defined': instance.defined_tags or {}
                    }
                }
                instances.append(instance_data)
            
            logger.info(f"✅ Found {len(instances)} instances via SDK")
            return instances
            
        except Exception as e:
            logger.error(f"SDK failed: {e}")
            raise
    
    async def get_instance_details_sdk(self, instance_id: str) -> Dict:
        """Get detailed instance information using OCI Python SDK"""
        if not self.compute_client:
            raise Exception("OCI SDK not available")
        
        try:
            logger.info(f"Getting instance details via SDK: {instance_id}")
            
            response = self.compute_client.get_instance(instance_id=instance_id)
            instance = response.data
            
            instance_data = {
                'id': instance.id,
                'name': instance.display_name,
                'shape': instance.shape,
                'state': instance.lifecycle_state,
                'availability_domain': instance.availability_domain,
                'compartment_id': instance.compartment_id,
                'created_time': instance.time_created.isoformat() if instance.time_created else None,
                'region': self.config.get('region', 'unknown'),
                'image_id': instance.image_id,
                'fault_domain': instance.fault_domain,
                'metadata': instance.metadata or {},
                'extended_metadata': instance.extended_metadata or {},
                'tags': {
                    'freeform': instance.freeform_tags or {},
                    'defined': instance.defined_tags or {}
                },
                'configuration': {
                    'launch_options': instance.launch_options.__dict__ if instance.launch_options else {},
                    'instance_options': instance.instance_options.__dict__ if instance.instance_options else {},
                    'availability_config': instance.availability_config.__dict__ if instance.availability_config else {},
                    'agent_config': instance.agent_config.__dict__ if instance.agent_config else {}
                }
            }
            
            logger.info(f"✅ Retrieved instance details via SDK")
            return instance_data
            
        except Exception as e:
            logger.error(f"SDK failed: {e}")
            raise
    
    async def get_instance_network_info_sdk(self, instance_id: str, compartment_id: str) -> List[Dict]:
        """Get network information for an instance using OCI Python SDK"""
        if not self.compute_client or not self.network_client:
            raise Exception("OCI SDK clients not available")
        
        try:
            # Get VNIC attachments
            vnic_response = self.compute_client.list_vnic_attachments(
                compartment_id=compartment_id,
                instance_id=instance_id
            )
            
            network_interfaces = []
            for vnic_attachment in vnic_response.data:
                # Get VNIC details
                try:
                    vnic_details_response = self.network_client.get_vnic(vnic_id=vnic_attachment.vnic_id)
                    vnic = vnic_details_response.data
                    
                    network_info = {
                        'attachment_id': vnic_attachment.id,
                        'vnic_id': vnic_attachment.vnic_id,
                        'is_primary': vnic.is_primary,
                        'private_ip': vnic.private_ip,
                        'public_ip': vnic.public_ip,
                        'hostname': vnic.hostname_label,
                        'mac_address': vnic.mac_address,
                        'subnet_id': vnic.subnet_id,
                        'nic_index': vnic_attachment.nic_index,
                        'state': vnic.lifecycle_state,
                        'skip_source_dest_check': vnic.skip_source_dest_check,
                        'security_groups': vnic.nsg_ids or []
                    }
                    network_interfaces.append(network_info)
                    
                except Exception as vnic_error:
                    logger.warning(f"Failed to get VNIC details for {vnic_attachment.vnic_id}: {vnic_error}")
            
            return network_interfaces
            
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return []
    
    async def instance_action_sdk(self, instance_id: str, action: str, compartment_id: str = None) -> Dict:
        """Perform instance lifecycle action using OCI Python SDK"""
        if not self.compute_client:
            raise Exception("OCI SDK not available")
        
        valid_actions = ["START", "STOP", "SOFTRESET", "RESET", "SOFTSTOP"]
        if action.upper() not in valid_actions:
            raise Exception(f"Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}")
        
        try:
            logger.info(f"Performing {action} action on instance {instance_id}")
            
            # Get current instance details first for validation and reporting
            instance_response = self.compute_client.get_instance(instance_id=instance_id)
            instance = instance_response.data
            current_state = instance.lifecycle_state
            
            logger.info(f"Instance '{instance.display_name}' current state: {current_state}")
            
            # Perform the action
            response = self.compute_client.instance_action(
                instance_id=instance_id,
                action=action.upper()
            )
            
            # Wait for work request completion if work request ID is provided
            work_request_id = response.headers.get('opc-work-request-id')
            if work_request_id:
                logger.info(f"Action initiated with work request ID: {work_request_id}")
            
            action_result = {
                'instance_id': instance_id,
                'instance_name': instance.display_name,
                'action': action.upper(),
                'previous_state': current_state,
                'work_request_id': work_request_id,
                'request_id': response.headers.get('opc-request-id'),
                'initiated_at': datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"✅ {action} action initiated successfully")
            return action_result
            
        except Exception as e:
            logger.error(f"Instance action failed: {e}")
            raise
    
    async def get_instance_state_sdk(self, instance_id: str) -> Dict:
        """Get current state of an instance using OCI Python SDK"""
        if not self.compute_client:
            raise Exception("OCI SDK not available")
        
        try:
            response = self.compute_client.get_instance(instance_id=instance_id)
            instance = response.data
            
            state_info = {
                'instance_id': instance_id,
                'instance_name': instance.display_name,
                'lifecycle_state': instance.lifecycle_state,
                'shape': instance.shape,
                'availability_domain': instance.availability_domain,
                'compartment_id': instance.compartment_id,
                'time_created': instance.time_created.isoformat() if instance.time_created else None,
                'retrieved_at': datetime.utcnow().isoformat() + "Z"
            }
            
            return state_info
            
        except Exception as e:
            logger.error(f"Failed to get instance state: {e}")
            raise
    
    async def list_databases_sdk(self, compartment_id: str, lifecycle_state: str = None) -> List[Dict]:
        """List database systems using OCI Python SDK"""
        if not self.database_client:
            raise Exception("OCI Database SDK not available")
        
        try:
            logger.info(f"Listing database systems - Compartment: {compartment_id}, State: {lifecycle_state or 'ALL'}")
            
            # List database systems
            list_params = {'compartment_id': compartment_id}
            if lifecycle_state:
                list_params['lifecycle_state'] = lifecycle_state
                
            response = self.database_client.list_db_systems(**list_params)
            
            databases = []
            for db_system in response.data:
                db_data = {
                    'id': db_system.id,
                    'display_name': db_system.display_name,
                    'shape': db_system.shape,
                    'lifecycle_state': db_system.lifecycle_state,
                    'availability_domain': db_system.availability_domain,
                    'compartment_id': db_system.compartment_id,
                    'time_created': db_system.time_created.isoformat() if db_system.time_created else None,
                    'database_edition': db_system.database_edition,
                    'version': db_system.version,
                    'node_count': db_system.node_count,
                    'cpu_core_count': db_system.cpu_core_count,
                    'data_storage_size_in_gbs': db_system.data_storage_size_in_gbs,
                    'hostname': db_system.hostname,
                    'domain': db_system.domain,
                    'tags': {
                        'freeform': db_system.freeform_tags or {},
                        'defined': db_system.defined_tags or {}
                    }
                }
                databases.append(db_data)
            
            logger.info(f"✅ Found {len(databases)} database systems via SDK")
            return databases
            
        except Exception as e:
            logger.error(f"Database SDK failed: {e}")
            raise
    
    async def database_action_sdk(self, db_system_id: str, action: str) -> Dict:
        """Perform database system lifecycle action using OCI Python SDK"""
        if not self.database_client:
            raise Exception("OCI Database SDK not available")
        
        valid_actions = ["START", "STOP"]
        if action.upper() not in valid_actions:
            raise Exception(f"Invalid database action '{action}'. Valid actions: {', '.join(valid_actions)}")
        
        try:
            logger.info(f"Performing {action} action on database system {db_system_id}")
            
            # Get current database system details first
            db_response = self.database_client.get_db_system(db_system_id=db_system_id)
            db_system = db_response.data
            current_state = db_system.lifecycle_state
            
            logger.info(f"Database system '{db_system.display_name}' current state: {current_state}")
            
            # Perform the action
            if action.upper() == "START":
                response = self.database_client.start_db_system(db_system_id=db_system_id)
            elif action.upper() == "STOP":
                response = self.database_client.stop_db_system(db_system_id=db_system_id)
            
            # Get work request information
            work_request_id = response.headers.get('opc-work-request-id')
            if work_request_id:
                logger.info(f"Database action initiated with work request ID: {work_request_id}")
            
            action_result = {
                'db_system_id': db_system_id,
                'db_system_name': db_system.display_name,
                'action': action.upper(),
                'previous_state': current_state,
                'work_request_id': work_request_id,
                'request_id': response.headers.get('opc-request-id'),
                'initiated_at': datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"✅ Database {action} action initiated successfully")
            return action_result
            
        except Exception as e:
            logger.error(f"Database action failed: {e}")
            raise
    
    async def get_database_state_sdk(self, db_system_id: str) -> Dict:
        """Get current state of a database system using OCI Python SDK"""
        if not self.database_client:
            raise Exception("OCI Database SDK not available")
        
        try:
            response = self.database_client.get_db_system(db_system_id=db_system_id)
            db_system = response.data
            
            state_info = {
                'db_system_id': db_system_id,
                'db_system_name': db_system.display_name,
                'lifecycle_state': db_system.lifecycle_state,
                'shape': db_system.shape,
                'database_edition': db_system.database_edition,
                'version': db_system.version,
                'node_count': db_system.node_count,
                'cpu_core_count': db_system.cpu_core_count,
                'availability_domain': db_system.availability_domain,
                'compartment_id': db_system.compartment_id,
                'time_created': db_system.time_created.isoformat() if db_system.time_created else None,
                'retrieved_at': datetime.utcnow().isoformat() + "Z"
            }
            
            return state_info
            
        except Exception as e:
            logger.error(f"Failed to get database system state: {e}")
            raise
    
    async def list_instances_cli_fallback(self, compartment_id: str, lifecycle_state: str = "RUNNING") -> List[Dict]:
        """Fallback to CLI for listing instances"""
        try:
            logger.info(f"Using CLI fallback for listing instances")
            
            cmd = [
                'oci', 'compute', 'instance', 'list',
                '--compartment-id', compartment_id,
                '--lifecycle-state', lifecycle_state,
                '--output', 'json'
            ]
            
            env = os.environ.copy()
            env['SUPPRESS_LABEL_WARNING'] = 'True'
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                raise Exception(f"CLI command failed: {result.stderr}")
            
            if not result.stdout.strip():
                return []
            
            response = json.loads(result.stdout)
            instances = []
            
            for instance_data in response.get('data', []):
                instance = {
                    'id': instance_data.get('id', ''),
                    'name': instance_data.get('display-name', 'Unknown'),
                    'shape': instance_data.get('shape', 'Unknown'),
                    'state': instance_data.get('lifecycle-state', 'Unknown'),
                    'availability_domain': instance_data.get('availability-domain', 'Unknown'),
                    'compartment_id': instance_data.get('compartment-id', ''),
                    'created_time': instance_data.get('time-created', ''),
                    'region': 'unknown',  # CLI doesn't return region directly
                    'image_id': instance_data.get('image-id', ''),
                    'fault_domain': instance_data.get('fault-domain', ''),
                    'metadata': instance_data.get('metadata', {}),
                    'tags': {
                        'freeform': instance_data.get('freeform-tags', {}),
                        'defined': instance_data.get('defined-tags', {})
                    }
                }
                instances.append(instance)
            
            logger.info(f"✅ Found {len(instances)} instances via CLI")
            return instances
            
        except Exception as e:
            logger.error(f"CLI fallback failed: {e}")
            raise

# Initialize OCI Core Services manager
core_manager = OCICoreServicesManager()

@mcp.tool()
async def list_compute_instances(compartment_id: str = None, lifecycle_state: str = "RUNNING") -> Dict[str, Any]:
    """
    List all compute instances in the compartment.
    
    Args:
        compartment_id: OCI compartment ID (uses default if not provided)
        lifecycle_state: Filter instances by lifecycle state (RUNNING, STOPPED, etc.)
    
    Returns:
        LLM-friendly JSON with summary, count, and detailed instance list
    """
    try:
        target_compartment = compartment_id or core_manager.get_compartment_id()
        if not target_compartment:
            raise Exception("Compartment ID is required")
        
        # Prefer SDK, fallback to CLI
        try:
            instances = await core_manager.list_instances_sdk(target_compartment, lifecycle_state)
            method = "OCI Python SDK"
        except Exception as sdk_error:
            logger.warning(f"SDK failed, trying CLI: {sdk_error}")
            instances = await core_manager.list_instances_cli_fallback(target_compartment, lifecycle_state)
            method = "OCI CLI"
        
        # Create LLM-friendly response
        summary = f"Found {len(instances)} {lifecycle_state.lower()} compute instances in {core_manager.config.get('region', 'unknown region') if core_manager.config else 'unknown region'}"
        
        response = {
            "success": True,
            "summary": summary,
            "count": len(instances),
            "method": method,
            "filters": {
                "compartment_id": target_compartment,
                "lifecycle_state": lifecycle_state
            },
            "instances": instances,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing compute instances: {e}")
        return {
            "success": False,
            "summary": f"Failed to list compute instances: {str(e)}",
            "count": 0,
            "method": "Error",
            "instances": [],
            "error": str(e),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def get_instance_details(instance_id: str, compartment_id: str = None, include_network: bool = True) -> Dict[str, Any]:
    """
    Get detailed information about a specific compute instance.
    
    Args:
        instance_id: OCI Compute instance OCID
        compartment_id: OCI compartment ID (uses default if not provided)
        include_network: Whether to include network interface details
    
    Returns:
        LLM-friendly JSON with comprehensive instance details
    """
    try:
        target_compartment = compartment_id or core_manager.get_compartment_id()
        
        # Get instance details
        if core_manager.compute_client:
            instance_details = await core_manager.get_instance_details_sdk(instance_id)
            method = "OCI Python SDK"
        else:
            raise Exception("Instance details require OCI SDK")
        
        # Add network information if requested
        network_info = []
        if include_network and core_manager.network_client and target_compartment:
            try:
                network_info = await core_manager.get_instance_network_info_sdk(instance_id, target_compartment)
            except Exception as e:
                logger.warning(f"Failed to get network info: {e}")
        
        # Create LLM-friendly response
        summary = f"Instance '{instance_details['name']}' ({instance_details['shape']}) is {instance_details['state'].lower()}"
        if network_info:
            primary_nic = next((nic for nic in network_info if nic['is_primary']), None)
            if primary_nic:
                summary += f" with private IP {primary_nic['private_ip']}"
                if primary_nic['public_ip']:
                    summary += f" and public IP {primary_nic['public_ip']}"
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "instance": instance_details,
            "network_interfaces": network_info,
            "network_info_included": include_network and len(network_info) > 0,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting instance details: {e}")
        return {
            "success": False,
            "summary": f"Failed to get instance details: {str(e)}",
            "method": "Error",
            "instance": {},
            "network_interfaces": [],
            "network_info_included": False,
            "error": str(e),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def list_instances_with_network(compartment_id: str = None, lifecycle_state: str = "RUNNING") -> Dict[str, Any]:
    """
    List compute instances with their network interface information.
    
    Args:
        compartment_id: OCI compartment ID (uses default if not provided)
        lifecycle_state: Filter instances by lifecycle state (RUNNING, STOPPED, etc.)
    
    Returns:
        LLM-friendly JSON with instances and their network details
    """
    try:
        target_compartment = compartment_id or core_manager.get_compartment_id()
        if not target_compartment:
            raise Exception("Compartment ID is required")
        
        # Get instances first
        if core_manager.compute_client:
            instances = await core_manager.list_instances_sdk(target_compartment, lifecycle_state)
            method = "OCI Python SDK"
        else:
            instances = await core_manager.list_instances_cli_fallback(target_compartment, lifecycle_state)
            method = "OCI CLI (limited network info)"
        
        # Enhance with network information if SDK available
        if core_manager.network_client:
            for instance in instances:
                try:
                    network_info = await core_manager.get_instance_network_info_sdk(instance['id'], target_compartment)
                    instance['network_interfaces'] = network_info
                    
                    # Add convenience fields for primary interface
                    primary_nic = next((nic for nic in network_info if nic['is_primary']), None)
                    if primary_nic:
                        instance['primary_private_ip'] = primary_nic['private_ip']
                        instance['primary_public_ip'] = primary_nic['public_ip']
                        instance['hostname'] = primary_nic['hostname']
                    else:
                        instance['primary_private_ip'] = None
                        instance['primary_public_ip'] = None
                        instance['hostname'] = None
                        
                except Exception as e:
                    logger.warning(f"Failed to get network info for instance {instance['id']}: {e}")
                    instance['network_interfaces'] = []
                    instance['primary_private_ip'] = None
                    instance['primary_public_ip'] = None
                    instance['hostname'] = None
        else:
            # Add empty network info for CLI fallback
            for instance in instances:
                instance['network_interfaces'] = []
                instance['primary_private_ip'] = None
                instance['primary_public_ip'] = None
                instance['hostname'] = None
        
        # Create LLM-friendly response
        network_enabled = core_manager.network_client is not None
        summary = f"Found {len(instances)} {lifecycle_state.lower()} compute instances"
        if network_enabled:
            summary += " with network information"
        else:
            summary += " (network details require SDK)"
        
        response = {
            "success": True,
            "summary": summary,
            "count": len(instances),
            "method": method,
            "network_info_included": network_enabled,
            "filters": {
                "compartment_id": target_compartment,
                "lifecycle_state": lifecycle_state
            },
            "instances": instances,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing instances with network info: {e}")
        return {
            "success": False,
            "summary": f"Failed to list instances with network info: {str(e)}",
            "count": 0,
            "method": "Error",
            "network_info_included": False,
            "instances": [],
            "error": str(e),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def start_compute_instance(instance_id: str, compartment_id: str = None) -> Dict[str, Any]:
    """
    Start a stopped compute instance.
    
    Args:
        instance_id: OCI Compute instance OCID
        compartment_id: OCI compartment ID (uses default if not provided)
    
    Returns:
        LLM-friendly JSON with action result and status
    """
    try:
        if core_manager.compute_client:
            action_result = await core_manager.instance_action_sdk(instance_id, "START", compartment_id)
            method = "OCI Python SDK"
            
            summary = f"Start action initiated for instance '{action_result['instance_name']}' (was {action_result['previous_state']})"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Instance lifecycle actions require OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error starting instance: {e}")
        return {
            "success": False,
            "summary": f"Failed to start instance: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def stop_compute_instance(instance_id: str, compartment_id: str = None, soft_stop: bool = True) -> Dict[str, Any]:
    """
    Stop a running compute instance.
    
    Args:
        instance_id: OCI Compute instance OCID
        compartment_id: OCI compartment ID (uses default if not provided)
        soft_stop: Use graceful shutdown (SOFTSTOP) if True, force stop (STOP) if False
    
    Returns:
        LLM-friendly JSON with action result and status
    """
    try:
        action = "SOFTSTOP" if soft_stop else "STOP"
        
        if core_manager.compute_client:
            action_result = await core_manager.instance_action_sdk(instance_id, action, compartment_id)
            method = "OCI Python SDK"
            
            stop_type = "graceful" if soft_stop else "forced"
            summary = f"{stop_type.capitalize()} stop action initiated for instance '{action_result['instance_name']}' (was {action_result['previous_state']})"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Instance lifecycle actions require OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error stopping instance: {e}")
        return {
            "success": False,
            "summary": f"Failed to stop instance: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def restart_compute_instance(instance_id: str, compartment_id: str = None, soft_restart: bool = True) -> Dict[str, Any]:
    """
    Restart a compute instance.
    
    Args:
        instance_id: OCI Compute instance OCID
        compartment_id: OCI compartment ID (uses default if not provided)
        soft_restart: Use graceful restart (SOFTRESET) if True, force restart (RESET) if False
    
    Returns:
        LLM-friendly JSON with action result and status
    """
    try:
        action = "SOFTRESET" if soft_restart else "RESET"
        
        if core_manager.compute_client:
            action_result = await core_manager.instance_action_sdk(instance_id, action, compartment_id)
            method = "OCI Python SDK"
            
            restart_type = "graceful" if soft_restart else "forced"
            summary = f"{restart_type.capitalize()} restart action initiated for instance '{action_result['instance_name']}' (was {action_result['previous_state']})"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Instance lifecycle actions require OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error restarting instance: {e}")
        return {
            "success": False,
            "summary": f"Failed to restart instance: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def get_compute_instance_state(instance_id: str) -> Dict[str, Any]:
    """
    Get the current lifecycle state of a compute instance.
    
    Args:
        instance_id: OCI Compute instance OCID
    
    Returns:
        LLM-friendly JSON with current instance state
    """
    try:
        if core_manager.compute_client:
            state_info = await core_manager.get_instance_state_sdk(instance_id)
            method = "OCI Python SDK"
            
            summary = f"Instance '{state_info['instance_name']}' is currently {state_info['lifecycle_state']}"
        else:
            raise Exception("Instance state check requires OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "state_info": state_info,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting instance state: {e}")
        return {
            "success": False,
            "summary": f"Failed to get instance state: {str(e)}",
            "method": "Error",
            "state_info": {},
            "error": str(e),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def list_database_systems(compartment_id: str = None, lifecycle_state: str = None) -> Dict[str, Any]:
    """
    List database systems in the compartment.
    
    Args:
        compartment_id: OCI compartment ID (uses default if not provided)
        lifecycle_state: Filter database systems by lifecycle state (AVAILABLE, STOPPED, etc.)
    
    Returns:
        LLM-friendly JSON with database systems list
    """
    try:
        target_compartment = compartment_id or core_manager.get_compartment_id()
        if not target_compartment:
            raise Exception("Compartment ID is required")
        
        if core_manager.database_client:
            databases = await core_manager.list_databases_sdk(target_compartment, lifecycle_state)
            method = "OCI Python SDK"
        else:
            raise Exception("Database listing requires OCI SDK")
        
        # Create LLM-friendly response
        state_filter = f" {lifecycle_state.lower()}" if lifecycle_state else ""
        summary = f"Found {len(databases)}{state_filter} database systems in {core_manager.config.get('region', 'unknown region') if core_manager.config else 'unknown region'}"
        
        response = {
            "success": True,
            "summary": summary,
            "count": len(databases),
            "method": method,
            "filters": {
                "compartment_id": target_compartment,
                "lifecycle_state": lifecycle_state
            },
            "database_systems": databases,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing database systems: {e}")
        return {
            "success": False,
            "summary": f"Failed to list database systems: {str(e)}",
            "count": 0,
            "method": "Error",
            "database_systems": [],
            "error": str(e),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def start_database_system(db_system_id: str) -> Dict[str, Any]:
    """
    Start a stopped database system.
    
    Args:
        db_system_id: OCI Database System OCID
    
    Returns:
        LLM-friendly JSON with action result and status
    """
    try:
        if core_manager.database_client:
            action_result = await core_manager.database_action_sdk(db_system_id, "START")
            method = "OCI Python SDK"
            
            summary = f"Start action initiated for database system '{action_result['db_system_name']}' (was {action_result['previous_state']})"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Database lifecycle actions require OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error starting database system: {e}")
        return {
            "success": False,
            "summary": f"Failed to start database system: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def stop_database_system(db_system_id: str) -> Dict[str, Any]:
    """
    Stop a running database system.
    
    Args:
        db_system_id: OCI Database System OCID
    
    Returns:
        LLM-friendly JSON with action result and status
    """
    try:
        if core_manager.database_client:
            action_result = await core_manager.database_action_sdk(db_system_id, "STOP")
            method = "OCI Python SDK"
            
            summary = f"Stop action initiated for database system '{action_result['db_system_name']}' (was {action_result['previous_state']})"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Database lifecycle actions require OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error stopping database system: {e}")
        return {
            "success": False,
            "summary": f"Failed to stop database system: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def get_database_system_state(db_system_id: str) -> Dict[str, Any]:
    """
    Get the current lifecycle state of a database system.
    
    Args:
        db_system_id: OCI Database System OCID
    
    Returns:
        LLM-friendly JSON with current database system state
    """
    try:
        if core_manager.database_client:
            state_info = await core_manager.get_database_state_sdk(db_system_id)
            method = "OCI Python SDK"
            
            summary = f"Database system '{state_info['db_system_name']}' is currently {state_info['lifecycle_state']}"
        else:
            raise Exception("Database state check requires OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "state_info": state_info,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting database system state: {e}")
        return {
            "success": False,
            "summary": f"Failed to get database system state: {str(e)}",
            "method": "Error",
            "state_info": {},
            "error": str(e),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def test_core_services_connection() -> Dict[str, Any]:
    """
    Test connectivity to OCI Core Services and validate configuration.
    
    Returns:
        Connection status and service availability information
    """
    try:
        results = {
            "success": True,
            "summary": "OCI Core Services connection test",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tests": {}
        }
        
        # Test SDK availability
        if core_manager.config:
            results['tests']['sdk_config'] = {
                'status': 'success',
                'message': 'OCI SDK configuration loaded',
                'region': core_manager.config.get('region', 'unknown'),
                'tenancy_preview': core_manager.config.get('tenancy', '')[:20] + '...'
            }
        else:
            results['tests']['sdk_config'] = {
                'status': 'failed',
                'message': 'OCI SDK configuration not available'
            }
        
        # Test compute client
        if core_manager.compute_client:
            try:
                compartment_id = core_manager.get_compartment_id()
                if compartment_id:
                    instances = await core_manager.list_instances_sdk(compartment_id, "RUNNING")
                    results['tests']['compute_service'] = {
                        'status': 'success',
                        'message': f'Compute service accessible - found {len(instances)} running instances',
                        'instance_count': len(instances)
                    }
                else:
                    results['tests']['compute_service'] = {
                        'status': 'warning',
                        'message': 'Compute client available but no compartment ID configured'
                    }
            except Exception as e:
                results['tests']['compute_service'] = {
                    'status': 'failed',
                    'message': f'Compute service test failed: {str(e)[:100]}...'
                }
        else:
            results['tests']['compute_service'] = {
                'status': 'failed',
                'message': 'Compute client not available'
            }
        
        # Test network client
        if core_manager.network_client:
            results['tests']['network_service'] = {
                'status': 'success',
                'message': 'Virtual Network client available'
            }
        else:
            results['tests']['network_service'] = {
                'status': 'failed',
                'message': 'Virtual Network client not available'
            }
        
        # Test database client
        if core_manager.database_client:
            try:
                compartment_id = core_manager.get_compartment_id()
                if compartment_id:
                    databases = await core_manager.list_databases_sdk(compartment_id)
                    results['tests']['database_service'] = {
                        'status': 'success',
                        'message': f'Database service accessible - found {len(databases)} database systems',
                        'database_count': len(databases)
                    }
                else:
                    results['tests']['database_service'] = {
                        'status': 'warning',
                        'message': 'Database client available but no compartment ID configured'
                    }
            except Exception as e:
                results['tests']['database_service'] = {
                    'status': 'failed',
                    'message': f'Database service test failed: {str(e)[:100]}...'
                }
        else:
            results['tests']['database_service'] = {
                'status': 'failed',
                'message': 'Database client not available'
            }
        
        # Overall status
        failed_tests = [test for test in results['tests'].values() if test['status'] == 'failed']
        if not failed_tests:
            results['summary'] = 'All OCI Core Services accessible'
        else:
            results['success'] = False
            results['summary'] = f'{len(failed_tests)} out of {len(results["tests"])} tests failed'
        
        return results
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            'success': False,
            'summary': f'Connection test failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'error': str(e)
        }

if __name__ == "__main__":
    # Print startup information
    print("🚀 Starting OCI Core Services FastMCP Server...", file=sys.stderr)
    print("📋 Available tools:", file=sys.stderr)
    print("   📊 Instance Information:", file=sys.stderr)
    print("     - list_compute_instances: List instances with basic details", file=sys.stderr)
    print("     - get_instance_details: Get comprehensive instance information", file=sys.stderr)
    print("     - list_instances_with_network: List instances with network details", file=sys.stderr)
    print("     - get_compute_instance_state: Get current instance lifecycle state", file=sys.stderr)
    print("   ⚡ Instance Lifecycle Management:", file=sys.stderr)
    print("     - start_compute_instance: Start a stopped instance", file=sys.stderr)
    print("     - stop_compute_instance: Stop a running instance (graceful or forced)", file=sys.stderr)
    print("     - restart_compute_instance: Restart an instance (graceful or forced)", file=sys.stderr)
    print("   🗄️ Database Management:", file=sys.stderr)
    print("     - list_database_systems: List database systems", file=sys.stderr)
    print("     - start_database_system: Start a stopped database system", file=sys.stderr)
    print("     - stop_database_system: Stop a running database system", file=sys.stderr)
    print("     - get_database_system_state: Get current database system state", file=sys.stderr)
    print("   🔧 Diagnostics:", file=sys.stderr)
    print("     - test_core_services_connection: Test OCI connectivity", file=sys.stderr)
    print("", file=sys.stderr)
    print("⚙️  Configuration:", file=sys.stderr)
    print(f"   - OCI SDK Available: {'✅' if core_manager.compute_client else '❌'}", file=sys.stderr)
    print(f"   - Network Client: {'✅' if core_manager.network_client else '❌'}", file=sys.stderr)
    print(f"   - Database Client: {'✅' if core_manager.database_client else '❌'}", file=sys.stderr)
    print(f"   - Region: {core_manager.config.get('region', 'Not configured') if core_manager.config else 'Not configured'}", file=sys.stderr)
    print(f"   - Compartment ID: {core_manager.get_compartment_id() or '❌ Not set'}", file=sys.stderr)
    print("", file=sys.stderr)
    print("💡 Lifecycle Actions:", file=sys.stderr)
    print("   Instance Actions:", file=sys.stderr)
    print("     - START: Power on a stopped instance", file=sys.stderr)
    print("     - STOP/SOFTSTOP: Power off a running instance", file=sys.stderr)
    print("     - RESET/SOFTRESET: Restart an instance", file=sys.stderr)
    print("   Database Actions:", file=sys.stderr)
    print("     - START: Power on a stopped database system", file=sys.stderr)
    print("     - STOP: Power off a running database system", file=sys.stderr)
    print("", file=sys.stderr)
    
    # Run the FastMCP server
    mcp.run()