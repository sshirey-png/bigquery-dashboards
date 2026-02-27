# Next Steps — Supervisor Dashboard & Dashboards Project

**Last Updated:** February 27, 2026

---

## Immediate — Pick Up Here

### 1. Integrate Position Control as a blueprint
Position Control is currently a separate Cloud Run service (`position-control-daem7b6ydq-uc.a.run.app`). Plan is to bring it into this app so it shares auth, nav, and deployment.
- Pull code into `blueprints/position_control.py`
- Add `get_position_control_access` to `auth.py` — access: C-Team + HR + School Leaders (by job title)
- Add `position_control_access` flag to auth status endpoint
- Add to dropdown nav on all dashboards

---

## Completed Recently

### February 26, 2026
- **Deploy script hardening**: `~/deploy.sh` now parses env vars via JSON/Python with `.strip()` and pipes through `tr -d '\r'` — prevents `\r` carriage returns from corrupting OAuth credentials on Windows deploys
- Added Talent Operations Manager and Recruitment Manager to HR team titles
- Fixed column name bug in `_check_employee_access`
- Auto-retry OAuth on CSRF error + auth check timeout
- Build version auto-reload and `apiFetch` wrapper across all dashboards

### February 19, 2026
- **Assessment Fidelity on Schools Dashboard**: Added Completion % and Mastery % columns to the staff table, sourced from actual class rosters (`class_schedules` + `results_raw`) for per-teacher accuracy
- School-level summary table showing current and previous formal assessment metrics per school, color-coded by threshold
- Teacher assessment detail modal with current/previous comparison and delta indicators
- Student drill-down: click "View Students" to see per-student test status, scores, and missing students highlighted in red
- **Bottom 25th percentile highlighting**: Students from `sps.24_25_bottom_25` shown with amber styling and "B25" badge (with ELA/Math specificity)
- **SPED co-teacher support**: SPED teachers in grades 3-8 automatically matched to inclusion sections (highest SPED student concentration) — each grade's test shown as separate data point (no cross-grade averaging)
- New API endpoints: `/api/schools/assessment-fidelity`, `/api/schools/assessment-students`
- New BigQuery tables integrated: `performance_matters.results_by_test`, `performance_matters.results_raw`, `class_schedules.class_schedules`, `student_rosters.student_roster`, `sps.24_25_bottom_25`

### February 14, 2026
- Dropdown nav rolled out to all remaining dashboards: Schools, Kickboard, Suspensions, Salary, Staff List
- Salary dashboard: added Standard column, fixed custom scenario bugs, prevented caching

### February 13, 2026
- Supervisor dashboard: committed and deployed dropdown nav (`index.html`)
- Moved Data Portal button into Dashboards dropdown on both Supervisor and HR dashboards
- Widened search bar (now `flex-1`) with filter buttons (All Staff / With Alerts / Action Needed) on the right
- Added redirect: non-supervisor HR users hitting `/` now auto-redirect to `/hr-dashboard`
- Certification: replaced Google Sheets-backed `state_certification_list` with CSV upload to `state_certification_list_native` — deleted old external table, scheduled query can be disabled
- Fixed OAuth `invalid_client` error caused by hidden `\r` characters in Cloud Run env vars — re-set env vars cleanly on both services
- Deployed both `bigquery-dashboards` and `supervisor-dashboard` services

### February 12, 2026
- Added `salary_dashboard_access` flag to `blueprints/auth_routes.py`
- HR dashboard: replaced individual nav links with role-aware dropdown (deployed)
- Fixed Staff List route (`/staff-list-dashboard`)
- Updated `docs/ACCESS_PERMISSIONS.md` with nav dropdown documentation

### January 19, 2026
- Certification badges for teachers/leaders
- Intent to Return popup with survey details
- Removed NPS column from main table

### January 17, 2026
- Native BigQuery tables with hourly refresh
- FirstLine Schools branding
- Google OAuth authentication

---

## Backlog

- **Custom Domain** — supervisordashboard.firstlineschools.org (waiting on IT for DNS)
- **Export to CSV/Excel** — download team data
- **Email Notifications** — alert supervisors when staff need action
- **Historical Trends** — observation counts over time

---

## Deployment

- Dashboard app: `~/deploy.sh dashboards`
- Supervisor app: `~/deploy.sh supervisor`
- Live URLs:
  - https://bigquery-dashboards-daem7b6ydq-uc.a.run.app
  - https://supervisor-dashboard-965913991496.us-central1.run.app
