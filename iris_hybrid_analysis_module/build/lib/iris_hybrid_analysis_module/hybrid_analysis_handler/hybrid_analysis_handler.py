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

import requests
import json
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import urlparse


class HybridAnalysisHandler:
    """
    Handles API interactions with Hybrid Analysis platform
    """

    def __init__(self, api_key: str, environment_id: int = 120, max_reports: int = 10):
        """
        Initialize Hybrid Analysis handler

        :param api_key: Hybrid Analysis API key
        :param environment_id: Analysis environment ID
        :param max_reports: Maximum reports to retrieve
        """
        self.api_key = api_key
        self.environment_id = environment_id
        self.max_reports = max_reports
        self.base_url = "https://www.hybrid-analysis.com/api/v2"
        self.headers = {
            'api-key': self.api_key,
            'User-Agent': 'Falcon Sandbox',
            'accept': 'application/json'
        }

    def search_hash(self, file_hash: str) -> Dict[str, Any]:
        """
        Search for file hash in Hybrid Analysis

        :param file_hash: File hash (MD5, SHA1, SHA256)
        :return: Search results
        """
        try:
            url = f"{self.base_url}/search/hash"
            data = {'hash': file_hash}

            response = requests.post(url, headers=self.headers, data=data, timeout=30)

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'hash': file_hash
                }
            elif response.status_code == 404:
                return {
                    'success': True,
                    'data': [],
                    'hash': file_hash,
                    'message': 'Hash not found in database'
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'hash': file_hash
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}",
                'hash': file_hash
            }

    def search_terms(self, term: str, term_type: str = 'domain') -> Dict[str, Any]:
        """
        Search for domains, URLs, or other terms

        :param term: Search term
        :param term_type: Type of term (domain, url, etc.)
        :return: Search results
        """
        try:
            url = f"{self.base_url}/search/terms"
            data = {
                term_type: term
            }

            response = requests.post(url, headers=self.headers, data=data, timeout=30)

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'term': term,
                    'type': term_type
                }
            elif response.status_code == 404:
                return {
                    'success': True,
                    'data': [],
                    'term': term,
                    'type': term_type,
                    'message': f'{term_type.title()} not found in database'
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'term': term,
                    'type': term_type
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}",
                'term': term,
                'type': term_type
            }

    def get_report_summary(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed report summary

        :param job_id: Analysis job ID
        :return: Report details
        """
        try:
            url = f"{self.base_url}/report/{job_id}/summary"

            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'job_id': job_id
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'job_id': job_id
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}",
                'job_id': job_id
            }

    def get_mitre_attack(self, job_id: str) -> Dict[str, Any]:
        """
        Get MITRE ATT&CK techniques for analysis

        :param job_id: Analysis job ID
        :return: MITRE ATT&CK data
        """
        try:
            url = f"{self.base_url}/report/{job_id}/mitre-attack"

            response = requests.get(url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'job_id': job_id
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'job_id': job_id
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}",
                'job_id': job_id
            }

    def determine_ioc_type(self, ioc_value: str) -> str:
        """
        Determine IOC type for Hybrid Analysis

        :param ioc_value: IOC value to analyze
        :return: IOC type
        """
        if self._is_file_hash(ioc_value):
            return 'hash'
        elif self._is_url(ioc_value):
            return 'url'
        elif self._is_domain(ioc_value):
            return 'domain'
        elif self._is_email(ioc_value):
            return 'email'
        else:
            return 'unknown'

    def _is_file_hash(self, value: str) -> bool:
        """Check if value is a file hash"""
        value = value.strip().lower()
        # MD5: 32 chars, SHA1: 40 chars, SHA256: 64 chars
        if re.match(r'^[a-f0-9]{32}$', value):  # MD5
            return True
        elif re.match(r'^[a-f0-9]{40}$', value):  # SHA1
            return True
        elif re.match(r'^[a-f0-9]{64}$', value):  # SHA256
            return True
        return False

    def _is_url(self, value: str) -> bool:
        """Check if value is a URL"""
        try:
            result = urlparse(value)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _is_domain(self, value: str) -> bool:
        """Check if value is a domain"""
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        return domain_pattern.match(value) is not None and not self._is_url(value)

    def _is_email(self, value: str) -> bool:
        """Check if value is an email address"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return email_pattern.match(value) is not None

    def format_report_markdown(self, ioc_value: str, ioc_type: str, search_data: Dict,
                             report_summaries: List[Dict] = None, mitre_data: List[Dict] = None) -> str:
        """
        Format Hybrid Analysis data as markdown report

        :param ioc_value: IOC value
        :param ioc_type: Type of IOC
        :param search_data: Search results
        :param report_summaries: Detailed report summaries
        :param mitre_data: MITRE ATT&CK data
        :return: Formatted markdown report
        """
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        markdown = f"""# Hybrid Analysis Report

**IOC:** `{ioc_value}`
**Type:** {ioc_type.upper()}
**Report Date:** {report_date}
**Analysis Platform:** Hybrid Analysis (Falcon Sandbox)

---

## Executive Summary

"""

        if not search_data.get('success'):
            markdown += f"❌ **Analysis Failed**\n\n**Error:** {search_data.get('error', 'Unknown error')}\n\n"
            return markdown

        results = search_data.get('data', [])
        if not results:
            markdown += f"ℹ️ **No Analysis Found**\n\n{search_data.get('message', 'No analysis reports found for this IOC.')}\n\n"
            return markdown

        # Summary statistics
        total_reports = len(results)
        malicious_count = sum(1 for r in results if r.get('verdict') == 'malicious')
        suspicious_count = sum(1 for r in results if r.get('verdict') == 'suspicious')
        clean_count = sum(1 for r in results if r.get('verdict') == 'no specific threat')

        markdown += f"""
| Metric | Value |
|--------|-------|
| **Total Reports** | {total_reports} |
| **Malicious** | {malicious_count} |
| **Suspicious** | {suspicious_count} |
| **Clean** | {clean_count} |

"""

        # Threat verdict
        if malicious_count > 0:
            verdict = "🔴 **MALICIOUS**"
            risk_level = "HIGH"
        elif suspicious_count > 0:
            verdict = "🟡 **SUSPICIOUS**"
            risk_level = "MEDIUM"
        else:
            verdict = "🟢 **CLEAN**"
            risk_level = "LOW"

        markdown += f"**Overall Verdict:** {verdict}  \n**Risk Level:** {risk_level}\n\n---\n\n"

        # Analysis Reports
        markdown += "## Analysis Reports\n\n"

        for i, result in enumerate(results[:self.max_reports], 1):
            job_id = result.get('job_id', 'N/A')
            verdict = result.get('verdict', 'unknown')
            threat_score = result.get('threat_score', 0)
            analysis_start = result.get('analysis_start_time', 'N/A')
            environment = result.get('environment_description', 'N/A')

            verdict_emoji = {
                'malicious': '🔴',
                'suspicious': '🟡',
                'no specific threat': '🟢',
                'whitelisted': '⚪'
            }.get(verdict, '❓')

            markdown += f"""### Report #{i} - {verdict_emoji} {verdict.upper()}

| Field | Value |
|-------|-------|
| **Job ID** | `{job_id}` |
| **Threat Score** | {threat_score}/100 |
| **Analysis Time** | {analysis_start} |
| **Environment** | {environment} |

"""

            # Add specific details based on IOC type
            if ioc_type == 'hash':
                file_type = result.get('type_short', 'N/A')
                file_size = result.get('size', 0)
                markdown += f"| **File Type** | {file_type} |\n"
                markdown += f"| **File Size** | {file_size:,} bytes |\n"

            # Add report link
            if job_id != 'N/A':
                markdown += f"\n[📊 View Full Report](https://www.hybrid-analysis.com/sample/{job_id})\n\n"

        # MITRE ATT&CK section
        if mitre_data:
            markdown += "---\n\n## MITRE ATT&CK Techniques\n\n"
            techniques = set()
            for report in mitre_data:
                if report.get('success') and report.get('data'):
                    for technique in report['data']:
                        tactic = technique.get('tactic', 'Unknown')
                        technique_id = technique.get('technique', 'Unknown')
                        technique_name = technique.get('technique_name', 'Unknown')
                        techniques.add((tactic, technique_id, technique_name))

            if techniques:
                markdown += "| Tactic | Technique ID | Technique Name |\n"
                markdown += "|--------|--------------|----------------|\n"
                for tactic, tech_id, tech_name in sorted(techniques):
                    markdown += f"| {tactic} | {tech_id} | {tech_name} |\n"
            else:
                markdown += "No MITRE ATT&CK techniques identified.\n"

        # Footer
        markdown += f"""

---

## Additional Information

- **API Source:** Hybrid Analysis (Falcon Sandbox)
- **IOC Analyzed:** `{ioc_value}`
- **Report Generated:** {report_date}
- **Analysis Environment:** Environment ID {self.environment_id}

**External Links:**
- [Hybrid Analysis Portal](https://www.hybrid-analysis.com/)
- [Search for IOC](https://www.hybrid-analysis.com/search?query={ioc_value})

*This report was automatically generated by the Decian Hybrid Analysis integration module.*
"""

        return markdown