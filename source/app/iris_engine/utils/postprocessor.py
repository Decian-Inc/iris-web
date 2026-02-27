#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS) - DFIR-IRIS Team
#  ir@cyberactionlab.net - contact@dfir-iris.org
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

import requests as http_requests
from app import app
from app.util import response_error


def get_postprocessor_url():
    url = app.config.get('POSTPROCESSOR_URL', '')
    if not url:
        return None
    return url.rstrip('/')


def postprocessor_get(path, params=None, timeout=15):
    base = get_postprocessor_url()
    if not base:
        return None, response_error(
            'Postprocessor URL is not configured. Set IRIS_POSTPROCESSOR_URL environment variable.',
            status=500
        )
    try:
        resp = http_requests.get(f"{base}{path}", params=params, timeout=timeout)
        return resp, None
    except http_requests.exceptions.ConnectionError:
        return None, response_error('Unable to connect to postprocessor service')
    except http_requests.exceptions.Timeout:
        return None, response_error('Postprocessor service request timed out')
    except Exception as e:
        app.logger.error(f"Postprocessor GET {path} failed: {e}")
        return None, response_error(f'Postprocessor request failed: {str(e)}')


def postprocessor_post(path, json_data=None, timeout=15):
    base = get_postprocessor_url()
    if not base:
        return None, response_error(
            'Postprocessor URL is not configured. Set IRIS_POSTPROCESSOR_URL environment variable.',
            status=500
        )
    try:
        resp = http_requests.post(f"{base}{path}", json=json_data, timeout=timeout)
        return resp, None
    except http_requests.exceptions.ConnectionError:
        return None, response_error('Unable to connect to postprocessor service')
    except http_requests.exceptions.Timeout:
        return None, response_error('Postprocessor service request timed out')
    except Exception as e:
        app.logger.error(f"Postprocessor POST {path} failed: {e}")
        return None, response_error(f'Postprocessor request failed: {str(e)}')


def postprocessor_put(path, json_data=None, timeout=15):
    base = get_postprocessor_url()
    if not base:
        return None, response_error(
            'Postprocessor URL is not configured. Set IRIS_POSTPROCESSOR_URL environment variable.',
            status=500
        )
    try:
        resp = http_requests.put(f"{base}{path}", json=json_data, timeout=timeout)
        return resp, None
    except http_requests.exceptions.ConnectionError:
        return None, response_error('Unable to connect to postprocessor service')
    except http_requests.exceptions.Timeout:
        return None, response_error('Postprocessor service request timed out')
    except Exception as e:
        app.logger.error(f"Postprocessor PUT {path} failed: {e}")
        return None, response_error(f'Postprocessor request failed: {str(e)}')


def postprocessor_patch(path, json_data=None, timeout=15):
    base = get_postprocessor_url()
    if not base:
        return None, response_error(
            'Postprocessor URL is not configured. Set IRIS_POSTPROCESSOR_URL environment variable.',
            status=500
        )
    try:
        resp = http_requests.patch(f"{base}{path}", json=json_data, timeout=timeout)
        return resp, None
    except http_requests.exceptions.ConnectionError:
        return None, response_error('Unable to connect to postprocessor service')
    except http_requests.exceptions.Timeout:
        return None, response_error('Postprocessor service request timed out')
    except Exception as e:
        app.logger.error(f"Postprocessor PATCH {path} failed: {e}")
        return None, response_error(f'Postprocessor request failed: {str(e)}')


def postprocessor_delete(path, timeout=15):
    base = get_postprocessor_url()
    if not base:
        return None, response_error(
            'Postprocessor URL is not configured. Set IRIS_POSTPROCESSOR_URL environment variable.',
            status=500
        )
    try:
        resp = http_requests.delete(f"{base}{path}", timeout=timeout)
        return resp, None
    except http_requests.exceptions.ConnectionError:
        return None, response_error('Unable to connect to postprocessor service')
    except http_requests.exceptions.Timeout:
        return None, response_error('Postprocessor service request timed out')
    except Exception as e:
        app.logger.error(f"Postprocessor DELETE {path} failed: {e}")
        return None, response_error(f'Postprocessor request failed: {str(e)}')
