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

import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class AbuseIPDBHandler:
    """Handler for AbuseIPDB API interactions"""

    def __init__(self, api_key: str, max_age_days: int = 90):
        self.api_key = api_key
        self.max_age_days = max_age_days
        self.base_url = "https://api.abuseipdb.com/api/v2"
        self.headers = {
            'Key': self.api_key,
            'Accept': 'application/json'
        }

    def check_ip(self, ip_address: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Check an IP address against AbuseIPDB

        Args:
            ip_address: IP address to check
            verbose: Include country info and usage type

        Returns:
            Dict containing AbuseIPDB response data
        """
        url = f"{self.base_url}/check"

        params = {
            'ipAddress': ip_address,
            'maxAgeInDays': self.max_age_days,
            'verbose': verbose
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return {
                'success': True,
                'data': data.get('data', {}),
                'raw_response': data
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f"JSON decode error: {str(e)}",
                'data': {}
            }

    def get_reports(self, ip_address: str, max_age_days: int = None, per_page: int = 25, page: int = 1) -> Dict[str, Any]:
        """
        Get reports for an IP address

        Args:
            ip_address: IP address to get reports for
            max_age_days: Maximum age of reports (defaults to instance setting)
            per_page: Number of reports per page (max 100)
            page: Page number

        Returns:
            Dict containing reports data
        """
        url = f"{self.base_url}/reports"

        params = {
            'ipAddress': ip_address,
            'maxAgeInDays': max_age_days or self.max_age_days,
            'perPage': min(per_page, 100),
            'page': page
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return {
                'success': True,
                'data': data.get('data', {}),
                'raw_response': data
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f"JSON decode error: {str(e)}",
                'data': {}
            }

    def format_report_markdown(self, ip_address: str, check_data: Dict[str, Any], reports_data: Dict[str, Any] = None) -> str:
        """
        Format AbuseIPDB data as markdown report

        Args:
            ip_address: The IP address that was checked
            check_data: Data from check_ip call
            reports_data: Optional reports data from get_reports call

        Returns:
            Formatted markdown report
        """
        if not check_data.get('success'):
            return f"# AbuseIPDB Report - {ip_address}\n\n**Error:** {check_data.get('error', 'Unknown error')}\n"

        data = check_data.get('data', {})
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Start building the markdown report
        markdown = f"""# AbuseIPDB Report - {ip_address}

**Generated:** {timestamp}
**Query Period:** Last {self.max_age_days} days

## Summary

| Field | Value |
|-------|-------|
| **IP Address** | `{data.get('ipAddress', ip_address)}` |
| **Abuse Confidence** | **{data.get('abuseConfidencePercentage', 0)}%** |
| **Reports Count** | {data.get('totalReports', 0)} |
| **Last Reported** | {data.get('lastReportedAt', 'Never') or 'Never'} |
| **Country** | {data.get('countryName', 'Unknown')} ({data.get('countryCode', 'N/A')}) |
| **ISP** | {data.get('isp', 'Unknown')} |
| **Usage Type** | {data.get('usageType', 'Unknown')} |
| **Whitelisted** | {'Yes' if data.get('isWhitelisted') else 'No'} |
| **Public IP** | {'Yes' if data.get('isPublic') else 'No'} |

"""

        # Add risk assessment
        confidence = data.get('abuseConfidencePercentage', 0)
        if confidence >= 75:
            risk_level = "🔴 **HIGH RISK**"
        elif confidence >= 25:
            risk_level = "🟡 **MEDIUM RISK**"
        elif confidence > 0:
            risk_level = "🟢 **LOW RISK**"
        else:
            risk_level = "⚪ **NO REPORTS**"

        markdown += f"## Risk Assessment\n\n{risk_level}\n\n"

        # Add domain info if available
        if data.get('domain'):
            markdown += f"**Associated Domain:** {data.get('domain')}\n\n"

        # Add reports summary if available
        if reports_data and reports_data.get('success'):
            reports = reports_data.get('data', {}).get('results', [])
            if reports:
                markdown += "## Recent Reports\n\n"
                markdown += "| Date | Country | Categories | Comment |\n"
                markdown += "|------|---------|------------|----------|\n"

                for report in reports[:10]:  # Show only first 10 reports
                    report_date = report.get('reportedAt', 'Unknown')[:10]  # Get date part
                    country = report.get('reporterCountryName', 'Unknown')
                    categories = ', '.join([str(cat) for cat in report.get('categories', [])])
                    comment = (report.get('comment', '') or 'No comment')[:50]
                    if len(comment) == 50:
                        comment += "..."

                    markdown += f"| {report_date} | {country} | {categories} | {comment} |\n"

                if len(reports) > 10:
                    markdown += f"\n*Showing 10 of {len(reports)} reports*\n"
            else:
                markdown += "## Recent Reports\n\nNo reports found in the specified time period.\n\n"

        # Add category legend
        markdown += """
## AbuseIPDB Category Reference

| ID | Category |
|----|----------|
| 3 | Fraud Orders |
| 4 | DDoS Attack |
| 5 | FTP Brute-Force |
| 6 | Ping of Death |
| 7 | Phishing |
| 8 | Fraud VoIP |
| 9 | Open Proxy |
| 10 | Web Spam |
| 11 | Email Spam |
| 12 | Blog Spam |
| 13 | VPN IP |
| 14 | Port Scan |
| 15 | Hacking |
| 16 | SQL Injection |
| 17 | Spoofing |
| 18 | Brute-Force |
| 19 | Bad Web Bot |
| 20 | Exploited Host |
| 21 | Web App Attack |
| 22 | SSH |
| 23 | IoT Targeted |

"""

        # Add direct link to AbuseIPDB
        markdown += f"**[View on AbuseIPDB →](https://www.abuseipdb.com/check/{ip_address})**\n"

        return markdown