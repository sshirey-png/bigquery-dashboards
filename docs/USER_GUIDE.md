# FirstLine Schools Dashboard System - User Guide

## Overview

The FirstLine Schools Dashboard System is a web-based platform that provides staff with access to various data views depending on their role. All dashboards require Google authentication with a `@firstlineschools.org` account.

**Live URL:** https://supervisor-dashboard-965913991496.us-central1.run.app

---

## Available Dashboards

| Dashboard | URL Path | Purpose |
|-----------|----------|---------|
| Supervisor Dashboard | `/` | View and manage direct reports, observations, certifications |
| HR Dashboard | `/hr-dashboard` | Network-wide staff data and filters |
| Schools Dashboard | `/schools-dashboard` | Academic team view of teacher data |
| Kickboard Dashboard | `/kickboard-dashboard` | Student behavior tracking and interactions |
| Org Chart | `/orgchart` | Visual organization hierarchy |
| Staff List | `/staff-list-dashboard` | Customizable, filterable staff directory |
| Salary Projection | `/salary-dashboard` | Salary modeling and scenario planning |
| Position Control | `/position-control-dashboard` | Manage position control form requests and approvals |
| Onboarding | `/onboarding-dashboard` | Track and manage new hire onboarding submissions |

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
**CPO + HR Team** (Tier 1a and 1b)

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
- **Schools Team** (Chief Experience Officer, K-8 Content Lead, Dir of Culture, Dir of ESYNOLA) - full access
- **Chief Academic Officer** - sees all schools (except C-Team)
- **ExDir of Teach and Learn** - sees teachers only
- **K-8 Content Lead** - sees teachers only
- **Admins** - full access

### What You See
- Staff table with observation data, certification status, action steps, and **assessment fidelity** (completion % and mastery %)
- Filters by school, supervisor, employee type, job function, subject, and grade band
- Filtered by role-appropriate scope

### Assessment Fidelity

#### School Summary Table
At the top of the page, a summary table shows the most recent formal assessment for each school:
- **Completion %** — what percentage of students took the test
- **Mastery %** — what percentage of tested students scored 75% or above
- Color-coded: green (high), amber (medium), red (low)
- Click a school row to see a detailed breakdown with per-teacher data

#### Staff Table Columns
Each teacher row shows two assessment columns:
- **Completion %** — this teacher's students who tested (bold = current, small text = previous with trend arrow)
- **Mastery %** — this teacher's students scoring 75%+ (same format)
- Non-teaching staff (Deans, Directors, etc.) show "—"
- Click a cell to open the assessment detail modal

#### Teacher Assessment Modal
Click a teacher's completion or mastery cell to see:
- Summary cards: current completion and mastery with deltas from previous
- Current and previous assessment cards with test name, date, and metrics
- **View Students** button on each assessment card

#### Student Drill-Down
Click "View Students" to see a per-student breakdown:
- **Summary**: Tested count, Missing count, Total count
- **Missing students** listed first (need attention), highlighted in red
- **Tested students** sorted by score (lowest first), with score and points
- **Bottom 25th percentile students** (from SPS data) highlighted with amber styling, bold names, and "B25" badge with subject specificity (ELA, Math, or both)

#### SPED Co-Teachers
SPED teachers who push into gen-ed classrooms (co-teaching model) are automatically matched to the inclusion section at their school — the section with the highest concentration of SPED students for each grade/course. Each grade's test is shown as a separate data point (no averaging across grades).

---

## 4. Kickboard Dashboard

### Who Can Access (Hybrid Permission Model)

| Role | Access Level |
|------|--------------|
| **Admins** | All schools, all data |
| **School Leaders** (Principal, AP, Dean, Head of School, Director of Culture) | Full data for their school |
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
- **Date Range**: Defaults to current school year (dynamically calculated)

---

## 5. Staff List Dashboard

### Who Can Access
Any user with a `@firstlineschools.org` Google account.

### What You See
A customizable staff directory with all current and past employees. The dashboard includes:
- **Stat cards** showing Total Staff, Active count, Locations, and current filtered count
- **Sortable, filterable table** with selectable columns

### Filters
- **Search**: Free-text search across name, email, title, location, department, supervisor
- **Location**: Filter by school/site
- **Status**: Active, Leave of Absence, Terminated, etc.
- **Department**: Filter by department
- **Supervisor**: Filter by supervisor name
- **Function**: Leadership, Network, Operations, Support, Teacher

