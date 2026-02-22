# FirstLine Schools Dashboard System - Technical Guide

## Overview

This guide is for developers and administrators who need to maintain, update, or extend the dashboard system. It covers the codebase structure, deployment process, and common maintenance tasks.

---

## Table of Contents

1. [Getting Started with GitHub](#1-getting-started-with-github)
2. [Project Structure](#2-project-structure)
3. [Local Development Setup](#3-local-development-setup)
4. [Making Changes](#4-making-changes)
5. [Deployment](#5-deployment)
6. [Common Maintenance Tasks](#6-common-maintenance-tasks)
7. [Understanding the Permission System](#7-understanding-the-permission-system)
8. [Database Schema](#8-database-schema)
9. [Troubleshooting](#9-troubleshooting)
10. [Using Claude Code](#10-using-claude-code)

---

## 1. Getting Started with GitHub

### What is GitHub?
GitHub is where the code is stored. Think of it as a cloud backup for code that also tracks all changes over time.

### Repository Location
```
https://github.com/sshirey-png/bigquery-dashboards
```

### Accessing the Code

#### Option A: View Online (No Installation)
1. Go to https://github.com/sshirey-png/bigquery-dashboards
2. Click on any file to view its contents
3. Use the file browser on the left to navigate

#### Option B: Download the Code
1. Go to the repository URL
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract to a folder on your computer

#### Option C: Clone with Git (Recommended for Making Changes)
```bash
git clone https://github.com/sshirey-png/bigquery-dashboards.git
cd bigquery-dashboards
```

---

## 2. Project Structure

```
bigquery-dashboards/
├── app.py                 # Main Flask application (slim orchestrator)
├── config.py              # Configuration and constants (ADMIN_EMAILS, etc.)
├── extensions.py          # BigQuery client and OAuth setup
├── auth.py                # Shared authentication helpers
├── blueprints/            # Route handlers organized by feature
│   ├── __init__.py
│   ├── auth_routes.py     # Login, logout, auth status
│   ├── supervisor.py      # Supervisor dashboard routes
│   ├── hr.py              # HR dashboard routes
│   ├── schools.py         # Schools dashboard routes
│   ├── kickboard.py       # Kickboard dashboard routes
│   ├── suspensions.py     # Suspensions dashboard routes
│   ├── staff_list.py      # Staff List dashboard routes
│   ├── salary.py          # Salary dashboard routes
│   ├── position_control.py # Position Control Form admin routes
│   ├── onboarding.py      # Onboarding Form admin routes
│   ├── orgchart.py        # Org chart routes
│   └── health.py          # Health check endpoint
├── index.html             # Supervisor Dashboard frontend
├── hr-dashboard.html      # HR Dashboard frontend
├── schools-dashboard.html # Schools Dashboard frontend
├── kickboard-dashboard.html # Kickboard Dashboard frontend
├── suspensions-dashboard.html # Suspensions Dashboard frontend
├── staff-list-dashboard.html  # Staff List Dashboard frontend
├── salary-dashboard.html      # Salary Dashboard frontend
├── position-control-dashboard.html # Position Control admin frontend
├── onboarding-dashboard.html      # Onboarding admin frontend
├── orgchart.html          # Org Chart frontend
├── Dockerfile             # Container build instructions
├── requirements.txt       # Python dependencies
└── docs/                  # Documentation
    ├── USER_GUIDE.md
    ├── TECHNICAL_GUIDE.md
    └── ACCESS_PERMISSIONS.md
```

### Key Files Explained

| File | Purpose | When to Edit |
|------|---------|--------------|
| `config.py` | Admin list, school mappings, table names | Adding admins, changing school names |
| `auth.py` | Permission logic, grade/subject mapping | Changing who can access what, updating grade or subject mappings |
| `blueprints/position_control.py` | Position Control admin API | Changing PCF approval logic, permissions |
| `blueprints/onboarding.py` | Onboarding admin API | Changing onboarding tracking logic, permissions |
| `blueprints/schools.py` | Schools dashboard API (staff, assessments, students) | Changing assessment fidelity logic, SPED matching |
| `blueprints/kickboard.py` | Kickboard API endpoints | Changing Kickboard data/features |
| `schools-dashboard.html` | Schools dashboard UI | Changing assessment display, modals, summary table |
| `kickboard-dashboard.html` | Kickboard UI | Changing how Kickboard looks |
| `Dockerfile` | Container build | Adding new dependencies |

---

## 3. Local Development Setup

### Prerequisites
- Python 3.9 or higher
- Google Cloud SDK (gcloud CLI)
- Git (optional but recommended)

### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sshirey-png/bigquery-dashboards.git
   cd bigquery-dashboards
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv

   # Windows:
   venv\Scripts\activate

   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google Cloud credentials**
   ```bash
   gcloud auth application-default login
   ```

5. **Run locally**
   ```bash
   # Set development mode (bypasses OAuth)
   set FLASK_ENV=development   # Windows
   export FLASK_ENV=development  # Mac/Linux

   python app.py
   ```

6. **Open in browser**
   ```
   http://localhost:5000
   ```

### Development Mode
When `FLASK_ENV=development`, the app:
- Skips Google OAuth (auto-logs in as dev user)
- Shows detailed error messages
- Dev user is set in `config.py` as `DEV_USER_EMAIL`

---

## 4. Making Changes

### Workflow Overview

```
1. Make changes locally
2. Test locally
3. Commit to Git
4. Push to GitHub
5. Deploy to Cloud Run
```

### Example: Adding a New Admin

1. **Open `config.py`**

2. **Find the appropriate tier list** (starting at line 25):
   - `CPO_EMAILS` — full access to everything
   - `HR_TEAM_EMAILS` — HR, Supervisor, Staff List, Position Control, Onboarding
   - `SCHOOLS_TEAM_EMAILS` — Schools, Kickboard, Suspensions

3. **Add the new email to the correct tier:**
   ```python
   HR_TEAM_EMAILS = [
       'brichardson@firstlineschools.org',   # Chief of Human Resources
       # ... existing emails ...
       'newemail@firstlineschools.org',  # New Person - Title
   ]
   ```

4. **Save the file**

5. **Commit and push:**
   ```bash
   git add config.py
   git commit -m "Add [Name] to HR team admin list"
   git push origin master
   ```

6. **Deploy** (see Section 5)

### School Year Dates

The school year start date is **automatically calculated** in `config.py` (line 91-97). It uses July 1 as the school year boundary — no manual update needed when the school year changes.

---

## 5. Deployment

### Where It Runs
The application runs on **Google Cloud Run** in the `talent-demo-482004` project.

### Deployment Command

From the project directory:
```bash
gcloud run deploy supervisor-dashboard \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### What Happens During Deployment
1. Google Cloud builds a Docker container from your code
2. The container is pushed to Google Container Registry
3. Cloud Run creates a new revision
4. Traffic is routed to the new revision
5. Old revisions are kept (can rollback if needed)

### Deployment Takes ~3-5 Minutes
You'll see progress output. When done:
```
Service URL: https://supervisor-dashboard-965913991496.us-central1.run.app
```

### Verifying Deployment
1. Open the Service URL
2. Hard refresh (Ctrl+Shift+R) to clear cache
3. Test the feature you changed

### Rolling Back
If something breaks, you can rollback in Google Cloud Console:
1. Go to https://console.cloud.google.com
2. Navigate to Cloud Run → supervisor-dashboard
3. Click "Revisions" tab
4. Select a previous revision → "Manage Traffic" → Route 100% to it

---

## 6. Common Maintenance Tasks

### Adding an Admin User

**File:** `config.py`
**Location:** The appropriate tier list (`CPO_EMAILS`, `HR_TEAM_EMAILS`, or `SCHOOLS_TEAM_EMAILS`)

```python
HR_TEAM_EMAILS = [
    # ... existing emails ...
    'newadmin@firstlineschools.org',  # Name - Title
]
```

> **Note:** `ADMIN_EMAILS` is computed automatically (`CPO_EMAILS + HR_TEAM_EMAILS`). Do not edit it directly.

Then commit, push, and deploy.

### Removing an Admin User

Same as above, but remove the line from the appropriate tier list.

### Adding a School Leader Title

**File:** `config.py`
**Location:** `KICKBOARD_SCHOOL_LEADER_TITLES` list

```python
KICKBOARD_SCHOOL_LEADER_TITLES = [
    'principal',
    'assistant principal',
    'dean',
    'head of school',
    'director of culture',
    'new title here',  # Add new title (lowercase)
]
```

### Changing School Mappings

**File:** `config.py`
**Location:** `KICKBOARD_SCHOOL_MAP`

```python
KICKBOARD_SCHOOL_MAP = {
    'Ashe': 'Arthur Ashe Charter School',
    'LHA': 'Langston Hughes Academy',
    'Wheatley': 'Phillis Wheatley Community School',
    'Green': 'Samuel J. Green Charter School',
    'NewCode': 'New School Full Name',  # Add new school
}
```

### School Year Date

The school year date (`CURRENT_SY_START`) is **automatically calculated** in `config.py` based on the current date. No manual update is needed when the school year rolls over.

### Adding an Email Alias

For users with multiple email addresses (e.g., @esynola.org):

**File:** `config.py`
**Location:** `EMAIL_ALIASES`

```python
EMAIL_ALIASES = {
    'alias@otherdomain.org': 'primary@firstlineschools.org',
}
```

---

## 7. Understanding the Permission System

### Authentication Flow

```
User visits site
    ↓
Has session cookie? ──No──→ Redirect to /login
    ↓ Yes                         ↓
Check permissions            Google OAuth
    ↓                             ↓
Grant appropriate access     Verify @firstlineschools.org
                                  ↓
                             Create session
                                  ↓
                             Redirect back
```

### Permission Check Order (Kickboard)

```python
def get_kickboard_access(email):
    # 1. Check if admin
    if is_admin(email):
        return full_access_to_all_schools

    # 2. Check if school leader (by job title)
    if job_title contains 'principal', 'dean', etc:
        return access_to_their_school

    # 3. Check if supervisor (has direct reports)
    if has_direct_reports:
        return access_to_downline_staff_interactions

    # 4. Check ACL table
    if in_acl_table:
        return access_to_granted_schools

    # 5. No access
    return None
```

### Key Functions in `auth.py`

| Function | Purpose |
|----------|---------|
| `is_cpo(email)` | Check if user is in CPO tier (Tier 1a) |
| `is_hr_team(email)` | Check if user is in HR Team tier (Tier 1b) |
| `is_hr_admin(email)` | Check if user is CPO or HR Team |
| `is_schools_team(email)` | Check if user is in Schools Team |
| `is_schools_admin(email)` | Check if user is CPO or Schools Team |
| `is_admin(email)` | Same as `is_hr_admin()` — backward compat |
| `get_kickboard_access(email)` | Determine Kickboard permissions (hybrid: admin/school leader/supervisor/ACL) |
| `get_suspensions_access(email)` | Determine Suspensions permissions (admin or school leader) |
| `get_salary_access(email)` | Determine Salary access (C-Team job titles only, no admin bypass) |
| `get_schools_dashboard_role(email)` | Determine Schools dashboard scope (admin/job title based) |
| `get_supervisor_name_for_email(email)` | Look up supervisor from email |
| `get_accessible_supervisors(email, name)` | Get list of supervisors user can view |
| `resolve_email_alias(email)` | Map alias emails to primary |
| `map_grade_desc_to_levels(grade_level_desc)` | Convert staff `Grade_Level_Desc` to list of integer grade levels |
| `map_subject_desc_to_assessment(subject_desc)` | Convert staff `Subject_Desc` to assessment subject strings |
| `get_pcf_access(email)` | Check if user has Position Control Form access |
| `get_pcf_permissions(email)` | Get detailed PCF permissions (can_approve, can_edit_final, etc.) |
| `get_onboarding_access(email)` | Check if user has Onboarding Form access |
| `get_onboarding_permissions(email)` | Get detailed onboarding permissions (can_edit, can_delete, etc.) |

---

## 8. Database Schema

### BigQuery Tables Used

#### Staff Data
```
Table: talent-demo-482004.talent_grow_observations.staff_master_list_with_function

Key Columns:
- Employee_Number (INTEGER)
- Email_Address (STRING)
- Job_Title (STRING)
- Dept (STRING)
- Location_Name (STRING)
- Supervisor_Name__Unsecured_ (STRING)
- Employment_Status (STRING)
```

#### Kickboard Interactions
```
Table: fls-data-warehouse.kickboard.interactions

Key Columns:
- Interaction_Date (DATE)
- School (STRING) - e.g., 'Ashe', 'LHA'
- Grade_Level (INTEGER)
- Student_Number (STRING)
- Student_LastFirst (STRING)
- Staff (STRING)
- UKG_Staff_ID (STRING)
- Interaction (STRING)
- Category (STRING)
- Dollar_Value (FLOAT)
- Comments (STRING)
```

#### Kickboard ACL
```
Table: fls-data-warehouse.acl.fls_acl_named

Key Columns:
- email (STRING)
- powerschool (STRING) - school code
```

#### Assessment Results (Aggregated by Test)
```
Table: fls-data-warehouse.performance_matters.results_by_test

Key Columns:
- Test_ID (STRING)
- Test_Name (STRING)
- Test_Date (DATE)
- Location_Name (STRING) - full school name
- Grade_Level (INTEGER) - 0-8
- Subject (STRING) - English, Math, Science, Social Studies
- Metric_Key (STRING) - 'completion_percent', 'percent_scoring_75_or_above'
- Metric_Value (FLOAT) - decimal 0.0 to 1.0
```

#### Assessment Results (Student-Level)
```
Table: fls-data-warehouse.performance_matters.results_raw

Key Columns:
- Test_ID (STRING)
- Test_Name (STRING)
- Student_Number (STRING)
- StudentLastFirst (STRING)
- School_Name (STRING) - short code (Ashe, LHA, etc.)
- Grade_Level_of_Test (INTEGER)
- Subject (STRING)
- Points_Earned (FLOAT)
- Points_Possible (FLOAT)
- Percent_Correct (FLOAT)
- Assessment_Category (STRING) - Quiz, Test, End of Module, etc.
```

#### Class Schedules
```
Table: fls-data-warehouse.class_schedules.class_schedules

Key Columns:
- Teacher_Email (STRING)
- CC_School (STRING) - short code
- Student_Number (STRING)
- Course_Number (STRING) - e.g., MAT07, ELA03
- Section_Number (STRING)
- Grade_Level (INTEGER)
```

#### Student Roster
```
Table: fls-data-warehouse.student_rosters.student_roster

Key Columns:
- Student_Number (STRING)
- School (STRING) - short code
- Grade_Level (INTEGER)
- SPEDIndicator (STRING) - 'Yes' or 'No'
```

#### SPS Bottom 25th Percentile
```
Table: fls-data-warehouse.sps.24_25_bottom_25

Key Columns:
- Student_Number (STRING)
- LastFirst (STRING)
- Bottom_25th (STRING) - 'Yes' if in bottom 25th
- ELA_25th (STRING)
- Math_25th (STRING)
```

#### Position Control Form Requests
```
Table: talent-demo-482004.position_control_form.requests

Key Columns:
- request_id (STRING)
- submitted_at (TIMESTAMP)
- requestor_name (STRING)
- requestor_email (STRING)
- request_type (STRING)
- position_title (STRING)
- employee_name (STRING)
- ceo_approval (STRING) - Pending/Approved/Denied
- finance_approval (STRING)
- talent_approval (STRING)
- hr_approval (STRING)
- final_status (STRING)
- offer_sent (DATE)
- offer_signed (DATE)
- position_id (STRING)
- is_archived (BOOL)
```

#### Onboarding Form Submissions
```
Table: talent-demo-482004.onboarding_form.submissions

Key Columns:
- submission_id (STRING)
- submitted_at (TIMESTAMP)
- email (STRING)
- first_name (STRING)
- last_name (STRING)
- school_location (STRING)
- onboarding_status (STRING) - Not Started/In Progress/Complete
- start_date (DATE)
- position_title (STRING)
- badge_printed (STRING)
- equipment_issued (STRING)
- orientation_complete (STRING)
- is_archived (BOOL)
```

### Assessment Fidelity Architecture

The Schools Dashboard assessment fidelity feature computes **per-teacher** completion and mastery metrics from actual class rosters rather than school-wide aggregates.

**Data flow:**
1. `results_raw` filtered to formal assessments (excluding Quiz, Reading Checkpoint) → `formal_tests`
2. `results_by_test` ranked by date per school/grade/subject → current and previous assessments
3. `class_schedules` joined with `results_raw` → per-teacher student-level results
4. SPED teachers without direct rosters get **virtual rosters** from inclusion sections

**SPED Virtual Roster Logic:**
- SPED teachers in grades 3-8 who have no entries in `class_schedules` are identified
- For each school/grade/course, the section with the highest count of `SPEDIndicator = 'Yes'` students is selected as the inclusion section
- All students in that section are assigned to the SPED teacher as a virtual roster
- Each grade's test is a separate data point — no averaging across grades

**API Endpoints:**
- `GET /api/schools/assessment-fidelity` — Returns school-level summary and per-teacher metrics
- `GET /api/schools/assessment-students?teacher_email=...&test_name=...` — Returns student-level drill-down with scores, missing students, and B25 flags

---

## 9. Troubleshooting

### Deployment Fails

**"Permission denied"**
```bash
gcloud auth login
gcloud config set project talent-demo-482004
```

**"Docker build failed"**
- Check `requirements.txt` for typos
- Check `Dockerfile` syntax

### Application Errors

**500 Internal Server Error**
- Check Cloud Run logs:
  ```bash
  gcloud run logs read supervisor-dashboard --region us-central1
  ```

**BigQuery Permission Denied**
- The Cloud Run service account needs BigQuery access
- Check IAM permissions in Google Cloud Console

### Local Development Issues

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"OAuth error" locally**
- Make sure `FLASK_ENV=development` is set
- Or set up OAuth credentials for local testing

---

## 10. Using Claude Code

Claude Code is an AI assistant that helped build this system. You can use it to make changes without deep coding knowledge.

### What is Claude Code?
- AI-powered coding assistant
- Runs in your terminal
- Can read, write, and modify code
- Can run commands and deploy

### Installing Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

### Basic Usage
```bash
cd bigquery-dashboards
claude

# Then type your request, for example:
> Add jsmith@firstlineschools.org as an admin

# Claude will:
# 1. Find the right file (config.py)
# 2. Make the change
# 3. Show you what changed
# 4. Offer to commit and deploy
```

### Example Prompts

**Adding an admin:**
```
Add jsmith@firstlineschools.org (John Smith - Director of Operations) as an admin
```

**Checking permissions:**
```
What can mtoussaint@firstlineschools.org see on the Kickboard dashboard?
```

**Making UI changes:**
```
Change the default date range on Kickboard to start from September 1st instead of August 4th
```

**Deploying:**
```
Deploy the changes to Cloud Run
```

### Tips for Using Claude Code
1. Be specific about what you want
2. Mention file names if you know them
3. Ask it to explain before making changes
4. Always test after deployment
5. Keep prompts focused on one task at a time

---

## Migration / Portability

This application is designed to be easily migrated to a different GCP project. All GCP project references are centralized in `config.py`.

### To Migrate to a New GCP Project

1. **Copy BigQuery datasets** to the new project:
   ```bash
   # Copy dataset using bq command
   bq cp talent-demo-482004:talent_grow_observations new-project:talent_grow_observations
   ```
   Or use the BigQuery Console: Dataset → Copy Dataset

2. **Update config.py** (one line):
   ```python
   PROJECT_ID = 'new-project-id'
   ```

3. **Enable required APIs** in the new project:
   - BigQuery API
   - Cloud Run API
   - Secret Manager API (for OAuth credentials)

4. **Set up service account** with BigQuery access

5. **Deploy to Cloud Run** in the new project:
   ```bash
   gcloud run deploy supervisor-dashboard --source . --region us-central1 --project new-project-id --allow-unauthenticated
   ```

6. **Update OAuth redirect URIs** in Google Cloud Console to include the new Cloud Run URL

### Configuration Files

| File | What to Change |
|------|----------------|
| config.py | `PROJECT_ID` variable |
| (Optional) Update OAuth credentials in Secret Manager |

---

## Quick Reference

### Important URLs

| Resource | URL |
|----------|-----|
| Live Application | https://supervisor-dashboard-965913991496.us-central1.run.app |
| GitHub Repository | https://github.com/sshirey-png/bigquery-dashboards |
| Google Cloud Console | https://console.cloud.google.com/run?project=talent-demo-482004 |
| BigQuery Console | https://console.cloud.google.com/bigquery?project=talent-demo-482004 |

### Common Commands

```bash
# Deploy
gcloud run deploy supervisor-dashboard --source . --region us-central1 --allow-unauthenticated

# View logs
gcloud run logs read supervisor-dashboard --region us-central1

# Git commit and push
git add .
git commit -m "Description of change"
git push origin master

# Run locally
set FLASK_ENV=development
python app.py
```

### Key Configuration Locations

| Setting | File | Variable/Section |
|---------|------|------------------|
| Admin emails | config.py | ADMIN_EMAILS |
| School mappings | config.py | KICKBOARD_SCHOOL_MAP |
| School year start | config.py | CURRENT_SY_START (auto-calculated) |
| School leader titles | config.py | KICKBOARD_SCHOOL_LEADER_TITLES |
| Email aliases | config.py | EMAIL_ALIASES |
| Position Control roles | config.py | POSITION_CONTROL_ROLES |
| Onboarding roles | config.py | ONBOARDING_ROLES |
| SMTP email config | config.py | SMTP_EMAIL, SMTP_PASSWORD (env vars) |
| BigQuery tables | config.py | PROJECT_ID, DATASET_ID, etc. |

---

## Support

For technical issues:
1. Check the troubleshooting section above
2. Review Cloud Run logs for error messages
3. Use Claude Code to help diagnose and fix issues
4. Check GitHub issues or create a new one

For access/permission issues:
- Contact an admin from the admin list in config.py
