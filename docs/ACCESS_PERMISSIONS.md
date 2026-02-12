# Access Permissions & Authorization Guide — All Projects

**Last Updated:** 2026-02-12
**GCP Project:** talent-demo-482004

---

## Table of Contents

1. [Supervisor Dashboard (bigquery-dashboards)](#1-supervisor-dashboard-bigquery-dashboards)
2. [Salary Calculator (salary-scale)](#2-salary-calculator-salary-scale)
3. [Impact Bonus Guide (impact-bonus)](#3-impact-bonus-guide-impact-bonus)
4. [Staff Referral Program (referral-program)](#4-staff-referral-program-referral-program)
5. [Sabbatical Program (sabbatical-program)](#5-sabbatical-program-sabbatical-program)
6. [Org Chart (firstline-orgchart)](#6-org-chart-firstline-orgchart)
7. [Grow Observations (grow-observations)](#7-grow-observations-grow-observations)
8. [Cloud Run Services Not in Repos](#8-cloud-run-services-not-in-repos)
9. [Master Admin List Across All Projects](#9-master-admin-list-across-all-projects)

---

## 1. Supervisor Dashboard (bigquery-dashboards)

**Repo:** github.com/sshirey-png/bigquery-dashboards
**Cloud Run:** supervisor-dashboard
**URLs:** https://supervisor-dashboard-965913991496.us-central1.run.app (also: https://supervisor-dashboard-daem7b6ydq-uc.a.run.app)
**Auth:** Google OAuth, `@firstlineschools.org` domain required

### Admin Users
| Email | Name/Role |
|-------|-----------|
| sshirey@firstlineschools.org | Scott Shirey - Chief People Officer |
| brichardson@firstlineschools.org | Brittney Richardson - Chief of Human Resources |
| spence@firstlineschools.org | Sabrina Pence |
| mtoussaint@firstlineschools.org | M. Toussaint |
| csmith@firstlineschools.org | C. Smith |
| aleibfritz@firstlineschools.org | A. Leibfritz |
| sdomango@firstlineschools.org | Sivi Domango - Chief Experience Officer |
| dgoodwin@firstlineschools.org | Dawn Goodwin - K-8 Content Lead |
| rjohnson@firstlineschools.org | Rameisha Johnson - Manager Family Engagement |
| krodriguez@firstlineschools.org | Kristin Rodriguez - Dir of Culture |
| csteele@firstlineschools.org | Charlotte Steele - Dir of ESYNOLA |

**Source:** `bigquery-dashboards/config.py` lines 25-38

### Email Aliases
| External Email | Maps To |
|----------------|---------|
| zach@esynola.org | zodonnell@firstlineschools.org |

### Dashboard Access Matrix

| Dashboard | Who Can Access | Data Scope |
|-----------|---------------|------------|
| **Supervisor** | All @firstlineschools.org users | Own team + downline (hierarchical) |
| **HR/Talent** | Admin users only (11 above) | All staff org-wide |
| **Schools** | Admins + specific job titles | Filtered by role scope (see below) |
| **Kickboard** | Admins, School Leaders, Supervisors, ACL grants | Hybrid: schools + staff IDs |
| **Suspensions** | Admins + School Leaders | School-level only |
| **Salary Projection** | C-Team only (Chief/Ex. Dir in title) | All staff, filterable by school |
| **Staff List** | All @firstlineschools.org users | All staff (read-only directory) |
| **Org Chart** | All @firstlineschools.org users | Full org structure |

### Schools Dashboard Roles
| Job Title | Scope | What They See |
|-----------|-------|---------------|
| (Admin users) | all_except_cteam | All staff except Chief/CEO titles |
| Chief Academic Officer | all_except_cteam | All staff except Chief/CEO titles |
| ExDir of Teach and Learn | teachers_only | Only Job_Function = 'Teacher' |
| K-8 Content Lead | teachers_only | Only Job_Function = 'Teacher' |

### Kickboard Access Tiers (checked in order)
| Tier | Who | Access Granted |
|------|-----|---------------|
| 1. Admin | ADMIN_EMAILS | All schools, all data |
| 2. School Leader | principal, assistant principal, dean, head of school, director of culture | Their school's data |
| 3. Supervisor | Any supervisor in org hierarchy | Their direct/indirect reports (by employee ID) |
| 4. ACL Fallback | Explicit grants in Google Sheet | Specific school(s) via `fls-data-warehouse.acl.fls_acl_named` |

### Suspensions Access
| Tier | Who | Access |
|------|-----|--------|
| 1. Admin | ADMIN_EMAILS | All schools |
| 2. School Leader | Same titles as Kickboard | Their school only |

### Salary Projection Access
- C-Team only (job title contains 'Chief' or 'Ex. Dir')
- **No admin bypass** — strictly job-title based

### BigQuery Tables

#### talent-demo-482004 (primary)
| Dataset | Table | Used By |
|---------|-------|---------|
| talent_grow_observations | supervisor_dashboard_data | Supervisor, HR, Schools |
| talent_grow_observations | ldg_action_steps | Action steps (LDG sync) |
| talent_grow_observations | ldg_meetings | Meetings (LDG sync) |
| Salary | salary_schedule | Salary dashboard |

#### fls-data-warehouse (shared project)
| Dataset | Table | Used By | Status |
|---------|-------|---------|--------|
| kickboard | interactions | Kickboard dashboard | OK |
| kickboard | interactions_acl | Kickboard dashboard | OK |
| acl | fls_acl_named | Kickboard ACL fallback | INACCESSIBLE (Drive permissions) |
| suspensions | iss_rates_25_26 | Suspensions dashboard | OK |
| suspensions | oss_rates_25_26 | Suspensions dashboard | OK |

---

## 2. Salary Calculator (salary-scale)

**Repo:** github.com/sshirey-png/salary-scale
**Cloud Run:** salary-calculator
**URL:** https://salary-calculator-daem7b6ydq-uc.a.run.app
**Auth:** NONE — Static HTML site, no authentication
**Backend:** None (Python http.server serves a single `index.html`)

### Access
- **Public** — anyone with the URL can access
- No login, no admin panel, no BigQuery
- All salary data is embedded in the HTML/JavaScript as a static JSON object
- Contains salary scales for all roles (Paraprofessional through School Director, steps 0-30)

### Security Notes
- Salary data for all positions is fully visible in page source
- No sensitive employee data (only generic scale, not individual salaries)

---

## 3. Impact Bonus Guide (impact-bonus)

**Repo:** github.com/sshirey-png/impact-bonus
**Cloud Run:** impact-bonus
**URL:** https://impact-bonus-daem7b6ydq-uc.a.run.app
**Auth:** NONE — Static HTML site, no authentication
**Backend:** None (Python http.server serves a single `index.html`)

### Access
- **Public** — anyone with the URL can access
- No login, no admin panel, no BigQuery
- Informational guide about the impact bonus program with a role-based bonus calculator
- All bonus amounts embedded in static JavaScript

---

## 4. Staff Referral Program (referral-program)

**Repo:** github.com/sshirey-png/referral-program
**Cloud Run:** staff-referral-program
**URL:** https://staff-referral-program-daem7b6ydq-uc.a.run.app
**Auth:** Google OAuth for admin panel; public referral submission form
**Backend:** Flask + BigQuery

### Admin Users
| Email | Role |
|-------|------|
| sshirey@firstlineschools.org | CPO (also CC'd on all referrals) |
| brichardson@firstlineschools.org | Chief of HR |
| talent@firstlineschools.org | Talent team inbox |
| hr@firstlineschools.org | HR inbox |
| awatts@firstlineschools.org | A. Watts |
| jlombas@firstlineschools.org | J. Lombas |

**Source:** `referral-program/app.py` lines 49-56

### Access Model
| Action | Who | Auth Required |
|--------|-----|--------------|
| Submit a referral | Anyone (public form) | No |
| Look up own referrals by email | Anyone | No (email-based lookup) |
| View all referrals (admin panel) | ADMIN_USERS only | Google OAuth |
| Update referral status | ADMIN_USERS only | Google OAuth |
| Delete/archive referrals | ADMIN_USERS only | Google OAuth |
| Trigger weekly rollup email | Cloud Scheduler or shared secret | Bearer token |

### Email Recipients
| Event | Sent To | CC |
|-------|---------|-----|
| New referral confirmation | Referrer | — |
| New referral alert | talent@firstlineschools.org | sshirey@firstlineschools.org |
| Status updates | Referrer | — |
| Payout eligible | hr@, talent@, payroll@firstlineschools.org | — |
| Weekly rollup | talent@firstlineschools.org | sshirey@firstlineschools.org |

### BigQuery Tables
| Dataset | Table | Purpose |
|---------|-------|---------|
| staff_referral | referrals | All referral records |

---

## 5. Sabbatical Program (sabbatical-program)

**Repo:** github.com/sshirey-png/sabbatical-program
**Cloud Run:** sabbatical-program
**URL:** https://sabbatical-program-daem7b6ydq-uc.a.run.app
**Auth:** Google OAuth, `@firstlineschools.org` domain required
**Backend:** Flask + BigQuery

### Network Admins (full access to ALL applications)
| Email | Role |
|-------|------|
| sshirey@firstlineschools.org | Chief People Officer |
| brichardson@firstlineschools.org | Chief of Human Resources |
| spence@firstlineschools.org | CEO |
| sdomango@firstlineschools.org | Chief Experience Officer |
| dcavato@firstlineschools.org | C-Team |
| talent@firstlineschools.org | Talent team inbox |
| hr@firstlineschools.org | HR inbox |
| awatts@firstlineschools.org | A. Watts |
| jlombas@firstlineschools.org | J. Lombas |
| tcole@firstlineschools.org | T. Cole |
| kfeil@firstlineschools.org | ExDir of Teaching and Learning |

**Source:** `sabbatical-program/app.py` lines 53-68

### School-Level Admins (see their school's applications only)
Job titles that grant school-level access:
- School Director
- Principal
- Assistant Principal
- Head of School

### Access Model
| Access Level | Who | What They See |
|-------------|-----|---------------|
| Network Admin | 11 people listed above | All applications across all schools |
| School Admin | School leaders by job title | Their school's applications only |
| Employee | Any @firstlineschools.org user | Their own application only |
| Supervisor | Direct supervisor chain | Their direct reports' applications |

### Admin Actions by Level
| Action | Network Admin | School Admin |
|--------|--------------|-------------|
| View applications | All | Own school only |
| Update status | Yes | No |
| Delete application | Yes | No |
| Approve date changes | Yes | No |
| View stats | All schools | Own school only |
| Resend confirmation | Yes | No |

### Email Recipients
| Event | Sent To | CC |
|-------|---------|-----|
| Application submitted | Employee, Supervisor chain | talent@, sshirey@ |
| Status update | Employee | sshirey@, talent@, supervisor chain |
| Date change approved | Employee | sshirey@, talent@, supervisor chain |
| Payout processing | HR, Benefits, Payroll | sshirey@, supervisor chain |

### Email Aliases
| External Email | Maps To |
|----------------|---------|
| zach@esynola.org | zodonnell@firstlineschools.org |

### BigQuery Tables
| Dataset | Table | Purpose |
|---------|-------|---------|
| sabbatical | applications | All sabbatical applications |

---

## 6. Org Chart (firstline-orgchart)

**Repo:** github.com/sshirey-png/firstline-orgchart
**Auth:** NONE — Static HTML file, no authentication
**Backend:** None

### Access
- **Public** — single static `index.html` with embedded org chart
- No login, no BigQuery, no backend
- References the FirstLine Schools logo from firstlineschools.org

---

## 7. Grow Observations (grow-observations)

**Repo:** github.com/sshirey-png/grow-observations
**Auth:** NONE — Static SQL files and HTML
**Backend:** None (SQL files only, no deployed app)

### Contents
- `create_clean_view.sql` — BigQuery view creation
- `final_views.sql` — BigQuery view definitions
- `summary_queries.sql` — Summary queries
- `dashboard.html` — Static dashboard HTML

### Access
- Not a deployed application — SQL reference files for BigQuery views
- No authentication, no access control

---

## 8. Cloud Run Services Not in Repos

These Cloud Run services exist but their source repos were not found on GitHub:

| Service | URL | Notes |
|---------|-----|-------|
| bigquery-dashboards | https://bigquery-dashboards-daem7b6ydq-uc.a.run.app | May be an older version of supervisor-dashboard |
| itr-dashboard | https://itr-dashboard-daem7b6ydq-uc.a.run.app | Intent-to-return dashboard (no repo found) |
| position-control | https://position-control-daem7b6ydq-uc.a.run.app | Position control dashboard (no repo found) |

---

## 9. Master Admin List Across All Projects

| Email | Supervisor Dashboard | Referral Program | Sabbatical Program |
|-------|---------------------|-----------------|-------------------|
| sshirey@firstlineschools.org | Admin | Admin | Network Admin |
| brichardson@firstlineschools.org | Admin | Admin | Network Admin |
| spence@firstlineschools.org | Admin | — | Network Admin |
| mtoussaint@firstlineschools.org | Admin | — | — |
| csmith@firstlineschools.org | Admin | — | — |
| aleibfritz@firstlineschools.org | Admin | — | — |
| sdomango@firstlineschools.org | Admin | — | Network Admin |
| dgoodwin@firstlineschools.org | Admin | — | — |
| rjohnson@firstlineschools.org | Admin | — | — |
| krodriguez@firstlineschools.org | Admin | — | — |
| csteele@firstlineschools.org | Admin | — | — |
| talent@firstlineschools.org | — | Admin | Network Admin |
| hr@firstlineschools.org | — | Admin | Network Admin |
| awatts@firstlineschools.org | — | Admin | Network Admin |
| jlombas@firstlineschools.org | — | Admin | Network Admin |
| tcole@firstlineschools.org | — | — | Network Admin |
| kfeil@firstlineschools.org | — | — | Network Admin |
| dcavato@firstlineschools.org | — | — | Network Admin |

**Note:** Salary Calculator, Impact Bonus Guide, Org Chart, and Grow Observations have NO authentication — they are public static sites.

---

## Known Issues

1. **ACL table inaccessible** — `fls-data-warehouse.acl.fls_acl_named` is backed by a Google Sheet that requires Drive permissions not currently granted. Non-blocking (Kickboard ACL fallback only).
2. **Hardcoded admin lists** — All projects use hardcoded email lists. Changes require code deployment.
3. **School year start date hardcoded** — `CURRENT_SY_START = '2025-08-04'` in bigquery-dashboards config.py must be manually updated each year.
4. **Inconsistent admin lists** — Different projects have different admin sets (e.g., dcavato is in sabbatical but not supervisor-dashboard; dgoodwin is in supervisor-dashboard but not sabbatical).
5. **Public referral form** — Staff Referral Program accepts submissions without authentication. Anyone with the URL can submit.
6. **Salary/bonus data public** — Salary Calculator and Impact Bonus contain all compensation data in client-side JavaScript, visible to anyone with the URL.
7. **Missing repos** — itr-dashboard and position-control Cloud Run services have no corresponding GitHub repos.
