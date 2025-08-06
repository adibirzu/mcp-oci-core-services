#!/usr/bin/env python3
"""
OCI Core Services FastMCP Server

A dedicated FastMCP server for Oracle Cloud Infrastructure Core Services including:
- Compute instance management and listing
- Network interface (VNIC) information
- Instance lifecycle operations (start, stop, restart)
- Detailed instance configurations
- Database system management (regular DB systems)
- Autonomous Database management and operations
- Autonomous Database scaling and lifecycle operations
- Connection testing and service validation

Uses official OCI Python SDK with CLI fallback for maximum compatibility.
Returns LLM-friendly JSON responses with human-readable summaries.

Prerequisites:
- OCI CLI installed and configured
- OCI config file at ~/.oci/config
- OCI Python SDK installed
- Appropriate OCI permissions for core services (compute, database, networking)
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

# Configure logging - disable for MCP protocol compatibility
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
            
            # Initialization successful (logging disabled for MCP compatibility)
            pass
            
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
    
    async def list_autonomous_databases_sdk(self, compartment_id: str, lifecycle_state: str = None, db_workload: str = None) -> List[Dict]:
        """List autonomous databases using OCI Python SDK"""
        if not self.database_client:
            raise Exception("OCI Database SDK not available")
        
        try:
            logger.info(f"Listing autonomous databases - Compartment: {compartment_id}, State: {lifecycle_state or 'ALL'}, Workload: {db_workload or 'ALL'}")
            
            # Build parameters
            list_params = {'compartment_id': compartment_id}
            if lifecycle_state:
                list_params['lifecycle_state'] = lifecycle_state
            if db_workload:
                list_params['db_workload'] = db_workload
                
            response = self.database_client.list_autonomous_databases(**list_params)
            
            autonomous_dbs = []
            for adb in response.data:
                adb_data = {
                    'id': adb.id,
                    'display_name': adb.display_name,
                    'db_name': adb.db_name,
                    'lifecycle_state': adb.lifecycle_state,
                    'lifecycle_details': adb.lifecycle_details,
                    'db_workload': adb.db_workload,
                    'db_version': adb.db_version,
                    'compute_model': adb.compute_model,
                    'compute_count': adb.compute_count,
                    'cpu_core_count': adb.cpu_core_count,
                    'data_storage_size_in_tbs': adb.data_storage_size_in_tbs,
                    'data_storage_size_in_gbs': adb.data_storage_size_in_gbs,
                    'is_auto_scaling_enabled': adb.is_auto_scaling_enabled,
                    'is_auto_scaling_for_storage_enabled': adb.is_auto_scaling_for_storage_enabled,
                    'is_free_tier': adb.is_free_tier,
                    'license_model': adb.license_model,
                    'whitelisted_ips': adb.whitelisted_ips or [],
                    'time_created': adb.time_created.isoformat() if adb.time_created else None,
                    'compartment_id': adb.compartment_id,
                    'connection_urls': {
                        'sql_dev_web_url': adb.connection_urls.sql_dev_web_url if adb.connection_urls else None,
                        'apex_url': adb.connection_urls.apex_url if adb.connection_urls else None,
                        'graph_studio_url': adb.connection_urls.graph_studio_url if adb.connection_urls else None,
                        'mongo_db_url': adb.connection_urls.mongo_db_url if adb.connection_urls else None,
                        'ords_url': adb.connection_urls.ords_url if adb.connection_urls else None
                    } if adb.connection_urls else {},
                    'service_console_url': adb.service_console_url,
                    'is_refreshable_clone': adb.is_refreshable_clone,
                    'refreshable_status': adb.refreshable_status,
                    'refreshable_mode': adb.refreshable_mode,
                    'time_of_last_refresh': adb.time_of_last_refresh.isoformat() if adb.time_of_last_refresh else None,
                    'tags': {
                        'freeform': adb.freeform_tags or {},
                        'defined': adb.defined_tags or {}
                    }
                }
                autonomous_dbs.append(adb_data)
            
            logger.info(f"✅ Found {len(autonomous_dbs)} autonomous databases via SDK")
            return autonomous_dbs
            
        except Exception as e:
            logger.error(f"Autonomous Database SDK failed: {e}")
            raise
    
    async def get_autonomous_database_details_sdk(self, autonomous_database_id: str) -> Dict:
        """Get detailed autonomous database information using OCI Python SDK"""
        if not self.database_client:
            raise Exception("OCI Database SDK not available")
        
        try:
            logger.info(f"Getting autonomous database details via SDK: {autonomous_database_id}")
            
            response = self.database_client.get_autonomous_database(autonomous_database_id=autonomous_database_id)
            adb = response.data
            
            adb_details = {
                'id': adb.id,
                'display_name': adb.display_name,
                'db_name': adb.db_name,
                'lifecycle_state': adb.lifecycle_state,
                'lifecycle_details': adb.lifecycle_details,
                'db_workload': adb.db_workload,
                'db_version': adb.db_version,
                'character_set': adb.character_set,
                'ncharacter_set': adb.ncharacter_set,
                
                # Compute and storage
                'compute_model': adb.compute_model,
                'compute_count': adb.compute_count,
                'cpu_core_count': adb.cpu_core_count,
                'data_storage_size_in_tbs': adb.data_storage_size_in_tbs,
                'data_storage_size_in_gbs': adb.data_storage_size_in_gbs,
                'provisionable_cpus': adb.provisionable_cpus or [],
                
                # Features and configuration
                'is_auto_scaling_enabled': adb.is_auto_scaling_enabled,
                'is_auto_scaling_for_storage_enabled': adb.is_auto_scaling_for_storage_enabled,
                'is_free_tier': adb.is_free_tier,
                'license_model': adb.license_model,
                'whitelisted_ips': adb.whitelisted_ips or [],
                'are_primary_whitelisted_ips_used': adb.are_primary_whitelisted_ips_used,
                
                # Connectivity
                'connection_strings': adb.connection_strings.__dict__ if adb.connection_strings else {},
                'connection_urls': adb.connection_urls.__dict__ if adb.connection_urls else {},
                'service_console_url': adb.service_console_url,
                
                # Timing information
                'time_created': adb.time_created.isoformat() if adb.time_created else None,
                'time_maintenance_begin': adb.time_maintenance_begin.isoformat() if adb.time_maintenance_begin else None,
                'time_maintenance_end': adb.time_maintenance_end.isoformat() if adb.time_maintenance_end else None,
                'time_deletion_of_free_autonomous_database': adb.time_deletion_of_free_autonomous_database.isoformat() if adb.time_deletion_of_free_autonomous_database else None,
                
                # Security
                'vault_id': adb.vault_id,
                'kms_key_id': adb.kms_key_id,
                'encryption_key': adb.encryption_key.__dict__ if adb.encryption_key else {},
                
                # Backup and DR
                'backup_retention_period_in_days': adb.backup_retention_period_in_days,
                'backup_config': adb.backup_config.__dict__ if adb.backup_config else {},
                'disaster_recovery_region_type': adb.disaster_recovery_region_type,
                'standby_lag_time_in_seconds': adb.standby_lag_time_in_seconds,
                'role': adb.role,
                'dataguard_region_type': adb.dataguard_region_type,
                'peer_db_ids': adb.peer_db_ids or [],
                
                # Clone information
                'is_refreshable_clone': adb.is_refreshable_clone,
                'refreshable_status': adb.refreshable_status,
                'refreshable_mode': adb.refreshable_mode,
                'time_of_last_refresh': adb.time_of_last_refresh.isoformat() if adb.time_of_last_refresh else None,
                'time_of_last_refresh_point': adb.time_of_last_refresh_point.isoformat() if adb.time_of_last_refresh_point else None,
                'time_of_next_refresh': adb.time_of_next_refresh.isoformat() if adb.time_of_next_refresh else None,
                
                # Advanced features
                'supported_regions_to_clone_to': adb.supported_regions_to_clone_to or [],
                'customer_contacts': [contact.__dict__ for contact in adb.customer_contacts] if adb.customer_contacts else [],
                
                # Metadata
                'compartment_id': adb.compartment_id,
                'tags': {
                    'freeform': adb.freeform_tags or {},
                    'defined': adb.defined_tags or {},
                    'system': adb.system_tags or {}
                }
            }
            
            logger.info(f"✅ Retrieved autonomous database details via SDK")
            return adb_details
            
        except Exception as e:
            logger.error(f"Autonomous Database details SDK failed: {e}")
            raise
    
    async def autonomous_database_action_sdk(self, autonomous_database_id: str, action: str) -> Dict:
        """Perform autonomous database lifecycle action using OCI Python SDK"""
        if not self.database_client:
            raise Exception("OCI Database SDK not available")
        
        valid_actions = ["START", "STOP", "RESTART"]
        if action.upper() not in valid_actions:
            raise Exception(f"Invalid autonomous database action '{action}'. Valid actions: {', '.join(valid_actions)}")
        
        try:
            logger.info(f"Performing {action} action on autonomous database {autonomous_database_id}")
            
            # Get current autonomous database details first
            adb_response = self.database_client.get_autonomous_database(autonomous_database_id=autonomous_database_id)
            adb = adb_response.data
            current_state = adb.lifecycle_state
            
            logger.info(f"Autonomous database '{adb.display_name}' current state: {current_state}")
            
            # Perform the action
            if action.upper() == "START":
                response = self.database_client.start_autonomous_database(autonomous_database_id=autonomous_database_id)
            elif action.upper() == "STOP":
                response = self.database_client.stop_autonomous_database(autonomous_database_id=autonomous_database_id)
            elif action.upper() == "RESTART":
                response = self.database_client.restart_autonomous_database(autonomous_database_id=autonomous_database_id)
            
            # Get work request information
            work_request_id = response.headers.get('opc-work-request-id')
            if work_request_id:
                logger.info(f"Autonomous database action initiated with work request ID: {work_request_id}")
            
            action_result = {
                'autonomous_database_id': autonomous_database_id,
                'database_name': adb.display_name,
                'db_name': adb.db_name,
                'action': action.upper(),
                'previous_state': current_state,
                'work_request_id': work_request_id,
                'request_id': response.headers.get('opc-request-id'),
                'initiated_at': datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"✅ Autonomous database {action} action initiated successfully")
            return action_result
            
        except Exception as e:
            logger.error(f"Autonomous database action failed: {e}")
            raise
    
    async def scale_autonomous_database_sdk(self, autonomous_database_id: str, **scale_params) -> Dict:
        """Scale autonomous database compute and storage using OCI Python SDK"""
        if not self.database_client:
            raise Exception("OCI Database SDK not available")
        
        try:
            # Get current autonomous database details
            adb_response = self.database_client.get_autonomous_database(autonomous_database_id=autonomous_database_id)
            adb = adb_response.data
            
            # Import the model class here to avoid import issues
            from oci.database.models import UpdateAutonomousDatabaseDetails
            
            # Build update details
            update_details = UpdateAutonomousDatabaseDetails()
            
            changes = []
            if 'compute_count' in scale_params and scale_params['compute_count'] is not None:
                update_details.compute_count = scale_params['compute_count']
                changes.append(f"ECPU: {scale_params['compute_count']}")
            
            if 'cpu_core_count' in scale_params and scale_params['cpu_core_count'] is not None:
                update_details.cpu_core_count = scale_params['cpu_core_count']
                changes.append(f"OCPU: {scale_params['cpu_core_count']}")
            
            if 'data_storage_size_in_tbs' in scale_params and scale_params['data_storage_size_in_tbs'] is not None:
                update_details.data_storage_size_in_tbs = scale_params['data_storage_size_in_tbs']
                changes.append(f"Storage: {scale_params['data_storage_size_in_tbs']}TB")
            
            if 'is_auto_scaling_enabled' in scale_params and scale_params['is_auto_scaling_enabled'] is not None:
                update_details.is_auto_scaling_enabled = scale_params['is_auto_scaling_enabled']
                changes.append(f"Auto-scaling: {'enabled' if scale_params['is_auto_scaling_enabled'] else 'disabled'}")
            
            if 'is_auto_scaling_for_storage_enabled' in scale_params and scale_params['is_auto_scaling_for_storage_enabled'] is not None:
                update_details.is_auto_scaling_for_storage_enabled = scale_params['is_auto_scaling_for_storage_enabled']
                changes.append(f"Storage auto-scaling: {'enabled' if scale_params['is_auto_scaling_for_storage_enabled'] else 'disabled'}")
            
            if not changes:
                raise Exception("No scaling parameters provided")
            
            logger.info(f"Scaling autonomous database {autonomous_database_id}: {', '.join(changes)}")
            
            # Perform the update
            response = self.database_client.update_autonomous_database(
                autonomous_database_id=autonomous_database_id,
                update_autonomous_database_details=update_details
            )
            
            # Get work request information
            work_request_id = response.headers.get('opc-work-request-id')
            if work_request_id:
                logger.info(f"Autonomous database scaling initiated with work request ID: {work_request_id}")
            
            action_result = {
                'autonomous_database_id': autonomous_database_id,
                'database_name': adb.display_name,
                'db_name': adb.db_name,
                'action': 'SCALE',
                'changes': changes,
                'work_request_id': work_request_id,
                'request_id': response.headers.get('opc-request-id'),
                'initiated_at': datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"✅ Autonomous database scaling action initiated successfully")
            return action_result
            
        except Exception as e:
            logger.error(f"Autonomous database scaling failed: {e}")
            raise
    
    async def get_autonomous_database_state_sdk(self, autonomous_database_id: str) -> Dict:
        """Get current state of an autonomous database using OCI Python SDK"""
        if not self.database_client:
            raise Exception("OCI Database SDK not available")
        
        try:
            response = self.database_client.get_autonomous_database(autonomous_database_id=autonomous_database_id)
            adb = response.data
            
            state_info = {
                'autonomous_database_id': autonomous_database_id,
                'database_name': adb.display_name,
                'db_name': adb.db_name,
                'lifecycle_state': adb.lifecycle_state,
                'lifecycle_details': adb.lifecycle_details,
                'db_workload': adb.db_workload,
                'compute_model': adb.compute_model,
                'compute_count': adb.compute_count,
                'cpu_core_count': adb.cpu_core_count,
                'data_storage_size_in_tbs': adb.data_storage_size_in_tbs,
                'is_auto_scaling_enabled': adb.is_auto_scaling_enabled,
                'is_free_tier': adb.is_free_tier,
                'compartment_id': adb.compartment_id,
                'time_created': adb.time_created.isoformat() if adb.time_created else None,
                'retrieved_at': datetime.utcnow().isoformat() + "Z"
            }
            
            return state_info
            
        except Exception as e:
            logger.error(f"Failed to get autonomous database state: {e}")
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
async def list_autonomous_databases(compartment_id: str = None, lifecycle_state: str = None, db_workload: str = None) -> Dict[str, Any]:
    """
    List autonomous databases in the compartment.
    
    Args:
        compartment_id: OCI compartment ID (uses default if not provided)
        lifecycle_state: Filter by lifecycle state (AVAILABLE, STOPPED, etc.)
        db_workload: Filter by workload type (OLTP, DW, AJD, APEX)
    
    Returns:
        LLM-friendly JSON with autonomous databases list
    """
    try:
        target_compartment = compartment_id or core_manager.get_compartment_id()
        if not target_compartment:
            raise Exception("Compartment ID is required")
        
        if core_manager.database_client:
            autonomous_dbs = await core_manager.list_autonomous_databases_sdk(target_compartment, lifecycle_state, db_workload)
            method = "OCI Python SDK"
        else:
            raise Exception("Autonomous database listing requires OCI SDK")
        
        # Create LLM-friendly response
        filters_desc = []
        if lifecycle_state:
            filters_desc.append(f"state: {lifecycle_state}")
        if db_workload:
            filters_desc.append(f"workload: {db_workload}")
        
        filter_text = f" ({', '.join(filters_desc)})" if filters_desc else ""
        summary = f"Found {len(autonomous_dbs)} autonomous databases{filter_text} in {core_manager.config.get('region', 'unknown region') if core_manager.config else 'unknown region'}"
        
        response = {
            "success": True,
            "summary": summary,
            "count": len(autonomous_dbs),
            "method": method,
            "filters": {
                "compartment_id": target_compartment,
                "lifecycle_state": lifecycle_state,
                "db_workload": db_workload
            },
            "autonomous_databases": autonomous_dbs,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing autonomous databases: {e}")
        return {
            "success": False,
            "summary": f"Failed to list autonomous databases: {str(e)}",
            "count": 0,
            "method": "Error",
            "autonomous_databases": [],
            "error": str(e),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def get_autonomous_database_details(autonomous_database_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific autonomous database.
    
    Args:
        autonomous_database_id: Autonomous Database OCID
    
    Returns:
        LLM-friendly JSON with comprehensive autonomous database details
    """
    try:
        if core_manager.database_client:
            adb_details = await core_manager.get_autonomous_database_details_sdk(autonomous_database_id)
            method = "OCI Python SDK"
        else:
            raise Exception("Autonomous database details require OCI SDK")
        
        # Create LLM-friendly response
        workload_names = {
            'OLTP': 'Transaction Processing',
            'DW': 'Data Warehouse',
            'AJD': 'JSON Database',
            'APEX': 'APEX Application Development'
        }
        workload_desc = workload_names.get(adb_details['db_workload'], adb_details['db_workload'])
        
        compute_desc = f"{adb_details['compute_count']} ECPUs" if adb_details['compute_model'] == 'ECPU' else f"{adb_details['cpu_core_count']} OCPUs"
        
        summary = f"Autonomous Database '{adb_details['display_name']}' ({workload_desc}) is {adb_details['lifecycle_state'].lower()} with {compute_desc} and {adb_details['data_storage_size_in_tbs']}TB storage"
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "autonomous_database": adb_details,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting autonomous database details: {e}")
        return {
            "success": False,
            "summary": f"Failed to get autonomous database details: {str(e)}",
            "method": "Error",
            "autonomous_database": {},
            "error": str(e),
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def start_autonomous_database(autonomous_database_id: str) -> Dict[str, Any]:
    """
    Start a stopped autonomous database.
    
    Args:
        autonomous_database_id: Autonomous Database OCID
    
    Returns:
        LLM-friendly JSON with action result and status
    """
    try:
        if core_manager.database_client:
            action_result = await core_manager.autonomous_database_action_sdk(autonomous_database_id, "START")
            method = "OCI Python SDK"
            
            summary = f"Start action initiated for autonomous database '{action_result['database_name']}' (was {action_result['previous_state']})"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Autonomous database lifecycle actions require OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error starting autonomous database: {e}")
        return {
            "success": False,
            "summary": f"Failed to start autonomous database: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def stop_autonomous_database(autonomous_database_id: str) -> Dict[str, Any]:
    """
    Stop a running autonomous database.
    
    Args:
        autonomous_database_id: Autonomous Database OCID
    
    Returns:
        LLM-friendly JSON with action result and status
    """
    try:
        if core_manager.database_client:
            action_result = await core_manager.autonomous_database_action_sdk(autonomous_database_id, "STOP")
            method = "OCI Python SDK"
            
            summary = f"Stop action initiated for autonomous database '{action_result['database_name']}' (was {action_result['previous_state']})"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Autonomous database lifecycle actions require OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error stopping autonomous database: {e}")
        return {
            "success": False,
            "summary": f"Failed to stop autonomous database: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def restart_autonomous_database(autonomous_database_id: str) -> Dict[str, Any]:
    """
    Restart an autonomous database.
    
    Args:
        autonomous_database_id: Autonomous Database OCID
    
    Returns:
        LLM-friendly JSON with action result and status
    """
    try:
        if core_manager.database_client:
            action_result = await core_manager.autonomous_database_action_sdk(autonomous_database_id, "RESTART")
            method = "OCI Python SDK"
            
            summary = f"Restart action initiated for autonomous database '{action_result['database_name']}' (was {action_result['previous_state']})"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Autonomous database lifecycle actions require OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error restarting autonomous database: {e}")
        return {
            "success": False,
            "summary": f"Failed to restart autonomous database: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def scale_autonomous_database(
    autonomous_database_id: str, 
    compute_count: float = None, 
    cpu_core_count: int = None, 
    data_storage_size_in_tbs: int = None,
    is_auto_scaling_enabled: bool = None,
    is_auto_scaling_for_storage_enabled: bool = None
) -> Dict[str, Any]:
    """
    Scale compute and storage for an autonomous database.
    
    Args:
        autonomous_database_id: Autonomous Database OCID
        compute_count: ECPU count (for ECPU model, recommended)
        cpu_core_count: CPU core count (for OCPU model, legacy)
        data_storage_size_in_tbs: Storage size in TB
        is_auto_scaling_enabled: Enable/disable auto-scaling for compute
        is_auto_scaling_for_storage_enabled: Enable/disable auto-scaling for storage
    
    Returns:
        LLM-friendly JSON with scaling action result
    """
    try:
        if core_manager.database_client:
            scale_params = {}
            if compute_count is not None:
                scale_params['compute_count'] = compute_count
            if cpu_core_count is not None:
                scale_params['cpu_core_count'] = cpu_core_count
            if data_storage_size_in_tbs is not None:
                scale_params['data_storage_size_in_tbs'] = data_storage_size_in_tbs
            if is_auto_scaling_enabled is not None:
                scale_params['is_auto_scaling_enabled'] = is_auto_scaling_enabled
            if is_auto_scaling_for_storage_enabled is not None:
                scale_params['is_auto_scaling_for_storage_enabled'] = is_auto_scaling_for_storage_enabled
            
            action_result = await core_manager.scale_autonomous_database_sdk(autonomous_database_id, **scale_params)
            method = "OCI Python SDK"
            
            summary = f"Scaling action initiated for autonomous database '{action_result['database_name']}': {', '.join(action_result['changes'])}"
            if action_result['work_request_id']:
                summary += f" - Work Request: {action_result['work_request_id']}"
        else:
            raise Exception("Autonomous database scaling requires OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "action_details": action_result,
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error scaling autonomous database: {e}")
        return {
            "success": False,
            "summary": f"Failed to scale autonomous database: {str(e)}",
            "method": "Error",
            "action_details": {},
            "error": str(e),
            "initiated_at": datetime.utcnow().isoformat() + "Z"
        }

@mcp.tool()
async def get_autonomous_database_state(autonomous_database_id: str) -> Dict[str, Any]:
    """
    Get the current lifecycle state of an autonomous database.
    
    Args:
        autonomous_database_id: Autonomous Database OCID
    
    Returns:
        LLM-friendly JSON with current autonomous database state
    """
    try:
        if core_manager.database_client:
            state_info = await core_manager.get_autonomous_database_state_sdk(autonomous_database_id)
            method = "OCI Python SDK"
            
            workload_names = {
                'OLTP': 'Transaction Processing',
                'DW': 'Data Warehouse', 
                'AJD': 'JSON Database',
                'APEX': 'APEX Application Development'
            }
            workload_desc = workload_names.get(state_info['db_workload'], state_info['db_workload'])
            
            summary = f"Autonomous Database '{state_info['database_name']}' ({workload_desc}) is currently {state_info['lifecycle_state']}"
        else:
            raise Exception("Autonomous database state check requires OCI SDK")
        
        response = {
            "success": True,
            "summary": summary,
            "method": method,
            "state_info": state_info,
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting autonomous database state: {e}")
        return {
            "success": False,
            "summary": f"Failed to get autonomous database state: {str(e)}",
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
        
        # Test autonomous database service
        if core_manager.database_client:
            try:
                compartment_id = core_manager.get_compartment_id()
                if compartment_id:
                    autonomous_dbs = await core_manager.list_autonomous_databases_sdk(compartment_id)
                    results['tests']['autonomous_database_service'] = {
                        'status': 'success',
                        'message': f'Autonomous Database service accessible - found {len(autonomous_dbs)} autonomous databases',
                        'autonomous_db_count': len(autonomous_dbs)
                    }
                else:
                    results['tests']['autonomous_database_service'] = {
                        'status': 'warning',
                        'message': 'Autonomous Database client available but no compartment ID configured'
                    }
            except Exception as e:
                results['tests']['autonomous_database_service'] = {
                    'status': 'failed',
                    'message': f'Autonomous Database service test failed: {str(e)[:100]}...'
                }
        else:
            results['tests']['autonomous_database_service'] = {
                'status': 'failed',
                'message': 'Autonomous Database client not available'
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
    # Run the FastMCP server (startup info disabled for MCP protocol compatibility)
    mcp.run()