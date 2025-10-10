#  IRIS Hybrid Analysis Module Source Code
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

module_name = "IrisHybridAnalysis"
module_description = "Provides Hybrid Analysis enrichment for IOCs (files, URLs, domains, emails) and automatic report generation in notes"
interface_version = "1.2.0"
module_version = "1.0.0"
pipeline_support = False
pipeline_info = {}

module_configuration = [
    {
        "param_name": "hybrid_analysis_api_key",
        "param_human_name": "Hybrid Analysis API Key",
        "param_description": "API key for Hybrid Analysis service",
        "default": "7058y8ixc5c5d6fbc2avqhlg24ef7719nceecd8d3d7af756n3v63wu48c0aaea0",
        "mandatory": True,
        "type": "sensitive_string"
    },
    {
        "param_name": "hybrid_analysis_on_create_hook_enabled",
        "param_human_name": "Enable on IOC create",
        "param_description": "Enable automatic enrichment when IOC is created",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "hybrid_analysis_on_update_hook_enabled",
        "param_human_name": "Enable on IOC update",
        "param_description": "Enable automatic enrichment when IOC is updated",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "hybrid_analysis_manual_hook_enabled",
        "param_human_name": "Enable manual trigger",
        "param_description": "Enable manual enrichment trigger",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "hybrid_analysis_auto_create_notes",
        "param_human_name": "Auto-create notes",
        "param_description": "Automatically create detailed reports in Notes section",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "hybrid_analysis_environment_id",
        "param_human_name": "Analysis Environment",
        "param_description": "Environment ID for analysis (100=Windows 7 32-bit, 110=Windows 7 64-bit, 120=Windows 10 64-bit, 200=Linux Ubuntu 16.04 64-bit, 300=Android Static Analysis)",
        "default": 120,
        "mandatory": True,
        "type": "int"
    },
    {
        "param_name": "hybrid_analysis_max_reports",
        "param_human_name": "Maximum Reports",
        "param_description": "Maximum number of analysis reports to retrieve per IOC",
        "default": 10,
        "mandatory": True,
        "type": "int"
    }
]