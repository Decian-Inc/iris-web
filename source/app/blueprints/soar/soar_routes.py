#  IRIS Source Code
#  Copyright (C) 2025 - DFIR-IRIS
#  contact@dfir-iris.org
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import traceback
import requests
import uuid
import os
import json
import time
import zipfile
from datetime import datetime
from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from flask import redirect
from flask import url_for
from flask_login import current_user, login_required

from app import db
from app.datamgmt.case.case_db import get_case
from app.models import Cases
from app.models.authorization import CaseAccessLevel
from app.util import response_success, response_error, ac_api_case_requires
from app.blueprints.manage.manage_integrations.manage_integrations_routes import get_integrations_config

soar_blueprint = Blueprint('soar',
                          __name__,
                          template_folder='templates')


@soar_blueprint.route('/soar', methods=['GET'])
@login_required
def soar_index():
    """
    Main SOAR page - job orchestration and management interface
    """
    print("DEBUG: SOAR route HIT!")
    try:
        caseid = request.args.get('cid', default=1, type=int)

        case = get_case(caseid)
        if not case:
            return response_error("Case not found")

        # Get all cases for the switcher dropdown
        all_cases = Cases.query.filter(Cases.case_id != None).order_by(Cases.case_id.asc()).all()

        return render_template('soar.html',
                             case=case,
                             case_id=caseid,
                             all_cases=all_cases)

    except Exception as e:
        traceback.print_exc()
        return response_error(f"An error occurred: {str(e)}")


