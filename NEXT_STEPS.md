# Next Steps - Supervisor Dashboard

## Current Status: ✓ LIVE & BRANDED

**Live URL:** https://supervisor-dashboard-965913991496.us-central1.run.app

### What's Working:
- ✓ Flask backend with BigQuery integration
- ✓ Native BigQuery tables with hourly refresh
- ✓ FirstLine Schools branding (logo, colors, fonts)
- ✓ Supervisor selection and team view
- ✓ Staff list with PMAP status, time off, NPS scores
- ✓ Color-coded alerts (red/yellow/green)
- ✓ Search and filtering (All Staff / With Alerts / Action Needed)
- ✓ Detail view modal
- ✓ Employment Status display (Active, Leave of Absence)
- ✓ Responsive design (desktop + mobile)

---

## Potential Future Enhancements

### High Priority
1. ~~**Authentication** - Add Google OAuth or SSO to restrict access~~ ✓ DONE
2. **Custom Domain** - Set up supervisordashboard.firstlineschools.org (waiting on IT for DNS)

### Medium Priority
3. **Export to CSV/Excel** - Allow supervisors to download their team data
4. **Email Notifications** - Alert supervisors when staff need action
5. **Historical Trends** - Show observation counts over time
6. **Bulk Actions** - Mark multiple items as reviewed

### Nice to Have
7. **Dark Mode** - Toggle for dark theme
8. **Print View** - Optimized layout for printing
9. **Dashboard Widgets** - Customizable stat cards
10. **Mobile App** - Progressive Web App (PWA) support

---

## Technical Notes

### Deployment
Due to Windows timestamp issues with gcloud, deploy using a temp directory:
```bash
# 1. Copy files to temp dir with fresh timestamps
# 2. Deploy from temp dir
# 3. Clean up temp dir
```

### Scheduled Queries
5 scheduled queries run hourly in BigQuery Console to refresh native tables from source Google Sheets.

### Key Files
- `app.py` - Flask backend
- `index.html` - Frontend (single-page app)
- `Dockerfile` - Cloud Run container config
- `requirements.txt` - Python dependencies

---

## Session Log

### January 17, 2026
- Converted external tables to native BigQuery tables
- Set up hourly scheduled refresh queries
- Added Leave of Absence employees to dashboard
- Redesigned UI with FirstLine Schools branding
- Fixed logo display

---

**Last Updated:** January 17, 2026
