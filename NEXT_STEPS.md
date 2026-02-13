# Next Steps — Supervisor Dashboard & Dashboards Project

**Last Updated:** February 12, 2026

---

## Immediate — Pick Up Here

### 1. Commit & deploy Supervisor dashboard dropdown
- `index.html` has the dropdown nav ready, **uncommitted**
- Same pattern as HR dashboard — role-aware "Dashboards" dropdown
- Shows: HR View (if access), Staff List, Schools, Kickboard, Suspensions, Salary (all if access), Org Chart
- Deploy with `~/deploy.sh supervisor`

### 2. Roll out dropdown to remaining 6 dashboards
Apply the same dropdown pattern to:
- [ ] Schools (`schools-dashboard.html`)
- [ ] Kickboard (`kickboard-dashboard.html`)
- [ ] Suspensions (`suspensions-dashboard.html`)
- [ ] Salary (`salary-dashboard.html`)
- [ ] Staff List (`staff-list-dashboard.html`)
- [ ] Org Chart (`orgchart.html`)

Each dashboard omits its own self-link. Decide per-dashboard which links are relevant (e.g. HR dashboard excludes Kickboard/Suspensions).

### 3. Integrate Position Control as a blueprint
Position Control is currently a separate Cloud Run service (`position-control-daem7b6ydq-uc.a.run.app`). Plan is to bring it into this app so it shares auth, nav, and deployment.
- Pull code into `blueprints/position_control.py`
- Add `get_position_control_access` to `auth.py` — access: C-Team + HR + School Leaders (by job title)
- Add `position_control_access` flag to auth status endpoint
- Add to dropdown nav on all dashboards

---

## Completed Recently

### February 12, 2026
- Added `salary_dashboard_access` flag to `blueprints/auth_routes.py`
- HR dashboard: replaced individual nav links with role-aware dropdown (deployed)
- Supervisor dashboard: dropdown nav added (uncommitted)
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
