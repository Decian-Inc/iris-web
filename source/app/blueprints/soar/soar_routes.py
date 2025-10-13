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
from app.util import response_success, response_error
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
                "name": "SentinelOne Quarantine Host",
                "description": "Quarantine a host using SentinelOne API",
                "vendor": "SentinelOne",
                "tags": ["containment"],
                "requires_approval": True,
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
@login_required
def soar_jobs_list():
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


@soar_blueprint.route('/soar/jobs', methods=['POST'])
@login_required
def soar_jobs_create():
    """
    API endpoint to create and execute a SOAR job
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['template_id', 'target']
        for field in required_fields:
            if field not in data:
                return response_error(f"Missing required field: {field}")

        template_id = data.get('template_id')
        target = data.get('target')
        case_id = request.args.get('cid', default=1, type=int)

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
@login_required
def soar_job_detail(job_id):
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
        if not config.get('enabled', False):
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"{integration_type.capitalize()} integration is not enabled",
                "error": "Please enable and configure the integration in Manage > Integrations"
            }

        # Validate required configuration
        if integration_type == 'sentinelone':
            if not config.get('base_url') or not config.get('api_token'):
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": "SentinelOne integration not properly configured",
                    "error": "Missing base_url or api_token in integration settings"
                }
        elif integration_type == 'velociraptor':
            if not config.get('base_url') or not config.get('api_key'):
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": "Velociraptor integration not properly configured",
                    "error": "Missing base_url or api_key in integration settings"
                }

        # Execute the specific job type
        if template_id == 'sentinel1-quarantine':
            result = execute_sentinelone_quarantine(job_id, target, config)
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
        'sentinel1-quarantine': 'SentinelOne Quarantine Host',
        'velociraptor-collect': 'Velociraptor Forensic Collection'
    }
    return template_names.get(template_id, template_id)


def execute_sentinelone_quarantine(job_id, target, config):
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
            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully quarantined agent {target}",
                "template_name": "SentinelOne Quarantine Host",
                "target": target,
                "start_time": datetime.now().isoformat() + "Z",
                "end_time": datetime.now().isoformat() + "Z",
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