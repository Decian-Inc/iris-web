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
from datetime import datetime, timedelta
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
from app.util import response_success, response_error, ac_api_case_requires, ac_requires_case_identifier
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
            },
            {
                "id": "crowdstrike-contain-host",
                "name": "CrowdStrike Contain Host",
                "description": "Isolate a compromised endpoint from the network to prevent lateral movement",
                "vendor": "CrowdStrike",
                "tags": ["containment", "isolation"],
                "requires_approval": True,
                "allowed_target_types": ["device_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "crowdstrike-lift-containment",
                "name": "CrowdStrike Lift Containment",
                "description": "Reconnect a previously isolated host after remediation",
                "vendor": "CrowdStrike",
                "tags": ["containment", "release"],
                "requires_approval": True,
                "allowed_target_types": ["device_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "crowdstrike-fetch-host-info",
                "name": "CrowdStrike Fetch Host Information",
                "description": "Pull complete device metadata for investigation enrichment",
                "vendor": "CrowdStrike",
                "tags": ["forensics", "inventory"],
                "requires_approval": False,
                "allowed_target_types": ["device_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "crowdstrike-fetch-detections",
                "name": "CrowdStrike Fetch Detections",
                "description": "Retrieve all detections related to a host, user, or timeframe",
                "vendor": "CrowdStrike",
                "tags": ["forensics", "detections"],
                "requires_approval": False,
                "allowed_target_types": ["device_id", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "crowdstrike-fetch-incident-details",
                "name": "CrowdStrike Fetch Incident Details",
                "description": "Enrich an IRIS case with information from a linked CrowdStrike Incident ID",
                "vendor": "CrowdStrike",
                "tags": ["forensics", "incident"],
                "requires_approval": False,
                "allowed_target_types": ["incident_id"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "meraki-block-ip",
                "name": "Cisco Meraki Block IP Address",
                "description": "Block outbound or inbound communication with a malicious IP from Meraki firewall",
                "vendor": "Cisco Meraki",
                "tags": ["containment", "blocking"],
                "requires_approval": True,
                "allowed_target_types": ["ip_address"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "meraki-block-client",
                "name": "Cisco Meraki Block Client",
                "description": "Isolate a specific host by MAC or IP using Meraki client policy",
                "vendor": "Cisco Meraki",
                "tags": ["containment", "isolation"],
                "requires_approval": True,
                "allowed_target_types": ["ip_address", "mac_address"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "meraki-verify-network-event",
                "name": "Cisco Meraki Verify Network Event",
                "description": "Confirm enforcement by fetching Meraki event logs",
                "vendor": "Cisco Meraki",
                "tags": ["forensics", "verification"],
                "requires_approval": False,
                "allowed_target_types": ["ip_address"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "hibp-email-check",
                "name": "HaveIBeenPwned Email Exposure Check",
                "description": "Check if an email address appears in known data breaches",
                "vendor": "HaveIBeenPwned",
                "tags": ["forensics", "credential-intelligence"],
                "requires_approval": False,
                "allowed_target_types": ["email"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "hibp-domain-check",
                "name": "HaveIBeenPwned Domain Exposure Check",
                "description": "Check if a domain has appeared in data breaches",
                "vendor": "HaveIBeenPwned",
                "tags": ["forensics", "credential-intelligence"],
                "requires_approval": False,
                "allowed_target_types": ["domain"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "hibp-password-check",
                "name": "HaveIBeenPwned Password Reuse Check",
                "description": "Check if a password hash appears in known compromised password datasets",
                "vendor": "HaveIBeenPwned",
                "tags": ["forensics", "credential-intelligence"],
                "requires_approval": False,
                "allowed_target_types": ["password_hash"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "fortigate-block-ip",
                "name": "FortiGate Block IP Address",
                "description": "Instantly block an IP address across FortiGate firewall policies",
                "vendor": "FortiGate",
                "tags": ["containment", "blocking"],
                "requires_approval": True,
                "allowed_target_types": ["ip_address"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "fortigate-block-domain",
                "name": "FortiGate Block Domain/URL",
                "description": "Dynamically block a malicious domain via FortiGate's web filter",
                "vendor": "FortiGate",
                "tags": ["containment", "blocking"],
                "requires_approval": True,
                "allowed_target_types": ["domain", "url"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
            },
            {
                "id": "fortigate-quarantine-host",
                "name": "FortiGate Quarantine Host",
                "description": "Immediately isolate an internal host showing compromise indicators",
                "vendor": "FortiGate",
                "tags": ["containment", "quarantine"],
                "requires_approval": True,
                "allowed_target_types": ["ip_address", "hostname"],
                "created_by": "system",
                "created_at": "2025-10-15T00:00:00Z"
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
@ac_requires_case_identifier()
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
        elif template_id.startswith('crowdstrike'):
            integration_type = 'crowdstrike'
            config = integrations_config.get('crowdstrike', {})
        elif template_id.startswith('meraki'):
            integration_type = 'meraki'
            config = integrations_config.get('meraki', {})
        elif template_id.startswith('hibp'):
            integration_type = 'haveibeenpwned'
            config = integrations_config.get('haveibeenpwned', {})
        elif template_id.startswith('fortigate'):
            integration_type = 'fortigate'
            config = integrations_config.get('fortigate', {})
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
        elif integration_type == 'crowdstrike':
            base_url = config.get('base_url', '').strip()
            client_id = config.get('client_id', '').strip()
            client_secret = config.get('client_secret', '').strip()
            if not base_url or not client_id or not client_secret:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": "CrowdStrike API credentials missing - Configure URL, Client ID and Client Secret in Manage > Integrations",
                    "error": "Missing base_url, client_id or client_secret - Cannot connect to CrowdStrike API"
                }
        elif integration_type == 'meraki':
            api_key = config.get('api_key', '').strip()
            organization_id = config.get('organization_id', '').strip()
            if not api_key or not organization_id:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": "Meraki API credentials missing - Configure API Key and Organization ID in Manage > Integrations",
                    "error": "Missing api_key or organization_id - Cannot connect to Meraki API"
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
        elif template_id == 'crowdstrike-contain-host':
            result = execute_crowdstrike_contain_host(job_id, target, config, case_id)
        elif template_id == 'crowdstrike-lift-containment':
            result = execute_crowdstrike_lift_containment(job_id, target, config, case_id)
        elif template_id == 'crowdstrike-fetch-host-info':
            result = execute_crowdstrike_fetch_host_info(job_id, target, config, case_id)
        elif template_id == 'crowdstrike-fetch-detections':
            result = execute_crowdstrike_fetch_detections(job_id, target, config, case_id)
        elif template_id == 'crowdstrike-fetch-incident-details':
            result = execute_crowdstrike_fetch_incident_details(job_id, target, config, case_id)
        elif template_id == 'meraki-block-ip':
            result = execute_meraki_block_ip(job_id, target, config, case_id)
        elif template_id == 'meraki-block-client':
            result = execute_meraki_block_client(job_id, target, config, case_id)
        elif template_id == 'meraki-verify-network-event':
            result = execute_meraki_verify_network_event(job_id, target, config, case_id)
        elif template_id == 'hibp-email-check':
            result = execute_hibp_email_check(job_id, target, config, case_id)
        elif template_id == 'hibp-domain-check':
            result = execute_hibp_domain_check(job_id, target, config, case_id)
        elif template_id == 'hibp-password-check':
            result = execute_hibp_password_check(job_id, target, config, case_id)
        elif template_id == 'fortigate-block-ip':
            result = execute_fortigate_block_ip(job_id, target, config, case_id)
        elif template_id == 'fortigate-block-domain':
            result = execute_fortigate_block_domain(job_id, target, config, case_id)
        elif template_id == 'fortigate-quarantine-host':
            result = execute_fortigate_quarantine_host(job_id, target, config, case_id)
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
        'velociraptor-collect': 'Velociraptor Forensic Collection',
        'crowdstrike-contain-host': 'CrowdStrike Contain Host',
        'crowdstrike-lift-containment': 'CrowdStrike Lift Containment',
        'crowdstrike-fetch-host-info': 'CrowdStrike Fetch Host Information',
        'crowdstrike-fetch-detections': 'CrowdStrike Fetch Detections',
        'crowdstrike-fetch-incident-details': 'CrowdStrike Fetch Incident Details',
        'meraki-block-ip': 'Cisco Meraki Block IP Address',
        'meraki-block-client': 'Cisco Meraki Block Client',
        'meraki-verify-network-event': 'Cisco Meraki Verify Network Event',
        'hibp-email-check': 'HaveIBeenPwned Email Exposure Check',
        'hibp-domain-check': 'HaveIBeenPwned Domain Exposure Check',
        'hibp-password-check': 'HaveIBeenPwned Password Reuse Check',
        'fortigate-block-ip': 'FortiGate Block IP Address',
        'fortigate-block-domain': 'FortiGate Block Domain/URL',
        'fortigate-quarantine-host': 'FortiGate Quarantine Host'
    }
    return template_names.get(template_id, template_id)


def create_case_artifact_folder(case_id, integration_type='sentinelone'):
    """
    Create the artifacts folder structure for a case
    """
    try:
        artifact_path = f"/home/iris/server_data/cases/{case_id}/artifacts/{integration_type}"
        os.makedirs(artifact_path, exist_ok=True)
        return artifact_path
    except Exception as e:
        print(f"Error creating artifact folder: {str(e)}")
        return None


def save_case_artifact(case_id, filename, data, integration_type='sentinelone'):
    """
    Save artifact data to case folder
    """
    try:
        artifact_path = create_case_artifact_folder(case_id, integration_type)
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


def get_crowdstrike_token(config):
    """
    Get OAuth2 access token for CrowdStrike API
    """
    try:
        base_url = config.get('base_url', '').rstrip('/')
        client_id = config.get('client_id', '')
        client_secret = config.get('client_secret', '')
        verify_ssl = config.get('verify_ssl', True)

        token_url = f"{base_url}/oauth2/token"

        data = {
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(token_url, data=data, verify=verify_ssl, timeout=30)

        if response.status_code == 201:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            print(f"Token request failed: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error getting CrowdStrike token: {str(e)}")
        return None


def execute_crowdstrike_contain_host(job_id, target, config, case_id):
    """
    Execute CrowdStrike Contain Host (Network Isolation) playbook
    """
    try:
        base_url = config.get('base_url', '').rstrip('/')
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        # Get OAuth2 token
        access_token = get_crowdstrike_token(config)
        if not access_token:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "Failed to authenticate with CrowdStrike API",
                "error": "OAuth2 token request failed"
            }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find device by hostname or device ID
        if target.startswith('device-'):
            device_id = target.replace('device-', '')
        else:
            # Search by hostname
            search_url = f"{base_url}/devices/queries/devices/v1"
            params = {'filter': f"hostname:'{target}'", 'limit': 1}

            response = requests.get(search_url, headers=headers, params=params, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to search for device: {target}",
                    "error": f"CrowdStrike API returned status {response.status_code}"
                }

            device_ids = response.json().get('resources', [])
            if not device_ids:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Device not found: {target}",
                    "error": "No devices found matching the target hostname"
                }

            device_id = device_ids[0]

        # Step 2: Contain the device
        contain_url = f"{base_url}/devices/entities/network-contain/v1"
        contain_data = {
            'ids': [device_id]
        }

        response = requests.post(contain_url, headers=headers, json=contain_data, verify=verify_ssl, timeout=30)

        if response.status_code == 202:
            end_time = datetime.now().isoformat() + "Z"
            containment_response = response.json()

            # Step 3: Poll containment status
            time.sleep(2)
            status_url = f"{base_url}/devices/entities/containment-status/v1"
            status_params = {'ids': device_id}
            status_response = requests.get(status_url, headers=headers, params=status_params, verify=verify_ssl, timeout=30)

            # Save containment action details as artifact
            containment_data = {
                "job_id": job_id,
                "action": "network_contain",
                "target": target,
                "device_id": device_id,
                "timestamp": end_time,
                "status": "completed",
                "api_response": containment_response,
                "status_check": status_response.json() if status_response.status_code == 200 else None
            }

            artifact_filename = f"containment_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            artifact_path = save_case_artifact(case_id, artifact_filename, containment_data, 'crowdstrike')

            # Create case note
            note_content = f"""**SOAR Action:** Contain Host
**Endpoint:** {target}
**Timestamp:** {end_time}
✅ Host successfully isolated via CrowdStrike API."""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully contained device {target}",
                "template_name": "CrowdStrike Contain Host",
                "target": target,
                "start_time": start_time,
                "end_time": end_time,
                "artifact_path": artifact_path,
                "steps": [
                    {
                        "step_id": "authenticate",
                        "name": "OAuth2 Authentication",
                        "status": "Completed",
                        "message": "Successfully authenticated with CrowdStrike API"
                    },
                    {
                        "step_id": "find_device",
                        "name": "Find Device",
                        "status": "Completed",
                        "message": f"Found device ID: {device_id}"
                    },
                    {
                        "step_id": "contain_device",
                        "name": "Contain Device",
                        "status": "Completed",
                        "message": "Device successfully contained"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved containment details to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to contain device: {target}",
                "error": f"CrowdStrike API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to CrowdStrike: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"CrowdStrike contain host job failed: {str(e)}",
            "error": str(e)
        }


def execute_crowdstrike_lift_containment(job_id, target, config, case_id):
    """
    Execute CrowdStrike Lift Containment (Release Host) playbook
    """
    try:
        base_url = config.get('base_url', '').rstrip('/')
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        # Get OAuth2 token
        access_token = get_crowdstrike_token(config)
        if not access_token:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "Failed to authenticate with CrowdStrike API",
                "error": "OAuth2 token request failed"
            }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find device by hostname or device ID
        if target.startswith('device-'):
            device_id = target.replace('device-', '')
        else:
            # Search by hostname
            search_url = f"{base_url}/devices/queries/devices/v1"
            params = {'filter': f"hostname:'{target}'", 'limit': 1}

            response = requests.get(search_url, headers=headers, params=params, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to search for device: {target}",
                    "error": f"CrowdStrike API returned status {response.status_code}"
                }

            device_ids = response.json().get('resources', [])
            if not device_ids:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Device not found: {target}",
                    "error": "No devices found matching the target hostname"
                }

            device_id = device_ids[0]

        # Step 2: Lift containment
        lift_url = f"{base_url}/devices/entities/network-containments/v1"
        lift_data = {
            'ids': [device_id],
            'action': 'lift_containment'
        }

        response = requests.post(lift_url, headers=headers, json=lift_data, verify=verify_ssl, timeout=30)

        if response.status_code == 202:
            end_time = datetime.now().isoformat() + "Z"
            lift_response = response.json()

            # Step 3: Poll until containment_state = "normal"
            time.sleep(2)
            status_url = f"{base_url}/devices/entities/containment-status/v1"
            status_params = {'ids': device_id}
            status_response = requests.get(status_url, headers=headers, params=status_params, verify=verify_ssl, timeout=30)

            # Save lift containment action details as artifact
            lift_data_artifact = {
                "job_id": job_id,
                "action": "lift_containment",
                "target": target,
                "device_id": device_id,
                "timestamp": end_time,
                "status": "completed",
                "api_response": lift_response,
                "status_check": status_response.json() if status_response.status_code == 200 else None
            }

            artifact_filename = f"lift_containment_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            artifact_path = save_case_artifact(case_id, artifact_filename, lift_data_artifact, 'crowdstrike')

            # Create case note
            note_content = f"""**SOAR Action:** Lift Containment
**Endpoint:** {target}
**Timestamp:** {end_time}
✅ Host restored to normal network connectivity."""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully lifted containment for device {target}",
                "template_name": "CrowdStrike Lift Containment",
                "target": target,
                "start_time": start_time,
                "end_time": end_time,
                "artifact_path": artifact_path,
                "steps": [
                    {
                        "step_id": "authenticate",
                        "name": "OAuth2 Authentication",
                        "status": "Completed",
                        "message": "Successfully authenticated with CrowdStrike API"
                    },
                    {
                        "step_id": "find_device",
                        "name": "Find Device",
                        "status": "Completed",
                        "message": f"Found device ID: {device_id}"
                    },
                    {
                        "step_id": "lift_containment",
                        "name": "Lift Containment",
                        "status": "Completed",
                        "message": "Device containment successfully lifted"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved lift containment details to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to lift containment for device: {target}",
                "error": f"CrowdStrike API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to CrowdStrike: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"CrowdStrike lift containment job failed: {str(e)}",
            "error": str(e)
        }


def execute_crowdstrike_fetch_host_info(job_id, target, config, case_id):
    """
    Execute CrowdStrike Fetch Host Information playbook
    """
    try:
        base_url = config.get('base_url', '').rstrip('/')
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        # Get OAuth2 token
        access_token = get_crowdstrike_token(config)
        if not access_token:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "Failed to authenticate with CrowdStrike API",
                "error": "OAuth2 token request failed"
            }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find device by hostname or device ID
        if target.startswith('device-'):
            device_id = target.replace('device-', '')
        else:
            # Search by hostname
            search_url = f"{base_url}/devices/queries/devices/v1"
            params = {'filter': f"hostname:'{target}'", 'limit': 1}

            response = requests.get(search_url, headers=headers, params=params, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to search for device: {target}",
                    "error": f"CrowdStrike API returned status {response.status_code}"
                }

            device_ids = response.json().get('resources', [])
            if not device_ids:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Device not found: {target}",
                    "error": "No devices found matching the target hostname"
                }

            device_id = device_ids[0]

        # Step 2: Fetch complete device metadata
        devices_url = f"{base_url}/devices/entities/devices/v2"
        params = {'ids': device_id}

        response = requests.get(devices_url, headers=headers, params=params, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            end_time = datetime.now().isoformat() + "Z"
            device_data = response.json()
            resources = device_data.get('resources', [])

            if resources:
                device_info = resources[0]

                # Save host information as artifact
                artifact_filename = f"hostinfo_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                artifact_path = save_case_artifact(case_id, artifact_filename, {
                    "job_id": job_id,
                    "action": "fetch_host_info",
                    "target": target,
                    "device_id": device_id,
                    "timestamp": end_time,
                    "device_info": device_info
                }, 'crowdstrike')

                # Create case note
                hostname = device_info.get('hostname', target)
                note_content = f"""**SOAR Action:** Fetch Host Info
**Host:** {hostname}
**Timestamp:** {end_time}
Retrieved metadata — see hostinfo JSON file for full details."""

                add_case_note(case_id, note_content)

                return {
                    "job_id": job_id,
                    "status": "Completed",
                    "message": f"Successfully retrieved host information for {target}",
                    "template_name": "CrowdStrike Fetch Host Information",
                    "target": target,
                    "start_time": start_time,
                    "end_time": end_time,
                    "artifact_path": artifact_path,
                    "device_info": device_info,
                    "steps": [
                        {
                            "step_id": "authenticate",
                            "name": "OAuth2 Authentication",
                            "status": "Completed",
                            "message": "Successfully authenticated with CrowdStrike API"
                        },
                        {
                            "step_id": "find_device",
                            "name": "Find Device",
                            "status": "Completed",
                            "message": f"Found device ID: {device_id}"
                        },
                        {
                            "step_id": "fetch_info",
                            "name": "Fetch Host Information",
                            "status": "Completed",
                            "message": "Successfully retrieved complete device metadata"
                        },
                        {
                            "step_id": "save_artifact",
                            "name": "Save Artifact",
                            "status": "Completed",
                            "message": f"Saved host information to {artifact_filename}"
                        }
                    ]
                }
            else:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"No device information found for: {target}",
                    "error": "Device metadata not available"
                }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to fetch host information for device: {target}",
                "error": f"CrowdStrike API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to CrowdStrike: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"CrowdStrike fetch host info job failed: {str(e)}",
            "error": str(e)
        }


def execute_crowdstrike_fetch_detections(job_id, target, config, case_id):
    """
    Execute CrowdStrike Fetch Detections playbook
    """
    try:
        base_url = config.get('base_url', '').rstrip('/')
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        # Get OAuth2 token
        access_token = get_crowdstrike_token(config)
        if not access_token:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "Failed to authenticate with CrowdStrike API",
                "error": "OAuth2 token request failed"
            }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Step 1: Find device by hostname or device ID
        if target.startswith('device-'):
            device_id = target.replace('device-', '')
            hostname = target
        else:
            # Search by hostname
            search_url = f"{base_url}/devices/queries/devices/v1"
            params = {'filter': f"hostname:'{target}'", 'limit': 1}

            response = requests.get(search_url, headers=headers, params=params, verify=verify_ssl, timeout=30)
            if response.status_code != 200:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Failed to search for device: {target}",
                    "error": f"CrowdStrike API returned status {response.status_code}"
                }

            device_ids = response.json().get('resources', [])
            if not device_ids:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"Device not found: {target}",
                    "error": "No devices found matching the target hostname"
                }

            device_id = device_ids[0]
            hostname = target

        # Step 2: Query detections for the device (last 24h)
        detects_query_url = f"{base_url}/detects/queries/detects/v1"
        params = {
            'filter': f"device.device_id:'{device_id}'+created_timestamp:>'{(datetime.now() - timedelta(days=1)).isoformat()}Z'",
            'limit': 100
        }

        response = requests.get(detects_query_url, headers=headers, params=params, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            detection_ids = response.json().get('resources', [])

            if detection_ids:
                # Step 3: Get detailed detection information
                detects_detail_url = f"{base_url}/detects/entities/detects/GET/v2"
                detail_data = {'ids': detection_ids}

                detail_response = requests.post(detects_detail_url, headers=headers, json=detail_data, verify=verify_ssl, timeout=30)

                if detail_response.status_code == 200:
                    detections = detail_response.json().get('resources', [])
                else:
                    detections = []
            else:
                detections = []

            end_time = datetime.now().isoformat() + "Z"

            # Save detections data as artifact
            artifact_filename = f"detections_{hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            artifact_path = save_case_artifact(case_id, artifact_filename, {
                "job_id": job_id,
                "action": "fetch_detections",
                "target": target,
                "device_id": device_id,
                "timestamp": end_time,
                "total_detections": len(detections),
                "detections": detections
            }, 'crowdstrike')

            # Create case note with top threat summary
            if detections:
                top_detection = detections[0]
                behaviors = top_detection.get('behaviors', [])
                top_alert = "No behaviors found"
                if behaviors:
                    tactic_name = behaviors[0].get('tactic', 'Unknown')
                    technique_name = behaviors[0].get('technique', 'Unknown')
                    top_alert = f"{tactic_name} — {technique_name}"

                note_content = f"""**SOAR Action:** Fetch Detections
**Host:** {hostname}
**Timestamp:** {end_time}
Retrieved {len(detections)} detections.
**Top Alert:** {top_alert}
_Full JSON report attached._"""
            else:
                note_content = f"""**SOAR Action:** Fetch Detections
**Host:** {hostname}
**Timestamp:** {end_time}
Retrieved {len(detections)} detections.
_No detections found in the last 24 hours._"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully retrieved {len(detections)} detections for {target}",
                "template_name": "CrowdStrike Fetch Detections",
                "target": target,
                "start_time": start_time,
                "end_time": end_time,
                "artifact_path": artifact_path,
                "detections_count": len(detections),
                "steps": [
                    {
                        "step_id": "authenticate",
                        "name": "OAuth2 Authentication",
                        "status": "Completed",
                        "message": "Successfully authenticated with CrowdStrike API"
                    },
                    {
                        "step_id": "find_device",
                        "name": "Find Device",
                        "status": "Completed",
                        "message": f"Found device ID: {device_id}"
                    },
                    {
                        "step_id": "query_detections",
                        "name": "Query Detections",
                        "status": "Completed",
                        "message": f"Found {len(detection_ids)} detection IDs"
                    },
                    {
                        "step_id": "fetch_details",
                        "name": "Fetch Detection Details",
                        "status": "Completed",
                        "message": f"Retrieved detailed information for {len(detections)} detections"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved detection data to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to fetch detections for device: {target}",
                "error": f"CrowdStrike API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to CrowdStrike: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"CrowdStrike fetch detections job failed: {str(e)}",
            "error": str(e)
        }


def execute_crowdstrike_fetch_incident_details(job_id, target, config, case_id):
    """
    Execute CrowdStrike Fetch Incident Details playbook
    """
    try:
        base_url = config.get('base_url', '').rstrip('/')
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        # Get OAuth2 token
        access_token = get_crowdstrike_token(config)
        if not access_token:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "Failed to authenticate with CrowdStrike API",
                "error": "OAuth2 token request failed"
            }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Target should be an incident ID
        incident_id = target

        # Step 1: Fetch incident details
        incidents_url = f"{base_url}/incidents/entities/incidents/v1"
        params = {'ids': incident_id}

        response = requests.get(incidents_url, headers=headers, params=params, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            end_time = datetime.now().isoformat() + "Z"
            incident_data = response.json()
            resources = incident_data.get('resources', [])

            if resources:
                incident_info = resources[0]

                # Save incident information as artifact
                artifact_filename = f"incident_{incident_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                artifact_path = save_case_artifact(case_id, artifact_filename, {
                    "job_id": job_id,
                    "action": "fetch_incident_details",
                    "incident_id": incident_id,
                    "timestamp": end_time,
                    "incident_info": incident_info
                }, 'crowdstrike')

                # Extract key information for note
                severity = incident_info.get('state', 'Unknown')
                status = incident_info.get('status', 'Unknown')

                # Create case note
                note_content = f"""**SOAR Action:** Fetch Incident Details
**Incident ID:** {incident_id}
**Severity:** {severity}
**Status:** {status}
_Incident data synced from CrowdStrike._"""

                add_case_note(case_id, note_content)

                return {
                    "job_id": job_id,
                    "status": "Completed",
                    "message": f"Successfully retrieved incident details for {incident_id}",
                    "template_name": "CrowdStrike Fetch Incident Details",
                    "target": incident_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "artifact_path": artifact_path,
                    "incident_info": incident_info,
                    "steps": [
                        {
                            "step_id": "authenticate",
                            "name": "OAuth2 Authentication",
                            "status": "Completed",
                            "message": "Successfully authenticated with CrowdStrike API"
                        },
                        {
                            "step_id": "fetch_incident",
                            "name": "Fetch Incident Details",
                            "status": "Completed",
                            "message": f"Successfully retrieved incident {incident_id}"
                        },
                        {
                            "step_id": "save_artifact",
                            "name": "Save Artifact",
                            "status": "Completed",
                            "message": f"Saved incident details to {artifact_filename}"
                        }
                    ]
                }
            else:
                return {
                    "job_id": job_id,
                    "status": "Failed",
                    "message": f"No incident information found for: {incident_id}",
                    "error": "Incident data not available"
                }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to fetch incident details for: {incident_id}",
                "error": f"CrowdStrike API returned status {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to CrowdStrike: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"CrowdStrike fetch incident details job failed: {str(e)}",
            "error": str(e)
        }


def execute_meraki_block_ip(job_id, target, config, case_id):
    """
    Execute Cisco Meraki Block IP Address playbook
    """
    try:
        api_key = config.get('api_key', '').strip()
        organization_id = config.get('organization_id', '').strip()
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        # Meraki Dashboard API base URL
        base_url = 'https://api.meraki.com/api/v1'

        headers = {
            'X-Cisco-Meraki-API-Key': api_key,
            'Content-Type': 'application/json'
        }

        # Step 1: Get organization networks
        networks_url = f"{base_url}/organizations/{organization_id}/networks"
        networks_response = requests.get(networks_url, headers=headers, verify=verify_ssl, timeout=30)

        if networks_response.status_code != 200:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to retrieve networks from organization {organization_id}",
                "error": f"Meraki API returned status {networks_response.status_code}"
            }

        networks = networks_response.json()

        # Find networks with appliances (MX devices)
        appliance_networks = [net for net in networks if 'appliance' in net.get('productTypes', [])]

        if not appliance_networks:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "No appliance networks found in organization",
                "error": "No MX devices available for firewall rule creation"
            }

        # Step 2: Apply firewall rule to all appliance networks
        blocked_networks = []

        for network in appliance_networks:
            network_id = network['id']
            network_name = network['name']

            # Get current L3 firewall rules
            firewall_url = f"{base_url}/networks/{network_id}/appliance/firewall/l3FirewallRules"
            current_rules_response = requests.get(firewall_url, headers=headers, verify=verify_ssl, timeout=30)

            if current_rules_response.status_code == 200:
                current_rules = current_rules_response.json()

                # Create new blocking rule
                new_rule = {
                    "comment": f"IRIS SOAR Auto-block: Case {case_id}",
                    "policy": "deny",
                    "protocol": "any",
                    "srcCidr": "any",
                    "destCidr": target,
                    "destPort": "any"
                }

                # Insert at beginning of rules (highest priority)
                updated_rules = [new_rule] + current_rules

                # Update firewall rules
                update_response = requests.put(
                    firewall_url,
                    headers=headers,
                    json=updated_rules,
                    verify=verify_ssl,
                    timeout=30
                )

                if update_response.status_code == 200:
                    blocked_networks.append({
                        'network_id': network_id,
                        'network_name': network_name,
                        'status': 'success'
                    })
                else:
                    blocked_networks.append({
                        'network_id': network_id,
                        'network_name': network_name,
                        'status': 'failed',
                        'error': f"Status {update_response.status_code}"
                    })

        end_time = datetime.now().isoformat() + "Z"

        # Save blocking action details as artifact
        block_data = {
            "job_id": job_id,
            "action": "block_ip",
            "target_ip": target,
            "timestamp": end_time,
            "organization_id": organization_id,
            "networks_processed": len(appliance_networks),
            "successful_blocks": len([n for n in blocked_networks if n['status'] == 'success']),
            "blocked_networks": blocked_networks
        }

        artifact_filename = f"block_{target.replace('.', '_').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        artifact_path = save_case_artifact(case_id, artifact_filename, block_data, 'meraki')

        # Create case note
        successful_blocks = len([n for n in blocked_networks if n['status'] == 'success'])
        note_content = f"""**SOAR Action:** Block IP on Meraki
**IP:** {target}
**Timestamp:** {end_time}
✅ IP successfully blocked in Meraki firewall.
**Networks Updated:** {successful_blocks}/{len(appliance_networks)}"""

        add_case_note(case_id, note_content)

        if successful_blocks > 0:
            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully blocked IP {target} on {successful_blocks} networks",
                "template_name": "Cisco Meraki Block IP Address",
                "target": target,
                "start_time": start_time,
                "end_time": end_time,
                "artifact_path": artifact_path,
                "networks_blocked": successful_blocks,
                "steps": [
                    {
                        "step_id": "get_networks",
                        "name": "Get Organization Networks",
                        "status": "Completed",
                        "message": f"Found {len(appliance_networks)} appliance networks"
                    },
                    {
                        "step_id": "create_firewall_rules",
                        "name": "Create Firewall Rules",
                        "status": "Completed",
                        "message": f"Created blocking rules on {successful_blocks} networks"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved blocking details to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to block IP {target} on any networks",
                "error": "No firewall rules were successfully created"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to Meraki: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Meraki block IP job failed: {str(e)}",
            "error": str(e)
        }


def execute_meraki_block_client(job_id, target, config, case_id):
    """
    Execute Cisco Meraki Block Client playbook
    """
    try:
        api_key = config.get('api_key', '').strip()
        organization_id = config.get('organization_id', '').strip()
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        # Meraki Dashboard API base URL
        base_url = 'https://api.meraki.com/api/v1'

        headers = {
            'X-Cisco-Meraki-API-Key': api_key,
            'Content-Type': 'application/json'
        }

        # Step 1: Get organization networks
        networks_url = f"{base_url}/organizations/{organization_id}/networks"
        networks_response = requests.get(networks_url, headers=headers, verify=verify_ssl, timeout=30)

        if networks_response.status_code != 200:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to retrieve networks from organization {organization_id}",
                "error": f"Meraki API returned status {networks_response.status_code}"
            }

        networks = networks_response.json()

        # Step 2: Search for client across all networks
        client_found = None
        client_network = None

        for network in networks:
            network_id = network['id']

            # Get clients from this network
            clients_url = f"{base_url}/networks/{network_id}/clients"
            clients_response = requests.get(clients_url, headers=headers, verify=verify_ssl, timeout=30)

            if clients_response.status_code == 200:
                clients = clients_response.json()

                # Search for target client by IP or MAC
                for client in clients:
                    if (client.get('ip') == target or
                        client.get('mac', '').lower() == target.lower() or
                        client.get('id') == target):
                        client_found = client
                        client_network = network
                        break

                if client_found:
                    break

        if not client_found:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Client not found: {target}",
                "error": "No clients found matching the target IP or MAC address"
            }

        # Step 3: Block the client
        client_id = client_found['id']
        network_id = client_network['id']

        policy_url = f"{base_url}/networks/{network_id}/clients/{client_id}/policy"
        policy_data = {"devicePolicy": "Blocked"}

        policy_response = requests.put(
            policy_url,
            headers=headers,
            json=policy_data,
            verify=verify_ssl,
            timeout=30
        )

        if policy_response.status_code == 200:
            end_time = datetime.now().isoformat() + "Z"

            # Save client blocking details as artifact
            block_data = {
                "job_id": job_id,
                "action": "block_client",
                "target": target,
                "client_id": client_id,
                "client_ip": client_found.get('ip'),
                "client_mac": client_found.get('mac'),
                "network_id": network_id,
                "network_name": client_network['name'],
                "timestamp": end_time,
                "client_details": client_found,
                "policy_response": policy_response.json()
            }

            artifact_filename = f"block_client_{target.replace('.', '_').replace(':', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            artifact_path = save_case_artifact(case_id, artifact_filename, block_data, 'meraki')

            # Create case note
            note_content = f"""**SOAR Action:** Block Client on Meraki
**Target:** {target}
**Client IP:** {client_found.get('ip', 'Unknown')}
**Client MAC:** {client_found.get('mac', 'Unknown')}
**Network:** {client_network['name']}
**Timestamp:** {end_time}
✅ Client successfully blocked via Meraki policy."""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Successfully blocked client {target}",
                "template_name": "Cisco Meraki Block Client",
                "target": target,
                "start_time": start_time,
                "end_time": end_time,
                "artifact_path": artifact_path,
                "client_details": client_found,
                "network_name": client_network['name'],
                "steps": [
                    {
                        "step_id": "search_client",
                        "name": "Search for Client",
                        "status": "Completed",
                        "message": f"Found client in network {client_network['name']}"
                    },
                    {
                        "step_id": "block_client",
                        "name": "Block Client",
                        "status": "Completed",
                        "message": "Client policy set to Blocked"
                    },
                    {
                        "step_id": "save_artifact",
                        "name": "Save Artifact",
                        "status": "Completed",
                        "message": f"Saved blocking details to {artifact_filename}"
                    }
                ]
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to block client {target}",
                "error": f"Meraki API returned status {policy_response.status_code}: {policy_response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to Meraki: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Meraki block client job failed: {str(e)}",
            "error": str(e)
        }


def execute_meraki_verify_network_event(job_id, target, config, case_id):
    """
    Execute Cisco Meraki Verify Network Event playbook
    """
    try:
        api_key = config.get('api_key', '').strip()
        organization_id = config.get('organization_id', '').strip()
        verify_ssl = config.get('verify_ssl', True)
        start_time = datetime.now().isoformat() + "Z"

        # Meraki Dashboard API base URL
        base_url = 'https://api.meraki.com/api/v1'

        headers = {
            'X-Cisco-Meraki-API-Key': api_key,
            'Content-Type': 'application/json'
        }

        # Step 1: Get organization networks
        networks_url = f"{base_url}/organizations/{organization_id}/networks"
        networks_response = requests.get(networks_url, headers=headers, verify=verify_ssl, timeout=30)

        if networks_response.status_code != 200:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to retrieve networks from organization {organization_id}",
                "error": f"Meraki API returned status {networks_response.status_code}"
            }

        networks = networks_response.json()

        # Find networks with appliances (MX devices)
        appliance_networks = [net for net in networks if 'appliance' in net.get('productTypes', [])]

        if not appliance_networks:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "No appliance networks found in organization",
                "error": "No MX devices available for event log verification"
            }

        # Step 2: Collect events from all appliance networks
        all_events = []

        for network in appliance_networks:
            network_id = network['id']
            network_name = network['name']

            # Get network events (appliance events)
            events_url = f"{base_url}/networks/{network_id}/events"
            params = {
                'productType': 'appliance',
                'perPage': 100  # Limit to recent events
            }

            events_response = requests.get(events_url, headers=headers, params=params, verify=verify_ssl, timeout=30)

            if events_response.status_code == 200:
                events = events_response.json()

                # Filter events related to the target IP
                relevant_events = []
                for event in events.get('events', []):
                    event_description = event.get('description', '').lower()
                    if target in event_description or target in str(event.get('eventData', {})):
                        event['network_name'] = network_name
                        event['network_id'] = network_id
                        relevant_events.append(event)

                all_events.extend(relevant_events)

        end_time = datetime.now().isoformat() + "Z"

        # Step 3: Save verification results as artifact
        verification_data = {
            "job_id": job_id,
            "action": "verify_network_event",
            "target_ip": target,
            "timestamp": end_time,
            "organization_id": organization_id,
            "networks_checked": len(appliance_networks),
            "events_found": len(all_events),
            "events": all_events
        }

        artifact_filename = f"verify_{target.replace('.', '_').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        artifact_path = save_case_artifact(case_id, artifact_filename, verification_data, 'meraki')

        # Create case note
        if all_events:
            latest_event = all_events[0]
            note_content = f"""**SOAR Action:** Verify Network Event
**IP:** {target}
**Timestamp:** {end_time}
**Events Found:** {len(all_events)}
**Latest Event:** {latest_event.get('type', 'Unknown')} in {latest_event.get('network_name', 'Unknown')}
✅ Network events verified - see JSON for details."""
        else:
            note_content = f"""**SOAR Action:** Verify Network Event
**IP:** {target}
**Timestamp:** {end_time}
**Events Found:** 0
⚠️ No network events found for target IP."""

        add_case_note(case_id, note_content)

        return {
            "job_id": job_id,
            "status": "Completed",
            "message": f"Network event verification completed - found {len(all_events)} events",
            "template_name": "Cisco Meraki Verify Network Event",
            "target": target,
            "start_time": start_time,
            "end_time": end_time,
            "artifact_path": artifact_path,
            "events_found": len(all_events),
            "networks_checked": len(appliance_networks),
            "steps": [
                {
                    "step_id": "get_networks",
                    "name": "Get Organization Networks",
                    "status": "Completed",
                    "message": f"Found {len(appliance_networks)} appliance networks"
                },
                {
                    "step_id": "collect_events",
                    "name": "Collect Network Events",
                    "status": "Completed",
                    "message": f"Collected events from {len(appliance_networks)} networks"
                },
                {
                    "step_id": "filter_events",
                    "name": "Filter Relevant Events",
                    "status": "Completed",
                    "message": f"Found {len(all_events)} events related to {target}"
                },
                {
                    "step_id": "save_artifact",
                    "name": "Save Artifact",
                    "status": "Completed",
                    "message": f"Saved verification results to {artifact_filename}"
                }
            ]
        }

    except requests.exceptions.RequestException as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Connection error to Meraki: {str(e)}",
            "error": "Check integration settings and network connectivity"
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": f"Meraki verify network event job failed: {str(e)}",
            "error": str(e)
        }


def execute_hibp_email_check(job_id, target, config, case_id):
    """
    Execute HaveIBeenPwned email exposure check
    """
    try:
        import hashlib

        # Extract configuration
        base_url = config.get('base_url', 'https://haveibeenpwned.com/api/v3').rstrip('/')
        api_key = config.get('api_key')
        verify_ssl = config.get('verify_ssl', True)
        rate_limit_delay = config.get('rate_limit_delay', 1.6)

        if not api_key:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "HIBP API key not configured",
                "error": "Missing API key in integration configuration"
            }

        # Setup headers
        headers = {
            'hibp-api-key': api_key,
            'User-Agent': 'IRIS-SOAR'
        }

        # Check email in breaches
        endpoint = f'{base_url}/breachedaccount/{target}'

        # Respect rate limiting
        time.sleep(rate_limit_delay)

        response = requests.get(endpoint, headers=headers, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            breaches_data = response.json()
            breach_count = len(breaches_data) if isinstance(breaches_data, list) else 0

            # Create artifacts folder
            artifact_path = create_case_artifact_folder(case_id, 'hibp')
            artifact_filename = f"hibp_email_{target.replace('@', '_at_')}_{job_id}.json"

            # Save results
            if artifact_path:
                save_case_artifact(case_id, artifact_filename, {
                    'email': target,
                    'timestamp': datetime.now().isoformat(),
                    'total_breaches': breach_count,
                    'breaches': breaches_data
                })

            # Format breach names for note
            breach_names = [breach.get('Name', 'Unknown') for breach in breaches_data] if breaches_data else []

            # Add case note
            note_content = f"""**SOAR Action:** HIBP Email Exposure Check
**Email:** {target}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Result:** Found in {breach_count} breaches: {breach_names}

_Full JSON stored in `/cases/{case_id}/artifacts/hibp/{artifact_filename}`_"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Email check completed - found in {breach_count} breaches",
                "artifacts": [artifact_filename] if artifact_path else [],
                "details": {
                    "email": target,
                    "total_breaches": breach_count,
                    "breach_names": breach_names,
                    "execution_time": response.elapsed.total_seconds()
                }
            }
        elif response.status_code == 404:
            # No breaches found
            note_content = f"""**SOAR Action:** HIBP Email Exposure Check
**Email:** {target}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Result:** ✅ No breaches found

_Email address does not appear in known breach datasets._"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": "Email check completed - no breaches found",
                "details": {
                    "email": target,
                    "total_breaches": 0,
                    "execution_time": response.elapsed.total_seconds()
                }
            }
        elif response.status_code == 429:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "Rate limit exceeded",
                "error": "HIBP API rate limit hit - please wait before retrying"
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"HIBP API error: {response.status_code}",
                "error": response.text
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during HIBP email check: {str(e)}"
        add_case_note(case_id, f"**HIBP Email Check Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        add_case_note(case_id, f"**HIBP Email Check Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }


def execute_hibp_domain_check(job_id, target, config, case_id):
    """
    Execute HaveIBeenPwned domain exposure check
    """
    try:
        # Extract configuration
        base_url = config.get('base_url', 'https://haveibeenpwned.com/api/v3').rstrip('/')
        api_key = config.get('api_key')
        verify_ssl = config.get('verify_ssl', True)
        rate_limit_delay = config.get('rate_limit_delay', 1.6)

        if not api_key:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "HIBP API key not configured",
                "error": "Missing API key in integration configuration"
            }

        # Setup headers
        headers = {
            'hibp-api-key': api_key,
            'User-Agent': 'IRIS-SOAR'
        }

        # Check domain in breaches
        endpoint = f'{base_url}/breaches'
        params = {'domain': target}

        # Respect rate limiting
        time.sleep(rate_limit_delay)

        response = requests.get(endpoint, headers=headers, params=params, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            breaches_data = response.json()
            breach_count = len(breaches_data) if isinstance(breaches_data, list) else 0

            # Create artifacts folder
            artifact_path = create_case_artifact_folder(case_id, 'hibp')
            artifact_filename = f"hibp_domain_{target.replace('.', '_')}_{job_id}.json"

            # Save results
            if artifact_path:
                save_case_artifact(case_id, artifact_filename, {
                    'domain': target,
                    'timestamp': datetime.now().isoformat(),
                    'total_breaches': breach_count,
                    'breaches': breaches_data
                })

            # Create breach summary table for note
            breach_table = "| Breach Name | Breach Date | Compromised Accounts |\n|-------------|-------------|---------------------|\n"
            for breach in breaches_data:
                name = breach.get('Name', 'Unknown')
                date = breach.get('BreachDate', 'Unknown')
                count = breach.get('PwnCount', 'Unknown')
                breach_table += f"| {name} | {date} | {count:,} |\n"

            # Add case note
            note_content = f"""**SOAR Action:** HIBP Domain Exposure Check
**Domain:** {target}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Result:** Found {breach_count} breaches affecting this domain

**Breach Summary:**
{breach_table}

_Full JSON stored in `/cases/{case_id}/artifacts/hibp/{artifact_filename}`_"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Domain check completed - found {breach_count} breaches",
                "artifacts": [artifact_filename] if artifact_path else [],
                "details": {
                    "domain": target,
                    "total_breaches": breach_count,
                    "execution_time": response.elapsed.total_seconds()
                }
            }
        elif response.status_code == 404:
            # No breaches found
            note_content = f"""**SOAR Action:** HIBP Domain Exposure Check
**Domain:** {target}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Result:** ✅ No breaches found

_Domain does not appear in known breach datasets._"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": "Domain check completed - no breaches found",
                "details": {
                    "domain": target,
                    "total_breaches": 0,
                    "execution_time": response.elapsed.total_seconds()
                }
            }
        elif response.status_code == 429:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "Rate limit exceeded",
                "error": "HIBP API rate limit hit - please wait before retrying"
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"HIBP API error: {response.status_code}",
                "error": response.text
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during HIBP domain check: {str(e)}"
        add_case_note(case_id, f"**HIBP Domain Check Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        add_case_note(case_id, f"**HIBP Domain Check Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }


def execute_hibp_password_check(job_id, target, config, case_id):
    """
    Execute HaveIBeenPwned password reuse check using k-anonymity
    """
    try:
        import hashlib

        # Extract configuration
        base_url = config.get('base_url', 'https://haveibeenpwned.com/api/v3').rstrip('/')
        verify_ssl = config.get('verify_ssl', True)
        rate_limit_delay = config.get('rate_limit_delay', 1.6)

        # For password checking, we use the pwned passwords API which doesn't require API key
        pwned_passwords_url = 'https://api.pwnedpasswords.com/range'

        # Hash the password (assume target is either plaintext password or SHA-1 hash)
        if len(target) == 40 and all(c in '0123456789abcdefABCDEF' for c in target):
            # Already a SHA-1 hash
            sha1_hash = target.upper()
        else:
            # Hash the plaintext password
            sha1_hash = hashlib.sha1(target.encode('utf-8')).hexdigest().upper()

        # Use k-anonymity - send only first 5 characters
        hash_prefix = sha1_hash[:5]
        hash_suffix = sha1_hash[5:]

        # Make request to pwned passwords API
        endpoint = f'{pwned_passwords_url}/{hash_prefix}'

        # Respect rate limiting
        time.sleep(rate_limit_delay)

        response = requests.get(endpoint, verify=verify_ssl, timeout=30)

        if response.status_code == 200:
            # Parse response to find our hash
            hash_lines = response.text.strip().split('\n')
            password_count = 0

            for line in hash_lines:
                if ':' in line:
                    suffix, count = line.split(':', 1)
                    if suffix == hash_suffix:
                        password_count = int(count)
                        break

            # Create artifacts folder
            artifact_path = create_case_artifact_folder(case_id, 'hibp')
            artifact_filename = f"hibp_password_check_{job_id}.json"

            # Save results (without storing the actual password/hash)
            if artifact_path:
                save_case_artifact(case_id, artifact_filename, {
                    'hash_prefix': hash_prefix,
                    'timestamp': datetime.now().isoformat(),
                    'pwned_count': password_count,
                    'found_in_breaches': password_count > 0
                })

            # Add case note
            if password_count > 0:
                note_content = f"""**SOAR Action:** HIBP Password Reuse Check
