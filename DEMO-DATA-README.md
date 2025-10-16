# IRIS Demo Data Creation Guide

This guide explains how to create comprehensive demo data for your IRIS (Incident Response Investigation System) instance using the automated demo data creation script.

## Overview

The `create-demo-data.py` script will create:
- **5 realistic companies** as customers in IRIS
- **10 incident response cases** (2 per company) with different security scenarios
- **70+ IOCs** (Indicators of Compromise) distributed across all cases

## Demo Companies Created

1. **TechCorp Industries** - Global technology corporation
2. **SecureBank Financial** - International banking institution
3. **HealthMed Systems** - Healthcare technology provider
4. **RetailMax Corporation** - E-commerce and retail chain
5. **EduTech University** - Educational institution

## Case Scenarios Included

Each company gets 2 realistic incident response cases based on their industry:

### TechCorp Industries
- Advanced Persistent Threat - Cloud Infrastructure Compromise
- Supply Chain Attack - Software Repository Compromise

### SecureBank Financial
- Business Email Compromise - Wire Transfer Fraud
- ATM Network Malware - Card Skimming Operation

### HealthMed Systems
- Ransomware Attack - Patient Data Encryption
- Insider Threat - Unauthorized Data Access

### RetailMax Corporation
- Point-of-Sale Compromise - Credit Card Data Theft
- E-commerce Platform DDoS - Service Disruption

### EduTech University
- Student Data Breach - Database Compromise
- Cryptomining Malware - Research Network Infection

## IOC Types Generated

Each case includes realistic but safe IOCs:
- **IP Addresses** (malicious external IPs and internal compromised IPs)
- **Domain Names** (C2 servers, phishing domains)
- **File Hashes** (MD5, SHA1, SHA256)
- **Email Addresses** (attacker emails, compromised accounts)
- **URLs** (phishing pages, malware download links)
- **File Paths** (malware locations, log files)

## Prerequisites

1. **IRIS Instance Running**: Ensure your IRIS instance is accessible at `https://localhost:443`
2. **API Key**: You need an IRIS API key with appropriate permissions
3. **Python 3**: The script requires Python 3 with the `requests` library

## Getting Your API Key

1. Log into your IRIS web interface
2. Navigate to **User Settings** (click your username in top right)
3. Go to the **API Keys** section
4. Generate a new API key or copy an existing one

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install requests urllib3
   ```

2. **Configure the Script**:
   Edit the `create-demo-data.py` file and update these variables:
   ```python
   IRIS_BASE_URL = "https://localhost:443"  # Your IRIS URL
   IRIS_API_KEY = "your_actual_api_key"     # Your API key
   ```

## Running the Script

1. **Execute the script**:
   ```bash
   python create-demo-data.py
   ```

2. **Monitor the progress**: The script will provide detailed output showing:
   - Connection status to IRIS
   - Customer creation progress
   - Case creation for each customer
   - IOC creation for each case

3. **Review the summary**: At the end, you'll see a complete summary of what was created

## Expected Output

The script will create:
- ✅ 5 customers (companies)
- ✅ 10 cases (2 per customer)
- ✅ 70+ IOCs across all cases

## Sample Output
```
🚀 Starting IRIS Demo Data Creation
============================================================
✅ Successfully connected to IRIS API

🏢 Processing company: TechCorp Industries
Creating customer: TechCorp Industries
✅ Created customer: TechCorp Industries (ID: 6)
  Creating case: Advanced Persistent Threat - Cloud Infrastructure Compromise
  ✅ Created case: Advanced Persistent Threat - Cloud Infrastructure Compromise (ID: 15)
    📊 Adding IOCs to case...
    ✅ Created IOC: 185.220.102.8
    ✅ Created IOC: 192.168.1.150
    ...

============================================================
📋 DEMO DATA CREATION SUMMARY
============================================================
✅ Customers created: 5
✅ Cases created: 10
✅ IOCs created: 74
```

## Accessing Your Demo Data

After successful execution:

1. **Log into IRIS**: Navigate to your IRIS web interface
2. **Dashboard**: You'll see the new cases on the dashboard
3. **Case Management**: Go to Manage → Cases to see all created cases
4. **Customer Management**: Go to Manage → Customers to see all companies
5. **Case Details**: Click on any case to explore its IOCs and details

## Customization Options

You can customize the script by modifying:

### Companies
Edit the `DEMO_COMPANIES` list to change company details:
```python
{
    "name": "Your Company Name",
    "description": "Company description",
    "sla": "SLA details"
}
```

### Case Scenarios
Modify the `CASE_SCENARIOS` dictionary to add/change incident types:
```python
"Your Company": [
    {
        "name": "Incident Name",
        "description": "Detailed incident description",
        "classification": "Incident Type",
        "severity": "Critical/High/Medium/Low",
        "case_type": "incident_category"
    }
]
```

### IOC Templates
Update `IOC_TEMPLATES` to include your own IOCs (ensure they're safe/fictional):
```python
"domains": {
    "c2_servers": ["your-safe-test-domain.example.com"]
}
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify IRIS is running and accessible
   - Check the IRIS_BASE_URL is correct
   - Ensure SSL certificates are properly configured

2. **Authentication Failed**
   - Verify your API key is correct and active
   - Check that your user has appropriate permissions
   - Ensure the API key hasn't expired

3. **Customer Creation Failed**
   - Check if customers with the same names already exist
   - Verify your user has customer creation permissions
   - Review IRIS logs for detailed error messages

4. **Case Creation Failed**
   - Ensure the customer was created successfully
   - Check case classification and severity values exist in IRIS
   - Verify case creation permissions

5. **IOC Creation Failed**
   - Check if IOC types exist in your IRIS instance
   - Verify IOC creation permissions
   - Ensure TLP levels are configured properly

### IOC Type IDs

If you encounter IOC type errors, you may need to adjust the IOC type IDs in the `get_ioc_type_id()` function. Check your IRIS instance for the correct type IDs:

1. Go to Manage → IOC Types in IRIS
2. Note the ID numbers for each type
3. Update the function accordingly

## Data Cleanup

To remove the demo data:

1. **Manual Cleanup**: Use IRIS web interface to delete cases and customers
2. **Database Cleanup**: If you have database access, you can remove the data directly
3. **Fresh Install**: Restore from a backup taken before running the script

## Security Notes

- All IOCs in this script are **fictional and safe** for demo purposes
- Do not use real malicious indicators in demo environments
- Ensure the demo environment is properly isolated
- Review all generated data before using in production training

## Support

For issues with:
- **IRIS Software**: Check [IRIS Documentation](https://docs.dfir-iris.org)
- **This Script**: Review the troubleshooting section above
- **API Documentation**: Visit the IRIS API reference

## License

This demo data creation script follows the same LGPL v3 license as IRIS.