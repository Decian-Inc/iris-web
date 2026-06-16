MS365 Graph API Integration — Implementation Guide
Overview
This integration sends email and/or Microsoft Teams notifications when new IRIS cases are created. The two notification channels are independently toggleable. Recipients for each channel are managed in a dedicated database table — individual addresses and channels can be added, removed, or temporarily disabled at any time without affecting anything else. Sensitive credentials are encrypted at rest using a key derived from IRIS's existing master secret. No new environment variables or pod restarts are required beyond a normal code deployment.

Part 1: Azure Setup (MSP Admin — Done Once Per Deployment)
1.1 Register an Azure AD Application
Sign into portal.azure.com as a Global Administrator
Go to Azure Active Directory → App registrations → New registration
Fill in:
Name: IRIS Case Notifications
Supported account types: Accounts in this organizational directory only
Redirect URI: leave blank
Click Register
Copy the Application (client) ID and Directory (tenant) ID from the overview page
1.2 Add API Permissions
Go to API permissions → Add a permission → Microsoft Graph → Application permissions
Add Mail.Send — required for email notifications
Add ChannelMessage.Send — required only if using Graph API for Teams (skip if using webhook URLs)
Click Grant admin consent for [your tenant] and confirm
1.3 Create a Client Secret
Go to Certificates & secrets → New client secret
Set an expiry (12 or 24 months)
Copy the Value immediately — it will not be shown again
1.4 Teams Webhook URL (Simpler Teams Option)
If you prefer not to configure ChannelMessage.Send in Azure:

In Microsoft Teams, open the target channel → ⋯ → Connectors
Add Incoming Webhook → name it → copy the URL
Paste this URL into the IRIS Teams channel list when adding a recipient. No additional Azure permissions or Teams app installation needed. This is the recommended Teams path for initial setup.

Part 2: Design Decisions
Recipient Storage
Recipients are stored in a dedicated ms365_notification_recipients table — one row per recipient. This means:

Adding a recipient inserts one row
Removing a recipient deletes one row
Temporarily disabling a recipient flips one boolean
None of these operations touch any other configuration
The main integration_config record for ms365 holds only credentials and channel toggles:

integration_config (type='ms365') config_data:
  tenant_id       → plain text
  client_id       → plain text
  client_secret   → ENCRYPTED
  from_email      → plain text
  send_email      → boolean
  send_teams      → boolean

ms365_notification_recipients table:
  id            → PK
  channel_type  → 'email' or 'teams'
  address       → email address (plain) or webhook URL (ENCRYPTED)
  display_name  → optional label
  enabled       → boolean
  created_at    → timestamp
  created_by    → username

Teams webhook URLs are encrypted per-row because they grant write access to a Teams channel. Email addresses are plain text.

Merge Strategy for Main Config
The main config (credentials + toggles) uses a merge-on-save approach:

Load existing DB config first
Apply incoming form values on top
For encrypted fields (client_secret): only overwrite if the incoming value is non-empty and not the 'configured' sentinel placeholder
Toggling send_email or send_teams off does not touch the recipients table — recipients stay in the DB and are immediately active again when the toggle is turned back on
Recipient UI Pattern
The recipient list has no Save button. Each action (Add, Remove, Toggle) hits an API endpoint immediately and the list re-renders. This is the same pattern used in live-editable lists elsewhere in IRIS.

Part 3: Code Implementation
File Map
source/app/
├── util_crypto.py                                                   NEW
├── integrations/
│   ├── __init__.py                                                  NEW (empty)
│   └── ms365.py                                                     NEW
├── models/
│   └── ms365_recipients.py                                          NEW
├── alembic/versions/
│   ├── 0d65689ff497_add_ms365_integration_config.py                 NEW
│   └── 0d65689ff498_add_ms365_notification_recipients.py            NEW
├── business/
│   └── cases.py                                                     MODIFIED (~line 107)
└── blueprints/
    ├── overview/templates/
    │   └── overview_docs.html                                       MODIFIED
    └── manage/manage_integrations/
        ├── manage_integrations_routes.py                            MODIFIED
        └── templates/
            └── manage_integrations.html                            MODIFIED

Step 1: Encryption Utility
New file: source/app/util_crypto.py

Takes the master key IRIS already has and derives a dedicated encryption key from it using HKDF. The same input always produces the same output so the derived key never needs to be stored anywhere. The cryptography library is already present in the project.

#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS) ...
#  [standard LGPL header]

