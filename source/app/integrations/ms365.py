#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS) - https://www.airbus-cyber-security.com
#
#  Licensed under the LGPL v3.0 - the "License";
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/lgpl-3.0.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging as log
import requests
from typing import Union, Optional

from app.models.integrations import IntegrationConfig
from app.models.ms365_recipients import MS365NotificationRecipient
from app.util_crypto import decrypt_field

_TOKEN_URL = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
_SEND_MAIL_URL = 'https://graph.microsoft.com/v1.0/users/{from_email}/sendMail'


def _load_auth_config() -> Optional[dict]:
    record = IntegrationConfig.query.filter_by(integration_type='ms365').first()
    if not record or not record.enabled:
        return None

    config = dict(record.config_data or {})

    raw_secret = config.get('client_secret', '')
    if raw_secret:
        try:
            config['client_secret'] = decrypt_field(raw_secret)
        except Exception:
            log.error('MS365: failed to decrypt client_secret — re-enter it in integrations settings')
            return None

    return config


def _get_access_token(tenant_id: str, client_id: str, client_secret: str) -> Optional[str]:
    try:
        response = requests.post(
            _TOKEN_URL.format(tenant_id=tenant_id),
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'https://graph.microsoft.com/.default'
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        log.error(f'MS365: token request failed: {e}')
        return None


def _send_email(token: str, from_email: str, recipients: list[str], case) -> None:
    to_recipients = [{'emailAddress': {'address': addr}} for addr in recipients]

    client_name = case.client.name if hasattr(case, 'client') and case.client else 'N/A'

    payload = {
        'message': {
            'subject': f'[IRIS] New Case Created: {case.name}',
            'body': {
                'contentType': 'HTML',
                'content': (
                    f'<h3>New IRIS Case Created</h3>'
                    f'<p><strong>Case:</strong> {case.name}</p>'
                    f'<p><strong>Case ID:</strong> {case.case_id}</p>'
                    f'<p><strong>Client:</strong> {client_name}</p>'
                    f'<p><strong>Description:</strong> {case.description or "No description provided"}</p>'
                )
            },
            'toRecipients': to_recipients
        },
        'saveToSentItems': False
    }

    try:
        response = requests.post(
            _SEND_MAIL_URL.format(from_email=from_email),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        log.info(f'MS365: email sent for case {case.case_id}')
    except Exception as e:
        log.error(f'MS365: email failed for case {case.case_id}: {e}')


def _send_teams_webhook(webhook_url: str, case) -> None:
    client_name = case.client.name if hasattr(case, 'client') and case.client else 'N/A'

    payload = {
        '@type': 'MessageCard',
        '@context': 'http://schema.org/extensions',
        'themeColor': '0078d4',
        'summary': f'New IRIS Case: {case.name}',
        'sections': [{
            'activityTitle': f'New Case Created: {case.name}',
            'facts': [
                {'name': 'Case ID', 'value': str(case.case_id)},
                {'name': 'Client', 'value': client_name},
                {'name': 'Description', 'value': case.description or 'No description provided'}
            ]
        }]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        log.info(f'MS365: Teams notification sent for case {case.case_id}')
    except Exception as e:
        log.error(f'MS365: Teams notification failed for case {case.case_id}: {e}')


def notify_case_created(case) -> None:
    config = _load_auth_config()
    if not config:
        return

    if config.get('send_email'):
        rows = MS365NotificationRecipient.query.filter_by(channel_type='email', enabled=True).all()
        emails = [r.address for r in rows]
        if emails:
            token = _get_access_token(
                config.get('tenant_id', ''),
                config.get('client_id', ''),
                config.get('client_secret', '')
            )
            if token:
                _send_email(token, config.get('from_email', ''), emails, case)

    if config.get('send_teams'):
        rows = MS365NotificationRecipient.query.filter_by(channel_type='teams', enabled=True).all()
        for row in rows:
            try:
                webhook_url = decrypt_field(row.address)
                _send_teams_webhook(webhook_url, case)
            except Exception as e:
                log.error(f'MS365: failed to decrypt Teams webhook for recipient {row.id}: {e}')