@soar_blueprint.route('/soar/templates', methods=['GET'])
@login_required
def soar_templates_list():
    """
    API endpoint to list available SOAR job templates
    """
    try:
        # TODO: Implement job template retrieval from database
        # For now, return sample templates based on the spec
        templates = [
            {
                "id": "sentinel1-quarantine",
                "name": "SentinelOne Network Quarantine",
                "description": "Isolate an endpoint from the network to prevent lateral movement",
                "vendor": "SentinelOne",
                "tags": ["containment", "isolation"],
                "requires_approval": True,
                "allowed_target_types": ["agent_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-13T00:00:00Z"
            },
            {
                "id": "sentinel1-fetch-apps",
                "name": "SentinelOne Fetch Installed Applications",
                "description": "Retrieve list of installed applications from endpoint",
                "vendor": "SentinelOne",
                "tags": ["forensics", "inventory"],
                "requires_approval": False,
                "allowed_target_types": ["agent_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-13T00:00:00Z"
            },
            {
                "id": "sentinel1-fetch-logs",
                "name": "SentinelOne Fetch Endpoint Logs",
                "description": "Collect endpoint logs for evidence gathering",
                "vendor": "SentinelOne",
                "tags": ["forensics", "logs"],
                "requires_approval": False,
                "allowed_target_types": ["agent_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-13T00:00:00Z"
            },
            {
                "id": "sentinel1-full-scan",
                "name": "SentinelOne Full Disk Scan",
                "description": "Initiate a complete disk scan on the endpoint",
                "vendor": "SentinelOne",
                "tags": ["scanning", "detection"],
                "requires_approval": False,
                "allowed_target_types": ["agent_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-13T00:00:00Z"
            },
            {
                "id": "velociraptor-collect",
                "name": "Velociraptor Forensic Collection",
                "description": "Collect forensic artifacts using Velociraptor",
                "vendor": "Velociraptor",
                "tags": ["forensics"],
                "requires_approval": False,
                "allowed_target_types": ["client_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-13T00:00:00Z"
            }
        ]

        return response_success("Templates retrieved successfully", data=templates)

    except Exception as e:
        traceback.print_exc()
        return response_error(f"Failed to retrieve templates: {str(e)}")


@soar_blueprint.route('/soar/jobs', methods=['GET'])
@ac_api_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def soar_jobs_list(caseid):
    """
    API endpoint to list SOAR jobs for the current case
    """
    try:
        # TODO: Implement job retrieval from database
        # For now, return sample jobs
        jobs = [
            {
                "job_id": "job-123",
                "template_id": "sentinel1-quarantine",
                "template_name": "SentinelOne Quarantine Host",
                "status": "Completed",
                "executor": current_user.name,
                "start_time": "2025-10-13T10:00:00Z",
                "end_time": "2025-10-13T10:05:30Z",
                "target": "agent-456789",
                "artifacts_count": 2
            }
        ]

        return response_success("Jobs retrieved successfully", data=jobs)

    except Exception as e:
        traceback.print_exc()
        return response_error(f"Failed to retrieve jobs: {str(e)}")


@soar_blueprint.route('/soar/test', methods=['GET'])
@login_required
def soar_test():
    """Test route to verify routing is working"""
    with open('/tmp/soar_debug.log', 'a') as f:
        f.write(f"[{datetime.now()}] soar_test route called!\n")
    return jsonify({"status": "success", "message": "Test route working"})

@soar_blueprint.route('/soar/jobs', methods=['POST'])
@ac_api_case_requires(CaseAccessLevel.full_access)
def soar_jobs_create(caseid):
    """
    API endpoint to create and execute a SOAR job
    """
    try:
        # File-based debugging to trace execution
        with open('/tmp/soar_debug.log', 'a') as f:
            f.write(f"[{datetime.now()}] soar_jobs_create called!\n")

        print("DEBUG: soar_jobs_create called!")
        data = request.get_json()

        with open('/tmp/soar_debug.log', 'a') as f:
            f.write(f"[{datetime.now()}] Request data: {data}\n")

        print(f"DEBUG: Request data: {data}")

        # Validate required fields
        required_fields = ['template_id', 'target']
        for field in required_fields:
            if field not in data:
                return response_error(f"Missing required field: {field}")

        template_id = data.get('template_id')
        target = data.get('target')
        case_id = caseid

        # Generate unique job ID
        job_id = f"job-{uuid.uuid4().hex[:8]}"

        # Get integration settings
        integrations_config = get_integrations_config()

        # Execute the job based on template type
        job_result = execute_soar_job(job_id, template_id, target, case_id, integrations_config)

        return response_success("Job created successfully", data=job_result)

    except Exception as e:
        traceback.print_exc()
        return response_error(f"Failed to create job: {str(e)}")


@soar_blueprint.route('/soar/jobs/<job_id>', methods=['GET'])
@ac_api_case_requires(CaseAccessLevel.read_only, CaseAccessLevel.full_access)
def soar_job_detail(job_id, caseid):
    """
    API endpoint to get detailed information about a specific job
    """
    try:
        # TODO: Implement job detail retrieval from database
        # For now, return mock data
        job_detail = {
            "job_id": job_id,
            "template_id": "sentinel1-quarantine",
            "template_name": "SentinelOne Quarantine Host",
            "status": "Completed",
            "executor": current_user.name,
            "case_id": request.args.get('cid', default=1, type=int),
            "start_time": "2025-10-13T10:00:00Z",
            "end_time": "2025-10-13T10:05:30Z",
            "target": "agent-456789",
            "steps": [
                {
                    "step_id": "step1",
                    "name": "Quarantine Host",
                    "status": "Completed",
                    "start_time": "2025-10-13T10:00:00Z",
                    "end_time": "2025-10-13T10:03:00Z"
                },
                {
                    "step_id": "step2",
                    "name": "Collect Logs",
                    "status": "Completed",
                    "start_time": "2025-10-13T10:03:00Z",
                    "end_time": "2025-10-13T10:05:30Z"
                }
            ],
            "artifacts": [
                {
                    "name": "quarantine_log.json",
                    "type": "json",
                    "size": "2.1 KB",
                    "url": f"/api/soar/jobs/{job_id}/artifacts/quarantine_log.json"
                },
                {
                    "name": "system_logs.zip",
                    "type": "archive",
                    "size": "15.3 MB",
                    "url": f"/api/soar/jobs/{job_id}/artifacts/system_logs.zip"
                }
            ]
        }

        return response_success("Job details retrieved successfully", data=job_detail)

    except Exception as e:
        traceback.print_exc()
        return response_error(f"Failed to retrieve job details: {str(e)}")


def execute_soar_job(job_id, template_id, target, case_id, integrations_config):
    """
    Execute a SOAR job based on the template type using integration settings
    """
    try:
        print(f"DEBUG: execute_soar_job called with template_id={template_id}, target={target}")
        print(f"DEBUG: integrations_config={integrations_config}")

        start_time = datetime.now().isoformat() + "Z"
        template_name = get_template_name(template_id)

        # Determine integration type from template
        if template_id.startswith('sentinel'):
            integration_type = 'sentinelone'
            config = integrations_config.get('sentinelone', {})
        elif template_id.startswith('velociraptor'):
            integration_type = 'velociraptor'
            config = integrations_config.get('velociraptor', {})
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "Unknown template type",
                "error": f"Template {template_id} not recognized"
            }

        # Check if integration is enabled and configured
        with open('/tmp/soar_debug.log', 'a') as f:
            f.write(f"[{datetime.now()}] checking enabled status for {integration_type}, config={config}\n")
            f.write(f"[{datetime.now()}] config.get('enabled', False)={config.get('enabled', False)}\n")

        print(f"DEBUG: checking enabled status for {integration_type}, config={config}")
        print(f"DEBUG: config.get('enabled', False)={config.get('enabled', False)}")

        if not config.get('enabled', False):
            with open('/tmp/soar_debug.log', 'a') as f:
                f.write(f"[{datetime.now()}] Integration {integration_type} is not enabled, returning failure\n")
            print(f"DEBUG: Integration {integration_type} is not enabled, returning failure")
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"{integration_type.capitalize()} integration is not enabled - Please configure it in Manage > Integrations",
                "error": "Integration disabled - API credentials required"
            }

        # Validate required configuration
        if integration_type == 'sentinelone':
            base_url = config.get('base_url', '').strip()
            api_token = config.get('api_token', '').strip()
            if not base_url or not api_token:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": "SentinelOne API credentials missing - Configure URL and API token in Manage > Integrations",
                    "error": "Missing base_url or api_token - Cannot connect to SentinelOne API"
                }
        elif integration_type == 'velociraptor':
            base_url = config.get('base_url', '').strip()
            api_key = config.get('api_key', '').strip()
            if not base_url or not api_key:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": "Velociraptor API credentials missing - Configure URL and API key in Manage > Integrations",
                    "error": "Missing base_url or api_key - Cannot connect to Velociraptor API"
                }

        # Execute the specific job type
        if template_id == 'sentinel1-quarantine':
            result = execute_sentinelone_quarantine(job_id, target, config, case_id)
        elif template_id == 'sentinel1-fetch-apps':
            result = execute_sentinelone_fetch_apps(job_id, target, config, case_id)
        elif template_id == 'sentinel1-fetch-logs':
            result = execute_sentinelone_fetch_logs(job_id, target, config, case_id)
        elif template_id == 'sentinel1-full-scan':
            result = execute_sentinelone_full_scan(job_id, target, config, case_id)
        elif template_id == 'velociraptor-collect':
            result = execute_velociraptor_collect(job_id, target, config)
        else:
            result = {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Template {template_id} execution not implemented",
                "error": "Template execution logic not found"
            }

        return result

    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Job execution failed: {str(e)}",
            "error": str(e)
        }


