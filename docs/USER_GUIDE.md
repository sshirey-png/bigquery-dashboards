# FirstLine Schools Dashboard System - User Guide

## Overview

The FirstLine Schools Dashboard System is a web-based platform that provides staff with access to various data views depending on their role. All dashboards require Google authentication with a `@firstlineschools.org` account.

**Live URL:** https://bigquery-dashboards-965913991496.us-central1.run.app

---

## Available Dashboards

| Dashboard | URL Path | Purpose |
|-----------|----------|---------|
| Supervisor Dashboard | `/` | View and manage direct reports, observations, certifications |
| HR Dashboard | `/hr-dashboard` | Network-wide staff data and filters |
| Schools Dashboard | `/schools-dashboard` | Academic team view of teacher data |
| Kickboard Dashboard | `/kickboard-dashboard` | Student behavior tracking and interactions |
| Org Chart | `/orgchart` | Visual organization hierarchy |

---

## 1. Supervisor Dashboard

### Who Can Access
- Any staff member who supervises others (appears in `Supervisor_Email` column in staff data)
- Admins can view all supervisors

### What You See
- **Your direct reports** and their:
  - Observation completion status
  - ITR (Instructional Teacher Rounds) data
  - Certification status (Science of Reading, Numeracy, Teacher Cert)
  - Action steps and meetings

### Navigation
1. Log in with your @firstlineschools.org Google account
2. If you're a supervisor, you'll see your team automatically
3. Admins can use the supervisor dropdown to view any team

---

## 2. HR Dashboard

### Who Can Access
**Admins only** (see Admin List below)

### What You See
- All staff across the network
- Filters by: School, Function, Job Title, Certification Status
- Export capabilities

### Navigation
1. Log in → Click "HR View" in header (only visible to admins)
2. Use filters to narrow down staff
3. Click on staff members for details

---

## 3. Schools Dashboard

### Who Can Access
- **Chief Academic Officer** - sees all schools (except C-Team)
- **ExDir of Teach and Learn** - sees teachers only
- **K-8 Content Lead** - sees teachers only
- **Admins** - full access

### What You See
- Teacher observation and certification data
- Filtered by role-appropriate scope

---

## 4. Kickboard Dashboard

### Who Can Access (Hybrid Permission Model)

| Role | Access Level |
|------|--------------|
| **Admins** | All schools, all data |
| **School Leaders** (Principal, AP, Dean, Head of School) | Full data for their school |
| **Supervisors** | Interactions logged by staff in their reporting chain |
| **ACL Grants** | Specific schools granted via ACL table |

### Features

#### Level 0: Network Summary
- School cards showing interactions, positive/negative counts, ratios
- Week-over-week trend indicators (green up, red down)
- Click a school card to drill down

#### Level 1: School View
- Toggle between **"By Grade"** and **"By Teacher"** views
- Summary stats: Total interactions, Positive, Negative, Ratio, Net Dollars
- Click a grade to see students, or click a teacher to see their interactions

#### Level 2: Student List (from Grade view)
- Sortable columns (click headers)
- Click a student to see their interaction history

#### Modals
- **Student Modal**: All interactions for a specific student
- **Teacher Modal**: All interactions logged by a specific teacher

#### Filters
- **School**: Filter by school (hidden if you only have access to one)
- **Grade**: Filter by grade level
- **Category**: Filter by interaction category
- **Staff**: Filter by staff member who logged the interaction
- **Date Range**: Defaults to current school year (8/4/2025 - today)

---

## Permission System

### Admin Users

Admins have full access to ALL dashboards and ALL data. Current admin list:

| Email | Name | Role |
|-------|------|------|
| sshirey@firstlineschools.org | Scott Shirey | Chief People Officer |
| brichardson@firstlineschools.org | Brittney Richardson | Chief of Human Resources |
| spence@firstlineschools.org | Sabrina Pence | |
| mtoussaint@firstlineschools.org | M. Toussaint | |
| csmith@firstlineschools.org | C. Smith | |
| aleibfritz@firstlineschools.org | A. Leibfritz | |
| sdomango@firstlineschools.org | Sivi Domango | Chief Experience Officer |
| dgoodwin@firstlineschools.org | Dawn Goodwin | K-8 Content Lead |
| rjohnson@firstlineschools.org | Rameisha Johnson | Manager Family Engagement |
| krodriguez@firstlineschools.org | Kristin Rodriguez | Dir of Culture |
| csteele@firstlineschools.org | Charlotte Steele | Dir of ESYNOLA |

### How Permissions Work

1. **User logs in** with Google (@firstlineschools.org only)
2. **System checks** (in order):
   - Is user in ADMIN_EMAILS list? → Full access
   - Is user a supervisor? → See their team's data
   - Does user have specific role? → Role-based access
   - Is user in ACL table? → Explicit grants
3. **Access denied** if none of the above apply

### School Leader Detection (Kickboard)

The system automatically detects school leaders by job title:
- Principal
- Assistant Principal
- Dean
- Head of School

These users automatically see full data for their school based on their `Location` field in the staff database.

---

## Data Sources

All data comes from Google BigQuery:

| Data | Source Table |
|------|--------------|
| Staff Information | `talent-demo-482004.talent_grow_observations.staff_master_list_with_function` |
| Supervisor Dashboard | `talent-demo-482004.talent_grow_observations.supervisor_dashboard_data` |
| Kickboard Interactions | `fls-data-warehouse.kickboard.interactions` |
| Kickboard ACL | `fls-data-warehouse.acl.fls_acl_named` |

---

## Common Tasks

### Adding a New Admin

Contact someone with access to the codebase (see Technical Guide) to add the email to `config.py` in the `ADMIN_EMAILS` list.

### Granting Kickboard Access to Non-Supervisors

Two options:
1. Add them to the `fls_acl_named` table in BigQuery (grants school-level access)
2. Add them to the `ADMIN_EMAILS` list (grants full access)

### Viewing Someone Else's Team (Admins Only)

1. Go to Supervisor Dashboard (`/`)
2. Use the supervisor dropdown to select the person
3. You'll see their team's data

### Checking Who Has Access

The permission system is code-based. To see who has access:
1. **Admins**: Check `config.py` → `ADMIN_EMAILS`
2. **School Leaders**: Anyone with matching job titles at a school
3. **Supervisors**: Anyone with direct reports in staff database
4. **ACL Grants**: Check `fls-data-warehouse.acl.fls_acl_named` in BigQuery

---

## Troubleshooting

### "Access Denied" Error

- Verify you're using your @firstlineschools.org account
- Check if you should have access (are you a supervisor? admin? school leader?)
- Contact an admin to verify your permissions

### Data Looks Wrong or Outdated

- Click the "Refresh" button in the header
- Data comes from BigQuery - check if source data is up to date

### Can't See Kickboard Dashboard

You need one of:
- Admin access
- School leader job title (Principal, AP, Dean)
- Direct reports (supervisor access)
- Entry in ACL table

### Page Won't Load

- Try a hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Clear browser cache
- Try a different browser

---

## School Codes Reference

| Code | Full Name |
|------|-----------|
| Ashe | Arthur Ashe Charter School |
| LHA | Langston Hughes Academy |
| Wheatley | Phillis Wheatley Community School |
| Green | Samuel J. Green Charter School |

---

## Contact

For access issues or questions, contact:
- Scott Shirey (sshirey@firstlineschools.org) - Chief People Officer
- Brittney Richardson (brichardson@firstlineschools.org) - Chief of Human Resources
