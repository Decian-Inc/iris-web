#  IRIS AbuseIPDB Module Source Code
#  Copyright (C) 2025 - Decian
#  contact@decian.org
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

module_name = "IrisAbuseIPDB"
module_description = "Provides AbuseIPDB enrichment for IOCs and automatic report generation in notes"
interface_version = "1.2.0"
module_version = "1.0.0"
pipeline_support = False
pipeline_info = {}

module_configuration = [
    {
        "param_name": "abuseipdb_api_key",
        "param_human_name": "AbuseIPDB API Key",
        "param_description": "API key for AbuseIPDB service",
        "default": "c06ed761ffb2c108ccc470f117883ca467e287ae0d883b60e465bc55a30d1a7cadbd23475c8b027e",
        "mandatory": True,
        "type": "sensitive_string"
    },
    {
        "param_name": "abuseipdb_on_create_hook_enabled",
        "param_human_name": "AbuseIPDB on IOC create",
        "param_description": "Enable AbuseIPDB lookup when an IOC is created",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "abuseipdb_on_update_hook_enabled",
        "param_human_name": "AbuseIPDB on IOC update",
        "param_description": "Enable AbuseIPDB lookup when an IOC is updated",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "abuseipdb_manual_hook_enabled",
        "param_human_name": "AbuseIPDB manual trigger",
        "param_description": "Enable manual AbuseIPDB lookups",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "abuseipdb_auto_create_notes",
        "param_human_name": "Auto-create notes",
        "param_description": "Automatically create notes with AbuseIPDB reports",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "abuseipdb_max_age_days",
        "param_human_name": "Maximum age in days",
        "param_description": "Maximum age of reports to include (default: 90 days)",
        "default": 90,
        "mandatory": True,
        "type": "int"
    }
]