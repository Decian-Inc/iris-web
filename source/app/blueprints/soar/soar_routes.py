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
from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from flask import redirect
from flask import url_for
from flask_login import current_user, login_required

from app import db
from app.datamgmt.case.case_db import get_case
from app.util import response_success, response_error

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

        return render_template('soar.html',
                             case=case,
                             case_id=caseid)

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

        # TODO: Implement job creation and execution logic
        # For now, return a mock response
        job_result = {
            "job_id": "job-new-123",
            "status": "Queued",
            "message": "Job has been queued for execution",
            "estimated_duration": "5-10 minutes"
        }

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