import base64
import logging as log

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import current_app


def _derive_integration_key() -> bytes:
    secret = current_app.config['SECRET_KEY']
    if isinstance(secret, str):
        secret = secret.encode()

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'iris-integration-encryption'
    )
    return base64.urlsafe_b64encode(hkdf.derive(secret))


def encrypt_field(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    try:
        return Fernet(_derive_integration_key()).encrypt(plaintext.encode()).decode()
    except Exception as e:
        log.error(f'Failed to encrypt integration field: {e}')
        raise


def decrypt_field(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    try:
        return Fernet(_derive_integration_key()).decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        log.error('Failed to decrypt integration field - key mismatch or data corrupted')
        raise
    except Exception as e:
        log.error(f'Failed to decrypt integration field: {e}')
        raise

Step 2: Recipients Model
New file: source/app/models/ms365_recipients.py

#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS) ...
#  [standard LGPL header]

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app import db


class MS365NotificationRecipient(db.Model):
    __tablename__ = 'ms365_notification_recipients'

    id = Column(Integer, primary_key=True)
    channel_type = Column(String(10), nullable=False)   # 'email' or 'teams'
    address = Column(Text, nullable=False)              # email address or encrypted webhook URL
    display_name = Column(String(255), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)

Step 3: Alembic Migrations
Two migrations — one for the main config row, one for the recipients table.

New file: source/app/alembic/versions/0d65689ff497_add_ms365_integration_config.py

"""Add MS365 integration config

Revision ID: 0d65689ff497
Revises: 0d65689ff496
Create Date: 2026-04-23 00:00:00.000000
"""
from alembic import op
import json

revision = '0d65689ff497'
down_revision = '0d65689ff496'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(f"""
        INSERT INTO integration_config (integration_type, enabled, config_data, created_by, description)
        VALUES (
            'ms365',
            FALSE,
            '{json.dumps({
                "tenant_id": "",
                "client_id": "",
                "client_secret": "",
                "from_email": "",
                "send_email": False,
                "send_teams": False
            })}',
            'system',
            'Microsoft 365 integration for email and Teams notifications on case creation'
        )
        ON CONFLICT (integration_type) DO NOTHING;
    """)


def downgrade():
    op.execute("DELETE FROM integration_config WHERE integration_type = 'ms365';")

New file: source/app/alembic/versions/0d65689ff498_add_ms365_notification_recipients.py

"""Add MS365 notification recipients table

Revision ID: 0d65689ff498
Revises: 0d65689ff497
Create Date: 2026-04-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0d65689ff498'
down_revision = '0d65689ff497'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ms365_notification_recipients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('channel_type', sa.String(10), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255), nullable=True)
    )
    op.create_index('ix_ms365_recipients_channel', 'ms365_notification_recipients', ['channel_type'])


def downgrade():
    op.drop_index('ix_ms365_recipients_channel', table_name='ms365_notification_recipients')
    op.drop_table('ms365_notification_recipients')

Both run automatically on the next pod restart via post_init.py. No manual steps needed.

Step 4: MS365 Notification Module
New file: source/app/integrations/__init__.py — leave empty.

New file: source/app/integrations/ms365.py

#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS) ...
#  [standard LGPL header]

import logging as log
import requests

from app.models.integrations import IntegrationConfig
from app.models.ms365_recipients import MS365NotificationRecipient
from app.util_crypto import decrypt_field

_TOKEN_URL = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
_SEND_MAIL_URL = 'https://graph.microsoft.com/v1.0/users/{from_email}/sendMail'


def _load_auth_config() -> dict | None:
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


def _get_access_token(tenant_id: str, client_id: str, client_secret: str) -> str | None:
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

Step 5: Update Integration Routes
Modified file: source/app/blueprints/manage/manage_integrations/manage_integrations_routes.py

5a. Add imports (~line 37):

from app.util_crypto import encrypt_field, decrypt_field
from app.models.ms365_recipients import MS365NotificationRecipient

5b. Add ms365 to default_configs inside get_integrations_config():

'ms365': {
    'enabled': False,
    'tenant_id': '',
    'client_id': '',
    'client_secret': '',
    'from_email': '',
    'send_email': False,
    'send_teams': False
},

5c. Add the merge helper and mask helper before save_integrations_config():

def _merge_ms365_config(incoming: dict, existing: dict) -> dict:
    merged = dict(existing)

    for field in ('enabled', 'tenant_id', 'client_id', 'from_email', 'send_email', 'send_teams'):
        if field in incoming:
            merged[field] = incoming[field]

    new_secret = incoming.get('client_secret', '')
    if new_secret and new_secret != 'configured':
        merged['client_secret'] = encrypt_field(new_secret)

    return merged


def _mask_ms365_config(config: dict) -> dict:
    masked = dict(config)
    if masked.get('client_secret'):
        masked['client_secret'] = 'configured'
    return masked

5d. Apply the merge in save_integrations_config() — when building what gets written to config_data:

if integration_type == 'ms365':
    existing_data = integration_config.config_data or {} if integration_config else {}
    config_data_to_save = _merge_ms365_config(config, existing_data)
else:
    config_data_to_save = {k: v for k, v in config.items() if k != 'enabled'}

Use config_data_to_save when assigning to integration_config.config_data.

5e. Apply the mask in get_integrations_config() after building the result dict:

if 'ms365' in result:
    result['ms365'] = _mask_ms365_config(result['ms365'])

5f. Add the test connection function after test_fortigate_connection:

def test_ms365_connection(config: dict) -> dict:
    tenant_id = config.get('tenant_id', '').strip()
    client_id = config.get('client_id', '').strip()
    client_secret = config.get('client_secret', '').strip()

    if not all([tenant_id, client_id, client_secret]):
        return {'success': False, 'message': 'tenant_id, client_id, and client_secret are all required'}

    if client_secret == 'configured':
        existing = IntegrationConfig.query.filter_by(integration_type='ms365').first()
        if not existing or not existing.config_data:
            return {'success': False, 'message': 'No stored secret found — enter a new client secret'}
        try:
            client_secret = decrypt_field(existing.config_data.get('client_secret', ''))
        except Exception:
            return {'success': False, 'message': 'Stored secret could not be decrypted — re-enter it'}

    try:
        response = requests.post(
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'https://graph.microsoft.com/.default'
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'message': 'Successfully authenticated with Microsoft Graph',
                'tenant_id': tenant_id,
                'token_expires_in': data.get('expires_in')
            }

        error = response.json()
        return {
            'success': False,
            'message': f'Authentication failed: {error.get("error_description", response.text)}'
        }

    except requests.exceptions.Timeout:
        return {'success': False, 'message': 'Connection timed out reaching login.microsoftonline.com'}
    except Exception as e:
        return {'success': False, 'message': f'Connection test failed: {str(e)}'}

5g. Add ms365 to the test route handler in test_integration_connection():

elif integration_type == 'ms365':
    result = test_ms365_connection(config)

5h. Add the four recipient management routes — these are new routes on the same blueprint:

@manage_integrations_blueprint.route('/manage/integrations/ms365/recipients', methods=['GET'])
@login_required
@ac_requires(Permissions.server_administrator, no_cid_required=True)
def ms365_list_recipients(caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_integrations.manage_integrations_index', cid=caseid))

    rows = MS365NotificationRecipient.query.order_by(
        MS365NotificationRecipient.channel_type,
        MS365NotificationRecipient.id
    ).all()

    result = []
    for row in rows:
        display_address = row.address
        if row.channel_type == 'teams':
            display_address = 'configured'

        result.append({
            'id': row.id,
            'channel_type': row.channel_type,
            'address': display_address,
            'display_name': row.display_name or '',
            'enabled': row.enabled,
            'created_by': row.created_by or '',
            'created_at': row.created_at.isoformat() if row.created_at else ''
        })

    return response_success('', data=result)


@manage_integrations_blueprint.route('/manage/integrations/ms365/recipients/add', methods=['POST'])
@login_required
@ac_requires(Permissions.server_administrator, no_cid_required=True)
def ms365_add_recipient(caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_integrations.manage_integrations_index', cid=caseid))

    data = request.get_json()
    channel_type = data.get('channel_type', '').strip()
    address = data.get('address', '').strip()
    display_name = data.get('display_name', '').strip()

    if channel_type not in ('email', 'teams'):
        return response_error('channel_type must be email or teams')

    if not address:
        return response_error('address is required')

    stored_address = encrypt_field(address) if channel_type == 'teams' else address

    recipient = MS365NotificationRecipient(
        channel_type=channel_type,
        address=stored_address,
        display_name=display_name or None,
        enabled=True,
        created_by=current_user.name if current_user.is_authenticated else 'system'
    )
    db.session.add(recipient)
    db.session.commit()

    track_activity(f'MS365 {channel_type} recipient added', caseid=None)

    return response_success('Recipient added', data={
        'id': recipient.id,
        'channel_type': recipient.channel_type,
        'address': 'configured' if channel_type == 'teams' else address,
        'display_name': recipient.display_name or '',
        'enabled': recipient.enabled
    })


@manage_integrations_blueprint.route('/manage/integrations/ms365/recipients/<int:recipient_id>', methods=['DELETE'])
@login_required
@ac_requires(Permissions.server_administrator, no_cid_required=True)
def ms365_remove_recipient(caseid, url_redir, recipient_id):
    if url_redir:
        return redirect(url_for('manage_integrations.manage_integrations_index', cid=caseid))

    recipient = MS365NotificationRecipient.query.get(recipient_id)
    if not recipient:
        return response_error('Recipient not found')

    db.session.delete(recipient)
    db.session.commit()

    track_activity(f'MS365 {recipient.channel_type} recipient removed', caseid=None)
    return response_success('Recipient removed')


@manage_integrations_blueprint.route('/manage/integrations/ms365/recipients/<int:recipient_id>/toggle', methods=['PATCH'])
@login_required
@ac_requires(Permissions.server_administrator, no_cid_required=True)
def ms365_toggle_recipient(caseid, url_redir, recipient_id):
    if url_redir:
        return redirect(url_for('manage_integrations.manage_integrations_index', cid=caseid))

    recipient = MS365NotificationRecipient.query.get(recipient_id)
    if not recipient:
        return response_error('Recipient not found')

    recipient.enabled = not recipient.enabled
    db.session.commit()

    return response_success('Recipient updated', data={'id': recipient.id, 'enabled': recipient.enabled})

Step 6: UI Card
Modified file: source/app/blueprints/manage/manage_integrations/templates/manage_integrations.html

6a. Add MS365 icon color in the <style> block:

.ms365-icon {
    color: #0078d4;
}
.recipient-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    margin-bottom: 4px;
    background: #f8f9fa;
}
.recipient-row.disabled-recipient {
    opacity: 0.5;
}

6b. Add the integration card after the last existing card:

<!-- Microsoft 365 Integration -->
<div class="integration-card">
    <div class="integration-header">
        <div class="d-flex align-items-center justify-content-between">
            <div class="d-flex align-items-center">
                <i class="fas fa-envelope ms365-icon integration-icon"></i>
                <div>
                    <h5 class="mb-1">Microsoft 365</h5>
                    <small class="text-muted">Email and Teams notifications on case creation via Microsoft Graph API</small>
                </div>
            </div>
            <div>
                <span class="status-badge {% if integrations.ms365.enabled %}status-enabled{% else %}status-disabled{% endif %}" id="ms365-status-badge">
                    {% if integrations.ms365.enabled %}Enabled{% else %}Disabled{% endif %}
                </span>
            </div>
        </div>
    </div>
    <div class="integration-body">
        <form id="ms365-form">

            <!-- Enable toggle -->
            <div class="row">
                <div class="col-md-12">
                    <div class="form-group">
                        <div class="custom-control custom-switch">
                            <input type="checkbox" class="custom-control-input" id="ms365-enabled"
                                   {% if integrations.ms365.enabled %}checked{% endif %}>
                            <label class="custom-control-label" for="ms365-enabled">
                                Enable Microsoft 365 integration
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Auth credentials -->
            <div class="row">
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="ms365-tenant-id">Tenant ID <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" id="ms365-tenant-id"
                               placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                               value="{{ integrations.ms365.tenant_id }}">
                        <small class="form-text text-muted">Directory (tenant) ID from Azure AD</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="ms365-client-id">Client ID <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" id="ms365-client-id"
                               placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                               value="{{ integrations.ms365.client_id }}">
                        <small class="form-text text-muted">Application (client) ID from Azure AD</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="ms365-client-secret">Client Secret <span class="text-danger">*</span></label>
                        <input type="password" class="form-control" id="ms365-client-secret"
                               placeholder="{% if integrations.ms365.client_secret == 'configured' %}Enter new value to replace{% else %}Enter client secret{% endif %}">
                        <small class="form-text text-muted">
                            {% if integrations.ms365.client_secret == 'configured' %}
                                <span class="text-success"><i class="fas fa-lock mr-1"></i>Secret saved and encrypted</span>
                            {% else %}
                                Client secret from Azure AD Certificates &amp; Secrets
                            {% endif %}
                        </small>
                    </div>
                </div>
            </div>

            <hr>

            <!-- Email channel -->
            <div class="row">
                <div class="col-md-12">
                    <div class="custom-control custom-switch mb-3">
                        <input type="checkbox" class="custom-control-input" id="ms365-send-email"
                               {% if integrations.ms365.send_email %}checked{% endif %}>
                        <label class="custom-control-label" for="ms365-send-email">
                            <strong>Send email notifications on new case</strong>
                        </label>
                    </div>
                </div>
            </div>

            <div id="ms365-email-section" {% if not integrations.ms365.send_email %}style="display:none;"{% endif %}>
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group">
                            <label for="ms365-from-email">From Email Address <span class="text-danger">*</span></label>
                            <input type="email" class="form-control" id="ms365-from-email"
                                   placeholder="iris-notifications@yourdomain.com"
                                   value="{{ integrations.ms365.from_email }}">
                            <small class="form-text text-muted">Mailbox the app has Mail.Send permission on</small>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-8">
                        <label>Email Recipients</label>
                        <div id="ms365-email-recipients-list" class="mb-2">
                            <div class="text-muted small"><i class="fas fa-spinner fa-spin"></i> Loading...</div>
                        </div>
                        <div class="input-group input-group-sm">
                            <input type="email" class="form-control" id="ms365-new-email-address"
                                   placeholder="analyst@company.com">
                            <input type="text" class="form-control" id="ms365-new-email-name"
                                   placeholder="Display name (optional)">
                            <div class="input-group-append">
                                <button type="button" class="btn btn-outline-primary btn-sm" onclick="ms365AddRecipient('email')">
                                    <i class="fas fa-plus mr-1"></i>Add
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <hr>

            <!-- Teams channel -->
            <div class="row">
                <div class="col-md-12">
                    <div class="custom-control custom-switch mb-3">
                        <input type="checkbox" class="custom-control-input" id="ms365-send-teams"
                               {% if integrations.ms365.send_teams %}checked{% endif %}>
                        <label class="custom-control-label" for="ms365-send-teams">
                            <strong>Send Teams notifications on new case</strong>
                        </label>
                    </div>
                </div>
            </div>

            <div id="ms365-teams-section" {% if not integrations.ms365.send_teams %}style="display:none;"{% endif %}>
                <div class="row">
                    <div class="col-md-8">
                        <label>Teams Channels</label>
                        <div id="ms365-teams-recipients-list" class="mb-2">
                            <div class="text-muted small"><i class="fas fa-spinner fa-spin"></i> Loading...</div>
                        </div>
                        <div class="input-group input-group-sm">
                            <input type="password" class="form-control" id="ms365-new-teams-url"
                                   placeholder="https://outlook.office.com/webhook/...">
                            <input type="text" class="form-control" id="ms365-new-teams-name"
                                   placeholder="Channel name (optional)">
                            <div class="input-group-append">
                                <button type="button" class="btn btn-outline-primary btn-sm" onclick="ms365AddRecipient('teams')">
                                    <i class="fas fa-plus mr-1"></i>Add
                                </button>
                            </div>
                        </div>
                        <small class="form-text text-muted">Webhook URL is encrypted after saving and cannot be retrieved</small>
                    </div>
                </div>
            </div>

            <hr>

            <!-- Actions -->
            <div class="row">
                <div class="col-md-12">
                    <button type="button" class="btn btn-info btn-sm" onclick="testConnection('ms365')">
                        <i class="fas fa-plug mr-1"></i>Test Connection
                    </button>
                    <button type="button" class="btn btn-success btn-sm ml-2" onclick="saveConfig('ms365')">
                        <i class="fas fa-save mr-1"></i>Save Configuration
                    </button>
                </div>
            </div>
            <div id="ms365-test-result" class="test-result" style="display: none;"></div>
        </form>
    </div>
</div>

6c. Add to getConfigFromForm() (after the fortigate branch):

} else if (integrationType === 'ms365') {
    return {
        enabled: document.getElementById('ms365-enabled').checked,
        tenant_id: document.getElementById('ms365-tenant-id').value,
        client_id: document.getElementById('ms365-client-id').value,
        client_secret: document.getElementById('ms365-client-secret').value || 'configured',
        from_email: document.getElementById('ms365-from-email').value,
        send_email: document.getElementById('ms365-send-email').checked,
        send_teams: document.getElementById('ms365-send-teams').checked
    };
}

6d. Add to testConnection() result div routing (after the fortigate branch):

} else if (integrationType === 'ms365') {
    resultDiv = document.getElementById('ms365-test-result');
}

6e. Add to the test success display block inside testConnection():

if (data.data.tenant_id) {
    resultDiv.innerHTML += `<br><small>Tenant ID: ${data.data.tenant_id}</small>`;
}
if (data.data.token_expires_in) {
    resultDiv.innerHTML += `<br><small>Token expires in: ${data.data.token_expires_in}s</small>`;
}

6f. Add all MS365 JavaScript functions at the bottom of the script section:

// MS365 recipient management

function ms365LoadRecipients() {
    fetch('/manage/integrations/ms365/recipients', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(r => r.json())
    .then(data => {
        if (data.status !== 'success') return;
        const recipients = data.data;

        const emailRows = recipients.filter(r => r.channel_type === 'email');
        const teamsRows = recipients.filter(r => r.channel_type === 'teams');

        ms365RenderRecipients('ms365-email-recipients-list', emailRows, 'email');
        ms365RenderRecipients('ms365-teams-recipients-list', teamsRows, 'teams');
    })
    .catch(() => {});
}

function ms365RenderRecipients(containerId, recipients, channelType) {
    const container = document.getElementById(containerId);
    if (!recipients.length) {
        container.innerHTML = `<div class="text-muted small">No ${channelType} recipients configured</div>`;
        return;
    }

    container.innerHTML = recipients.map(r => `
        <div class="recipient-row ${r.enabled ? '' : 'disabled-recipient'}" id="recipient-row-${r.id}">
            <span>
                <i class="fas fa-${channelType === 'email' ? 'envelope' : 'comments'} mr-2 text-muted"></i>
                <strong>${r.display_name || r.address}</strong>
                ${r.display_name ? `<small class="text-muted ml-2">${r.address}</small>` : ''}
                ${!r.enabled ? '<span class="badge badge-secondary ml-2">Disabled</span>' : ''}
            </span>
            <span>
                <button type="button" class="btn btn-xs btn-outline-secondary mr-1"
                        onclick="ms365ToggleRecipient(${r.id})">
                    ${r.enabled ? 'Disable' : 'Enable'}
                </button>
                <button type="button" class="btn btn-xs btn-outline-danger"
                        onclick="ms365RemoveRecipient(${r.id})">
                    <i class="fas fa-times"></i>
                </button>
            </span>
        </div>
    `).join('');
}

function ms365AddRecipient(channelType) {
    const addressInput = document.getElementById(
        channelType === 'email' ? 'ms365-new-email-address' : 'ms365-new-teams-url'
    );
    const nameInput = document.getElementById(
        channelType === 'email' ? 'ms365-new-email-name' : 'ms365-new-teams-name'
    );

    const address = addressInput.value.trim();
    const displayName = nameInput.value.trim();

    if (!address) {
        showNotification('error', 'Validation', 'Address is required');
        return;
    }

    fetch('/manage/integrations/ms365/recipients/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({channel_type: channelType, address: address, display_name: displayName})
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            addressInput.value = '';
            nameInput.value = '';
            ms365LoadRecipients();
        } else {
            showNotification('error', 'Error', data.message);
        }
    })
    .catch(e => showNotification('error', 'Error', e.message));
}

function ms365RemoveRecipient(id) {
    fetch(`/manage/integrations/ms365/recipients/${id}`, {method: 'DELETE'})
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            ms365LoadRecipients();
        } else {
            showNotification('error', 'Error', data.message);
        }
    })
    .catch(e => showNotification('error', 'Error', e.message));
}

function ms365ToggleRecipient(id) {
    fetch(`/manage/integrations/ms365/recipients/${id}/toggle`, {method: 'PATCH'})
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            ms365LoadRecipients();
        } else {
            showNotification('error', 'Error', data.message);
        }
    })
    .catch(e => showNotification('error', 'Error', e.message));
}

// Show/hide sections based on toggles
document.getElementById('ms365-send-email').addEventListener('change', function () {
    document.getElementById('ms365-email-section').style.display = this.checked ? '' : 'none';
});
document.getElementById('ms365-send-teams').addEventListener('change', function () {
    document.getElementById('ms365-teams-section').style.display = this.checked ? '' : 'none';
});

// Load recipients when page loads
ms365LoadRecipients();

Step 7: Case Creation Hook
Modified file: source/app/business/cases.py

7a. Add import at the top:

from app.integrations.ms365 import notify_case_created

7b. Add the call at ~line 107, after call_modules_hook('on_postload_case_create', ...) and before add_obj_history_entry(...):

        case = call_modules_hook('on_postload_case_create', case, None)

        try:
            notify_case_created(case)
        except Exception as e:
            log.error(f'MS365 notification failed for case {case.case_id}: {e}')

        add_obj_history_entry(case, 'created')

The try/except is mandatory — a notification failure must never prevent case creation.

Step 8: Documentation Page
Modified file: source/app/blueprints/overview/templates/overview_docs.html

8a. Add the MS365 tab to nav pills (after the FortiGate tab):

<li class="nav-item" role="presentation">
    <a class="nav-link" id="ms365-tab" data-toggle="pill" href="#ms365" role="tab">
        <i class="fas fa-envelope mr-1"></i>Microsoft 365
    </a>
</li>

8b. Add MS365 to the Overview tab — add a new section after the FortiGate card row, under the SOAR section:

<div class="section-divider"></div>
<h4 class="mt-4"><i class="fas fa-bell text-primary mr-2"></i>Notification Integrations</h4>
<p>Integrations that automatically notify your team when key events occur in IRIS.</p>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card" style="border-color: #0078d4;">
            <div class="card-header text-white" style="background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);">
                <h5 class="mb-0"><i class="fas fa-envelope mr-2"></i>Microsoft 365 Integration</h5>
            </div>
            <div class="card-body">
                <p>Automated email and Teams notifications when new cases are created.</p>
                <ul class="list-unstyled">
                    <li><i class="fas fa-check text-success mr-2"></i>Email notifications via Microsoft Graph</li>
                    <li><i class="fas fa-check text-success mr-2"></i>Teams channel notifications via webhook</li>
                    <li><i class="fas fa-check text-success mr-2"></i>Per-recipient enable/disable control</li>
                    <li><i class="fas fa-check text-success mr-2"></i>Credentials encrypted at rest</li>
                </ul>
                <span class="badge" style="background-color: #0078d4; color: white;">Event-Driven Notification</span>
            </div>
        </div>
    </div>
</div>

8c. Add the full MS365 tab pane after the FortiGate tab pane:

<!-- Microsoft 365 Tab -->
<div class="tab-pane fade" id="ms365" role="tabpanel">
    <div class="integration-card">
        <div class="integration-header" style="background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);">
            <h3><i class="fas fa-envelope mr-2"></i>Microsoft 365 Integration</h3>
            <p class="mb-0">Automated notifications via Microsoft Graph API</p>
        </div>
        <div class="p-4">

            <h5><i class="fas fa-info-circle text-primary mr-2"></i>About This Integration</h5>
            <p>The Microsoft 365 integration sends notifications to your team whenever a new case is created in IRIS.
            You can enable email notifications, Teams notifications, or both independently. Each channel maintains
            its own recipient list — addresses and channels can be added, removed, or temporarily disabled at any
            time without affecting the other channel or requiring reconfiguration.</p>

            <div class="section-divider"></div>

            <h5><i class="fas fa-list-ol text-primary mr-2"></i>Azure Setup (Done Once Per Deployment)</h5>

            <div class="playbook-item">
                <strong>Step 1 — Register an Azure AD Application</strong>
                <ol class="mt-2">
                    <li>Sign into <strong>portal.azure.com</strong> as a Global Administrator</li>
                    <li>Navigate to <strong>Azure Active Directory → App registrations → New registration</strong></li>
                    <li>Name it (e.g. <em>IRIS Case Notifications</em>), set account type to <strong>this directory only</strong>, leave redirect URI blank</li>
                    <li>Copy the <strong>Application (client) ID</strong> and <strong>Directory (tenant) ID</strong></li>
                </ol>
            </div>

            <div class="playbook-item forensics">
                <strong>Step 2 — Configure API Permissions</strong>
                <ol class="mt-2">
                    <li>Go to <strong>API permissions → Add a permission → Microsoft Graph → Application permissions</strong></li>
                    <li>Add <code>Mail.Send</code> for email notifications</li>
                    <li>Add <code>ChannelMessage.Send</code> only if using Graph API for Teams (not needed for webhook approach)</li>
                    <li>Click <strong>Grant admin consent for [your tenant]</strong></li>
                </ol>
            </div>

            <div class="playbook-item scanning">
                <strong>Step 3 — Create a Client Secret</strong>
                <ol class="mt-2">
                    <li>Go to <strong>Certificates &amp; secrets → New client secret</strong></li>
                    <li>Set expiry (12 or 24 months recommended)</li>
                    <li>Copy the <strong>Value immediately</strong> — it will not be shown again</li>
                </ol>
            </div>

            <div class="playbook-item" style="border-left-color: #0078d4;">
                <strong>Step 4 — Teams Webhook URL (Simpler Teams Option)</strong>
                <ol class="mt-2">
                    <li>In Teams, open target channel → <strong>⋯ → Connectors → Incoming Webhook</strong></li>
                    <li>Name it and copy the webhook URL</li>
                    <li>Paste it into the Teams Channels list in IRIS</li>
                </ol>
                <small class="text-muted">This approach requires no Azure API permissions and no Teams app installation.</small>
            </div>

            <div class="section-divider"></div>

            <h5><i class="fas fa-cog text-primary mr-2"></i>Configuring in IRIS</h5>
            <p>Go to <strong>Manage → Integrations → Microsoft 365</strong> and complete the following:</p>

            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card border-secondary mb-3">
                        <div class="card-header bg-secondary text-white">1. Authentication</div>
                        <div class="card-body">
                            <ul class="list-unstyled mb-0">
                                <li><strong>Tenant ID</strong> — Directory (tenant) ID from Azure AD</li>
                                <li><strong>Client ID</strong> — Application (client) ID</li>
                                <li><strong>Client Secret</strong> — Secret value from Certificates &amp; Secrets</li>
                            </ul>
                            <small class="text-muted mt-2 d-block">Click Test Connection to validate before saving</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card border-secondary mb-3">
                        <div class="card-header bg-secondary text-white">2. Notification Channels</div>
                        <div class="card-body">
                            <ul class="list-unstyled mb-0">
                                <li><strong>Enable Email</strong> — toggle + set from address</li>
                                <li><strong>Add email recipients</strong> — one address at a time</li>
                                <li><strong>Enable Teams</strong> — toggle</li>
                                <li><strong>Add Teams channels</strong> — one webhook URL at a time</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section-divider"></div>

            <h5><i class="fas fa-users text-primary mr-2"></i>Managing Recipients</h5>
            <p>Recipients for each channel are managed independently in a live list:</p>
            <ul>
                <li><strong>Add</strong> — enter an address or URL and click Add. It is saved immediately.</li>
                <li><strong>Disable</strong> — temporarily stops notifications to that recipient without removing them. Re-enable at any time.</li>
                <li><strong>Remove</strong> — permanently removes the recipient.</li>
            </ul>
            <p>Adding a Teams channel later does not affect any email recipients, and vice versa. Each list is fully independent.</p>

            <div class="section-divider"></div>

            <h5><i class="fas fa-shield-alt text-primary mr-2"></i>Security Notes</h5>
            <ul>
                <li>The client secret and all Teams webhook URLs are <strong>encrypted at rest</strong> using AES-128 encryption</li>
                <li>Neither the client secret nor webhook URLs are ever returned to the browser after saving</li>
                <li>Access tokens from Microsoft Graph are used immediately and never stored</li>
                <li>Only IRIS server administrators can view or modify this configuration</li>
                <li>If <code>IRIS_SECRET_KEY</code> is ever rotated, credentials and webhook URLs will need to be re-entered once</li>
            </ul>

        </div>
    </div>
</div>

Part 4: Verification Checklist
 Integrations page loads and shows the MS365 card
 Toggling Send Email shows/hides the email section
 Toggling Send Teams shows/hides the Teams section
 Test Connection with valid credentials returns success, tenant ID, and token expiry
 Test Connection with wrong credentials returns a clear error
 After saving, client secret field shows lock indicator — secret not returned to browser
 Adding an email recipient immediately appears in the list without a page refresh
 Adding a Teams webhook URL immediately appears as "configured" in the list — URL is never shown
 Disabling a recipient greys it out and it no longer receives notifications
 Re-enabling a recipient restores it
 Removing a recipient deletes it from the list and the DB
 Adding a Teams channel later leaves all email recipients untouched
 SELECT * FROM ms365_notification_recipients; — Teams address column contains unreadable ciphertext
 Pod restart — all configuration and recipients persist
 Creating a case with email enabled → emails arrive at all enabled email recipients
 Creating a case with Teams enabled → messages arrive in all enabled Teams channels
 Disabling the integration entirely → creating a case → no notifications sent
 Docs page → Microsoft 365 tab loads correctly
 Overview tab shows the Notification Integrations section