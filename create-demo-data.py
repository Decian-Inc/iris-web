#!/usr/bin/env python3
"""
IRIS Demo Data Creator
Creates comprehensive demo data for IRIS (Incident Response Investigation System)
- 5 companies as customers
- 2 incident response cases per company (10 total)
- Realistic IOCs for each case
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
import random
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# IRIS API Configuration
IRIS_BASE_URL = "https://localhost:443"  # Update if using different URL
IRIS_API_KEY = "your_api_key_here"       # Replace with your IRIS API key

# Demo Companies Data
DEMO_COMPANIES = [
    {
        "name": "TechCorp Industries",
        "description": "Global technology corporation specializing in cloud infrastructure and cybersecurity solutions. Fortune 500 company with operations in 45 countries.",
        "sla": "24/7 Premium Support - 1 hour response time"
    },
    {
        "name": "SecureBank Financial",
        "description": "International banking institution providing financial services to over 10 million customers worldwide. Highly regulated environment with strict compliance requirements.",
        "sla": "Critical: 30min, High: 2hrs, Medium: 8hrs"
    },
    {
        "name": "HealthMed Systems",
        "description": "Healthcare technology provider managing electronic health records and medical device networks for 200+ hospitals and clinics.",
        "sla": "HIPAA-compliant incident response - 1 hour SLA"
    },
    {
        "name": "RetailMax Corporation",
        "description": "E-commerce and retail chain with 1,500 physical stores and major online presence. Processes millions of customer transactions daily.",
        "sla": "Business hours: 4hrs, After hours: 8hrs"
    },
    {
        "name": "EduTech University",
        "description": "Leading educational institution with 40,000 students and faculty. Extensive research network and distance learning infrastructure.",
        "sla": "Standard business hours support - 8 hour response"
    }
]

# Case scenarios for different industries
CASE_SCENARIOS = {
    "TechCorp Industries": [
        {
            "name": "Advanced Persistent Threat - Cloud Infrastructure Compromise",
            "description": "Sophisticated APT group gained unauthorized access to cloud management console. Evidence of lateral movement and data exfiltration from customer environments. Multi-stage attack involving compromised service accounts and privilege escalation.",
            "classification": "APT",
            "severity": "Critical",
            "case_type": "intrusion"
        },
        {
            "name": "Supply Chain Attack - Software Repository Compromise",
            "description": "Malicious code injection discovered in internal software repository affecting multiple customer deployments. Potential backdoor implementation in production systems. Investigation into source of compromise and impact assessment ongoing.",
            "classification": "Supply Chain",
            "severity": "High",
            "case_type": "malware"
        }
    ],
    "SecureBank Financial": [
        {
            "name": "Business Email Compromise - Wire Transfer Fraud",
            "description": "CFO's email account compromised leading to fraudulent wire transfer requests totaling $2.3M. Social engineering attack targeting C-level executives. Investigation into email security controls and transaction approval processes.",
            "classification": "BEC",
            "severity": "Critical",
            "case_type": "phishing"
        },
        {
            "name": "ATM Network Malware - Card Skimming Operation",
            "description": "Malware detected on ATM network designed to capture card data and PINs. Coordinated attack across multiple branch locations. Forensic analysis of compromised terminals and review of physical security measures.",
            "classification": "Financial Fraud",
            "severity": "High",
            "case_type": "malware"
        }
    ],
    "HealthMed Systems": [
        {
            "name": "Ransomware Attack - Patient Data Encryption",
            "description": "Conti ransomware variant deployed across hospital network encrypting patient records and medical systems. Critical medical equipment offline. Emergency incident response with focus on patient safety and HIPAA compliance.",
            "classification": "Ransomware",
            "severity": "Critical",
            "case_type": "malware"
        },
        {
            "name": "Insider Threat - Unauthorized Data Access",
            "description": "Healthcare worker accessing patient records outside of normal duties. Pattern of unauthorized access to celebrity and high-profile patient files. Investigation into access controls and monitoring systems.",
            "classification": "Insider Threat",
            "severity": "Medium",
            "case_type": "data_breach"
        }
    ],
    "RetailMax Corporation": [
        {
            "name": "Point-of-Sale Compromise - Credit Card Data Theft",
            "description": "POS terminals compromised with memory-scraping malware capturing credit card data during transactions. Potential exposure of 500,000+ customer payment records. Investigation into payment processing security and network segmentation.",
            "classification": "POS Malware",
            "severity": "Critical",
            "case_type": "data_breach"
        },
        {
            "name": "E-commerce Platform DDoS - Service Disruption",
            "description": "Large-scale DDoS attack against e-commerce platform during Black Friday sales period. Multi-vector attack including volumetric and application-layer components. Revenue impact estimated at $1.2M per hour.",
            "classification": "DDoS",
            "severity": "High",
            "case_type": "service_disruption"
        }
    ],
    "EduTech University": [
        {
            "name": "Student Data Breach - Database Compromise",
            "description": "Unauthorized access to student information system exposing personal and academic records of 35,000 students. SQL injection vulnerability exploited in legacy web application. FERPA compliance investigation required.",
            "classification": "Data Breach",
            "severity": "High",
            "case_type": "data_breach"
        },
        {
            "name": "Cryptomining Malware - Research Network Infection",
            "description": "Cryptocurrency mining malware detected on high-performance computing cluster used for research. Performance degradation affecting ongoing research projects. Investigation into infection vector and impact on research data.",
            "classification": "Cryptomining",
            "severity": "Medium",
            "case_type": "malware"
        }
    ]
}

# IOC Templates for different types of incidents
IOC_TEMPLATES = {
    "ip_addresses": {
        "malicious_external": [
            "185.220.102.8", "103.85.24.155", "159.203.45.95", "91.134.144.86",
            "45.146.164.110", "185.142.236.34", "198.51.100.42", "203.0.113.15",
            "94.156.35.47", "178.62.214.99"
        ],
        "internal_compromised": [
            "192.168.1.150", "10.0.0.45", "172.16.2.33", "192.168.100.75",
            "10.10.10.220", "172.20.1.88", "192.168.50.167", "10.1.1.99"
        ]
    },
    "domains": {
        "c2_servers": [
            "malware-command.example.com", "evil-c2-server.net", "badactor-control.org",
            "suspicious-domain.info", "threat-command.biz", "malicious-host.club"
        ],
        "phishing": [
            "secure-bank-login.phishing.example", "microsoft-security-alert.fake.com",
            "amazon-verification.scam.net", "paypal-account-review.evil.org"
        ]
    },
    "file_hashes": {
        "md5": [
            "5d41402abc4b2a76b9719d911017c592", "098f6bcd4621d373cade4e832627b4f6",
            "1dcca23355272056f04fe8bf20edfce0", "827ccb0eea8a706c4c34a16891f84e7b"
        ],
        "sha1": [
            "356a192b7913b04c54574d18c28d46e6395428ab", "da39a3ee5e6b4b0d3255bfef95601890afd80709",
            "77de68daecd823babbb58edb1c8e14d7106e83bb", "1af17e73721dbe0c40011b82ed4bb1a7dbe3ce29"
        ],
        "sha256": [
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
            "6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d"
        ]
    },
    "email_addresses": [
        "attacker@malicious-domain.evil", "phishing@scammer.net", "admin@compromised-account.com",
        "noreply@fake-service.org", "security@spoofed-bank.com", "support@fraudulent-site.biz"
    ],
    "urls": [
        "https://malicious-site.example.com/payload.exe",
        "http://phishing-page.scam.net/login.php",
        "https://evil-download.org/trojan.zip",
        "http://c2-server.malware.com/beacon",
        "https://fake-update.net/critical-security-patch.exe"
    ],
    "file_paths": [
        "C:\\Windows\\Temp\\malware.exe", "C:\\Users\\Public\\suspicious.dll",
        "/tmp/backdoor.sh", "/var/log/compromised.log", "C:\\ProgramData\\evil.bat",
        "/home/user/Downloads/trojan.elf", "C:\\Windows\\System32\\fake_system.exe"
    ]
}

def create_iris_session():
    """Create authenticated session with IRIS"""
    session = requests.Session()
    session.verify = False  # Disable SSL verification for self-signed certs
    session.headers.update({
        'Authorization': f'Bearer {IRIS_API_KEY}',
        'Content-Type': 'application/json'
    })
    return session

def create_customer(session, customer_data):
    """Create a customer/company in IRIS"""
    print(f"Creating customer: {customer_data['name']}")

    response = session.post(f"{IRIS_BASE_URL}/manage/customers/add", json=customer_data)

    if response.status_code == 200:
        customer_id = response.json()['data']['client_id']
        print(f"✅ Created customer: {customer_data['name']} (ID: {customer_id})")
        return customer_id
    else:
        print(f"❌ Failed to create customer {customer_data['name']}: {response.status_code}")
        print(response.text)
        return None

def create_case(session, customer_id, case_data):
    """Create a case for a specific customer"""
    case_payload = {
        "case_name": case_data["name"],
        "case_description": case_data["description"],
        "case_customer": customer_id,
        "case_classification": 1,  # Default classification
        "case_soc_id": f"INC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    }

    print(f"  Creating case: {case_data['name']}")

    response = session.post(f"{IRIS_BASE_URL}/api/v2/cases", json=case_payload)

    if response.status_code == 201:
        case_id = response.json()['data']['case_id']
        print(f"  ✅ Created case: {case_data['name']} (ID: {case_id})")
        return case_id
    else:
        print(f"  ❌ Failed to create case {case_data['name']}: {response.status_code}")
        print(response.text)
        return None

def get_ioc_type_id(ioc_value):
    """Determine IOC type ID based on the value"""
    # Common IOC type mappings (these may need adjustment based on your IRIS setup)
    if ioc_value.count('.') == 3 and all(part.isdigit() for part in ioc_value.split('.')):
        return 79  # IP Address
    elif '@' in ioc_value:
        return 82  # Email Address
    elif ioc_value.startswith(('http://', 'https://')):
        return 76  # URL
    elif '.' in ioc_value and not ioc_value.startswith(('C:', '/')) and not ioc_value.count('.') == 3:
        return 73  # Domain
    elif len(ioc_value) == 32 and all(c in '0123456789abcdef' for c in ioc_value.lower()):
        return 78  # MD5
    elif len(ioc_value) == 40 and all(c in '0123456789abcdef' for c in ioc_value.lower()):
        return 77  # SHA1
    elif len(ioc_value) == 64 and all(c in '0123456789abcdef' for c in ioc_value.lower()):
        return 81  # SHA256
    elif '\\' in ioc_value or ioc_value.startswith('/'):
        return 74  # File Path
    else:
        return 75  # Generic/Other

def get_tlp_id(classification):
    """Map case classification to appropriate TLP level"""
    high_risk = ["APT", "Ransomware", "BEC", "Financial Fraud", "POS Malware"]
    if classification in high_risk:
        return 4  # TLP:RED
    else:
        return 3  # TLP:AMBER

def create_ioc(session, case_id, ioc_value, description, classification):
    """Create an IOC in the specified case"""
    ioc_payload = {
        "ioc_value": ioc_value,
        "ioc_description": description,
        "ioc_type_id": get_ioc_type_id(ioc_value),
        "ioc_tlp_id": get_tlp_id(classification),
        "ioc_tags": "demo,automated,testing"
    }

    response = session.post(f"{IRIS_BASE_URL}/api/v2/cases/{case_id}/iocs", json=ioc_payload)

    if response.status_code == 201:
        print(f"    ✅ Created IOC: {ioc_value}")
        return True
    else:
        print(f"    ❌ Failed to create IOC {ioc_value}: {response.status_code}")
        return False

def generate_case_iocs(case_type, classification):
    """Generate realistic IOCs based on case type"""
    iocs = []

    # Add IP addresses
    iocs.extend([
        (random.choice(IOC_TEMPLATES["ip_addresses"]["malicious_external"]), "Malicious external IP address associated with threat actor"),
        (random.choice(IOC_TEMPLATES["ip_addresses"]["internal_compromised"]), "Internal IP address showing signs of compromise")
    ])

    # Add domains based on case type
    if case_type in ["phishing", "BEC"]:
        iocs.append((random.choice(IOC_TEMPLATES["domains"]["phishing"]), "Phishing domain used in attack"))
    else:
        iocs.append((random.choice(IOC_TEMPLATES["domains"]["c2_servers"]), "Command and control server domain"))

    # Add file hashes
    iocs.extend([
        (random.choice(IOC_TEMPLATES["file_hashes"]["md5"]), "MD5 hash of malicious file"),
        (random.choice(IOC_TEMPLATES["file_hashes"]["sha1"]), "SHA1 hash of malicious executable"),
        (random.choice(IOC_TEMPLATES["file_hashes"]["sha256"]), "SHA256 hash of suspicious binary")
    ])

    # Add email addresses for appropriate case types
    if case_type in ["phishing", "BEC", "data_breach"]:
        iocs.append((random.choice(IOC_TEMPLATES["email_addresses"]), "Attacker email address used in campaign"))

    # Add URLs
    iocs.append((random.choice(IOC_TEMPLATES["urls"]), "Malicious URL hosting payload or phishing page"))

    # Add file paths
    iocs.extend([
        (random.choice(IOC_TEMPLATES["file_paths"]), "File path of malicious binary on compromised system"),
        (random.choice(IOC_TEMPLATES["file_paths"]), "Log file path containing evidence of compromise")
    ])

    return iocs

def main():
    """Main function to create demo data"""
    print("🚀 Starting IRIS Demo Data Creation")
    print("=" * 60)

    # Validate configuration
    if IRIS_API_KEY == "your_api_key_here":
        print("❌ Please configure your IRIS API key in the script")
        print("   Update IRIS_API_KEY variable with your actual API key")
        print("   You can get your API key from IRIS web interface under User Settings")
        sys.exit(1)

    # Create authenticated session
    session = create_iris_session()

    # Test connection
    try:
        test_response = session.get(f"{IRIS_BASE_URL}/api/ping")
        if test_response.status_code == 200:
            print("✅ Successfully connected to IRIS API")
        else:
            print(f"❌ Failed to connect to IRIS API: {test_response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("   Make sure IRIS is running and accessible at the configured URL")
        sys.exit(1)

    created_customers = []
    created_cases = []
    created_iocs_count = 0

    # Create customers and their cases
    for company in DEMO_COMPANIES:
        print(f"\n🏢 Processing company: {company['name']}")

        # Create customer
        customer_data = {
            "customer_name": company["name"],
            "customer_description": company["description"],
            "customer_sla": company["sla"]
        }

        customer_id = create_customer(session, customer_data)
        if not customer_id:
            print(f"⚠️  Skipping cases for {company['name']} due to customer creation failure")
            continue

        created_customers.append((customer_id, company["name"]))

        # Create cases for this customer
        cases = CASE_SCENARIOS[company["name"]]
        for case_data in cases:
            case_id = create_case(session, customer_id, case_data)
            if not case_id:
                continue

            created_cases.append((case_id, case_data["name"]))

            # Generate and create IOCs for this case
            print(f"    📊 Adding IOCs to case...")
            iocs = generate_case_iocs(case_data["case_type"], case_data["classification"])

            for ioc_value, ioc_description in iocs:
                if create_ioc(session, case_id, ioc_value, ioc_description, case_data["classification"]):
                    created_iocs_count += 1

                # Small delay to avoid overwhelming the API
                time.sleep(0.1)

        # Delay between customers
        time.sleep(1)

    # Summary
    print("\n" + "=" * 60)
    print("📋 DEMO DATA CREATION SUMMARY")
    print("=" * 60)
    print(f"✅ Customers created: {len(created_customers)}")
    print(f"✅ Cases created: {len(created_cases)}")
    print(f"✅ IOCs created: {created_iocs_count}")

    print(f"\n🌐 Access your IRIS instance at: {IRIS_BASE_URL}")
    print("\n📁 Created Customers:")
    for customer_id, customer_name in created_customers:
        print(f"   • {customer_name} (ID: {customer_id})")

    print(f"\n📋 Created Cases:")
    for case_id, case_name in created_cases:
        print(f"   • {case_name} (ID: {case_id}) - {IRIS_BASE_URL}/case?cid={case_id}")

    print(f"\n🔍 Next Steps:")
    print("1. Log into your IRIS web interface")
    print("2. Navigate to the Dashboard to see the new cases")
    print("3. Explore the cases and their IOCs")
    print("4. Use this data for training, demos, or testing")
    print("5. Configure IRIS modules for IOC enrichment")

if __name__ == "__main__":
    main()