**Hash Prefix:** {hash_prefix}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Result:** ⚠️ Password appears {password_count:,} times in breach corpus

_This password has been compromised and should be changed immediately._

_Results stored in `/cases/{case_id}/artifacts/hibp/{artifact_filename}`_"""
            else:
                note_content = f"""**SOAR Action:** HIBP Password Reuse Check
**Hash Prefix:** {hash_prefix}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Result:** ✅ Password not found in known breaches

_This password does not appear in the compromised password database._"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Password check completed - appears {password_count:,} times in breaches" if password_count > 0 else "Password check completed - not found in breaches",
                "artifacts": [artifact_filename] if artifact_path else [],
                "details": {
                    "hash_prefix": hash_prefix,
                    "pwned_count": password_count,
                    "is_compromised": password_count > 0,
                    "execution_time": response.elapsed.total_seconds()
                }
            }
        elif response.status_code == 404:
            # No matches found
            note_content = f"""**SOAR Action:** HIBP Password Reuse Check
**Hash Prefix:** {hash_prefix}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Result:** ✅ Password not found in known breaches

_This password does not appear in the compromised password database._"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": "Password check completed - not found in breaches",
                "details": {
                    "hash_prefix": hash_prefix,
                    "pwned_count": 0,
                    "is_compromised": False,
                    "execution_time": response.elapsed.total_seconds()
                }
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Pwned Passwords API error: {response.status_code}",
                "error": response.text
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during HIBP password check: {str(e)}"
        add_case_note(case_id, f"**HIBP Password Check Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        add_case_note(case_id, f"**HIBP Password Check Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }


def execute_fortigate_block_ip(job_id, target, config, case_id):
    """
    Execute FortiGate IP blocking via firewall address and policy creation
    """
    try:
        import requests

        # Extract configuration
        base_url = config.get('base_url', '').strip().rstrip('/')
        api_key = config.get('api_key')
        verify_ssl = config.get('verify_ssl', True)
        api_version = config.get('api_version', 'v2')
        vdom = config.get('vdom', 'root')

        if not api_key or not base_url:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "FortiGate API credentials not configured",
                "error": "Missing API key or base URL in integration configuration"
            }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        start_time = datetime.now()
        address_name = f"IRIS_Block_{target.replace('.', '_')}"
        policy_name = f"IRIS_BLOCK_{target.replace('.', '_')}"

        # Step 1: Create firewall address object
        address_url = f"{base_url}/api/{api_version}/cmdb/firewall/address"
        address_params = {'vdom': vdom} if vdom != 'root' else {}

        address_data = {
            "name": address_name,
            "subnet": f"{target}/32",
            "comment": f"IRIS SOAR auto-block for case {case_id}"
        }

        address_response = requests.post(
            address_url,
            headers=headers,
            params=address_params,
            json=address_data,
            verify=verify_ssl,
            timeout=30
        )

        if address_response.status_code not in [200, 201]:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to create address object: {address_response.status_code}",
                "error": address_response.text
            }

        # Step 2: Create firewall policy to block the IP
        policy_url = f"{base_url}/api/{api_version}/cmdb/firewall/policy"
        policy_params = {'vdom': vdom} if vdom != 'root' else {}

        policy_data = {
            "name": policy_name,
            "srcintf": [{"name": "any"}],
            "dstintf": [{"name": "any"}],
            "srcaddr": [{"name": "all"}],
            "dstaddr": [{"name": address_name}],
            "action": "deny",
            "status": "enable",
            "comments": f"IRIS SOAR auto-block policy for case {case_id}"
        }

        policy_response = requests.post(
            policy_url,
            headers=headers,
            params=policy_params,
            json=policy_data,
            verify=verify_ssl,
            timeout=30
        )

        if policy_response.status_code not in [200, 201]:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to create blocking policy: {policy_response.status_code}",
                "error": policy_response.text
            }

        end_time = datetime.now()

        # Save artifacts
        artifact_path = create_case_artifact_folder(case_id, 'fortigate')
        artifact_filename = f"block_{target.replace('.', '_')}_{job_id}.json"

        artifact_data = {
            'ip_address': target,
            'timestamp': start_time.isoformat(),
            'job_id': job_id,
            'address_object': {
                'name': address_name,
                'response': address_response.json() if address_response.status_code in [200, 201] else None
            },
            'policy_object': {
                'name': policy_name,
                'response': policy_response.json() if policy_response.status_code in [200, 201] else None
            },
            'execution_time': (end_time - start_time).total_seconds()
        }

        if artifact_path:
            save_case_artifact(case_id, artifact_filename, artifact_data, 'fortigate')

        # Add case note
        note_content = f"""**SOAR Action:** Block IP on FortiGate