def get_template_name(template_id):
    """
    Get the display name for a template ID
    """
    template_names = {
        'sentinel1-quarantine': 'SentinelOne Network Quarantine',
        'sentinel1-fetch-apps': 'SentinelOne Fetch Installed Applications',
        'sentinel1-fetch-logs': 'SentinelOne Fetch Endpoint Logs',
        'sentinel1-full-scan': 'SentinelOne Full Disk Scan',
        'velociraptor-collect': 'Velociraptor Forensic Collection'
    }
    return template_names.get(template_id, template_id)


def create_case_artifact_folder(case_id):
    """
    Create the artifacts folder structure for a case
    """
    try:
        artifact_path = f"/home/iris/server_data/cases/{case_id}/artifacts/sentinelone"
        os.makedirs(artifact_path, exist_ok=True)
        return artifact_path
    except Exception as e:
        print(f"Error creating artifact folder: {str(e)}")
        return None


def save_case_artifact(case_id, filename, data):
    """
    Save artifact data to case folder
    """
    try:
        artifact_path = create_case_artifact_folder(case_id)
        if not artifact_path:
            return None

        file_path = os.path.join(artifact_path, filename)

        if isinstance(data, dict):
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        elif isinstance(data, bytes):
            with open(file_path, 'wb') as f:
                f.write(data)
        else:
            with open(file_path, 'w') as f:
                f.write(str(data))

        return file_path
    except Exception as e:
        print(f"Error saving artifact: {str(e)}")
        return None