Active filter badges appear below the toolbar — click the × on any badge to remove that filter.

### Column Customization
1. Click the **Columns** button in the toolbar
2. Toggle columns on/off by clicking the checkboxes
3. Drag columns to reorder them
4. Use **Select All**, **Defaults**, or **Deselect All** for quick changes
5. Click **Apply Changes**

> **Note:** Your column preferences are saved in your browser. They will persist across sessions until you clear your browser data or click **Defaults** to reset.

**Default columns:** Location, First Name, Last Name, Email, Job Title, Supervisor, Status, Hire Date

### Row Selection & Emailing
1. Use the **checkboxes** on the left side of the table to select individual staff members
2. Use the **header checkbox** to select/deselect all on the current page
3. A blue **selection banner** appears showing the count of selected staff
4. Click **Email Selected** (on the banner) or **Email List** (in the toolbar) to open a Gmail compose window addressed to all selected staff
5. Click **Deselect All** on the banner to clear selections

> **Note:** Row selections do not persist across page reloads — they are temporary.

### Exporting Data
Click **Export** to choose from:
- **Export as CSV** — downloads a CSV file of the filtered data with your visible columns
- **Export as JSON** — downloads a JSON file
- **Print** — opens the browser print dialog

### Staff Detail View
Click on any row to open a detail panel showing all available fields for that staff member.

### Privacy
- Birthdays display month and day only (no year)

---

## Permission System

### Permission Tiers

Access is controlled by role tiers defined in `config.py`. Each tier grants different dashboard access.

#### Tier 1a: CPO — full access to everything
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

#### Schools Team — Schools, Kickboard, Suspensions
| Email | Name |
|-------|------|
| sdomango@firstlineschools.org | Sivi Domango - Chief Experience Officer |
| dgoodwin@firstlineschools.org | Dawn Goodwin - K-8 Content Lead |
| krodriguez@firstlineschools.org | Kristin Rodriguez - Dir of Culture |
| csteele@firstlineschools.org | Charlotte Steele - Dir of ESYNOLA |

### Dashboard Access Matrix

| Dashboard | Who Can Access |
|-----------|---------------|
| **Supervisor** | All @firstlineschools.org users |
| **HR/Talent** | CPO + HR Team |
| **Schools** | CPO + Schools Team + specific job titles |
| **Kickboard** | CPO + Schools Team + School Leaders + Supervisors + ACL |
| **Suspensions** | CPO + Schools Team + School Leaders |
| **Salary Projection** | C-Team only (Chief/Ex. Dir in title) |
| **Position Control** | PCF role holders (see Position Control section) |
| **Onboarding** | Onboarding role holders (see Onboarding section) |
| **Staff List** | All @firstlineschools.org users |
| **Org Chart** | All @firstlineschools.org users |

### What You See in the Nav Dropdown

Every dashboard has a "Dashboards" dropdown that shows only the dashboards you can access.

| Role | Dashboards Visible |
|------|--------------------|
| CPO | All: Supervisor, HR, Staff List, Schools, Kickboard, Suspensions, Salary, Position Control, Onboarding, Org Chart |
| HR Team | Supervisor, HR, Staff List, Position Control, Onboarding, Org Chart |
| Schools Team | Supervisor, Staff List, Schools, Kickboard, Suspensions, Org Chart (+Salary if C-Team title) |
| School Leaders | Supervisor, Staff List, Kickboard, Suspensions, Org Chart |
| Supervisors | Supervisor, Staff List, Org Chart (+Kickboard if they have downline staff) |
| All Staff | Supervisor, Staff List, Org Chart |

### How Permissions Work

1. **User logs in** with Google (@firstlineschools.org only)
2. **System checks** (in order):
   - Is user in a permission tier? → Tier-based access
   - Is user a school leader (by job title)? → School-level access
   - Is user a supervisor? → See their team's data
   - Is user in ACL table? → Explicit grants
3. **Access denied** if none of the above apply

### School Leader Detection (Kickboard/Suspensions)

The system automatically detects school leaders by job title:
- Principal
- Assistant Principal
- Dean
- Head of School
- Director of Culture

These users automatically see full data for their school based on their `Location` field in the staff database.

---

