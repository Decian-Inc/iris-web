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

import requests
import ipaddress
import hashlib
import re
from typing import Dict, Any, Optional
from datetime import datetime
import json


class OTXHandler:
    """Handler for AlienVault OTX API interactions"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://otx.alienvault.com/api/v1"
        self.headers = {
            'X-OTX-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

    def _is_valid_ip(self, ip_str: str) -> bool:
        """Check if the string is a valid IP address"""
        try:
            ip = ipaddress.ip_address(ip_str)
            return not ip.is_private and not ip.is_loopback
        except ValueError:
            return False

    def _is_valid_domain(self, domain: str) -> bool:
        """Check if the string is a valid domain"""
        domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        return bool(domain_pattern.match(domain)) and len(domain) <= 253

    def _is_valid_hash(self, hash_str: str) -> bool:
        """Check if the string is a valid hash (MD5, SHA1, SHA256)"""
        if len(hash_str) == 32:
            try:
                int(hash_str, 16)
                return True
            except ValueError:
                return False
        elif len(hash_str) == 40:
            try:
                int(hash_str, 16)
                return True
            except ValueError:
                return False
        elif len(hash_str) == 64:
            try:
                int(hash_str, 16)
                return True
            except ValueError:
                return False
        return False

    def _determine_indicator_type(self, indicator: str) -> str:
        """Determine the type of indicator"""
        if self._is_valid_ip(indicator):
            return 'IPv4'
        elif self._is_valid_domain(indicator):
            return 'domain'
        elif self._is_valid_hash(indicator):
            if len(indicator) == 32:
                return 'FileHash-MD5'
            elif len(indicator) == 40:
                return 'FileHash-SHA1'
            elif len(indicator) == 64:
                return 'FileHash-SHA256'
        return 'unknown'

    def query_indicator(self, indicator: str) -> Dict[str, Any]:
        """Query OTX for indicator information"""
        indicator_type = self._determine_indicator_type(indicator)

        if indicator_type == 'unknown':
            return {
                'error': f'Unsupported indicator type for: {indicator}',
                'indicator': indicator
            }

        try:
            # Get general information
            general_url = f"{self.base_url}/indicators/{indicator_type}/{indicator}/general"
            general_response = requests.get(general_url, headers=self.headers, timeout=30)

            if general_response.status_code != 200:
                return {
                    'error': f'API request failed with status {general_response.status_code}',
                    'indicator': indicator,
                    'status_code': general_response.status_code
                }

            general_data = general_response.json()

            # Get malware information
            malware_url = f"{self.base_url}/indicators/{indicator_type}/{indicator}/malware"
            malware_response = requests.get(malware_url, headers=self.headers, timeout=30)
            malware_data = malware_response.json() if malware_response.status_code == 200 else {}

            # Get passive DNS (for IPs and domains)
            passive_dns_data = {}
            if indicator_type in ['IPv4', 'domain']:
                passive_dns_url = f"{self.base_url}/indicators/{indicator_type}/{indicator}/passive_dns"
                passive_dns_response = requests.get(passive_dns_url, headers=self.headers, timeout=30)
                passive_dns_data = passive_dns_response.json() if passive_dns_response.status_code == 200 else {}

            # Get URL list (for IPs and domains)
            url_list_data = {}
            if indicator_type in ['IPv4', 'domain']:
                url_list_url = f"{self.base_url}/indicators/{indicator_type}/{indicator}/url_list"
                url_list_response = requests.get(url_list_url, headers=self.headers, timeout=30)
                url_list_data = url_list_response.json() if url_list_response.status_code == 200 else {}

            return {
                'indicator': indicator,
                'indicator_type': indicator_type,
                'general': general_data,
                'malware': malware_data,
                'passive_dns': passive_dns_data,
                'url_list': url_list_data,
                'fetched_at': datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            return {
                'error': f'Network error: {str(e)}',
                'indicator': indicator
            }
        except Exception as e:
            return {
                'error': f'Unexpected error: {str(e)}',
                'indicator': indicator
            }

    def format_report_markdown(self, indicator: str, otx_data: Dict) -> str:
        """Format OTX data into a markdown report"""
        if 'error' in otx_data:
            return f"""# AlienVault OTX Report - Error

