import requests as http_requests
from app import app
from app.util import response_error


def get_aisocagent_url():
    url = app.config.get('AISOCAGENT_URL', '')
    if not url:
        return None
    return url.rstrip('/')


def aisocagent_get(path, params=None, timeout=30):
    base = get_aisocagent_url()
    if not base:
        return None, response_error(
            'AI SOC Agent URL is not configured. Set IRIS_AISOCAGENT_URL environment variable.',
            status=500
        )
    try:
        resp = http_requests.get(f"{base}{path}", params=params, timeout=timeout)
        return resp, None
    except http_requests.exceptions.ConnectionError:
        return None, response_error('Unable to connect to AI SOC Agent service')
    except http_requests.exceptions.Timeout:
        return None, response_error('AI SOC Agent service request timed out')
    except Exception as e:
        app.logger.error(f"AI SOC Agent GET {path} failed: {e}")
        return None, response_error(f'AI SOC Agent request failed: {str(e)}')


def aisocagent_post(path, json_data=None, timeout=600):
    base = get_aisocagent_url()
    if not base:
        return None, response_error(
            'AI SOC Agent URL is not configured. Set IRIS_AISOCAGENT_URL environment variable.',
            status=500
        )
    try:
        resp = http_requests.post(f"{base}{path}", json=json_data, timeout=timeout)
        return resp, None
    except http_requests.exceptions.ConnectionError:
        return None, response_error('Unable to connect to AI SOC Agent service')
    except http_requests.exceptions.Timeout:
        return None, response_error('AI SOC Agent service request timed out (analysis may still be running)')
    except Exception as e:
        app.logger.error(f"AI SOC Agent POST {path} failed: {e}")
        return None, response_error(f'AI SOC Agent request failed: {str(e)}')