## Common Tasks

### Adding a New Admin

Contact someone with access to the codebase (see Technical Guide) to add the email to `config.py` in the appropriate tier list.

### Granting Kickboard Access to Non-Supervisors

Two options:
1. Add them to the `fls_acl_named` table in BigQuery (grants school-level access)
2. Add them to the appropriate admin tier in `config.py` (grants full access)

### Viewing Someone Else's Team (Admins Only)

1. Go to Supervisor Dashboard (`/`)
2. Use the supervisor dropdown to select the person
3. You'll see their team's data

### Checking Who Has Access

The permission system is code-based. See [Access Permissions](ACCESS_PERMISSIONS.md) for the full reference, or:
1. **Admin tiers**: Check `config.py` → `ADMIN_EMAILS`
2. **PCF roles**: Check `config.py` → `POSITION_CONTROL_ROLES`
3. **Onboarding roles**: Check `config.py` → `ONBOARDING_ROLES`
4. **School Leaders**: Anyone with matching job titles at a school
5. **Supervisors**: Anyone with direct reports in staff database
6. **ACL Grants**: Check `fls-data-warehouse.acl.fls_acl_named` in BigQuery

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

## 6. Salary Projection Dashboard

### Who Can Access
- **C-Team only** — job title must contain "Chief" or "Ex. Dir"

### What You See
- All staff salary data with Current, Standard, and Custom salary comparison
- Custom scenario builder for modeling salary changes
- CSV export with YOS and bonus columns

---

## 7. Position Control Dashboard

### Who Can Access
Position Control has its own role system (separate from the main admin list):

| Email | Role | Can Approve | Can Edit Final Status | Can Create Position |
|-------|------|------------|----------------------|-------------------|
| sshirey@ | Super Admin | CEO, Finance, Talent, HR | Yes | Yes |
| spence@ | CEO | CEO | Yes | No |
| rcain@ | Finance | Finance | No | No |
| lhunter@ | Finance | Finance | No | No |
| brichardson@ | HR | HR, Talent | Yes | Yes |
| mtoussaint@ | HR | HR | No | No |
| aleibfritz@ | Viewer | — | No | No |
| csmith@ | Viewer | — | No | No |

### What You See
- **Stats cards**: Total requests, Pending, Approved, Denied, Awaiting Offer
- **Filterable, sortable table** of all position control form requests
- **Archive/Unarchive** toggle to hide completed requests
- **Edit modal** with role-based field access (approval fields, final status, offer dates, admin notes)
- **Create Position** button for approved requests (creates entry in position control table)

### How It Works
1. School leaders submit position requests via the **standalone Position Control Form** (separate app)
2. Requests appear on this dashboard for HR/Finance/CEO review
3. Each approver sets their approval field (Approved/Denied)
4. Final status is set by authorized users
5. Once fully approved, HR can "Create Position" to add to the position control table

### Navigation
1. Log in → "Position Control" appears in the Dashboards dropdown (if you have access)
2. Use filters to find requests by status, school year, or request type
3. Click a request row to open the edit modal
4. Submit New Request link opens the standalone form app

---

## 8. Onboarding Dashboard

### Who Can Access
Onboarding has its own role system:

| Email | Role | Can Edit | Can Delete |
|-------|------|---------|-----------|
| sshirey@ | Super Admin | Yes | Yes |
| brichardson@ | HR | Yes | No |
| mtoussaint@ | HR | Yes | No |
| csmith@ | Viewer | No | No |
| aleibfritz@ | Viewer | No | No |

### What You See
- **Stats cards**: Total submissions, Not Started, In Progress, Complete, Needs Accommodation
- **Filterable, sortable table** of all onboarding form submissions
- **Archive/Unarchive** toggle
- **Edit modal** for updating onboarding status, position title, badge printed, equipment issued, orientation complete, start date, and admin notes

### How It Works
1. New hires fill out the **standalone Onboarding Form** (separate app)
2. Submissions appear on this dashboard for HR to track and manage
3. HR updates status fields as the new hire progresses through onboarding
4. Completed onboardings can be archived

### Navigation
1. Log in → "Onboarding" appears in the Dashboards dropdown (if you have access)
2. Use filters to find submissions by status, school, or name
3. Click a row to open the edit modal
4. Share Form Link button opens the standalone onboarding form

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