**Indicator:** {indicator}
**Error:** {otx_data['error']}
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        general = otx_data.get('general', {})
        malware = otx_data.get('malware', {})
        passive_dns = otx_data.get('passive_dns', {})
        url_list = otx_data.get('url_list', {})

        # Build the markdown report
        report = f"""# AlienVault OTX Report

**Indicator:** {indicator}
**Type:** {otx_data.get('indicator_type', 'Unknown')}
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## General Information

"""

        if general:
            pulse_count = general.get('pulse_info', {}).get('count', 0)
            pulses = general.get('pulse_info', {}).get('pulses', [])

            report += f"**Pulse Count:** {pulse_count}\n"
            report += f"**Reputation:** {general.get('reputation', 'N/A')}\n"
            report += f"**Country:** {general.get('country_name', 'N/A')}\n"
            if general.get('city'):
                report += f"**City:** {general.get('city')}\n"
            if general.get('asn'):
                report += f"**ASN:** {general.get('asn')}\n"

            # Add pulse information
            if pulses:
                report += f"\n### Related Pulses ({len(pulses)} total)\n\n"
                for i, pulse in enumerate(pulses[:5], 1):  # Show first 5 pulses
                    report += f"**{i}. {pulse.get('name', 'Unnamed Pulse')}**\n"
                    report += f"   - **ID:** {pulse.get('id', 'N/A')}\n"
                    report += f"   - **Created:** {pulse.get('created', 'N/A')}\n"
                    report += f"   - **TLP:** {pulse.get('TLP', 'N/A')}\n"
                    report += f"   - **Author:** {pulse.get('author_name', 'N/A')}\n"
                    if pulse.get('description'):
                        description = pulse.get('description', '')[:200]
                        if len(pulse.get('description', '')) > 200:
                            description += "..."
                        report += f"   - **Description:** {description}\n"
                    if pulse.get('tags'):
                        report += f"   - **Tags:** {', '.join(pulse.get('tags', []))}\n"
                    if pulse.get('malware_families'):
                        report += f"   - **Malware Families:** {', '.join([mf.get('display_name', '') for mf in pulse.get('malware_families', [])])}\n"
                    report += "\n"

                if len(pulses) > 5:
                    report += f"*...and {len(pulses) - 5} more pulses*\n\n"

        # Add malware information
        if malware and malware.get('data'):
            report += "## Malware Information\n\n"
            malware_list = malware.get('data', [])
            for i, mal in enumerate(malware_list[:5], 1):  # Show first 5
                report += f"**{i}. {mal.get('detections', {}).get('avast', 'Unknown')}**\n"
                if mal.get('date'):
                    report += f"   - **Date:** {mal.get('date')}\n"
                if mal.get('hash'):
                    report += f"   - **Hash:** {mal.get('hash')}\n"
                report += "\n"

        # Add passive DNS information
        if passive_dns and passive_dns.get('passive_dns'):
            dns_records = passive_dns.get('passive_dns', [])
            if dns_records:
                report += f"## Passive DNS ({len(dns_records)} records)\n\n"
                for i, dns in enumerate(dns_records[:10], 1):  # Show first 10
                    report += f"**{i}.** {dns.get('hostname', 'N/A')} → {dns.get('address', 'N/A')}\n"
                    if dns.get('first'):
                        report += f"   - **First Seen:** {dns.get('first')}\n"
                    if dns.get('last'):
                        report += f"   - **Last Seen:** {dns.get('last')}\n"
                    report += "\n"

                if len(dns_records) > 10:
                    report += f"*...and {len(dns_records) - 10} more DNS records*\n\n"

        # Add URL list information
        if url_list and url_list.get('url_list'):
            urls = url_list.get('url_list', [])
            if urls:
                report += f"## Associated URLs ({len(urls)} total)\n\n"
                for i, url_info in enumerate(urls[:10], 1):  # Show first 10
                    report += f"**{i}.** {url_info.get('url', 'N/A')}\n"
                    if url_info.get('date'):
                        report += f"   - **Date:** {url_info.get('date')}\n"
                    if url_info.get('domain'):
                        report += f"   - **Domain:** {url_info.get('domain')}\n"
                    report += "\n"

                if len(urls) > 10:
                    report += f"*...and {len(urls) - 10} more URLs*\n\n"

        # Add footer
        report += "---\n\n"
        report += f"**Source:** AlienVault OTX\n"
        report += f"**API Documentation:** https://otx.alienvault.com/api\n"
        report += f"**Fetched At:** {otx_data.get('fetched_at', 'N/A')}\n"

        return report