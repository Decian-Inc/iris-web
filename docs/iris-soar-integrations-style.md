# IRIS SOAR Integrations Implementation Guide

## Overview

This document outlines the architecture and implementation patterns for SOAR (Security Orchestration, Automation and Response) integrations in IRIS. The implementation ensures proper validation, database persistence, and real API integration rather than mock responses.

## Key Implementation Points

### 1. **Database-First Architecture**
- All integration settings are stored in PostgreSQL database via `integration_config` table
- No hardcoded credentials or configurations in code
- Settings persist across container restarts and deployments
- Proper audit trail with `created_by`, `updated_by`, and timestamps

### 2. **Proper Validation Flow**
IRIS now follows this validation sequence for SOAR jobs:
1. Check if integration is enabled (`enabled: TRUE`)
2. Validate required credentials exist and are not empty
3. Execute real API calls using stored credentials
4. Save actual response data to case artifacts
5. Create case notes with real execution details

### 3. **Real Integration vs Mock Data**
- **Before**: Hardcoded empty configs returned mock/fake artifacts
- **After**: Database-stored configs enable real API calls with actual data

## Database Structure

### Integration Config Table

```sql
CREATE TABLE integration_config (
    config_id SERIAL PRIMARY KEY,
    integration_type VARCHAR(50) UNIQUE NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    config_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    description TEXT
);

CREATE INDEX ix_integration_config_type ON integration_config (integration_type);
```

### Data Storage Pattern

**SentinelOne Example:**
```json
{
  "integration_type": "sentinelone",
  "enabled": true,
  "config_data": {
    "base_url": "https://your-tenant.sentinelone.net",
    "api_token": "your-api-token",
    "verify_ssl": true,
    "site_id": "optional-site-id"
  }
}
```

**Velociraptor Example:**
```json
{
  "integration_type": "velociraptor",
  "enabled": true,
  "config_data": {
    "base_url": "https://your-velociraptor.server",
    "api_key": "your-api-key",
    "ca_cert": "optional-ca-cert",
    "verify_ssl": true
  }
}
```

## File Structure

### Core Components

```
source/app/
├── models/integrations.py              # Database model
├── blueprints/manage/manage_integrations/
│   ├── manage_integrations_routes.py   # CRUD operations
│   └── templates/manage_integrations.html # Web interface
├── blueprints/soar/
│   └── soar_routes.py                   # Job execution logic
└── alembic/versions/
    └── *_add_integration_config_table.py # Database migration
```

### Model Implementation

```python
# app/models/integrations.py
class IntegrationConfig(db.Model):
    __tablename__ = 'integration_config'

    config_id = Column(Integer, primary_key=True)
    integration_type = Column(String(50), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=False)
    config_data = Column(JSONB, nullable=True)
    # ... audit fields
```

## Adding New Integrations

### Step 1: Database Configuration

Add default config to `get_integrations_config()`:

```python
def get_integrations_config():
    # Add to default_configs dictionary
    default_configs = {
        'your_new_integration': {
            'enabled': False,
            'base_url': '',
            'api_key': '',
            'custom_field': '',
            'verify_ssl': True
        }
    }
```

### Step 2: Validation Logic

Add validation in `execute_soar_job()`:

```python
# Determine integration type from template
elif template_id.startswith('yournew'):
    integration_type = 'your_new_integration'
    config = integrations_config.get('your_new_integration', {})

# Add validation logic
elif integration_type == 'your_new_integration':
    base_url = config.get('base_url', '').strip()
    api_key = config.get('api_key', '').strip()
    if not base_url or not api_key:
        return {
            "job_id": job_id,
            "status": "Failed",
            "message": "Your Integration not properly configured",
            "error": "Missing or empty base_url or api_key"
        }
```

### Step 3: Execution Functions

Create specific execution functions:

```python
def execute_yournew_action(job_id, target, config, case_id):
    """Execute Your New Integration action"""
    try:
        base_url = config.get('base_url').rstrip('/')
        api_key = config.get('api_key')

        # Real API calls here
        response = requests.get(f'{base_url}/api/endpoint',
                              headers={'Authorization': f'Bearer {api_key}'})

        # Save artifacts and create case notes
        artifact_filename = f"yournew_action_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        artifact_path = save_case_artifact(case_id, artifact_filename, response.json())
        add_case_note(case_id, f"**SOAR Action:** Your Action completed...")

        return {"job_id": job_id, "status": "Completed", ...}
    except Exception as e:
        return {"job_id": job_id, "status": "Failed", "error": str(e)}
```

### Step 4: Template Registration

Add templates to `soar_templates_list()`:

```python
{
    "id": "yournew-action",
    "name": "Your New Integration Action",
    "description": "Description of what this does",
    "vendor": "Your Vendor",
    "tags": ["category"],
    "requires_approval": False,
    "allowed_target_types": ["hostname", "custom_id"]
}
```

### Step 5: Frontend Form

Add configuration form to `manage_integrations.html`:

```html
<!-- Add tab and form sections following SentinelOne/Velociraptor patterns -->
<div class="form-group">
    <label for="yournew-url">API Base URL</label>
    <input type="text" class="form-control" id="yournew-url"
           value="{{ integrations.your_new_integration.base_url }}">
</div>
```

Update JavaScript `getConfigFromForm()` and `saveConfig()` functions.

## Best Practices

### 1. **Database Migrations**
- Always create Alembic migrations for schema changes
- Use descriptive migration names
- Include both upgrade() and downgrade() functions
- Test migrations in development before production

### 2. **Error Handling**
- Validate integration enabled status first
- Check for empty/whitespace-only credential strings
- Use try/catch blocks around API calls
- Return structured error responses with actionable messages
- Log errors for debugging but don't expose sensitive data

### 3. **Security**
- Store credentials in JSONB config_data field, not as separate columns
- Use proper PostgreSQL permissions
- Validate SSL certificates by default (`verify_ssl: true`)
- Never log API keys or sensitive credentials
- Use connection timeouts for API calls

### 4. **Code Organization**
- Keep integration-specific logic in separate functions
- Use consistent naming patterns (`execute_{integration}_{action}`)
- Follow IRIS code style (f-strings, no shebangs, LGPL headers)
- Implement proper case artifact storage
- Create meaningful case notes with markdown formatting

### 5. **Testing Strategy**
- Test with integration disabled (should fail)
- Test with empty credentials (should fail)
- Test connection functionality before full implementation
- Verify artifacts are saved to correct case folder structure
- Confirm case notes are properly formatted

### 6. **API Integration Patterns**
- Use requests library with proper timeout values
- Implement retry logic for transient failures
- Handle different HTTP status codes appropriately
- Parse API responses defensively (check for expected fields)
- Store raw API responses in artifacts for forensic value

## File Storage Convention

All SOAR job artifacts follow this structure:
```
/home/iris/server_data/cases/{case_id}/artifacts/{integration}/
├── action_name_{target}_{timestamp}.json
├── logs_{hostname}_{timestamp}.zip
└── scan_report_{hostname}_{timestamp}.json
```

## Validation Flow Summary

```python
# 1. Get integration config from database
integrations_config = get_integrations_config()

# 2. Check if integration is enabled
if not config.get('enabled', False):
    return failure_response("Integration not enabled")

# 3. Validate required credentials
if not config.get('base_url', '').strip():
    return failure_response("Missing base_url")

# 4. Execute real API call
response = requests.get(api_endpoint, headers=auth_headers)

# 5. Save artifacts and create case notes
save_case_artifact(case_id, filename, response.json())
add_case_note(case_id, formatted_note)
```

This architecture ensures that SOAR jobs only execute when properly configured and always produce real integration data rather than mock responses.