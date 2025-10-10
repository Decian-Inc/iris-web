# AbuseIPDB Module Test Cases

This document provides a comprehensive set of test IOCs for validating the AbuseIPDB enrichment module functionality.

## Test Cases Overview

The following test cases cover different scenarios:
1. **Known Malicious IPs** - IPs with high abuse confidence scores
2. **Suspicious IPs** - IPs with moderate abuse reports
3. **Clean IPs** - Well-known legitimate IPs (should show low/no abuse)
4. **Edge Cases** - Invalid or special-use IPs

## Test IOC Set 1: Known Malicious IPs

### IOC 1: High-Confidence Malicious IP
- **IP Address**: `185.220.102.8`
- **Expected Result**: High abuse confidence, multiple categories
- **Description**: Known Tor exit node with historical abuse reports
- **Test Purpose**: Verify high-confidence threat detection

### IOC 2: Botnet C2 Server
- **IP Address**: `103.85.24.155`
- **Expected Result**: Botnet/C2 categorization with abuse reports
- **Description**: Previously identified botnet command & control server
- **Test Purpose**: Test C2 server categorization

### IOC 3: Scanning/Probing Activity
- **IP Address**: `159.203.45.95`
- **Expected Result**: Port scanning/probing abuse reports
- **Description**: IP with history of scanning activities
- **Test Purpose**: Verify scanning activity detection

### IOC 4: Brute Force Attacks
- **IP Address**: `91.134.144.86`
- **Expected Result**: SSH/FTP brute force attack reports
- **Description**: IP with brute force attack history
- **Test Purpose**: Test brute force categorization

## Test IOC Set 2: Moderate Risk IPs

### IOC 5: Suspicious Activity
- **IP Address**: `45.146.164.110`
- **Expected Result**: Moderate confidence score with some reports
- **Description**: IP with occasional abuse reports
- **Test Purpose**: Test moderate threat level handling

### IOC 6: Potential Compromise
- **IP Address**: `185.142.236.34`
- **Expected Result**: Mixed abuse categories
- **Description**: IP with varied abuse report types
- **Test Purpose**: Verify multiple category handling

## Test IOC Set 3: Clean/Legitimate IPs

### IOC 7: Google Public DNS
- **IP Address**: `8.8.8.8`
- **Expected Result**: Clean IP with 0% abuse confidence
- **Description**: Google's public DNS server
- **Test Purpose**: Verify clean IP handling

### IOC 8: Cloudflare DNS
- **IP Address**: `1.1.1.1`
- **Expected Result**: Clean IP with minimal/no abuse reports
- **Description**: Cloudflare's public DNS server
- **Test Purpose**: Test legitimate service IP

### IOC 9: Microsoft Public Service
- **IP Address**: `13.107.42.14`
- **Expected Result**: Clean IP from legitimate service
- **Description**: Microsoft service IP
- **Test Purpose**: Verify enterprise IP handling

## Test IOC Set 4: Edge Cases

### IOC 10: Private Network IP
- **IP Address**: `192.168.1.1`
- **Expected Result**: Should not be enriched (private IP)
- **Description**: Common private network gateway
- **Test Purpose**: Test private IP filtering

### IOC 11: Localhost
- **IP Address**: `127.0.0.1`
- **Expected Result**: Should not be enriched (localhost)
- **Description**: Loopback address
- **Test Purpose**: Test localhost handling

### IOC 12: Invalid IP Format
- **IP Address**: `999.999.999.999`
- **Expected Result**: Error handling or rejection
- **Description**: Invalid IP address format
- **Test Purpose**: Test input validation

## Expected Module Behavior

### Automatic Enrichment
1. Module should trigger on IOC creation/update
2. Only valid, public IP addresses should be processed
3. Enrichment data should populate IOC fields
4. Automatic notes should be created in "AbuseIPDB Reports" folder

### Note Creation
Each successful enrichment should create a note containing:
- **Report Header**: IP address and report date
- **Summary Table**: Key metrics (confidence, reports, etc.)
- **Threat Categories**: Detailed breakdown of abuse types
- **Recent Reports**: Latest abuse reports if available
- **Risk Assessment**: Color-coded risk level
- **External Links**: Direct links to AbuseIPDB profile

### Expected Enrichment Fields
- `abuse_confidence`: Confidence percentage (0-100)
- `is_whitelisted`: Boolean for whitelisted status
- `country_code`: Two-letter country code
- `usage_type`: ISP, hosting, etc.
- `total_reports`: Number of abuse reports
- `last_reported_at`: Date of most recent report

## Test Execution Steps

### Step 1: Enable Module
1. Navigate to IRIS Modules section
2. Find "IrisAbuseIPDB" module
3. Enable the module
4. Configure with API key: `c06ed761ffb2c108ccc470f117883ca467e287ae0d883b60e465bc55a30d1a7cadbd23475c8b027e`

### Step 2: Create Test Case
1. Create new case: "AbuseIPDB Module Testing"
2. Add case description: "Testing AbuseIPDB enrichment functionality"

### Step 3: Add IOCs
For each test IOC:
1. Navigate to IOCs section
2. Click "Add IOC"
3. Set IOC type to "IP"
4. Enter IP address from test cases
5. Set description with test case purpose
6. Save IOC

### Step 4: Verify Enrichment
After adding each IOC:
1. Check IOC details for enrichment data
2. Verify Notes section for "AbuseIPDB Reports" folder
3. Review generated report content
4. Confirm data accuracy against expected results

### Step 5: Test Manual Trigger
1. Select existing IOC
2. Use manual trigger option for AbuseIPDB
3. Verify re-enrichment works correctly
4. Check for updated report in Notes

## Success Criteria

### Functional Requirements
- ✅ Module appears in dashboard
- ✅ Module can be enabled/configured
- ✅ Automatic enrichment on IOC creation
- ✅ Automatic enrichment on IOC update
- ✅ Manual trigger functionality works
- ✅ Notes automatically created
- ✅ Private IPs filtered out
- ✅ Error handling for invalid IPs

### Data Quality Requirements
- ✅ Accurate abuse confidence scores
- ✅ Correct threat categorization
- ✅ Proper country/ISP information
- ✅ Recent report data when available
- ✅ Formatted markdown reports
- ✅ Working external links

### Performance Requirements
- ✅ Enrichment completes within 30 seconds
- ✅ No errors in application logs
- ✅ Multiple IOCs can be processed
- ✅ System remains responsive

## Troubleshooting

### Common Issues
1. **Module Not Enriching**: Check API key configuration
2. **No Notes Created**: Verify Notes permissions and folder creation
3. **Timeout Errors**: Check API rate limits and network connectivity
4. **Missing Data**: Verify IP is in AbuseIPDB database

### Debug Commands
```bash
# Check module status
docker-compose logs app | grep -i abuseipdb

# Verify API connectivity
docker-compose exec app python -c "import requests; print(requests.get('https://api.abuseipdb.com/api/v2/check', headers={'Key': 'your_api_key'}).status_code)"

# Check Notes creation
docker-compose logs app | grep -i note
```

## Additional Test Scenarios

### Bulk Testing
Create multiple IOCs simultaneously to test:
- Concurrent processing
- Rate limit handling
- System performance under load

### Integration Testing
Test module alongside other enrichment modules:
- VirusTotal integration
- MISP integration
- Multiple enrichments on same IOC

### Error Scenarios
Test error handling with:
- Invalid API key
- Network connectivity issues
- API rate limit exceeded
- Malformed IP addresses

This comprehensive test suite ensures the AbuseIPDB module functions correctly across all expected use cases and edge conditions.