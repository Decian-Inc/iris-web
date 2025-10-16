#!/usr/bin/env python3
"""
IRIS Demo Data Creator
Creates 5 companies and 2 cases with IOCs for each company
"""

import requests
import json
import urllib3
from datetime import datetime, timedelta

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
IRIS_BASE_URL = "https://localhost:443"
API_KEY = "fAgRCP657FCXt8jkpToj6coVxqRSQ5mu-ybs6QO69sWhyKoEfH78G_-kx-oaaYz5Agt02wjEpZ6Zzzp7wy9SMg"

# HTTP Headers
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def make_api_request(method, endpoint, data=None):
    """Make API request to IRIS"""
    url = f"{IRIS_BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS, verify=False)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data, verify=False)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=HEADERS, json=data, verify=False)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def create_customer(name, description):
    """Create a new customer/company"""
    print(f"Creating customer: {name}")

    customer_data = {
        "customer_name": name,
        "customer_description": description,
        "customer_sla": "Standard SLA",
        "custom_attributes": {}
    }

    result = make_api_request("POST", "/manage/customers/add", customer_data)
    if result and result.get("status") == "success":
        customer_id = result["data"]["customer_id"]
        print(f"[+] Created customer '{name}' with ID: {customer_id}")
        return customer_id
    else:
        print(f"[-] Failed to create customer '{name}'")
        return None

def create_case(customer_id, case_name, case_description, classification="malicious-code:virus"):
    """Create a new case for a customer"""
    print(f"  Creating case: {case_name}")

    case_data = {
        "case_name": case_name,
        "case_description": case_description,
        "case_customer": customer_id,
        "case_classification": classification,
        "case_soc_id": f"SOC-{datetime.now().strftime('%Y%m%d')}-{customer_id}",
        "custom_attributes": {}
    }

    result = make_api_request("POST", "/manage/cases/add", case_data)
    if result and result.get("status") == "success":
        case_id = result["data"]["case_id"]
        print(f"  [+] Created case '{case_name}' with ID: {case_id}")
        return case_id
    else:
        print(f"  [-] Failed to create case '{case_name}'")
        return None

def add_ioc_to_case(case_id, ioc_value, ioc_type, ioc_description, tlp="amber"):
    """Add an IOC to a case"""

    ioc_data = {
        "ioc_value": ioc_value,
        "ioc_type_id": get_ioc_type_id(ioc_type),
        "ioc_description": ioc_description,
        "ioc_tlp_id": get_tlp_id(tlp),
        "case_id": case_id,
        "custom_attributes": {}
    }

    result = make_api_request("POST", f"/case/ioc/add", ioc_data)
    if result and result.get("status") == "success":
        return True
    else:
        print(f"    [-] Failed to add IOC: {ioc_value}")
        return False

def get_ioc_type_id(ioc_type):
    """Get IOC type ID based on type name"""
    type_mapping = {
        "ip-dst": 76,
        "ip-src": 77,
        "domain": 11,
        "hostname": 3,
        "url": 93,
        "md5": 22,
        "sha1": 23,
        "sha256": 24,
        "email": 12,
        "filename": 17,
        "filepath": 18
    }
    return type_mapping.get(ioc_type, 76)  # Default to ip-dst

def get_tlp_id(tlp):
    """Get TLP ID based on TLP name"""
    tlp_mapping = {
        "white": 1,
        "green": 2,
        "amber": 3,
        "red": 4
    }
    return tlp_mapping.get(tlp, 3)  # Default to amber

