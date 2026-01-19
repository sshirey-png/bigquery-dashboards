# Supervisor Dashboard

A live, interactive web dashboard for supervisors to monitor their team's performance, observations, time off balances, and intent to return status. Built with Flask backend and modern JavaScript frontend, powered by BigQuery.

## Features

- **Live BigQuery Integration**: Real-time data from your BigQuery `supervisor_dashboard_data` view
- **Supervisor Selection**: Choose from a dropdown of all supervisors
- **Team Overview**: View all staff members with key metrics at a glance
- **Color-Coded Alerts**:
  - 🔴 Red: Action needed (missing observations, low PTO, intent not to return)
  - 🟡 Yellow: Warnings (pending responses, approaching deadlines)
  - 🟢 Green: All requirements met
- **Detailed Staff Profiles**: Click any staff member for complete information
- **Search & Filters**: Find staff by name or filter by alert status
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-Time Refresh**: Update data on demand

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up BigQuery Authentication

**Option A: Application Default Credentials (Recommended)**
```bash
gcloud auth application-default login
```

**Option B: Service Account JSON**
1. Download your service account JSON file from Google Cloud Console
2. Set the environment variable:
   ```bash
   # Windows
   set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\credentials.json

   # Mac/Linux
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
   ```

### 3. Start the Flask Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 4. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

1. Select your supervisor name from the dropdown
2. Click "View Dashboard"
3. Explore your team's data

## BigQuery Data Requirements

The application expects a BigQuery view named `supervisor_dashboard_data` in the following location:
- **Project**: `talent-demo-482004`
- **Dataset**: `talent_grow_observations`
- **View**: `supervisor_dashboard_data`

### Required Fields

The view should contain these columns:

**Identification:**
- `Supervisor_Name` - Name of the supervisor
- `Staff_Name` - Name of the staff member
- `Email_Address` or `Email` - Staff email
- `Job_Title` - Staff job title

**Personal Info:**
- `Hire_Date` - Date staff was hired
- `Birthday` - Staff birthday

**Time Off:**
- `PTO_Hours` - PTO balance
- `Vacation_Hours` - Vacation balance
- `Personal_Hours` - Personal time balance
- `Sick_Hours` - Sick time balance

**Observations:**
- `Total_Observations` - Total number of observations
- `Last_Observation_Type` - Type of last observation
- `Last_Observation_Date` - Date of last observation
- `SR1_Status` or `SR1_Complete` - SR1 completion status
- `SR2_Status` or `SR2_Complete` - SR2 completion status
- `PMAP1_Status` or `PMAP1_Complete` - PMAP1 completion status

**Performance:**
- `IAP_Count` - Number of IAPs
- `Writeup_Count` - Number of write-ups
- `Intent_To_Return_Status` - Whether staff intends to return
- `Intent_To_Return_Response_Date` - Date of response
- `NPS_Score` - Net Promoter Score

### Example Query to Create View

```sql
CREATE OR REPLACE VIEW `talent-demo-482004.talent_grow_observations.supervisor_dashboard_data` AS
SELECT
    supervisor_name AS Supervisor_Name,
    staff_name AS Staff_Name,
    email AS Email_Address,
    job_title AS Job_Title,
    hire_date AS Hire_Date,
    birthday AS Birthday,
    pto_hours AS PTO_Hours,
    vacation_hours AS Vacation_Hours,
    personal_hours AS Personal_Hours,
    sick_hours AS Sick_Hours,
    total_observations AS Total_Observations,
    last_observation_type AS Last_Observation_Type,
    last_observation_date AS Last_Observation_Date,
    sr1_complete AS SR1_Complete,
    sr2_complete AS SR2_Complete,
    pmap1_complete AS PMAP1_Complete,
    iap_count AS IAP_Count,
    writeup_count AS Writeup_Count,
    intent_to_return AS Intent_To_Return_Status,
    intent_response_date AS Intent_To_Return_Response_Date,
    nps_score AS NPS_Score
FROM your_source_table;
```

## Dashboard Sections

### List View
Displays all staff members in a sortable table with:
- Name (clickable for details)
- Job Title
- Years of Service
- Time Off Balance
- Total Observations
- SR1/SR2/PMAP1 Status (✓ or ✗)
- Intent to Return (Yes/No/Pending)
- NPS Score
- Alert Status (color-coded badge)

### Detail View
Click any staff member to see complete profile:
- **Personal Information**: Full details, hire date, years of service
- **Time Off Balances**: All time off types with hours
- **Observations & Performance**: Complete observation history and status
- **Intent to Return & Satisfaction**: Intent status and NPS score
- **Alerts & Action Items**: All alerts with color-coding and recommendations

