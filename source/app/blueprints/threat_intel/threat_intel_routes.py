#  IRIS Source Code
#  DFIR-IRIS Team
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

import requests
import json
import urllib3
from flask import Blueprint, request, flash, redirect, url_for
from flask import render_template
from flask_login import current_user
from flask_wtf import FlaskForm

from app.util import ac_requires, response_success, response_error

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

threat_intel_blueprint = Blueprint(
    'threat_intel',
    __name__,
    template_folder='templates'
)

# MISP Configuration
MISP_URL = "https://misp.ironclad.decianx"
MISP_API_KEY = "Nn5NRLKfmdJNDZA64MV15s5PqGbradL253RG9T2Z"

def submit_to_misp(ioc_value, ioc_type, category="Network activity", comment=""):
    """Submit IOC to MISP instance"""

    headers = {
        "Authorization": MISP_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Map IOC types to appropriate categories
    category_mapping = {
        "ip-dst": "Network activity",
        "ip-src": "Network activity",
        "domain": "Network activity",
        "url": "Network activity",
        "email": "Payload delivery",
        "md5": "Payload delivery",
        "sha256": "Payload delivery",
        "filename": "Payload delivery"
    }

    category = category_mapping.get(ioc_type, "Network activity")

    # Create a new event first
    event_data = {
        "info": f"Threat Intel Submission - {ioc_type.upper()} IOC",
        "distribution": "1",  # This community only
        "threat_level_id": "2",  # Medium
        "analysis": "1",  # Initial
        "orgc_id": "1",
        "org_id": "1",
        "published": False
    }

    try:
        # Create event
        event_response = requests.post(
            f"{MISP_URL}/events/add",
            headers=headers,
            json=event_data,
            verify=False
        )

        if event_response.status_code != 200:
            return False, f"Failed to create MISP event: {event_response.text}"

        event_result = event_response.json()
        event_id = event_result["Event"]["id"]

        # Add attribute to event
        attribute_data = {
            "value": ioc_value,
            "type": ioc_type,
            "category": category,
            "to_ids": True,
            "comment": comment,
            "distribution": "1"
        }

        attr_response = requests.post(
            f"{MISP_URL}/attributes/add/{event_id}",
            headers=headers,
            json=attribute_data,
            verify=False
        )

        if attr_response.status_code == 200:
            return True, "IOC successfully submitted to MISP"
        else:
            return False, f"Failed to add attribute: {attr_response.text}"

    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


@threat_intel_blueprint.route('/threat-intel', methods=['GET'])
@ac_requires()
def threat_intel_page(caseid, url_redir):
    """
    Return the threat intelligence page
    """
    form = FlaskForm()
    return render_template('threat_intel.html', form=form)


@threat_intel_blueprint.route('/threat-intel/submit', methods=['POST'])
@ac_requires()
def submit_threat_intel(caseid, url_redir):
    """
    Submit IOC to MISP
    """
    ioc_value = request.form.get('ioc_value', '').strip()
    ioc_type = request.form.get('ioc_type', '')
    comment = request.form.get('comment', '')

    if not ioc_value or not ioc_type:
        flash('IOC value and type are required', 'error')
        return redirect(url_for('threat_intel.threat_intel_page'))

    success, message = submit_to_misp(ioc_value, ioc_type, comment=comment)

    if success:
        flash(f'Successfully submitted {ioc_type}: {ioc_value} to MISP', 'success')
    else:
        flash(f'Failed to submit IOC: {message}', 'error')

    return redirect(url_for('threat_intel.threat_intel_page'))