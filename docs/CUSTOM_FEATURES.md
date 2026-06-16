# Decian Custom IRIS Features

## Overview
This document outlines all custom modifications made to the base IRIS platform for the Decian deployment.

## Custom Features Added

### 1. Threat Intelligence Integration (NEW)
**Location:** `/threat-intel`
**Files Modified/Added:**
- `source/app/blueprints/threat_intel/` (entire directory)
- `source/app/templates/includes/sidenav.html` (added Threat Intel menu item)
- `source/app/views.py` (registered threat_intel_blueprint)

**Features:**
- Global-level "Threat Intel" tab in navigation
- MISP integration for IOC submission
- Support for IP addresses, domains, MD5/SHA256 hashes, URLs, and email addresses
- Automatic MISP event creation with proper categorization
- Modern responsive UI with form validation

**Configuration:**
- MISP URL: `https://misp.ironclad.decianx`
- API Key: `Nn5NRLKfmdJNDZA64MV15s5PqGbradL253RG9T2Z`

### 2. Enhanced Logo Branding
**Files Modified:**
- `source/app/templates/includes/navigation.html`
- `source/app/templates/includes/navigation_ext.html`

**Changes:**
- Updated logo from "IRIS" to "Ironclad"
- Added "Case Management" subtitle
- Enhanced styling with proper font sizing and spacing

### 3. SOAR Integrations
**Files Modified:**
- `source/app/blueprints/soar/soar_routes.py`
- `source/app/blueprints/manage/manage_integrations/`
- Multiple SOAR playbook templates and integration configs

**Integrations Added:**
- SentinelOne integration
- Velociraptor integration
- Custom playbook templates
- Integration management dashboard

### 4. Enhanced Documentation
**Files Modified:**
- `source/app/blueprints/overview/templates/overview_docs.html`

**Features:**
- Added comprehensive SOAR integration documentation
- Playbook usage guides
- Integration setup instructions

## Demo Data
**Script:** `scripts/create_demo_data.py`
**Content:**
- 5 sample companies (TechCorp, SecureBank, HealthMed, RetailMax, EduTech)
- 10 cases (2 per company: APT Campaign, Ransomware Incident)
- 100 IOCs (10 per case with various types)

## Production Deployment Requirements

### Environment Variables
```bash
# MISP Configuration
MISP_URL=https://misp.ironclad.decianx
MISP_API_KEY=Nn5NRLKfmdJNDZA64MV15s5PqGbradL253RG9T2Z

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<secure_password>
POSTGRES_DB=iris_db

# IRIS Configuration
IRIS_SECRET_KEY=<secure_secret_key>
IRIS_SECURITY_PASSWORD_SALT=<secure_salt>
```

### SSL/TLS Configuration
- NGINX configured for HTTPS on port 443
- Self-signed certificates supported
- Production should use proper SSL certificates

### Dependencies Added
- `urllib3` (for SSL warning suppression)
- Additional Python packages for MISP integration

## File Structure Changes
```
source/app/blueprints/
├── threat_intel/           # NEW - Threat Intel feature
│   ├── __init__.py
│   ├── threat_intel_routes.py
│   └── templates/
│       └── threat_intel.html
├── soar/                   # ENHANCED - Additional integrations
└── manage/
    └── manage_integrations/ # ENHANCED - Integration management

source/app/templates/includes/
├── navigation.html         # MODIFIED - Logo branding
├── navigation_ext.html     # MODIFIED - Logo branding
└── sidenav.html           # MODIFIED - Added Threat Intel menu

scripts/                    # NEW - Utility scripts
└── create_demo_data.py
```

## Security Considerations
- MISP API key should be stored securely (environment variable or secrets management)
- SSL verification disabled for self-signed certificates (configure properly for production)
- All user inputs validated and sanitized
- CSRF protection enabled on all forms

## Integration Points
- Wazuh agent alerts → Post processor → Auto case creation
- MISP threat intelligence sharing
- SentinelOne EDR integration
- Velociraptor endpoint monitoring

## Maintenance Notes
- MISP API key rotation recommended every 90 days
- Monitor MISP instance connectivity
- Regular backup of custom configurations
- Update base IRIS version carefully to preserve customizations