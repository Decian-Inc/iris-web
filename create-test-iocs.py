#!/usr/bin/env python3
"""
AbuseIPDB Module Test IOC Creator
Creates test IOCs in IRIS for validating the AbuseIPDB enrichment module
"""

import requests
import json
import sys
from datetime import datetime

# IRIS API Configuration
IRIS_BASE_URL = "https://localhost"  # Change if using different URL
IRIS_API_KEY = "your_api_key_here"   # Replace with your IRIS API key

# Test IOCs with descriptions
TEST_IOCS = [
    {
        "value": "185.220.102.8",
        "description": "Test Case 1: High-Confidence Malicious IP (Tor exit node)",
        "ioc_type": "ip",
        "tlp": "amber"
    },
    {
        "value": "103.85.24.155",
        "description": "Test Case 2: Botnet C2 Server",
        "ioc_type": "ip",
        "tlp": "amber"
    },
    {
        "value": "159.203.45.95",
        "description": "Test Case 3: Scanning/Probing Activity",
        "ioc_type": "ip",
        "tlp": "amber"
    },
    {
        "value": "91.134.144.86",
        "description": "Test Case 4: Brute Force Attacks",
        "ioc_type": "ip",
        "tlp": "amber"
    },
    {
        "value": "45.146.164.110",
        "description": "Test Case 5: Suspicious Activity (Moderate Risk)",
        "ioc_type": "ip",
        "tlp": "green"
    },
    {
        "value": "185.142.236.34",
        "description": "Test Case 6: Potential Compromise (Mixed Categories)",
        "ioc_type": "ip",
        "tlp": "green"
    },
    {
        "value": "8.8.8.8",
        "description": "Test Case 7: Google Public DNS (Clean IP)",
        "ioc_type": "ip",
        "tlp": "white"
    },
    {
        "value": "1.1.1.1",
        "description": "Test Case 8: Cloudflare DNS (Clean IP)",
        "ioc_type": "ip",
        "tlp": "white"
    },
    {
        "value": "13.107.42.14",
        "description": "Test Case 9: Microsoft Public Service (Clean IP)",
        "ioc_type": "ip",
        "tlp": "white"
    },
    {
        "value": "192.168.1.1",
        "description": "Test Case 10: Private Network IP (Should not enrich)",
        "ioc_type": "ip",
        "tlp": "white"
    }
]

def create_iris_session():
    """Create authenticated session with IRIS"""
    session = requests.Session()
    session.verify = False  # Disable SSL verification for self-signed certs
    session.headers.update({
        'Authorization': f'Bearer {IRIS_API_KEY}',
        'Content-Type': 'application/json'
    })
    return session

def create_test_case(session):
    """Create a test case for the IOCs"""
    case_data = {
        "case_name": f"AbuseIPDB Module Testing - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "case_description": "Automated test case for validating AbuseIPDB enrichment module functionality",
        "case_customer": 1,  # Default customer ID
        "case_classification": 1,  # Default classification
        "case_soc_id": f"TEST-ABUSEIPDB-{datetime.now().strftime('%Y%m%d%H%M')}"
    }

    response = session.post(f"{IRIS_BASE_URL}/api/v2/cases", json=case_data)
    if response.status_code == 201:
        case_id = response.json()['data']['case_id']
        print(f"✅ Created test case: {case_id}")
        return case_id
    else:
        print(f"❌ Failed to create test case: {response.status_code}")
        print(response.text)
        return None

def create_ioc(session, case_id, ioc_data):
    """Create an IOC in the specified case"""
    ioc_payload = {
        "ioc_value": ioc_data["value"],
        "ioc_description": ioc_data["description"],
        "ioc_type_id": 79,  # IP address type ID (may need adjustment)
        "ioc_tlp_id": get_tlp_id(ioc_data["tlp"]),
        "ioc_tags": "test,abuseipdb,automation"
    }

    response = session.post(f"{IRIS_BASE_URL}/api/v2/cases/{case_id}/iocs", json=ioc_payload)
    if response.status_code == 201:
        print(f"✅ Created IOC: {ioc_data['value']} - {ioc_data['description']}")
        return True
    else:
        print(f"❌ Failed to create IOC {ioc_data['value']}: {response.status_code}")
        print(response.text)
        return False

def get_tlp_id(tlp_color):
    """Map TLP colors to IDs"""
    tlp_mapping = {
        "white": 1,
        "green": 2,
        "amber": 3,
        "red": 4
    }
    return tlp_mapping.get(tlp_color.lower(), 2)

def main():
    """Main function to create test IOCs"""
    print("🚀 Starting AbuseIPDB Module Test IOC Creation")
    print("=" * 50)

    # Validate configuration
    if IRIS_API_KEY == "your_api_key_here":
        print("❌ Please configure your IRIS API key in the script")
        print("   Update IRIS_API_KEY variable with your actual API key")
        sys.exit(1)

    # Create authenticated session
    session = create_iris_session()

    # Create test case
    case_id = create_test_case(session)
    if not case_id:
        print("❌ Cannot proceed without test case")
        sys.exit(1)

    # Create IOCs
    print(f"\n📝 Creating {len(TEST_IOCS)} test IOCs...")
    success_count = 0

    for ioc in TEST_IOCS:
        if create_ioc(session, case_id, ioc):
            success_count += 1

    print("\n" + "=" * 50)
    print(f"✅ Successfully created {success_count}/{len(TEST_IOCS)} test IOCs")
    print(f"📋 Test case ID: {case_id}")
    print(f"🌐 View case: {IRIS_BASE_URL}/case?cid={case_id}")

    if success_count < len(TEST_IOCS):
        print(f"⚠️  {len(TEST_IOCS) - success_count} IOCs failed to create")
        print("   Check IRIS logs and API permissions")

    print("\n🔍 Next Steps:")
    print("1. Navigate to the test case in IRIS")
    print("2. Enable AbuseIPDB module if not already enabled")
    print("3. Configure module with your API key")
    print("4. Watch for automatic enrichment on the IOCs")
    print("5. Check Notes section for AbuseIPDB reports")

if __name__ == "__main__":
    main()