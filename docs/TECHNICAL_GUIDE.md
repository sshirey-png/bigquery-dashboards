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
│   ├── orgchart.py        # Org chart routes
│   └── health.py          # Health check endpoint
├── index.html             # Supervisor Dashboard frontend
├── hr-dashboard.html      # HR Dashboard frontend
├── schools-dashboard.html # Schools Dashboard frontend
├── kickboard-dashboard.html # Kickboard Dashboard frontend
├── orgchart.html          # Org Chart frontend
├── Dockerfile             # Container build instructions
├── requirements.txt       # Python dependencies
└── docs/                  # Documentation
    ├── USER_GUIDE.md
    └── TECHNICAL_GUIDE.md
```

### Key Files Explained

| File | Purpose | When to Edit |
|------|---------|--------------|
| `config.py` | Admin list, school mappings, table names | Adding admins, changing school names |
| `auth.py` | Permission logic | Changing who can access what |
| `blueprints/kickboard.py` | Kickboard API endpoints | Changing Kickboard data/features |
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
   http://localhost:8080
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

2. **Find the `ADMIN_EMAILS` list** (around line 25)

3. **Add the new email:**
   ```python
   ADMIN_EMAILS = [
       'sshirey@firstlineschools.org',
       'brichardson@firstlineschools.org',
       # ... existing emails ...
       'newemail@firstlineschools.org',  # New Person - Title
   ]
   ```

4. **Save the file**

5. **Commit and push:**
   ```bash
   git add config.py
   git commit -m "Add [Name] to admin list"
   git push origin master
   ```

6. **Deploy** (see Section 5)

### Example: Changing the School Year Start Date

1. **Open `config.py`**

2. **Find `CURRENT_SY_START`** (around line 66)

3. **Update the date:**
   ```python
   CURRENT_SY_START = '2026-08-03'  # First day of 2026-27 school year
   ```

4. **Commit, push, and deploy**

---

## 5. Deployment

### Where It Runs
The application runs on **Google Cloud Run** in the `talent-demo-482004` project.

### Deployment Command

From the project directory:
```bash
gcloud run deploy bigquery-dashboards \
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
Service URL: https://bigquery-dashboards-965913991496.us-central1.run.app
```

### Verifying Deployment
1. Open the Service URL
2. Hard refresh (Ctrl+Shift+R) to clear cache
3. Test the feature you changed

### Rolling Back
If something breaks, you can rollback in Google Cloud Console:
1. Go to https://console.cloud.google.com
2. Navigate to Cloud Run → bigquery-dashboards
3. Click "Revisions" tab
4. Select a previous revision → "Manage Traffic" → Route 100% to it

---

## 6. Common Maintenance Tasks

### Adding an Admin User

**File:** `config.py`
**Location:** `ADMIN_EMAILS` list

```python
ADMIN_EMAILS = [
    # ... existing emails ...
    'newadmin@firstlineschools.org',  # Name - Title
]
```

Then commit, push, and deploy.

### Removing an Admin User

Same as above, but remove the line instead of adding.

### Adding a School Leader Title

**File:** `config.py`
**Location:** `KICKBOARD_SCHOOL_LEADER_TITLES` list

```python
KICKBOARD_SCHOOL_LEADER_TITLES = [
    'principal',
    'assistant principal',
    'dean',
    'head of school',
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

### Updating the School Year Date

**File:** `config.py`
**Location:** `CURRENT_SY_START`

```python
CURRENT_SY_START = '2026-08-03'  # Update to new school year start
```

Also update the default dates in `kickboard-dashboard.html` (search for `2025-08-04`).

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
| `is_admin(email)` | Check if user is in admin list |
| `get_kickboard_access(email)` | Determine Kickboard permissions |
| `get_supervisor_name_for_email(email)` | Look up supervisor from email |
| `get_accessible_supervisors(email, name)` | Get list of supervisors user can view |
| `resolve_email_alias(email)` | Map alias emails to primary |

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
  gcloud run logs read bigquery-dashboards --region us-central1
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

## Quick Reference

### Important URLs

| Resource | URL |
|----------|-----|
| Live Application | https://bigquery-dashboards-965913991496.us-central1.run.app |
| GitHub Repository | https://github.com/sshirey-png/bigquery-dashboards |
| Google Cloud Console | https://console.cloud.google.com/run?project=talent-demo-482004 |
| BigQuery Console | https://console.cloud.google.com/bigquery?project=talent-demo-482004 |

### Common Commands

```bash
# Deploy
gcloud run deploy bigquery-dashboards --source . --region us-central1 --allow-unauthenticated

# View logs
gcloud run logs read bigquery-dashboards --region us-central1

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
| School year start | config.py | CURRENT_SY_START |
| School leader titles | config.py | KICKBOARD_SCHOOL_LEADER_TITLES |
| Email aliases | config.py | EMAIL_ALIASES |
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