def create_demo_data():
    """Create all demo data"""
    print("Starting IRIS Demo Data Creation")
    print("=" * 50)

    # Define companies
    companies = [
        {
            "name": "TechCorp Industries",
            "description": "Global technology corporation specializing in software development and cloud services"
        },
        {
            "name": "SecureBank Financial",
            "description": "International banking institution providing comprehensive financial services"
        },
        {
            "name": "HealthMed Systems",
            "description": "Healthcare technology provider offering medical device software and patient management systems"
        },
        {
            "name": "RetailMax Corporation",
            "description": "E-commerce and retail chain with online and physical store presence"
        },
        {
            "name": "EduTech University",
            "description": "Educational institution providing online learning platforms and digital education services"
        }
    ]

    # Define cases for each company
    cases_template = [
        {
            "name": "APT Campaign Investigation",
            "description": "Advanced Persistent Threat detected targeting corporate infrastructure with sophisticated malware and lateral movement techniques",
            "classification": "malicious-code:trojan",
            "iocs": [
                {"value": "185.243.115.84", "type": "ip-dst", "desc": "Malicious C2 server communicating with infected workstations"},
                {"value": "192.168.1.105", "type": "ip-src", "desc": "Compromised internal workstation showing suspicious outbound connections"},
                {"value": "evil-corp-update.com", "type": "domain", "desc": "Fake software update domain used for malware distribution"},
                {"value": "mail-server-patch.com", "type": "hostname", "desc": "Malicious hostname masquerading as legitimate update server"},
                {"value": "https://evil-corp-update.com/patch/update.exe", "type": "url", "desc": "Malware download URL disguised as software update"},
                {"value": "d41d8cd98f00b204e9800998ecf8427e", "type": "md5", "desc": "MD5 hash of trojan payload"},
                {"value": "da39a3ee5e6b4b0d3255bfef95601890afd80709", "type": "sha1", "desc": "SHA1 hash of malicious executable"},
                {"value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "type": "sha256", "desc": "SHA256 hash of APT backdoor"},
                {"value": "attacker@evil-domain.net", "type": "email", "desc": "Attacker email address used in spear-phishing campaign"},
                {"value": "C:\\Windows\\Temp\\svchost.exe", "type": "filepath", "desc": "Malicious file masquerading as legitimate Windows service"}
            ]
        },
        {
            "name": "Ransomware Incident Response",
            "description": "Ransomware attack encrypting critical business files with ransom demands and system compromise indicators",
            "classification": "malicious-code:ransomware",
            "iocs": [
                {"value": "203.45.67.123", "type": "ip-dst", "desc": "Ransomware command and control server"},
                {"value": "10.0.2.89", "type": "ip-src", "desc": "First infected endpoint in the network"},
                {"value": "crypto-pay-now.onion", "type": "domain", "desc": "Tor hidden service for ransom payment"},
                {"value": "payment-gateway.darkweb", "type": "hostname", "desc": "Alternative payment portal hostname"},
                {"value": "https://crypto-pay-now.onion/victim-12345", "type": "url", "desc": "Personalized ransom payment page"},
                {"value": "f2d1db7e9b8c4a5d6e7f8a9b0c1d2e3f", "type": "md5", "desc": "MD5 of ransomware executable"},
                {"value": "a1b2c3d4e5f6789012345678901234567890abcd", "type": "sha1", "desc": "SHA1 of encryption payload"},
                {"value": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08", "type": "sha256", "desc": "SHA256 of ransomware binary"},
                {"value": "ransom@darkmail.org", "type": "email", "desc": "Contact email provided in ransom note"},
                {"value": "C:\\Users\\Public\\README_DECRYPT.txt", "type": "filepath", "desc": "Ransom note file location"}
            ]
        }
    ]

    # Create companies and cases
    created_data = []

    for company in companies:
        print(f"\nProcessing company: {company['name']}")
        customer_id = create_customer(company["name"], company["description"])

        if customer_id:
            company_cases = []

            for i, case_template in enumerate(cases_template):
                # Customize case name for each company
                case_name = f"{case_template['name']} - {company['name']}"
                case_id = create_case(
                    customer_id,
                    case_name,
                    case_template["description"],
                    case_template["classification"]
                )

                if case_id:
                    print(f"    Adding IOCs to case {case_id}")
                    iocs_added = 0

                    for ioc in case_template["iocs"]:
                        if add_ioc_to_case(case_id, ioc["value"], ioc["type"], ioc["desc"]):
                            iocs_added += 1

                    print(f"    Added {iocs_added}/{len(case_template['iocs'])} IOCs")
                    company_cases.append({
                        "case_id": case_id,
                        "case_name": case_name,
                        "iocs_count": iocs_added
                    })

            created_data.append({
                "customer_id": customer_id,
                "customer_name": company["name"],
                "cases": company_cases
            })

    # Summary
    print("\n" + "=" * 50)
    print("Demo Data Creation Summary")
    print("=" * 50)

    total_companies = len(created_data)
    total_cases = sum(len(company["cases"]) for company in created_data)
    total_iocs = sum(case["iocs_count"] for company in created_data for case in company["cases"])

    print(f"Companies created: {total_companies}")
    print(f"Cases created: {total_cases}")
    print(f"IOCs added: {total_iocs}")

    print("\nDetailed breakdown:")
    for company in created_data:
        print(f"\n{company['customer_name']} (ID: {company['customer_id']})")
        for case in company["cases"]:
            print(f"  {case['case_name']} (ID: {case['case_id']}) - {case['iocs_count']} IOCs")

    print(f"\nDemo data creation complete!")
    print(f"Access your IRIS instance at: {IRIS_BASE_URL}")

if __name__ == "__main__":
    create_demo_data()