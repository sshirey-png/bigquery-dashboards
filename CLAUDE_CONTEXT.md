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

## Last Session: February 12, 2026 — Dashboard Nav Consistency

### What was done
- Added `salary_dashboard_access` flag to `blueprints/auth_routes.py` (imports `get_salary_access` from auth)
- HR dashboard (`hr-dashboard.html`): replaced individual nav links (Supervisor View, Schools View, Kickboard) with role-aware "Dashboards" dropdown
- HR dropdown shows: Supervisor, Staff List, Schools (if access), Salary (if access), Org Chart
- Supervisor dashboard (`index.html`): added same dropdown pattern — **changes are ready but NOT committed**
- Supervisor dropdown shows: HR View (if access), Staff List, Schools/Kickboard/Suspensions/Salary (if access), Org Chart
- Fixed Staff List route: `/staff-list-dashboard` (not `/staff-list`)
- HR dashboard deployed to Cloud Run (commit `bf62704`)

### Uncommitted work
- `index.html` has the Supervisor dashboard dropdown nav ready to commit & deploy

### Next steps
1. Commit & deploy Supervisor dashboard dropdown (`index.html`)
2. Phase 2: Roll out dropdown to remaining 6 dashboards (Schools, Kickboard, Suspensions, Salary, Staff List, Org Chart) — each omits its own self-link
3. Phase 3: Integrate Position Control into this app as a blueprint (currently separate Cloud Run service)
   - Access should be: C-Team + HR + School Leaders (by job title)
   - Add `get_position_control_access` to `auth.py`
   - Add `position_control_access` flag to auth status endpoint
   - Add to dropdown nav on all dashboards

## Previous Session: January 19, 2026 (Evening)
- Added certification badges for teachers and leaders (not network staff)
- Orange "C" badge appears next to certified staff names
- Click badge to see popup with all certifications (active and expired)
- New BigQuery dataset: `talent_certification` with native tables:
  - `staff_list_LASID_native` - Staff with LASID identifiers
  - `state_certification_list_native` - State certification records
- New views: `certification_summary_native`, `staff_with_certifications_native`, `staff_certifications_detail_native`
- New API endpoints: `/api/cert-status` (all certified teachers/leaders), `/api/cert-detail/<email>` (individual details)
- Certification data refreshed monthly (manual upload)

## Previous Session: January 19, 2026 (Morning)
- Removed NPS column from main staff table
- Added clickable Intent to Return popup with detailed survey responses
- New API endpoint: `/api/itr-detail/<email>` queries `intent_to_return_native` table
- ITR popup shows: intent status, NPS score, decision factors, culture feedback, retention suggestions
- Important: Use native tables (not views) to avoid Google Sheets permission issues

## Previous Session: January 17, 2026
- Converted 5 external tables to native BigQuery tables
- Set up hourly scheduled refreshes in BigQuery
- Fixed Employment Status to include "Leave of Absence" employees
- Redesigned UI to match FirstLine Schools branding (logo, colors, fonts)
- Added Google OAuth authentication with domain restriction