def add_case_note(case_id, note_content):
    """
    Add a note to the case (placeholder - would integrate with IRIS notes system)
    """
    try:
        # TODO: Integrate with actual IRIS notes API
        print(f"Case {case_id} Note: {note_content}")
        return True
    except Exception as e:
        print(f"Error adding case note: {str(e)}")
        return False


def execute_sentinelone_quarantine(job_id, target, config, case_id):
    """
    Execute SentinelOne quarantine job
    """
    try:
        base_url = config.get('base_url').rstrip('/')
        api_token = config.get('api_token')
        verify_ssl = config.get('verify_ssl', True)

        headers = {
            'Authorization': f'ApiToken {api_token}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find agent by hostname or agent ID
        if target.startswith('agent-'):
            agent_id = target.replace('agent-', '')
            agents_endpoint = f'{base_url}/web/api/v2.1/agents/{agent_id}'
        else:
            # Search by hostname
            agents_endpoint = f'{base_url}/web/api/v2.1/agents'
            params = {'computerName': target, 'limit': 1}

            response = requests.get(agents_endpoint, headers=headers, params=params, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to find agent: {target}",
                    "error": f"SentinelOne API returned status {response.status_code}"
                }

            agents = response.json().get('data', [])
            if not agents:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Agent not found: {target}",
                    "error": "No agents found matching the target hostname"
                }

            agent_id = agents[0]['id']

        # Step 2: Quarantine the agent
        quarantine_endpoint = f'{base_url}/web/api/v2.1/agents/actions/disconnect'
        quarantine_data = {
            'filter': {
                'ids': [agent_id]
            }
        }

        response = requests.post(quarantine_endpoint, headers=headers, json=quarantine_data, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            end_time = datetime.now().isoformat() + "Z"

            # Save quarantine action details as artifact
            quarantine_data = {
                "job_id": job_id,
                "action": "network_quarantine",
                "target": target,
                "agent_id": agent_id,
                "timestamp": end_time,
                "status": "completed",
                "api_response": response.json()
            }

            artifact_filename = f"quarantine_action_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            artifact_path = save_case_artifact(case_id, artifact_filename, quarantine_data)

            # Create case note
            note_content = f"""**SOAR Action:** Network Quarantine
**Endpoint:** {target}
**Timestamp:** {end_time}
**Status:** ✅ Host successfully isolated from network.
_This action prevents all inbound/outbound connections except SentinelOne management._

**Artifact:** `/cases/{case_id}/artifacts/sentinelone/{artifact_filename}`"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully quarantined agent {target}",
                "template_name": "SentinelOne Network Quarantine",
                "target": target,
                "start_time": datetime.now().isoformat() + "Z",
                "end_time": end_time,
                "artifact_path": artifact_path,
                "steps": [
                    {
                        "step_id": "find_agent",
                        "name": "Find Agent",
                        "status": "Completed",
                        "message": f"Found agent ID: {agent_id}"
                    },
                    {
                        "step_id": "quarantine",
                        "name": "Quarantine Agent",
                        "status": "Completed",
                        "message": "Agent successfully quarantined"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved quarantine details to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to quarantine agent: {target}",
                "error": f"SentinelOne API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to SentinelOne: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"SentinelOne quarantine job failed: {str(e)}",
            "error": str(e)
        }


def execute_sentinelone_fetch_apps(job_id, target, config, case_id):
    """
    Execute SentinelOne fetch installed applications playbook
    """
    try:
        base_url = config.get('base_url').rstrip('/')
        api_token = config.get('api_token')
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        headers = {
            'Authorization': f'ApiToken {api_token}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find agent by hostname or agent ID
        if target.startswith('agent-'):
            agent_id = target.replace('agent-', '')
        else:
            # Search by hostname
            agents_endpoint = f'{base_url}/web/api/v2.1/agents'
            params = {'computerName': target, 'limit': 1}

            response = requests.get(agents_endpoint, headers=headers, params=params, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to find agent: {target}",
                    "error": f"SentinelOne API returned status {response.status_code}"
                }

            agents = response.json().get('data', [])
            if not agents:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Agent not found: {target}",
                    "error": "No agents found matching the target hostname"
                }

            agent_id = agents[0]['id']

        # Step 2: Fetch installed applications
        apps_endpoint = f'{base_url}/web/api/v2.1/agents/{agent_id}/installed-applications'
        response = requests.get(apps_endpoint, headers=headers, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            end_time = datetime.now().isoformat() + "Z"
            apps_data = response.json()
            installed_apps = apps_data.get('data', [])

            # Save applications data as artifact
            artifact_filename = f"fetch_installed_apps_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            artifact_path = save_case_artifact(case_id, artifact_filename, {
                "job_id": job_id,
                "action": "fetch_installed_applications",
                "target": target,
                "agent_id": agent_id,
                "timestamp": end_time,
                "total_applications": len(installed_apps),
                "applications": installed_apps
            })

            # Create formatted app list for case note
            app_list = []
            for i, app in enumerate(installed_apps[:20], 1):  # Limit to first 20 for note
                name = app.get('name', 'Unknown')
                version = app.get('version', 'Unknown')
                publisher = app.get('publisher', 'Unknown')
                app_list.append(f"{i}. {name} {version} ({publisher})")

            if len(installed_apps) > 20:
                app_list.append(f"... and {len(installed_apps) - 20} more applications")

            # Create case note
            note_content = f"""**SOAR Action:** Fetch Installed Apps
**Endpoint:** {target}
**Timestamp:** {end_time}
**Results:** Retrieved {len(installed_apps)} applications.

**Installed Apps:**
{chr(10).join(app_list)}

**Artifact:** `/cases/{case_id}/artifacts/sentinelone/{artifact_filename}`"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully retrieved {len(installed_apps)} applications from {target}",
                "template_name": "SentinelOne Fetch Installed Applications",
                "target": target,
                "start_time": start_time,
                "end_time": end_time,
                "artifact_path": artifact_path,
                "applications_count": len(installed_apps),
                "steps": [
                    {
                        "step_id": "find_agent",
                        "name": "Find Agent",
                        "status": "Completed",
                        "message": f"Found agent ID: {agent_id}"
                    },
                    {
                        "step_id": "fetch_apps",
                        "name": "Fetch Applications",
                        "status": "Completed",
                        "message": f"Retrieved {len(installed_apps)} installed applications"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved applications list to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to fetch applications from agent: {target}",
                "error": f"SentinelOne API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to SentinelOne: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"SentinelOne fetch applications job failed: {str(e)}",
            "error": str(e)
        }


def execute_velociraptor_collect(job_id, target, config):
    """
    Execute Velociraptor collection job
    """
    try:
        base_url = config.get('base_url').rstrip('/')
        api_key = config.get('api_key')
        verify_ssl = config.get('verify_ssl', True)

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find client by hostname or client ID
        if target.startswith('client-'):
            client_id = target.replace('client-', '')
        else:
            # Search by hostname
            search_endpoint = f'{base_url}/api/v1/SearchClients'
            search_data = {
                'query': target,
                'limit': 1
            }

            response = requests.post(search_endpoint, headers=headers, json=search_data, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to find client: {target}",
                    "error": f"Velociraptor API returned status {response.status_code}"
                }

            clients = response.json().get('clients', [])
            if not clients:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Client not found: {target}",
                    "error": "No clients found matching the target hostname"
                }

            client_id = clients[0]['client_id']

        # Step 2: Create collection flow
        collect_endpoint = f'{base_url}/api/v1/CollectArtifacts'
        collect_data = {
            'client_id': client_id,
            'artifacts': [
                'Windows.System.ProcessInfo',
                'Windows.Network.Netstat',
                'Windows.Registry.RecentDocs'
            ],
            'specs': [
                {
                    'artifact': 'Windows.System.ProcessInfo'
                },
                {
                    'artifact': 'Windows.Network.Netstat'
                },
                {
                    'artifact': 'Windows.Registry.RecentDocs'
                }
            ]
        }

        response = requests.post(collect_endpoint, headers=headers, json=collect_data, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            flow_info = response.json()
            flow_id = flow_info.get('flow_id', 'unknown')

            return {
                "job_id": job_id,
                "status": "Running",
                "message": f"Collection started for client {target}",
                "template_name": "Velociraptor Forensic Collection",
                "target": target,
                "start_time": datetime.now().isoformat() + "Z",
                "flow_id": flow_id,
                "estimated_duration": "5-10 minutes",
                "steps": [
                    {
                        "step_id": "find_client",
                        "name": "Find Client",
                        "status": "Completed",
                        "message": f"Found client ID: {client_id}"
                    },
                    {
                        "step_id": "start_collection",
                        "name": "Start Collection",
                        "status": "Running",
                        "message": f"Collection flow started: {flow_id}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to start collection for client: {target}",
                "error": f"Velociraptor API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to Velociraptor: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Velociraptor collection job failed: {str(e)}",
            "error": str(e)
        }


def execute_sentinelone_fetch_logs(job_id, target, config, case_id):
    """
    Execute SentinelOne fetch endpoint logs playbook
    """
    try:
        base_url = config.get('base_url').rstrip('/')
        api_token = config.get('api_token')
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        headers = {
            'Authorization': f'ApiToken {api_token}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find agent by hostname or agent ID
        if target.startswith('agent-'):
            agent_id = target.replace('agent-', '')
        else:
            # Search by hostname
            agents_endpoint = f'{base_url}/web/api/v2.1/agents'
            params = {'computerName': target, 'limit': 1}

            response = requests.get(agents_endpoint, headers=headers, params=params, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to find agent: {target}",
                    "error": f"SentinelOne API returned status {response.status_code}"
                }

            agents = response.json().get('data', [])
            if not agents:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Agent not found: {target}",
                    "error": "No agents found matching the target hostname"
                }

            agent_id = agents[0]['id']

        # Step 2: Initiate log fetch
        logs_endpoint = f'{base_url}/web/api/v2.1/agents/actions/fetch-logs'
        logs_data = {
            'filter': {
                'ids': [agent_id]
            },
            'data': {
                'logTypes': ['agent', 'security']
            }
        }

        response = requests.post(logs_endpoint, headers=headers, json=logs_data, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            fetch_response = response.json()
            activity_id = fetch_response.get('data', {}).get('activityId')

            # Poll for completion (simplified - in real implementation would poll properly)
            time.sleep(2)  # Wait a moment for processing

            # Step 3: Check status and get download URL
            status_endpoint = f'{base_url}/web/api/v2.1/activities/{activity_id}'
            status_response = requests.get(status_endpoint, headers=headers, verify=verify_ssl, timeout=30)

            end_time = datetime.now().isoformat() + "Z"

            # Save log fetch details as artifact
            artifact_filename = f"logs_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            logs_data = {
                "job_id": job_id,
                "action": "fetch_endpoint_logs",
                "target": target,
                "agent_id": agent_id,
                "timestamp": end_time,
                "activity_id": activity_id,
                "status": "completed",
                "fetch_response": fetch_response
            }

            artifact_path = save_case_artifact(case_id, artifact_filename, logs_data)

            # Create case note
            note_content = f"""**SOAR Action:** Fetch Endpoint Logs
**Endpoint:** {target}
**Timestamp:** {end_time}
**Status:** ✅ Completed
**Log Fetch Activity:** {activity_id}

_Logs collected for forensic review._

**Artifact:** `/cases/{case_id}/artifacts/sentinelone/{artifact_filename}`"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully initiated log fetch for {target}",
                "template_name": "SentinelOne Fetch Endpoint Logs",
                "target": target,
                "start_time": start_time,
                "end_time": end_time,
                "activity_id": activity_id,
                "artifact_path": artifact_path,
                "steps": [
                    {
                        "step_id": "find_agent",
                        "name": "Find Agent",
                        "status": "Completed",
                        "message": f"Found agent ID: {agent_id}"
                    },
                    {
                        "step_id": "initiate_fetch",
                        "name": "Initiate Log Fetch",
                        "status": "Completed",
                        "message": f"Log fetch started with activity ID: {activity_id}"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved log fetch details to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to fetch logs from agent: {target}",
                "error": f"SentinelOne API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to SentinelOne: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"SentinelOne fetch logs job failed: {str(e)}",
            "error": str(e)
        }


def execute_sentinelone_full_scan(job_id, target, config, case_id):
    """
    Execute SentinelOne full disk scan playbook
    """
    try:
        base_url = config.get('base_url').rstrip('/')
        api_token = config.get('api_token')
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        headers = {
            'Authorization': f'ApiToken {api_token}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find agent by hostname or agent ID
        if target.startswith('agent-'):
            agent_id = target.replace('agent-', '')
        else:
            # Search by hostname
            agents_endpoint = f'{base_url}/web/api/v2.1/agents'
            params = {'computerName': target, 'limit': 1}

            response = requests.get(agents_endpoint, headers=headers, params=params, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to find agent: {target}",
                    "error": f"SentinelOne API returned status {response.status_code}"
                }

            agents = response.json().get('data', [])
            if not agents:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Agent not found: {target}",
                    "error": "No agents found matching the target hostname"
                }

            agent_id = agents[0]['id']

        # Step 2: Initiate full scan
        scan_endpoint = f'{base_url}/web/api/v2.1/agents/actions/initiate-scan'
        scan_data = {
            'filter': {
                'ids': [agent_id]
            },
            'data': {
                'scanType': 'full'
            }
        }

        response = requests.post(scan_endpoint, headers=headers, json=scan_data, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            scan_response = response.json()
            activity_id = scan_response.get('data', {}).get('activityId')

            # Step 3: Poll scan status (simplified)
            time.sleep(3)  # Wait for scan to start
            end_time = datetime.now().isoformat() + "Z"

            # Save scan details as artifact
            artifact_filename = f"scan_report_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            scan_data_artifact = {
                "job_id": job_id,
                "action": "full_disk_scan",
                "target": target,
                "agent_id": agent_id,
                "timestamp": end_time,
                "activity_id": activity_id,
                "scan_type": "full",
                "status": "initiated",
                "scan_response": scan_response
            }

            artifact_path = save_case_artifact(case_id, artifact_filename, scan_data_artifact)

            # Create case note
            note_content = f"""**SOAR Action:** Full Disk Scan
**Endpoint:** {target}
**Timestamp:** {end_time}
**Result:** Scan initiated - Activity ID: {activity_id}

_Full scan started on endpoint. Check SentinelOne console for completion status._

**Artifact:** `/cases/{case_id}/artifacts/sentinelone/{artifact_filename}`"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Running",
                "message": f"Full disk scan initiated for {target}",
                "template_name": "SentinelOne Full Disk Scan",
                "target": target,
                "start_time": start_time,
                "end_time": end_time,
                "activity_id": activity_id,
                "artifact_path": artifact_path,
                "estimated_duration": "30-60 minutes",
                "steps": [
                    {
                        "step_id": "find_agent",
                        "name": "Find Agent",
                        "status": "Completed",
                        "message": f"Found agent ID: {agent_id}"
                    },
                    {
                        "step_id": "initiate_scan",
                        "name": "Initiate Full Scan",
                        "status": "Running",
                        "message": f"Full disk scan started with activity ID: {activity_id}"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved scan details to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to initiate scan on agent: {target}",
                "error": f"SentinelOne API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to SentinelOne: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"SentinelOne full scan job failed: {str(e)}",
            "error": str(e)
        }