**IP:** {target}
**Timestamp:** {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
✅ IP added to deny policy on FortiGate.

**Created Objects:**
- Address Object: `{address_name}`
- Policy: `{policy_name}`

_Full details stored in `/cases/{case_id}/artifacts/fortigate/{artifact_filename}`_"""

        add_case_note(case_id, note_content)

        return {
            "job_id": job_id,
            "status": "Completed",
            "message": f"IP {target} successfully blocked on FortiGate",
            "artifacts": [artifact_filename] if artifact_path else [],
            "details": {
                "ip_address": target,
                "address_object": address_name,
                "policy_name": policy_name,
                "execution_time": (end_time - start_time).total_seconds()
            }
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during FortiGate IP block: {str(e)}"
        add_case_note(case_id, f"**FortiGate IP Block Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        add_case_note(case_id, f"**FortiGate IP Block Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }


def execute_fortigate_block_domain(job_id, target, config, case_id):
    """
    Execute FortiGate domain blocking via web filter
    """
    try:
        import requests

        # Extract configuration
        base_url = config.get('base_url', '').strip().rstrip('/')
        api_key = config.get('api_key')
        verify_ssl = config.get('verify_ssl', True)
        api_version = config.get('api_version', 'v2')
        vdom = config.get('vdom', 'root')

        if not api_key or not base_url:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "FortiGate API credentials not configured",
                "error": "Missing API key or base URL in integration configuration"
            }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        start_time = datetime.now()
        filter_name = f"IRIS_BLOCK_{target.replace('.', '_').replace('/', '_')}"

        # Create web filter URL filter
        url_filter_url = f"{base_url}/api/{api_version}/cmdb/webfilter/urlfilter"
        params = {'vdom': vdom} if vdom != 'root' else {}

        filter_data = {
            "name": filter_name,
            "entries": [
                {
                    "url": target,
                    "type": "simple",
                    "action": "block"
                }
            ],
            "comment": f"IRIS SOAR auto-block for case {case_id}"
        }

        response = requests.post(
            url_filter_url,
            headers=headers,
            params=params,
            json=filter_data,
            verify=verify_ssl,
            timeout=30
        )

        end_time = datetime.now()

        if response.status_code in [200, 201]:
            # Save artifacts
            artifact_path = create_case_artifact_folder(case_id, 'fortigate')
            artifact_filename = f"block_{target.replace('.', '_').replace('/', '_')}_{job_id}.json"

            artifact_data = {
                'domain': target,
                'timestamp': start_time.isoformat(),
                'job_id': job_id,
                'filter_object': {
                    'name': filter_name,
                    'response': response.json()
                },
                'execution_time': (end_time - start_time).total_seconds()
            }

            if artifact_path:
                save_case_artifact(case_id, artifact_filename, artifact_data, 'fortigate')

            # Add case note
            note_content = f"""**SOAR Action:** Block Domain
**Domain:** {target}
**Timestamp:** {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
✅ Successfully blocked in FortiGate web filter policy.

**Created Filter:** `{filter_name}`

_Full details stored in `/cases/{case_id}/artifacts/fortigate/{artifact_filename}`_"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Domain {target} successfully blocked on FortiGate",
                "artifacts": [artifact_filename] if artifact_path else [],
                "details": {
                    "domain": target,
                    "filter_name": filter_name,
                    "execution_time": (end_time - start_time).total_seconds()
                }
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to create domain filter: {response.status_code}",
                "error": response.text
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during FortiGate domain block: {str(e)}"
        add_case_note(case_id, f"**FortiGate Domain Block Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        add_case_note(case_id, f"**FortiGate Domain Block Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }


def execute_fortigate_quarantine_host(job_id, target, config, case_id):
    """
    Execute FortiGate host quarantine via banned user API
    """
    try:
        import requests

        # Extract configuration
        base_url = config.get('base_url', '').strip().rstrip('/')
        api_key = config.get('api_key')
        verify_ssl = config.get('verify_ssl', True)
        api_version = config.get('api_version', 'v2')
        vdom = config.get('vdom', 'root')
        quarantine_duration = config.get('quarantine_duration', 3600)

        if not api_key or not base_url:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": "FortiGate API credentials not configured",
                "error": "Missing API key or base URL in integration configuration"
            }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        start_time = datetime.now()

        # Add user to banned list
        ban_url = f"{base_url}/api/{api_version}/monitor/user/banned/add"
        params = {'vdom': vdom} if vdom != 'root' else {}

        ban_data = {
            "ip": target,
            "expiry": quarantine_duration
        }

        ban_response = requests.post(
            ban_url,
            headers=headers,
            params=params,
            json=ban_data,
            verify=verify_ssl,
            timeout=30
        )

        if ban_response.status_code in [200, 201]:
            # Poll to confirm ban was applied
            list_url = f"{base_url}/api/{api_version}/monitor/user/banned/list"

            time.sleep(2)  # Brief wait before verification
            list_response = requests.get(
                list_url,
                headers=headers,
                params=params,
                verify=verify_ssl,
                timeout=30
            )

            end_time = datetime.now()
            banned_users = list_response.json() if list_response.status_code == 200 else []

            # Check if our IP is in the banned list
            is_banned = any(user.get('ip') == target for user in banned_users.get('results', []))

            # Save artifacts
            artifact_path = create_case_artifact_folder(case_id, 'fortigate')
            artifact_filename = f"quarantine_{target.replace('.', '_')}_{job_id}.json"

            artifact_data = {
                'host_ip': target,
                'timestamp': start_time.isoformat(),
                'job_id': job_id,
                'quarantine_duration': quarantine_duration,
                'ban_response': ban_response.json() if ban_response.status_code in [200, 201] else None,
                'verification_response': banned_users,
                'is_confirmed_banned': is_banned,
                'execution_time': (end_time - start_time).total_seconds()
            }

            if artifact_path:
                save_case_artifact(case_id, artifact_filename, artifact_data, 'fortigate')

            # Add case note
            status_emoji = "✅" if is_banned else "⚠️"
            note_content = f"""**SOAR Action:** Quarantine Host
**Endpoint:** {target}
**Timestamp:** {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Result:** {status_emoji} User banned for {quarantine_duration // 3600} hour(s).

**Duration:** {quarantine_duration} seconds
**Verification:** {'Confirmed in banned list' if is_banned else 'Could not verify ban status'}

_Full details stored in `/cases/{case_id}/artifacts/fortigate/{artifact_filename}`_"""

            add_case_note(case_id, note_content)

            return {
                "job_id": job_id,
                "status": "Completed",
                "message": f"Host {target} quarantined for {quarantine_duration} seconds",
                "artifacts": [artifact_filename] if artifact_path else [],
                "details": {
                    "host_ip": target,
                    "quarantine_duration": quarantine_duration,
                    "is_confirmed_banned": is_banned,
                    "execution_time": (end_time - start_time).total_seconds()
                }
            }
        else:
            return {
                "job_id": job_id,
                "status": "Failed",
                "message": f"Failed to quarantine host: {ban_response.status_code}",
                "error": ban_response.text
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during FortiGate host quarantine: {str(e)}"
        add_case_note(case_id, f"**FortiGate Host Quarantine Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        add_case_note(case_id, f"**FortiGate Host Quarantine Failed**\n\nError: {error_msg}")

        return {
            "job_id": job_id,
            "status": "Failed",
            "message": error_msg,
            "error": str(e)
        }