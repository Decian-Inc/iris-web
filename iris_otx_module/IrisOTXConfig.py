#  IRIS AlienVault OTX Module Source Code
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

module_name = "IrisOTX"
module_description = "Provides AlienVault OTX enrichment for IOCs and automatic report generation in notes"
interface_version = "1.2.0"
module_version = "1.0.0"
pipeline_support = False
pipeline_info = {}

module_configuration = [
    {
        "param_name": "otx_api_key",
        "param_human_name": "AlienVault OTX API Key",
        "param_description": "API key for AlienVault OTX service",
        "default": "0b95c1189f850ed5d8cd9cea8b648695f0612c0254a0b8ff2d68a22eb4b6ecbb",
        "mandatory": True,
        "type": "sensitive_string"
    },
    {
        "param_name": "otx_on_create_hook_enabled",
        "param_human_name": "OTX on IOC create",
        "param_description": "Enable OTX lookup when an IOC is created",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "otx_on_update_hook_enabled",
        "param_human_name": "OTX on IOC update",
        "param_description": "Enable OTX lookup when an IOC is updated",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "otx_manual_hook_enabled",
        "param_human_name": "OTX manual trigger",
        "param_description": "Enable manual OTX lookups",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "otx_auto_create_notes",
        "param_human_name": "Auto-create notes",
        "param_description": "Automatically create notes with OTX reports",
        "default": True,
        "mandatory": True,
        "type": "bool"
    }
]