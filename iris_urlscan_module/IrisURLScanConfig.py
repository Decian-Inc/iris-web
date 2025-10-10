#!/usr/bin/env python3

#  IRIS URLScan.io Module Source Code
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

module_name = "IrisURLScan"
module_description = "Provides URLScan.io enrichment for URL IOCs with screenshot capture and automatic report generation in notes"
interface_version = "1.2.0"
module_version = "1.0.0"
pipeline_support = False
pipeline_info = {}

module_configuration = [
    {
        "param_name": "urlscan_api_key",
        "param_human_name": "URLScan.io API Key",
        "param_description": "API key for URLScan.io service",
        "default": "0199cbf2-cc03-719c-81b2-19568043af61",
        "mandatory": True,
        "type": "sensitive_string"
    },
    {
        "param_name": "urlscan_on_create_hook_enabled",
        "param_human_name": "Enable on IOC create",
        "param_description": "Enable automatic enrichment when URL IOC is created",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "urlscan_on_update_hook_enabled",
        "param_human_name": "Enable on IOC update",
        "param_description": "Enable automatic enrichment when URL IOC is updated",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "urlscan_manual_hook_enabled",
        "param_human_name": "Enable manual trigger",
        "param_description": "Enable manual enrichment trigger",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "urlscan_auto_create_notes",
        "param_human_name": "Auto-create notes",
        "param_description": "Automatically create detailed reports with screenshots in Notes section",
        "default": True,
        "mandatory": True,
        "type": "bool"
    },
    {
        "param_name": "urlscan_visibility",
        "param_human_name": "Scan Visibility",
        "param_description": "Visibility level for URLScan.io submissions (public, unlisted, private)",
        "default": "unlisted",
        "mandatory": True,
        "type": "str"
    },
    {
        "param_name": "urlscan_timeout",
        "param_human_name": "Scan Timeout",
        "param_description": "Maximum time to wait for scan completion (seconds)",
        "default": 120,
        "mandatory": True,
        "type": "int"
    }
]