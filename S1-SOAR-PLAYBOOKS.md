# 🧩 IRIS SOAR Playbooks — SentinelOne Integrations

Each playbook follows the same operational pattern:

1. Initiated manually from the **IRIS case screen**.  
2. Executes the SentinelOne action via API.  
3. Waits/polls until completion.  
4. Saves the resulting data (JSON, CSV, or summary text) into a **case-specific folder**,  
   and embeds a reference + summary into the **Notes section** of that case.

---

## **Playbook: Fetch Installed Applications**
**Purpose:** Retrieve a list of installed applications from a SentinelOne agent for forensic or compliance purposes.  

### Steps:
1. **Trigger:** Analyst clicks **“Fetch Installed Apps”** within the SOAR job screen.  
2. **Action:**  
   - Call `GET /agents/{agent_id}/installed-applications`  
   - Include parameters for pagination if necessary.  
3. **Process:**  
   - Store response (JSON) under `/cases/{case_id}/artifacts/sentinelone/fetch_installed_apps.json`  
   - Parse key details: Application Name, Version, Publisher, Install Date.  
4. **Output:**  
   - Write a Markdown summary to Notes:  
     ```markdown
     **SOAR Action:** Fetch Installed Apps  
     **Endpoint:** {hostname}  
     **Timestamp:** {datetime}  
     **Results:** Retrieved {count} applications.  
     **Installed Apps:**  
     **(List all apps below)**
     1. Chrome 129.0  
     2. Adobe Acrobat 24.3  
     3. Zoom 6.0  
     4. SentinelOne Agent 24.2  
     5. WinRAR 6.2  
     etc etc
     _
     ```

---

## **Playbook: Fetch Endpoint Logs**
**Purpose:** Collect endpoint logs directly from SentinelOne for evidence gathering or investigation.  

### Steps:
1. **Trigger:** Analyst runs **“Fetch Logs”** SOAR job.  
2. **Action:**  
   - Call `POST /agents/actions/fetch-logs`  
   - Body includes agent ID and optional date range.  
3. **Process:**  
   - Poll until job status changes to “completed.”  
   - Download resulting log archive.  
   - Save as `/cases/{case_id}/artifacts/sentinelone/logs_{hostname}_{datetime}.zip`  
4. **Output:**  
   - Create a case note:  
     ```markdown
     **SOAR Action:** Fetch Endpoint Logs  
     **Endpoint:** {hostname}  
     **Timestamp:** {datetime}  
     **Status:** ✅ Completed  
     **Log File:** `/cases/{case_id}/artifacts/sentinelone/logs_{hostname}_{datetime}.zip`  
     _Logs collected for forensic review._
     ```

---

## **Playbook: Start Full Disk Scan**
**Purpose:** Force a full disk scan on an endpoint to verify post-incident hygiene.  

### Steps:
1. **Trigger:** Analyst selects **“Run Full Disk Scan”** from the SOAR job list.  
2. **Action:**  
   - Call `POST /agents/actions/initiate-scan`  
   - Body: `{ "data": { "filter": { "ids": ["{agent_id}"] }, "scan_type": "full" } }`  
3. **Process:**  
   - Poll `/scans/{scan_id}` until status = “completed.”  
   - Retrieve scan summary.  
   - Store summary JSON at `/cases/{case_id}/artifacts/sentinelone/scan_report_{hostname}.json`  
4. **Output:**  
   - Add to Notes:  
     ```markdown
     **SOAR Action:** Full Disk Scan  
     **Endpoint:** {hostname}  
     **Timestamp:** {datetime}  
     **Result:** Completed — {threat_count} threats detected.  
     _Full scan report saved in `/cases/{case_id}/artifacts/sentinelone/scan_report_{hostname}.json`_
     ```

---

## **Playbook: Quarantine from Network**
**Purpose:** Immediately isolate an endpoint to prevent lateral movement or exfiltration.  

### Steps:
1. **Trigger:** Analyst selects **“Quarantine Host (Network Isolation)”**.  
2. **Action:**  
   - Call `POST /agents/actions/network-quarantine`  
   - Body: `{ "filter": { "ids": ["{agent_id}"] } }`  
3. **Process:**  
   - Poll agent status until `networkStatus = "quarantined"`.  
   - Log event to IRIS activity feed.  
4. **Output:**  
   - Create note entry:  
     ```markdown
     **SOAR Action:** Network Quarantine  
     **Endpoint:** {hostname}  
     **Timestamp:** {datetime}  
     **Status:** ✅ Host successfully isolated from network.  
     _This action prevents all inbound/outbound connections except SentinelOne management._
     ```

---

### 🗂 File Storage Convention
Each playbook writes data to the case’s SentinelOne sub-folder:
/cases/{case_id}/artifacts/sentinelone/
├── fetch_installed_apps.json
├── logs_{hostname}{datetime}.zip
├── scan_report{hostname}.json
└── quarantine_action_{hostname}.json

pgsql
Copy code

---

### 🧠 Implementation Notes
- All jobs use the same wrapper function `sentinelone_api_call(action, agent_id)`  
- The playbook results are injected into the IRIS case via the **Notes API** and logged as “Artifacts.”  
- Use tags like `#SOAR #SentinelOne #Automation` for searchability.