### Search & Filters
- **Search**: Type staff name to filter list
- **All Staff**: Show everyone
- **With Alerts**: Show only staff with red or yellow alerts
- **Action Needed**: Show only staff with red alerts

## Alert Logic

### Red Alerts (Action Needed)
- Missing required observations (SR1, SR2, or PMAP1 incomplete)
- Intent to Return: "No"
- Low time off balance (< 20 hours)

### Yellow Alerts (Warning)
- Intent to Return: Pending or no response
- Medium time off balance (20-40 hours)
- Disciplinary actions on record (IAPs or write-ups)

### Green (Good Standing)
- All observations complete
- Intent to Return: "Yes"
- Adequate time off balance (≥ 40 hours)

## API Endpoints

The Flask backend provides two API endpoints:

### GET /api/supervisors
Returns list of all unique supervisor names.

**Example:**
```bash
curl http://localhost:5000/api/supervisors
```

**Response:**
```json
["John Smith", "Jane Doe", "Bob Johnson"]
```

### GET /api/staff/<supervisor_name>
Returns all staff data for the specified supervisor.

**Example:**
```bash
curl http://localhost:5000/api/staff/John%20Smith
```

**Response:**
```json
[
  {
    "Staff_Name": "Alice Brown",
    "Job_Title": "Teacher",
    "Hire_Date": "2020-08-15",
    "SR1_Complete": true,
    "SR2_Complete": false,
    ...
  }
]
```

### GET /api/health
Health check endpoint to verify server and BigQuery connection status.

**Example:**
```bash
curl http://localhost:5000/api/health
```

## Troubleshooting

### "BigQuery client not initialized"
- Ensure you've run `gcloud auth application-default login`
- Or set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Verify your credentials have BigQuery read access

### "Failed to fetch supervisors"
- Check that the BigQuery view exists and is accessible
- Verify the view has a `Supervisor_Name` column
- Ensure your credentials have permissions to query the dataset

### "Failed to load staff data"
- Verify the supervisor name exists in the data
- Check that all required columns are present in the view
- Review the Flask server logs for detailed error messages

### Port 5000 already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# Mac/Linux
lsof -i :5000
kill -9 <process_id>
```

Or change the port in `app.py`:
```python
app.run(debug=True, port=8080, host='0.0.0.0')
```

## Development

### Running in Debug Mode
The Flask app runs in debug mode by default, providing:
- Auto-reload on code changes
- Detailed error messages
- Request logging

### Customizing Alert Thresholds
Edit the JavaScript alert logic in `index.html` (around line 675):

```javascript
// Check PTO balance
const ptoHours = parseFloat(staff.PTO_Hours) || parseFloat(staff.Vacation_Hours) || 0;
if (ptoHours < 20) {  // Change this threshold
    alerts.push({ level: 'red', message: `Low time off balance (${ptoHours.toFixed(1)} hours)` });
} else if (ptoHours < 40) {  // Change this threshold
    alerts.push({ level: 'yellow', message: `Medium time off balance (${ptoHours.toFixed(1)} hours)` });
}
```

### Adjusting BigQuery Configuration
Edit the constants in `app.py`:

```python
PROJECT_ID = 'your-project-id'
DATASET_ID = 'your-dataset-id'
TABLE_ID = 'your-view-name'
```

## Production Deployment

For production deployment, consider:

1. **Use Gunicorn** instead of Flask development server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Deploy to Google Cloud Run**:
   - Containerize the application
   - Deploy with BigQuery permissions
   - Use service account authentication

3. **Add Authentication**:
   - Implement OAuth or SSO
   - Restrict supervisor access to their own teams
   - Add role-based access control

4. **Enable HTTPS**:
   - Use a reverse proxy (nginx, Apache)
   - Configure SSL certificates
   - Update CORS settings

## File Structure

```
bigquery_dashboards/
├── app.py                      # Flask backend with BigQuery integration
├── index.html                  # Supervisor dashboard (frontend)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── deploy_to_gcs.py           # GCS deployment script (legacy)
├── serve_dashboard.py         # Simple HTTP server (legacy)
└── update_dashboard*.py       # Old SR2/PMAP2 scripts (legacy)
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Flask server logs for error messages
3. Verify BigQuery view schema matches requirements
4. Check browser console for frontend JavaScript errors

## License

Internal use only - Talent Grow Observations Dashboard
