# Deploying Supervisor Dashboard to Google Cloud Run

## Prerequisites
- Google Cloud SDK (`gcloud`) installed
- Access to the `talent-demo-482004` GCP project
- Docker installed (optional - Cloud Build can build for you)

## Step 1: Authenticate with Google Cloud

```bash
gcloud auth login
gcloud config set project talent-demo-482004
```

## Step 2: Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## Step 3: Build and Deploy to Cloud Run

From the `bigquery_dashboards` directory, run:

```bash
gcloud run deploy supervisor-dashboard \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "FLASK_DEBUG=false"
```

This command will:
1. Build the Docker image using Cloud Build
2. Push it to Artifact Registry
3. Deploy to Cloud Run

After deployment, you'll get a URL like:
`https://supervisor-dashboard-xxxxx-uc.a.run.app`

## Step 4: Verify Deployment

Test the Cloud Run URL to make sure everything works:
- Visit the URL in your browser
- Select a supervisor and verify data loads

## Step 5: Set Up Custom Domain

### A. In Google Cloud Console:
1. Go to Cloud Run → supervisor-dashboard → Domain Mappings
2. Click "Add Mapping"
3. Select "Add custom domain"
4. Enter: `supervisordashboard.firstlineschools.org`
5. Google will provide DNS records to configure

### B. DNS Configuration:
You'll need someone with access to your DNS (domain registrar or IT department) to add these records:

**Option 1: CNAME Record (Recommended)**
```
Type: CNAME
Host: supervisordashboard
Value: ghs.googlehosted.com
```

**Option 2: A Records (if CNAME doesn't work)**
```
Type: A
Host: supervisordashboard
Values:
  216.239.32.21
  216.239.34.21
  216.239.36.21
  216.239.38.21
```

### C. Verify Domain:
Google may require domain verification. Follow the prompts in Cloud Console.

## Step 6: SSL Certificate

Cloud Run automatically provisions and manages SSL certificates for custom domains.
After DNS propagation (can take up to 48 hours), HTTPS will work automatically.

---

## Updating the Application

To deploy updates after making changes:

```bash
gcloud run deploy supervisor-dashboard \
  --source . \
  --region us-central1
```

## Viewing Logs

```bash
gcloud run logs read supervisor-dashboard --region us-central1
```

## Rolling Back

To roll back to a previous version:

```bash
gcloud run revisions list --service supervisor-dashboard --region us-central1
gcloud run services update-traffic supervisor-dashboard --to-revisions=REVISION_NAME=100 --region us-central1
```

---

## Cost Estimate

Cloud Run pricing is pay-per-use:
- Free tier: 2 million requests/month
- CPU: $0.00002400/vCPU-second
- Memory: $0.00000250/GiB-second

For a school dashboard with ~50-100 users, expect costs well under $10/month.

---

## Troubleshooting

**"Permission denied" errors:**
```bash
gcloud auth application-default login
```

**BigQuery access issues:**
Ensure the Cloud Run service account has BigQuery access:
```bash
gcloud projects add-iam-policy-binding talent-demo-482004 \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

**Domain not resolving:**
- DNS changes can take 24-48 hours to propagate
- Verify records with: `nslookup supervisordashboard.firstlineschools.org`
