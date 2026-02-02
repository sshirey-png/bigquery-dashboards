# Sabbatical Program Application System - Implementation Plan

## Overview
A web-based sabbatical application system honoring long-tenured employees (10+ years) with a professional, celebratory design. The system supports multiple user roles with distinct views and a two-stage approval workflow (Talent → HR).

---

## 1. Repository Setup

Create new repository: `sabbatical-program`
- Separate from bigquery_dashboards
- Follow same Flask patterns for consistency
- Deploy to GCS as static site + Cloud Run for API

---

## 2. BigQuery Tables

### Table: `sabbatical_applications`
```sql
CREATE TABLE `talent-demo-482004.sabbatical.applications` (
  application_id STRING,           -- UUID
  employee_name_key STRING,        -- Links to staff_master_list
  employee_name STRING,
  employee_email STRING,
  hire_date DATE,
  years_of_service FLOAT64,
  job_title STRING,
  department STRING,
  site STRING,

  -- Application Details
  requested_start_date DATE,
  requested_end_date DATE,
  duration_weeks INT64,
  sabbatical_purpose STRING,       -- What they plan to do

  -- Status & Workflow
  status STRING,                   -- 'pending_talent', 'pending_hr', 'approved', 'denied', 'withdrawn'
  submitted_at TIMESTAMP,

  -- Talent Review
  talent_reviewer STRING,
  talent_decision STRING,          -- 'approved', 'denied', 'needs_info'
  talent_notes STRING,
  talent_reviewed_at TIMESTAMP,

  -- HR Review
  hr_reviewer STRING,
  hr_decision STRING,
  hr_notes STRING,
  hr_reviewed_at TIMESTAMP,

  -- Metadata
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Table: `sabbatical_approval_history`
```sql
CREATE TABLE `talent-demo-482004.sabbatical.approval_history` (
  history_id STRING,
  application_id STRING,
  action STRING,                   -- 'submitted', 'talent_approved', 'talent_denied', 'hr_approved', 'hr_denied', 'withdrawn'
  actor_email STRING,
  actor_name STRING,
  notes STRING,
  created_at TIMESTAMP
);
```

### Table: `sabbatical_notifications_log`
```sql
CREATE TABLE `talent-demo-482004.sabbatical.notifications_log` (
  notification_id STRING,
  application_id STRING,
  recipient_email STRING,
  notification_type STRING,        -- 'submission_confirmation', 'pending_review', 'approved', 'denied'
  sent_at TIMESTAMP,
  status STRING                    -- 'sent', 'failed'
);
```

---

## 3. Flask Backend Structure

### File Structure
```
sabbatical-program/
├── app.py                    # Main Flask application
├── requirements.txt
├── templates/
│   └── index.html           # Single-page app with role-based views
├── static/
│   ├── styles.css           # Celebratory, professional styling
│   └── app.js               # Frontend logic
└── deploy.py                # GCS deployment script
```

### API Endpoints

| Endpoint | Method | Description | Access |
|----------|--------|-------------|--------|
| `/api/employee-lookup` | GET | Fetch employee data by email | All |
| `/api/eligibility-check` | GET | Check 10-year eligibility | All |
| `/api/applications` | GET | List applications (filtered by role) | All |
| `/api/applications` | POST | Submit new application | Staff |
| `/api/applications/<id>` | GET | Get application details | All |
| `/api/applications/<id>/review` | POST | Submit Talent/HR review | Talent/HR |
| `/api/applications/<id>/withdraw` | POST | Withdraw application | Staff |
| `/api/site-conflicts` | GET | Check for date/site conflicts | Talent/HR |
| `/api/duplicate-check` | GET | Check for existing applications | All |

### Authentication
- Google OAuth (same pattern as supervisor-dashboard)
- Role detection from staff_master_list (Talent Team, HR Team, etc.)
- Demo mode toggle for testing

---

## 4. Frontend Views

### 4.1 Staff View (Default)
- **My Applications**: List of submitted applications with status
- **New Application** button (if eligible)
- Application form with:
  - Auto-populated employee info (from BigQuery lookup)
  - Date pickers for start/end dates
  - Purpose/plans text area
  - Eligibility indicator (green checkmark if 10+ years)
- Status tracking with timeline visualization

### 4.2 Talent View
- **Pending Reviews**: Applications awaiting Talent approval
- **All Applications**: Full list with filters
- Review panel:
  - Employee details & history
  - Site conflict warnings
  - Approve/Deny/Request Info buttons
  - Notes field

### 4.3 HR View
- **Pending Final Approval**: Applications approved by Talent
- **All Applications**: Full list with filters
- Same review panel as Talent
- Final approval authority

### 4.4 Director View
- **Team Applications**: Applications from their direct/indirect reports
- Read-only status view
- No approval actions

---

## 5. Key Features

### Eligibility Validation
```python
def check_eligibility(employee_email):
    # Query staff_master_list for hire_date
    # Calculate years of service
    # Return eligible: True/False, years: X.X
```

### Duplicate Detection
```python
def check_duplicates(employee_name_key):
    # Check for pending/approved applications
    # Return warning if exists
```

### Site Conflict Detection
```python
def check_site_conflicts(site, start_date, end_date):
    # Query approved sabbaticals at same site
    # Return list of conflicts with dates
```

### Notification System
- Email notifications via SendGrid or similar
- Triggers: submission, approval, denial, reminders

---

## 6. UI/UX Design

### Color Palette (Celebratory)
- Primary: Deep purple (#6B46C1) - represents achievement
- Accent: Gold (#D4AF37) - celebration
- Success: Emerald (#10B981)
- Background: Warm cream (#FFFBEB)

### Design Elements
- Confetti animation on approval
- Years-of-service badge prominently displayed
- Timeline visualization for application progress
- Professional card layouts
- Mobile-responsive design

---

## 7. Implementation Order

### Phase 1: Foundation
1. Create repository and basic Flask structure
2. Set up BigQuery tables
3. Implement OAuth authentication
4. Create employee lookup API

### Phase 2: Application Flow
5. Build application form with validations
6. Implement eligibility check
7. Create submission endpoint
8. Build staff view with application list

### Phase 3: Review Workflow
9. Implement Talent review view and API
10. Implement HR review view and API
11. Add approval history tracking
12. Implement site conflict detection

### Phase 4: Polish
13. Add Director read-only view
14. Implement notification system
15. Add celebratory UI elements
16. Mobile responsiveness
17. Deploy to GCS/Cloud Run

---

## 8. Data Integration

### Staff Master List Query
```sql
SELECT
  name_key,
  First_Name,
  Last_Name,
  CONCAT(First_Name, ' ', Last_Name) as full_name,
  Email,
  Hire_Date,
  DATE_DIFF(CURRENT_DATE(), Hire_Date, DAY) / 365.25 as years_of_service,
  Job_Title,
  Function as department,
  Site
FROM `talent-demo-482004.talent_grow_observations.staff_master_list_with_function`
WHERE Email = @email
```

---

## Summary

This plan creates a complete sabbatical application system that:
- Honors employees with 10+ years of service
- Provides clear workflow: Staff → Talent → HR
- Includes all validation (eligibility, duplicates, conflicts)
- Features a celebratory, professional design
- Supports all required user roles
- Integrates with existing BigQuery staff data
