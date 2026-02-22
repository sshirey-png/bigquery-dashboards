# Access Permissions & Authorization Guide — All Projects

**Last Updated:** 2026-02-21
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
8. [Position Control Form (position-control-form)](#8-position-control-form-position-control-form)
9. [Onboarding Form (onboarding-form)](#9-onboarding-form-onboarding-form)
10. [Cloud Run Services Not in Repos](#10-cloud-run-services-not-in-repos)
11. [Master Admin List Across All Projects](#11-master-admin-list-across-all-projects)

---

## 1. Supervisor Dashboard (bigquery-dashboards)

**Repo:** github.com/sshirey-png/bigquery-dashboards
**Cloud Run:** bigquery-dashboards (serves all dashboards), supervisor-dashboard (supervisor only)
**URLs:** https://bigquery-dashboards-daem7b6ydq-uc.a.run.app, https://supervisor-dashboard-daem7b6ydq-uc.a.run.app
**Auth:** Google OAuth, `@firstlineschools.org` domain required

### Permission Tiers

Access is controlled by three role tiers defined in `config.py`. Each tier grants different dashboard access.

#### Tier 1a: CPO — full access to everything
| Email | Name |
|-------|------|
| sshirey@firstlineschools.org | Scott Shirey - Chief People Officer |

#### Tier 1b: HR Team — Supervisor, HR, Staff List dashboards
| Email | Name |
|-------|------|
| brichardson@firstlineschools.org | Brittney Richardson - Chief of Human Resources |
| spence@firstlineschools.org | Sabrina Pence |
| mtoussaint@firstlineschools.org | M. Toussaint |
| csmith@firstlineschools.org | C. Smith |
| aleibfritz@firstlineschools.org | A. Leibfritz |

#### Schools Team — Schools, Kickboard, Suspensions dashboards
| Email | Name |
|-------|------|
| sdomango@firstlineschools.org | Sivi Domango - Chief Experience Officer |
| dgoodwin@firstlineschools.org | Dawn Goodwin - K-8 Content Lead |
| krodriguez@firstlineschools.org | Kristin Rodriguez - Dir of Culture |
| csteele@firstlineschools.org | Charlotte Steele - Dir of ESYNOLA |

**Source:** `config.py` lines 25-46

### Email Aliases
| External Email | Maps To |
|----------------|---------|
| zach@esynola.org | zodonnell@firstlineschools.org |

### Dashboard Access Matrix

| Dashboard | Who Can Access | Auth Flag | Data Scope |
|-----------|---------------|-----------|------------|
| **Supervisor** | All @firstlineschools.org users | always | Own team + downline (hierarchical) |
| **HR/Talent** | CPO + HR Team | `hr_dashboard_access` | All staff org-wide |
| **Schools** | CPO + Schools Team + specific job titles | `schools_dashboard_access` | Filtered by role scope (see below) |
| **Kickboard** | CPO + Schools Team + School Leaders + Supervisors + ACL | `kickboard_dashboard_access` | Hybrid: schools + staff IDs |
| **Suspensions** | CPO + Schools Team + School Leaders | `suspensions_dashboard_access` | School-level only |
| **Salary Projection** | C-Team only (Chief/Ex. Dir in title) | `salary_dashboard_access` | All staff, filterable by school |
| **Position Control** | PCF role holders (see below) | `pcf_dashboard_access` | All position requests |
| **Onboarding** | Onboarding role holders (see below) | `onboarding_dashboard_access` | All onboarding submissions |
| **Staff List** | All @firstlineschools.org users | always | All staff (read-only directory) |
| **Org Chart** | All @firstlineschools.org users | always | Full org structure |

### What Each Role Sees in the Nav Dropdown

Every dashboard has a "Dashboards" dropdown menu that shows only the dashboards the user can access. Each page omits its own self-link.

| Role | Dashboards Visible |
|------|--------------------|
| CPO (sshirey) | All: Supervisor, HR, Staff List, Schools, Kickboard, Suspensions, Salary, Position Control, Onboarding, Org Chart |
| HR Team (brichardson, spence, etc.) | Supervisor, HR, Staff List, Position Control, Onboarding, Org Chart |
| Schools Team (sdomango, dgoodwin, etc.) | Supervisor, Staff List, Schools, Kickboard, Suspensions, Org Chart (+Salary if C-Team title) |
| School Leaders (principals, APs, etc.) | Supervisor, Staff List, Kickboard, Suspensions, Org Chart (+Schools if job title qualifies) |
| Supervisors | Supervisor, Staff List, Org Chart (+Kickboard if they have downline staff) |
| All Staff | Supervisor, Staff List, Org Chart |

### Schools Dashboard Roles
| Job Title | Scope | What They See |
|-----------|-------|---------------|
| CPO + Schools Team | all_except_cteam | All staff except Chief/CEO titles |
| Chief Academic Officer | all_except_cteam | All staff except Chief/CEO titles |
| ExDir of Teach and Learn | teachers_only | Only Job_Function = 'Teacher' |
| K-8 Content Lead | teachers_only | Only Job_Function = 'Teacher' |

### Kickboard Access Tiers (checked in order)
| Tier | Who | Access Granted |
|------|-----|---------------|
| 1. Admin | CPO + Schools Team | All schools, all data |
| 2. School Leader | principal, assistant principal, dean, head of school, director of culture | Their school's data |
| 3. Supervisor | Any supervisor in org hierarchy | Their direct/indirect reports (by employee ID) |
| 4. ACL Fallback | Explicit grants in Google Sheet | Specific school(s) via `fls-data-warehouse.acl.fls_acl_named` |

### Suspensions Access
| Tier | Who | Access |
|------|-----|--------|
| 1. Admin | CPO + Schools Team | All schools |
| 2. School Leader | Same titles as Kickboard | Their school only |

### Salary Projection Access
- C-Team only (job title contains 'Chief' or 'Ex. Dir')
- **No admin bypass** — strictly job-title based
- Custom scenario builder with Current/Standard/Custom salary comparison
- CSV export includes YOS, Current YOS Bonus, and Custom YOS Bonus columns

### Position Control Dashboard Access

Separate role system defined in `POSITION_CONTROL_ROLES` in `config.py`:

| Email | Role | Can Approve | Edit Final Status | Create Position | Edit Dates | Delete |
|-------|------|------------|-------------------|----------------|------------|--------|
| sshirey@ | super_admin | CEO, Finance, Talent, HR | Yes | Yes | Yes | Yes |
| spence@ | ceo | CEO | Yes | No | No | No |
| rcain@ | finance | Finance | No | No | No | No |
| lhunter@ | finance | Finance | No | No | No | No |
| brichardson@ | hr | HR, Talent | Yes | Yes | Yes | No |
| mtoussaint@ | hr | HR | No | No | Yes | No |
| aleibfritz@ | viewer | — | No | No | No | No |
| csmith@ | viewer | — | No | No | No | No |

**Source:** `config.py` `POSITION_CONTROL_ROLES`

### Onboarding Dashboard Access

Separate role system defined in `ONBOARDING_ROLES` in `config.py`:

| Email | Role | Can Edit | Can Delete | Can Archive |
|-------|------|---------|-----------|------------|
| sshirey@ | super_admin | Yes | Yes | Yes |
| brichardson@ | hr | Yes | No | Yes |
| mtoussaint@ | hr | Yes | No | Yes |
| csmith@ | viewer | No | No | No |
| aleibfritz@ | viewer | No | No | No |

**Source:** `config.py` `ONBOARDING_ROLES`

### BigQuery Tables

#### talent-demo-482004 (primary)
| Dataset | Table | Used By |
|---------|-------|---------|
| talent_grow_observations | supervisor_dashboard_data | Supervisor, HR, Schools |
| talent_grow_observations | staff_master_list_with_function | Auth lookups, Schools, Kickboard, Suspensions, Salary |
| talent_grow_observations | ldg_action_steps | Action steps (LDG sync) |
| talent_grow_observations | ldg_meetings | Meetings (LDG sync) |
| Salary | salary_schedule | Salary dashboard |

#### talent-demo-482004 (Position Control & Onboarding)
| Dataset | Table | Used By |
|---------|-------|---------|
| position_control_form | requests | Position Control dashboard |
| talent_grow_observations | position_control | Position Control (create position target) |
| onboarding_form | submissions | Onboarding dashboard |

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

## 8. Position Control Form (position-control-form)

**Repo:** github.com/sshirey-png/position-control-form *(needs to be created)*
**Cloud Run:** position-control-form
**URL:** https://position-control-form-965913991496.us-central1.run.app
**Auth:** Google OAuth for admin panel; public form submission
**Backend:** Flask + BigQuery

### Dual Deployment
This app serves two purposes:
1. **Public form** — School leaders submit position requests (no admin login required for submission)
2. **Admin panel** — HR/Finance/CEO review and approve requests (OAuth required)

The **admin panel** is now also available within the main dashboard at `/position-control-dashboard`, sharing the same BigQuery tables. The standalone app continues to serve as the submission form.

### BigQuery Tables
| Dataset | Table | Purpose |
|---------|-------|---------|
| position_control_form | requests | All PCF requests |
| talent_grow_observations | position_control | Position control master table |

---

## 9. Onboarding Form (onboarding-form)

**Repo:** github.com/sshirey-png/onboarding-form *(needs to be created)*
**Cloud Run:** onboarding-form
**URL:** https://onboarding-form-965913991496.us-central1.run.app
**Auth:** Google OAuth for admin panel; public form for new hires
**Backend:** Flask + BigQuery

### Dual Deployment
This app serves two purposes:
1. **Public form** — New hires fill out onboarding information
2. **Admin panel** — HR tracks and manages onboarding progress (OAuth required)

The **admin panel** is now also available within the main dashboard at `/onboarding-dashboard`, sharing the same BigQuery tables. The standalone app continues to serve as the submission form.

### BigQuery Tables
| Dataset | Table | Purpose |
|---------|-------|---------|
| onboarding_form | submissions | All onboarding submissions |

---

## 10. Cloud Run Services Not in Repos

These Cloud Run services exist but their source repos were not found on GitHub:

| Service | URL | Notes |
|---------|-----|-------|
| itr-dashboard | https://itr-dashboard-daem7b6ydq-uc.a.run.app | Intent-to-return dashboard (no repo found) |

---

## 11. Master Admin List Across All Projects

| Email | Dashboard Role | PCF Role | Onboarding Role | Referral Program | Sabbatical Program |
|-------|---------------|----------|----------------|-----------------|-------------------|
| sshirey@firstlineschools.org | CPO (Tier 1a) | super_admin | super_admin | Admin | Network Admin |
| brichardson@firstlineschools.org | HR Team (Tier 1b) | hr | hr | Admin | Network Admin |
| spence@firstlineschools.org | HR Team (Tier 1b) | ceo | — | — | Network Admin |
| mtoussaint@firstlineschools.org | HR Team (Tier 1b) | hr | hr | — | — |
| csmith@firstlineschools.org | HR Team (Tier 1b) | viewer | viewer | — | — |
| aleibfritz@firstlineschools.org | HR Team (Tier 1b) | viewer | viewer | — | — |
| rcain@firstlineschools.org | — | finance | — | — | — |
| lhunter@firstlineschools.org | — | finance | — | — | — |
| sdomango@firstlineschools.org | Schools Team | — | — | — | Network Admin |
| dgoodwin@firstlineschools.org | Schools Team | — | — | — | — |
| krodriguez@firstlineschools.org | Schools Team | — | — | — | — |
| csteele@firstlineschools.org | Schools Team | — | — | — | — |
| talent@firstlineschools.org | — | — | — | Admin | Network Admin |
| hr@firstlineschools.org | — | — | — | Admin | Network Admin |
| awatts@firstlineschools.org | — | — | — | Admin | Network Admin |
| jlombas@firstlineschools.org | — | — | — | Admin | Network Admin |
| kfeil@firstlineschools.org | — | — | — | — | Network Admin |
| dcavato@firstlineschools.org | — | — | — | — | Network Admin |

**Note:** Salary Calculator, Impact Bonus Guide, Org Chart, and Grow Observations have NO authentication — they are public static sites.

---

## Dashboard Navigation — Role-Aware Dropdown

**Status:** Complete (deployed Feb 13, 2026)

All 8 dashboards now have a "Dashboards" dropdown menu in the header. The dropdown is role-aware: it only shows links to dashboards the logged-in user has permission to access. Each page omits its own self-link.

### Auth Flags (returned by `/api/auth/status`)
| Flag | Grants Nav Link To | Based On |
|------|-------------------|----------|
| `hr_dashboard_access` | HR View | `is_hr_admin()` — CPO + HR Team |
| `schools_dashboard_access` | Schools | `get_schools_dashboard_role()` — CPO + Schools Team + job title |
| `kickboard_dashboard_access` | Kickboard | `get_kickboard_access()` — CPO + Schools Team + School Leaders + Supervisors + ACL |
| `suspensions_dashboard_access` | Suspensions | `get_suspensions_access()` — CPO + Schools Team + School Leaders |
| `salary_dashboard_access` | Salary | `get_salary_access()` — C-Team job titles only |
| `pcf_dashboard_access` | Position Control | `get_pcf_access()` — `POSITION_CONTROL_ROLES` dict |
| `pcf_permissions` | (object) | `get_pcf_permissions()` — role, can_approve, can_edit_final, etc. |
| `onboarding_dashboard_access` | Onboarding | `get_onboarding_access()` — `ONBOARDING_ROLES` dict |
| `onboarding_permissions` | (object) | `get_onboarding_permissions()` — role, can_edit, can_delete, etc. |

Supervisor, Staff List, Org Chart, and Data Portal links are always visible.

---

## Known Issues

1. **ACL table inaccessible** — `fls-data-warehouse.acl.fls_acl_named` is backed by a Google Sheet that requires Drive permissions not currently granted. Non-blocking (Kickboard ACL fallback only).
2. **Hardcoded admin lists** — All projects use hardcoded email lists. Changes require code deployment.
3. **Inconsistent admin lists** — Different projects have different admin sets (e.g., dcavato is in sabbatical but not supervisor-dashboard; dgoodwin is in supervisor-dashboard but not sabbatical).
4. **Public referral form** — Staff Referral Program accepts submissions without authentication. Anyone with the URL can submit.
5. **Salary/bonus data public** — Salary Calculator and Impact Bonus contain all compensation data in client-side JavaScript, visible to anyone with the URL.
6. **Missing repos** — itr-dashboard Cloud Run service has no corresponding GitHub repo. Position Control Form and Onboarding Form repos need to be created on GitHub (source exists locally).
