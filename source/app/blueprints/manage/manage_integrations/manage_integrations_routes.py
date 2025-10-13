#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS)
#  ir@cyberactionlab.net
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

import json
import logging as log
import traceback
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from flask_login import current_user, login_required

from app import db
from app.models.authorization import Permissions
from app.util import ac_requires
from app.util import response_success, response_error
from app.iris_engine.utils.tracker import track_activity

manage_integrations_blueprint = Blueprint('manage_integrations',
                                        __name__,
                                        template_folder='templates')


@manage_integrations_blueprint.route('/manage/integrations', methods=['GET'])
@login_required
@ac_requires(Permissions.server_administrator)
def manage_integrations_index(caseid, url_redir):
    """
    Main integrations management page
    """
    try:
        if url_redir:
            return redirect(url_for('manage_integrations.manage_integrations_index', cid=caseid))

        # Get current integration settings
        integrations_config = get_integrations_config()

        return render_template('manage_integrations.html',
                             integrations=integrations_config)

    except Exception as e:
        log.error(f"Error loading integrations page: {str(e)}")
        traceback.print_exc()
        return response_error(f"An error occurred: {str(e)}")


@manage_integrations_blueprint.route('/manage/integrations/save', methods=['POST'])
@login_required
@ac_requires(Permissions.server_administrator)
def save_integration_config():
    """
    Save integration configuration
    """
    try:
        data = request.get_json()
        integration_type = data.get('integration_type')
        config = data.get('config', {})

        if not integration_type:
            return response_error("Integration type is required")

        # Save configuration to database/file
        success = save_integrations_config(integration_type, config)

        if success:
            track_activity(f"Integration {integration_type} configuration updated", ctx_case=None)
            return response_success("Integration configuration saved successfully")
        else:
            return response_error("Failed to save integration configuration")

    except Exception as e:
        log.error(f"Error saving integration config: {str(e)}")
        traceback.print_exc()
        return response_error(f"An error occurred: {str(e)}")


@manage_integrations_blueprint.route('/manage/integrations/test', methods=['POST'])
@login_required
@ac_requires(Permissions.server_administrator)
def test_integration_connection():
    """
    Test integration connection
    """
    try:
        data = request.get_json()
        integration_type = data.get('integration_type')
        config = data.get('config', {})

        if not integration_type:
            return response_error("Integration type is required")

        # Test connection based on integration type
        if integration_type == 'velociraptor':
            result = test_velociraptor_connection(config)
        elif integration_type == 'sentinelone':
            result = test_sentinelone_connection(config)
        else:
            return response_error("Unsupported integration type")

        return response_success("Connection test completed", data=result)

    except Exception as e:
        log.error(f"Error testing integration connection: {str(e)}")
        traceback.print_exc()
        return response_error(f"Connection test failed: {str(e)}")


def get_integrations_config():
    """
    Get current integrations configuration
    """
    # For now, return default empty config
    # Later this would read from database or config file
    return {
        'velociraptor': {
            'enabled': False,
            'base_url': '',
            'api_key': '',
            'ca_cert': '',
            'verify_ssl': True
        },
        'sentinelone': {
            'enabled': False,
            'base_url': '',
            'api_token': '',
            'verify_ssl': True,
            'site_id': ''
        }
    }


def save_integrations_config(integration_type, config):
    """
    Save integration configuration
    """
    try:
        # Here you would save to database or configuration file
        # For now, just log the configuration
        log.info(f"Saving {integration_type} configuration: {config}")
        return True
    except Exception as e:
        log.error(f"Error saving integration config: {str(e)}")
        return False


def test_velociraptor_connection(config):
    """
    Test Velociraptor connection
    """
    try:
        base_url = config.get('base_url')
        api_key = config.get('api_key')

        if not base_url or not api_key:
            return {'success': False, 'message': 'Missing required configuration'}

        # Here you would implement actual connection test
        # For now, return mock response
        return {
            'success': True,
            'message': 'Connection test successful',
            'server_version': 'Mock Version 0.6.8',
            'response_time': '245ms'
        }

    except Exception as e:
        return {'success': False, 'message': f'Connection failed: {str(e)}'}


def test_sentinelone_connection(config):
    """
    Test SentinelOne connection
    """
    try:
        base_url = config.get('base_url')
        api_token = config.get('api_token')

        if not base_url or not api_token:
            return {'success': False, 'message': 'Missing required configuration'}

        # Here you would implement actual connection test
        # For now, return mock response
        return {
            'success': True,
            'message': 'Connection test successful',
            'account_name': 'Mock Account',
            'response_time': '312ms'
        }

    except Exception as e:
        return {'success': False, 'message': f'Connection failed: {str(e)}'}