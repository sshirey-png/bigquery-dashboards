# FirstLine Schools Dashboard System

A unified web platform for FirstLine Schools staff to access HR, academic, and operational dashboards. Built with Flask and BigQuery, deployed on Google Cloud Run.

**Live URL:** https://supervisor-dashboard-965913991496.us-central1.run.app

## Dashboards

| Dashboard | URL Path | Purpose |
|-----------|----------|---------|
| Supervisor | `/` | View direct reports — observations, certifications, time off, intent to return |
| HR/Talent | `/hr-dashboard` | Network-wide staff data with filters |
| Schools | `/schools-dashboard` | Academic team view — teacher data, assessment fidelity |
| Kickboard | `/kickboard-dashboard` | Student behavior tracking and interactions |
| Suspensions | `/suspensions-dashboard` | ISS/OSS rates by school |
| Salary Projection | `/salary-dashboard` | Salary modeling with scenario builder |
| Position Control | `/position-control-dashboard` | Manage position requests and approvals |
| Onboarding | `/onboarding-dashboard` | Track new hire onboarding progress |
| Staff List | `/staff-list-dashboard` | Filterable, exportable staff directory |
| Org Chart | `/orgchart` | Visual organization hierarchy |

All dashboards require Google OAuth with a `@firstlineschools.org` account. A role-aware nav dropdown shows only the dashboards each user can access.

## Quick Start

```bash
# Clone
git clone https://github.com/sshirey-png/bigquery-dashboards.git
cd bigquery-dashboards

# Install
pip install -r requirements.txt

# Authenticate with GCP
gcloud auth application-default login

# Run locally (bypasses OAuth)
set FLASK_ENV=development    # Windows
export FLASK_ENV=development # Mac/Linux
python app.py
```

Open http://localhost:5000

## Project Structure

```
bigquery-dashboards/
├── app.py                          # Flask app factory + blueprint registration
├── config.py                       # Role-based title lists, table names, constants
├── extensions.py                   # BigQuery client and OAuth setup
├── auth.py                         # Permission logic for all dashboards
├── blueprints/                     # Route handlers by feature
│   ├── auth_routes.py              #   Login, logout, /api/auth/status
│   ├── supervisor.py               #   Supervisor dashboard API
│   ├── hr.py                       #   HR dashboard API
│   ├── schools.py                  #   Schools dashboard API (incl. assessment fidelity)
│   ├── kickboard.py                #   Kickboard dashboard API
│   ├── suspensions.py              #   Suspensions dashboard API
│   ├── salary.py                   #   Salary projection API
│   ├── position_control.py         #   Position Control Form admin API
│   ├── onboarding.py               #   Onboarding Form admin API
│   ├── staff_list.py               #   Staff List API
│   ├── orgchart.py                 #   Org chart API
│   └── health.py                   #   Health check
├── index.html                      # Supervisor Dashboard frontend
├── hr-dashboard.html               # HR Dashboard frontend
├── schools-dashboard.html          # Schools Dashboard frontend
├── kickboard-dashboard.html        # Kickboard Dashboard frontend
├── suspensions-dashboard.html      # Suspensions Dashboard frontend
├── salary-dashboard.html           # Salary Dashboard frontend
├── position-control-dashboard.html # Position Control admin frontend
├── onboarding-dashboard.html       # Onboarding admin frontend
├── staff-list-dashboard.html       # Staff List frontend
├── orgchart.html                   # Org Chart frontend
├── Dockerfile                      # Container build
├── requirements.txt                # Python dependencies
└── docs/                           # Documentation
    ├── USER_GUIDE.md               #   End-user guide for all dashboards
    ├── TECHNICAL_GUIDE.md          #   Developer/maintenance guide
    └── ACCESS_PERMISSIONS.md       #   Master access control reference
```

## Deployment

```bash
gcloud run deploy supervisor-dashboard \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

See [DEPLOY.md](DEPLOY.md) for full details.

## Documentation

| Guide | Audience | Contents |
|-------|----------|----------|
| [User Guide](docs/USER_GUIDE.md) | End users | How to use each dashboard, navigation, features |
| [Technical Guide](docs/TECHNICAL_GUIDE.md) | Developers | Code structure, local setup, common changes, deployment |
| [Access Permissions](docs/ACCESS_PERMISSIONS.md) | System admin | Role-based access by job title, named admin tiers, auth flags across all projects |

## Common Maintenance

| Task | File | What to Change |
|------|------|----------------|
| Add/remove admin title | `config.py` | `CPO_TITLE`, `HR_TEAM_TITLES`, or `SCHOOLS_TEAM_TITLES` |
| Add school leader title (role-based) | `config.py` | `KICKBOARD_SCHOOL_LEADER_TITLES` list |
| Add Schools Dashboard role (role-based) | `config.py` | `SCHOOLS_DASHBOARD_ROLES` dict |
| Change PCF permissions | `config.py` | `POSITION_CONTROL_TITLE_ROLES` dict |
| Change onboarding permissions | `config.py` | `ONBOARDING_TITLE_ROLES` dict |
| Add email alias | `config.py` | `EMAIL_ALIASES` dict |

> **Note:** Admin access is now determined by job title from BigQuery — when someone changes roles, access transfers automatically. `CURRENT_SY_START` is auto-calculated from the date — no update needed. Salary access is purely job-title based ("Chief" or "Ex. Dir") — no list to maintain. Team inbox emails (talent@, hr@) are the only email-based exceptions.

After any change: commit, push, and redeploy.

## GCP Project

- **Project:** `talent-demo-482004`
- **Region:** `us-central1`
- **Service:** `supervisor-dashboard`

## Related Repos

| Repo | Purpose |
|------|---------|
| [position-control-form](https://github.com/sshirey-png/position-control-form) | Standalone PCF submission form (public) |
| [onboarding-form](https://github.com/sshirey-png/onboarding-form) | Standalone onboarding submission form (public) |
| [referral-program](https://github.com/sshirey-png/referral-program) | Staff referral program |
| [sabbatical-program](https://github.com/sshirey-png/sabbatical-program) | Sabbatical program |
| [salary-scale](https://github.com/sshirey-png/salary-scale) | Salary calculator (static) |
| [impact-bonus](https://github.com/sshirey-png/impact-bonus) | Impact bonus guide (static) |

## License

Internal use only — FirstLine Schools
