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

import requests
import time
import base64
import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, Optional, Any


class URLScanHandler:

    def __init__(self, api_key: str, visibility: str = "unlisted", timeout: int = 120):
        self.api_key = api_key
        self.visibility = visibility
        self.timeout = timeout
        self.base_url = "https://urlscan.io/api/v1"
        self.headers = {
            'API-Key': self.api_key,
            'Content-Type': 'application/json'
        }

    def determine_ioc_type(self, ioc_value: str) -> str:
        if self._is_url(ioc_value):
            return 'url'
        elif self._is_domain(ioc_value):
            return 'domain'
        else:
            return 'unknown'

    def _is_url(self, value: str) -> bool:
        try:
            parsed = urlparse(value)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False

    def _is_domain(self, value: str) -> bool:
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(domain_pattern, value)) and '.' in value and not self._is_url(value)

    def submit_url(self, url: str) -> Dict[str, Any]:
        try:
            if not self._is_url(url) and self._is_domain(url):
                url = f"https://{url}"

            data = {
                'url': url,
                'visibility': self.visibility
            }

            response = requests.post(
                f"{self.base_url}/scan/",
                headers=self.headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'uuid': result.get('uuid'),
                    'api_url': result.get('api'),
                    'result_url': result.get('result'),
                    'visibility': result.get('visibility')
                }
            else:
                return {
                    'success': False,
                    'error': f"URLScan.io submission failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Error submitting URL to URLScan.io: {str(e)}"
            }

    def get_scan_result(self, uuid: str, wait_for_completion: bool = True) -> Dict[str, Any]:
        try:
            result_url = f"{self.base_url}/result/{uuid}/"

            if wait_for_completion:
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    response = requests.get(result_url, timeout=30)

                    if response.status_code == 200:
                        return {
                            'success': True,
                            'data': response.json(),
                            'uuid': uuid
                        }
                    elif response.status_code == 404:
                        time.sleep(10)
                        continue
                    else:
                        return {
                            'success': False,
                            'error': f"URLScan.io result fetch failed: {response.status_code} - {response.text}"
                        }

                return {
                    'success': False,
                    'error': f"Scan did not complete within {self.timeout} seconds"
                }
            else:
                response = requests.get(result_url, timeout=30)
                if response.status_code == 200:
                    return {
                        'success': True,
                        'data': response.json(),
                        'uuid': uuid
                    }
                else:
                    return {
                        'success': False,
                        'error': f"URLScan.io result not ready yet: {response.status_code}"
                    }

        except Exception as e:
            return {
                'success': False,
                'error': f"Error fetching URLScan.io result: {str(e)}"
            }

    def get_screenshot_base64(self, uuid: str) -> Optional[str]:
        try:
            screenshot_url = f"https://urlscan.io/screenshots/{uuid}.png"
            response = requests.get(screenshot_url, timeout=30)

            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
            else:
                return None

        except Exception as e:
            return None

    def search_existing_scans(self, query: str, limit: int = 10) -> Dict[str, Any]:
        try:
            search_url = f"{self.base_url}/search/"
            params = {
                'q': query,
                'size': limit
            }

            response = requests.get(
                search_url,
                headers={'API-Key': self.api_key},
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"URLScan.io search failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Error searching URLScan.io: {str(e)}"
            }

    def analyze_url(self, url: str) -> Dict[str, Any]:
        try:
            original_url = url

            if not self._is_url(url) and self._is_domain(url):
                url = f"https://{url}"

            search_result = self.search_existing_scans(original_url)

            if search_result.get('success') and search_result.get('data', {}).get('results'):
                latest_scan = search_result['data']['results'][0]
                scan_uuid = latest_scan.get('_id')

                if scan_uuid:
                    existing_result = self.get_scan_result(scan_uuid, wait_for_completion=False)
                    if existing_result.get('success'):
                        screenshot_b64 = self.get_screenshot_base64(scan_uuid)
                        result_data = existing_result['data']
                        result_data['screenshot_base64'] = screenshot_b64
                        result_data['scan_uuid'] = scan_uuid
                        return {
                            'success': True,
                            'data': result_data,
                            'source': 'existing_scan',
                            'uuid': scan_uuid
                        }

            submission = self.submit_url(url)
            if not submission.get('success'):
                return submission

            scan_uuid = submission['uuid']
            result = self.get_scan_result(scan_uuid, wait_for_completion=True)

            if result.get('success'):
                screenshot_b64 = self.get_screenshot_base64(scan_uuid)
                result_data = result['data']
                result_data['screenshot_base64'] = screenshot_b64
                result_data['scan_uuid'] = scan_uuid
                return {
                    'success': True,
                    'data': result_data,
                    'source': 'new_scan',
                    'uuid': scan_uuid
                }
            else:
                return result

        except Exception as e:
            return {
                'success': False,
                'error': f"Error analyzing URL: {str(e)}"
            }

    def extract_intelligence_data(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            task = scan_data.get('task', {})
            page = scan_data.get('page', {})
            verdicts = scan_data.get('verdicts', {})
            lists = scan_data.get('lists', {})
            meta = scan_data.get('meta', {})

            overall_verdict = "Clean"
            verdict_details = []

            if verdicts.get('overall', {}).get('malicious'):
                overall_verdict = "Malicious"
            elif verdicts.get('overall', {}).get('suspicious'):
                overall_verdict = "Suspicious"

            for engine, verdict in verdicts.items():
                if isinstance(verdict, dict) and verdict.get('malicious'):
                    verdict_details.append(f"{engine}: Malicious")
                elif isinstance(verdict, dict) and verdict.get('suspicious'):
                    verdict_details.append(f"{engine}: Suspicious")

            domain_age = "Unknown"
            if page.get('domain'):
                domain_age = "Domain age data not available"

            geolocation = {
                'country': page.get('country', 'Unknown'),
                'city': page.get('city', 'Unknown'),
                'asn': page.get('asn', 'Unknown'),
                'ip': page.get('ip', 'Unknown')
            }

            brands = []
            if lists.get('brands'):
                brands = lists['brands']

            return {
                'url': task.get('url', 'Unknown'),
                'domain': task.get('domain', 'Unknown'),
                'final_url': page.get('url', task.get('url', 'Unknown')),
                'title': page.get('title', 'No title'),
                'overall_verdict': overall_verdict,
                'verdict_details': verdict_details,
                'domain_age': domain_age,
                'geolocation': geolocation,
                'server': page.get('server', 'Unknown'),
                'ip_address': page.get('ip', 'Unknown'),
                'asn': page.get('asn', 'Unknown'),
                'country': page.get('country', 'Unknown'),
                'city': page.get('city', 'Unknown'),
                'brands': brands,
                'screenshot_available': scan_data.get('screenshot_base64') is not None,
                'scan_time': task.get('time', datetime.now().isoformat()),
                'technologies': lists.get('technologies', []),
                'certificates': lists.get('certificates', [])
            }

        except Exception as e:
            return {
                'error': f"Error extracting intelligence data: {str(e)}"
            }

    def format_report_markdown(self, url: str, intelligence_data: Dict[str, Any], screenshot_b64: Optional[str] = None) -> str:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

            markdown = f"""# URLScan.io Report - URL - {current_time}

## 🌐 Scan Overview
- **Original URL**: {url}
- **Final URL**: {intelligence_data.get('final_url', 'Unknown')}
- **Domain**: {intelligence_data.get('domain', 'Unknown')}
- **Page Title**: {intelligence_data.get('title', 'No title')}
- **Scan Time**: {intelligence_data.get('scan_time', 'Unknown')}

## 🚨 Security Verdict
- **Overall Assessment**: {intelligence_data.get('overall_verdict', 'Unknown')}
"""

            if intelligence_data.get('verdict_details'):
                markdown += "\n### Detection Details:\n"
                for detail in intelligence_data['verdict_details']:
                    markdown += f"- {detail}\n"

            markdown += f"""
## 📸 Website Screenshot
"""

            if screenshot_b64:
                markdown += f"![Website Screenshot](data:image/png;base64,{screenshot_b64})\n"
            else:
                markdown += "*Screenshot not available*\n"

            geolocation = intelligence_data.get('geolocation', {})
            markdown += f"""
## 🌍 Geolocation & Network Information
- **IP Address**: {geolocation.get('ip', 'Unknown')}
- **Country**: {geolocation.get('country', 'Unknown')}
- **City**: {geolocation.get('city', 'Unknown')}
- **ASN**: {geolocation.get('asn', 'Unknown')}
- **Server**: {intelligence_data.get('server', 'Unknown')}

## 📊 Domain Information
- **Domain Age**: {intelligence_data.get('domain_age', 'Unknown')}
"""

            if intelligence_data.get('brands'):
                markdown += "\n## 🏢 Detected Brands\n"
                for brand in intelligence_data['brands']:
                    markdown += f"- {brand}\n"

            if intelligence_data.get('technologies'):
                markdown += "\n## 🔧 Technologies Detected\n"
                for tech in intelligence_data['technologies']:
                    markdown += f"- {tech}\n"

            if intelligence_data.get('certificates'):
                markdown += "\n## 🔒 SSL/TLS Certificates\n"
                for cert in intelligence_data['certificates']:
                    markdown += f"- {cert}\n"

            markdown += f"""
## 🔗 URLScan.io Links
- **View Full Report**: https://urlscan.io/result/{intelligence_data.get('scan_uuid', '')}
- **Search Similar**: https://urlscan.io/search/#{intelligence_data.get('domain', '')}

---
*Report generated by IRIS URLScan.io Module*
*Scan performed at {current_time}*
"""

            return markdown

        except Exception as e:
            return f"Error generating markdown report: {str(e)}"