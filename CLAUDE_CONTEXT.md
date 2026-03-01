# Project Context for Claude

## User
- Name: Scott Shirey
- Email: sshirey@firstlineschools.org

## Project: Supervisor Dashboard
- Location: C:\Users\sshirey\bigquery_dashboards
- GCP Project: talent-demo-482004
- BigQuery Dataset: talent_grow_observations
- BigQuery View: supervisor_dashboard_data

## Deployment
- Cloud Run Service: supervisor-dashboard
- Region: us-central1
- Live URL: https://supervisor-dashboard-965913991496.us-central1.run.app
- Service Account: 965913991496-compute@developer.gserviceaccount.com

## Tech Stack
- Frontend: Vanilla JS + Tailwind CSS (via CDN) + Open Sans font
- Backend: Flask + gunicorn
- Data: Native BigQuery tables (converted from external Google Sheets)
- Hosting: Google Cloud Run
- Branding: FirstLine Schools (orange #e47727, navy #002f60)

## Data Architecture (Updated Jan 17, 2026)

### Native Tables (hourly refresh via scheduled queries)
| Table | Dataset | Description |
|-------|---------|-------------|
| observations_raw_native | talent_grow_observations | Talent Grow observation data |
| staff_master_list_native | talent_grow_observations | Staff master list |
| goals_native | talent_grow_observations | Staff goals |
| accrual_balance_native | payroll_validation | PTO/vacation/sick balances |
| intent_to_return_native | intent_to_return | Intent to return survey responses |

### Key Views
- `supervisor_dashboard_data` - Main view for dashboard (includes Active + Leave of Absence staff)
- `observations_summary` - Aggregated observations by staff
- `staff_with_observations_by_type` - Observation counts by type (SR1, PMAP1, etc.)
- `accrual_with_staff_info` - Accrual balances with staff details
- `intent_to_return_with_staff` - ITR responses with staff details

### Scheduled Queries (hourly refresh)
Set up in BigQuery Console to refresh native tables from source Google Sheets.

## Pending Tasks
1. **Custom Domain** - DNS request sent to IT for:
   - Domain: supervisordashboard.firstlineschools.org
   - DNS Record: CNAME → ghs.googlehosted.com

## Deployment Notes
Due to Windows timestamp issues, deploy using temp directory:
```python
# Copy files to temp dir with fresh timestamps, then deploy from there
```

## Last Session: February 27, 2026 — Salary Double Login Fix

### What was done
- **Salary double login fix**: Replaced all 8 plain `fetch()` calls in `salary-dashboard.html` with `apiFetch()` wrapper — session cookies were missing (`credentials: 'include'`), forcing users to log in twice

### Next steps
- See NEXT_STEPS.md for current backlog

## Previous Sessions

### February 26, 2026
- **Deploy script hardening**: `~/deploy.sh` now parses env vars via JSON/Python with `.strip()` and pipes through `tr -d '\r'` — prevents `\r` from corrupting OAuth credentials on Windows
- Added Talent Operations Manager and Recruitment Manager to HR team titles
- Fixed column name bug in `_check_employee_access`
- Auto-retry OAuth on CSRF error + auth check timeout
- Build version auto-reload and `apiFetch` wrapper across all dashboards

### February 19, 2026
- **Assessment Fidelity on Schools Dashboard**: Completion % and Mastery % columns sourced from actual class rosters
- School-level summary table with color-coded metrics, teacher detail modal, student drill-down
- Bottom 25th percentile highlighting (amber "B25" badge)
- SPED co-teacher virtual roster support (inclusion sections)
- New API endpoints: `/api/schools/assessment-fidelity`, `/api/schools/assessment-students`

### February 14, 2026
- Dropdown nav rolled out to all remaining dashboards (Schools, Kickboard, Suspensions, Salary, Staff List)
- Salary dashboard: added Standard column, fixed custom scenario bugs

### February 13, 2026
- Dropdown nav Phase 1: Supervisor and HR dashboards got role-aware "Dashboards" dropdown
- Non-supervisor HR users auto-redirect from `/` to `/hr-dashboard`
- Certification CSV upload replaced Google Sheets-backed table
- OAuth `invalid_client` fix (hidden `\r` in Cloud Run env vars)

### January 19, 2026
- Certification badges for teachers/leaders (orange "C" badge with popup)
- Intent to Return popup with survey details, removed NPS column from main table

### January 17, 2026
- Native BigQuery tables with hourly refresh
- FirstLine Schools branding (logo, colors, fonts)
- Google OAuth authentication with domain restriction
