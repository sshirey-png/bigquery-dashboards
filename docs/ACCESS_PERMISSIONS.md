# Access Permissions & Authorization Guide — All Projects

**Last Updated:** 2026-02-21
**GCP Project:** talent-demo-482004

---

## Access Design Principles

FirstLine Schools systems use two types of access control:

### Role-Based (Dynamic) Access
Access is determined by the employee's **job title** or **position in the org hierarchy**, looked up from the staff database (BigQuery) at login. When someone changes roles, access automatically transfers to whoever holds that title next — **no code changes needed**.

| Access Type | Qualifying Titles | Dashboards / Apps Affected |
|-------------|-------------------|---------------------------|
| **C-Team** | Job title contains "Chief" or "Ex. Dir" | Salary Projection |
| **School Leader** | Principal, Assistant Principal, Dean, Head of School, Director of Culture | Kickboard (school data), Suspensions (school data) |
| **Schools Academic Roles** | Chief Academic Officer, ExDir of Teach and Learn, K-8 Content Lead | Schools Dashboard (scoped by role) |
| **Supervisor** | Anyone with direct reports in the org hierarchy | Supervisor Dashboard (own team), Kickboard (downline interactions) |
| **Sabbatical School Admin** | School Director, Principal, Assistant Principal, Head of School | Sabbatical Program (own school's applications) |

### Named (Hardcoded) Access
Access is determined by **email address lists** in application code. Requires a code deployment to add or remove people. Used for specific operational teams where membership is controlled centrally and doesn't map cleanly to a single job title.

| List | Location | Purpose |
|------|----------|---------|
| CPO (Tier 1a) | `config.py` → `CPO_EMAILS` | Full access to all dashboards |
| HR Team (Tier 1b) | `config.py` → `HR_TEAM_EMAILS` | Supervisor, HR, Staff List, Position Control, Onboarding |
| Schools Team | `config.py` → `SCHOOLS_TEAM_EMAILS` | Schools, Kickboard, Suspensions admin |
| Position Control Roles | `config.py` → `POSITION_CONTROL_ROLES` | Position Control approval workflow |
| Onboarding Roles | `config.py` → `ONBOARDING_ROLES` | Onboarding management |
| Referral Admins | `referral-program/app.py` → `ADMIN_USERS` | Referral admin panel |
| Sabbatical Network Admins | `sabbatical-program/app.py` → `SABBATICAL_NETWORK_ADMINS` | All sabbatical applications |

### Open Access (No Restrictions)
Some dashboards require only a `@firstlineschools.org` Google login, with no additional permissions:
- **Supervisor Dashboard** — sees own team only (or all teams for admins)
- **Staff List** — read-only directory of all staff
- **Org Chart** — visual org hierarchy

Some apps are fully public with no login at all:
- **Salary Calculator** — static salary scale reference
- **Impact Bonus Guide** — informational bonus calculator

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
11. [Master Access Reference](#11-master-access-reference)

---

## 1. Supervisor Dashboard (bigquery-dashboards)

**Repo:** github.com/sshirey-png/bigquery-dashboards
**Cloud Run:** supervisor-dashboard (serves all 10 dashboards)
**URL:** https://supervisor-dashboard-965913991496.us-central1.run.app
**Auth:** Google OAuth, `@firstlineschools.org` domain required

### Role-Based (Dynamic) Access

These dashboards determine access from the employee's **job title** or **org position** in BigQuery. No code changes needed when people change roles.

#### Salary Projection — C-Team by Job Title
- Access granted when job title contains **"Chief"** or **"Ex. Dir"**
- **No admin bypass** — even CPO gets access through title match, not the admin list
- Lookup: `auth.py` → `get_salary_access()` queries `staff_master_list_with_function`

#### Kickboard — School Leaders by Job Title
School leaders automatically see their school's full Kickboard data based on their job title and Location field:

| Qualifying Title | Access Granted |
|------------------|---------------|
| Principal | Full data for their school |
| Assistant Principal | Full data for their school |
| Dean | Full data for their school |
| Head of School | Full data for their school |
| Director of Culture | Full data for their school |

**Source:** `config.py` → `KICKBOARD_SCHOOL_LEADER_TITLES`
**Lookup:** `auth.py` → `get_kickboard_access()` checks title against list, maps Location to school code

#### Suspensions — School Leaders by Job Title
Same title list as Kickboard. School leaders see their school's suspension data.

**Source:** Uses the same `KICKBOARD_SCHOOL_LEADER_TITLES` list
**Lookup:** `auth.py` → `get_suspensions_access()`

#### Schools Dashboard — Academic Roles by Job Title

| Qualifying Title | Scope | What They See |
|------------------|-------|---------------|
| Chief Academic Officer | all_except_cteam | All staff except Chief/CEO titles |
| ExDir of Teach and Learn | teachers_only | Only staff with Job_Function = 'Teacher' |
| K-8 Content Lead | teachers_only | Only staff with Job_Function = 'Teacher' |

**Source:** `config.py` → `SCHOOLS_DASHBOARD_ROLES`
**Lookup:** `auth.py` → `get_schools_dashboard_role()` queries job title from BigQuery

#### Supervisor Dashboard — Org Hierarchy
- Any employee with direct reports automatically sees their team's data
- Supervisors also see all supervisors in their downline (recursive CTE traversal)
- **No admin list needed** — access follows the org chart

#### Kickboard — Supervisors with Downline
- Any supervisor with staff in their reporting chain sees Kickboard interactions logged by those staff
- Uses the same recursive CTE to find all employees in the supervisor's downline
- This is in addition to (not instead of) school leader access — both can apply

### Named (Hardcoded) Access — Admin Tiers

These grant admin-level access to specific dashboards. Membership is controlled by email lists in `config.py` and requires a code deployment to change.

#### Tier 1a: CPO — full access to all 10 dashboards
| Email | Name |
|-------|------|
| sshirey@firstlineschools.org | Scott Shirey - Chief People Officer |

#### Tier 1b: HR Team — Supervisor, HR, Staff List, Position Control, Onboarding
| Email | Name |
|-------|------|
| brichardson@firstlineschools.org | Brittney Richardson - Chief of Human Resources |
| spence@firstlineschools.org | Sabrina Pence |
| mtoussaint@firstlineschools.org | M. Toussaint |
| csmith@firstlineschools.org | C. Smith |
| aleibfritz@firstlineschools.org | A. Leibfritz |

#### Schools Team — Schools, Kickboard, Suspensions (admin-level)
| Email | Name |
|-------|------|
| sdomango@firstlineschools.org | Sivi Domango - Chief Experience Officer |
| dgoodwin@firstlineschools.org | Dawn Goodwin - K-8 Content Lead |
| krodriguez@firstlineschools.org | Kristin Rodriguez - Dir of Culture |
| csteele@firstlineschools.org | Charlotte Steele - Dir of ESYNOLA |

**Source:** `config.py` lines 25-46

> **Note:** `ADMIN_EMAILS` is computed as `CPO_EMAILS + HR_TEAM_EMAILS` (line 49). Schools Team is a separate list.

### Email Aliases
| External Email | Maps To |
|----------------|---------|
| zach@esynola.org | zodonnell@firstlineschools.org |

### Dashboard Access Matrix

| Dashboard | Access Method | Who Can Access | Data Scope |
|-----------|--------------|---------------|------------|
| **Supervisor** | Open + Org hierarchy | All staff (own team); CPO + HR Team (all teams) | Own team + downline |
| **HR/Talent** | Named list | CPO + HR Team | All staff org-wide |
| **Schools** | Named list + Job title | CPO + Schools Team + Chief Academic Officer + ExDir of Teach and Learn + K-8 Content Lead | Scoped by role |
| **Kickboard** | Named list + Job title + Org hierarchy + ACL | CPO + Schools Team + School Leaders + Supervisors + ACL | Hybrid: schools + staff IDs |
| **Suspensions** | Named list + Job title | CPO + Schools Team + School Leaders | School-level |
| **Salary** | Job title only | C-Team (Chief/Ex. Dir in title) | All staff |
| **Position Control** | Named list | PCF role holders (8 people) | All requests |
| **Onboarding** | Named list | Onboarding role holders (5 people) | All submissions |
| **Staff List** | Open | All @firstlineschools.org users | All staff (read-only) |
| **Org Chart** | Open | All @firstlineschools.org users | Full org structure |

### What Each Role Sees in the Nav Dropdown

Every dashboard has a "Dashboards" dropdown menu that shows only the dashboards the user can access. Each page omits its own self-link.

| Role | Dashboards Visible |
|------|--------------------|
| CPO | All 10: Supervisor, HR, Staff List, Schools, Kickboard, Suspensions, Salary, Position Control, Onboarding, Org Chart |
| HR Team | Supervisor, HR, Staff List, Position Control, Onboarding, Org Chart |
| Schools Team | Supervisor, Staff List, Schools, Kickboard, Suspensions, Org Chart (+Salary if their title qualifies as C-Team) |
| C-Team (by title) | +Salary (in addition to whatever other access they have) |
| School Leaders (by title) | Supervisor, Staff List, Kickboard, Suspensions, Org Chart (+Schools if their title qualifies) |
| Supervisors (by org chart) | Supervisor, Staff List, Org Chart (+Kickboard if they have downline staff) |
| All Staff | Supervisor, Staff List, Org Chart |

### Kickboard Access Tiers (checked in order)
| Tier | Who | How Determined | Access Granted |
|------|-----|---------------|---------------|
| 1. Admin | CPO + Schools Team | Named email list | All schools, all data |
| 2. School Leader | Principal, AP, Dean, Head of School, Dir of Culture | Job title lookup | Their school's full data |
| 3. Supervisor | Any supervisor in org hierarchy | Recursive CTE on org chart | Their direct/indirect reports' interactions (by employee ID) |
| 4. ACL Fallback | Explicit grants | Google Sheet lookup | Specific school(s) via `fls-data-warehouse.acl.fls_acl_named` |

### Salary Projection Access
- C-Team only — job title must contain **"Chief"** or **"Ex. Dir"** (case-insensitive)
- **No admin bypass** — strictly job-title based, looked up from BigQuery at login
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
| performance_matters | results_by_test | Schools dashboard (assessment fidelity) | OK |
| performance_matters | results_raw | Schools dashboard (student drill-down) | OK |
| class_schedules | class_schedules | Schools dashboard (teacher rosters) | OK |
| student_rosters | student_roster | Schools dashboard (SPED matching) | OK |
| sps | 24_25_bottom_25 | Schools dashboard (B25 flagging) | OK |

---

## 2. Salary Calculator (salary-scale)

**Repo:** github.com/sshirey-png/salary-scale
**Cloud Run:** salary-calculator
**URL:** https://salary-calculator-965913991496.us-central1.run.app
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
**URL:** https://impact-bonus-965913991496.us-central1.run.app
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
**URL:** https://staff-referral-program-965913991496.us-central1.run.app
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
| aleibfritz@firstlineschools.org | A. Leibfritz |

**Source:** `referral-program/app.py` lines 49-57

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
**URL:** https://sabbatical-program-965913991496.us-central1.run.app
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

**Source:** `sabbatical-program/app.py` lines 53-67

### School-Level Admins (see their school's applications only)
Job titles that grant school-level access:
- School Director
- Principal
- Assistant Principal
- Head of School

### Access Model
| Access Level | Who | What They See |
|-------------|-----|---------------|
| Network Admin | 10 people listed above | All applications across all schools |
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

**Repo:** github.com/sshirey-png/position-control-form
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

**Repo:** github.com/sshirey-png/onboarding-form
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

## 10. Cloud Run Services Without Repos

| Service | URL | Notes |
|---------|-----|-------|
| itr-dashboard | https://itr-dashboard-965913991496.us-central1.run.app | Intent-to-return dashboard (no repo found) |
| position-control | https://position-control-965913991496.us-central1.run.app | Legacy position control service (replaced by position-control-form) |
| bigquery-dashboards | https://bigquery-dashboards-965913991496.us-central1.run.app | Legacy deployment (replaced by supervisor-dashboard) |

---

## 11. Master Access Reference

### Role-Based (Dynamic) Access — By Job Title

These access grants require **no code changes** when personnel change. Access follows the role automatically.

| Job Title Contains | Dashboard / App | Access Level | Source |
|--------------------|----------------|-------------|--------|
| "Chief" or "Ex. Dir" | Salary Projection | Full access (all staff salary data) | `auth.py` → `get_salary_access()` |
| Principal | Kickboard, Suspensions | Their school's data | `config.py` → `KICKBOARD_SCHOOL_LEADER_TITLES` |
| Assistant Principal | Kickboard, Suspensions | Their school's data | `config.py` → `KICKBOARD_SCHOOL_LEADER_TITLES` |
| Dean | Kickboard, Suspensions | Their school's data | `config.py` → `KICKBOARD_SCHOOL_LEADER_TITLES` |
| Head of School | Kickboard, Suspensions | Their school's data | `config.py` → `KICKBOARD_SCHOOL_LEADER_TITLES` |
| Director of Culture | Kickboard, Suspensions | Their school's data | `config.py` → `KICKBOARD_SCHOOL_LEADER_TITLES` |
| Chief Academic Officer | Schools Dashboard | All staff except C-Team | `config.py` → `SCHOOLS_DASHBOARD_ROLES` |
| ExDir of Teach and Learn | Schools Dashboard | Teachers only | `config.py` → `SCHOOLS_DASHBOARD_ROLES` |
| K-8 Content Lead | Schools Dashboard | Teachers only | `config.py` → `SCHOOLS_DASHBOARD_ROLES` |
| School Director | Sabbatical Program | Their school's applications | `sabbatical-program/app.py` → `SABBATICAL_SCHOOL_LEADER_TITLES` |
| Principal | Sabbatical Program | Their school's applications | `sabbatical-program/app.py` → `SABBATICAL_SCHOOL_LEADER_TITLES` |
| Assistant Principal | Sabbatical Program | Their school's applications | `sabbatical-program/app.py` → `SABBATICAL_SCHOOL_LEADER_TITLES` |
| Head of School | Sabbatical Program | Their school's applications | `sabbatical-program/app.py` → `SABBATICAL_SCHOOL_LEADER_TITLES` |
| (Any supervisor) | Supervisor Dashboard | Own team + downline | `auth.py` → `get_accessible_supervisors()` |
| (Any supervisor) | Kickboard | Downline staff interactions | `auth.py` → `get_kickboard_access()` |

> **Note:** Sabbatical and Kickboard/Suspensions use different school leader title lists. Dean and Director of Culture qualify for Kickboard/Suspensions but not Sabbatical school admin. School Director qualifies for Sabbatical but not Kickboard/Suspensions.

### Named (Hardcoded) Access — By Email

These access grants are tied to specific email addresses in code. Requires a code deployment to change.

| Email | Dashboard Role | PCF Role | Onboarding Role | Referral Program | Sabbatical Program |
|-------|---------------|----------|----------------|-----------------|-------------------|
| sshirey@firstlineschools.org | CPO (Tier 1a) | super_admin | super_admin | Admin | Network Admin |
| brichardson@firstlineschools.org | HR Team (Tier 1b) | hr | hr | Admin | Network Admin |
| spence@firstlineschools.org | HR Team (Tier 1b) | ceo | — | — | Network Admin |
| mtoussaint@firstlineschools.org | HR Team (Tier 1b) | hr | hr | — | — |
| csmith@firstlineschools.org | HR Team (Tier 1b) | viewer | viewer | — | — |
| aleibfritz@firstlineschools.org | HR Team (Tier 1b) | viewer | viewer | Admin | — |
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

### Open Access (No Special Permissions)

| Dashboard / App | Auth Required | Who Can Access |
|----------------|---------------|---------------|
| Supervisor Dashboard | Google login (@firstlineschools.org) | All staff (sees own team) |
| Staff List | Google login (@firstlineschools.org) | All staff (read-only directory) |
| Org Chart | Google login (@firstlineschools.org) | All staff |
| Salary Calculator | None (public) | Anyone with URL |
| Impact Bonus Guide | None (public) | Anyone with URL |
| Grow Observations | None (SQL files only) | Not deployed |

---

## Dashboard Navigation — Role-Aware Dropdown

**Status:** Complete (deployed Feb 13, 2026)

All 10 dashboards have a "Dashboards" dropdown menu in the header. The dropdown is role-aware: it only shows links to dashboards the logged-in user has permission to access. Each page omits its own self-link.

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

Supervisor, Staff List, and Org Chart links are always visible.

---

## Known Issues

1. **ACL table inaccessible** — `fls-data-warehouse.acl.fls_acl_named` is backed by a Google Sheet that requires Drive permissions not currently granted. Non-blocking (Kickboard ACL fallback only).
2. **Named admin lists require deployment** — Admin tiers (CPO, HR Team, Schools Team), Position Control Roles, Onboarding Roles, Referral Admins, and Sabbatical Network Admins are all hardcoded by email. Adding or removing people requires a code change and deployment. Role-based access (Salary, School Leaders, Supervisors, Schools Dashboard academic roles) transfers automatically.
3. **Inconsistent admin lists across projects** — Different projects have different named admin sets. For example, dcavato is a Sabbatical Network Admin but not in the dashboard admin tiers; dgoodwin is in the dashboard Schools Team but not a Sabbatical Network Admin. This is by design (each project has different operational needs), but should be reviewed periodically.
4. **Different school leader title lists** — Kickboard/Suspensions uses 5 titles (principal, assistant principal, dean, head of school, director of culture). Sabbatical uses 4 titles (school director, principal, assistant principal, head of school). Dean and Director of Culture do not get Sabbatical school admin access; School Director does not get Kickboard/Suspensions school leader access.
5. **Public referral form** — Staff Referral Program accepts submissions without authentication. Anyone with the URL can submit.
6. **Salary/bonus data public** — Salary Calculator and Impact Bonus contain all compensation data in client-side JavaScript, visible to anyone with the URL.
7. **Missing repos** — itr-dashboard Cloud Run service has no corresponding GitHub repo. Legacy services (position-control, bigquery-dashboards) should be decommissioned.
