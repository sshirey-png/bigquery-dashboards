# FirstLine Schools: Claude Code & BigQuery Setup Guide

## Complete Setup Instructions for Data Dashboards and Web Applications

**Created:** January 2026
**Author:** Scott Shirey / Talent Team
**Last Updated:** February 2026
**Purpose:** Step-by-step guide to replicate our Claude Code + BigQuery + GitHub development environment

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Part 1: Google Cloud Platform (GCP) Setup](#part-1-google-cloud-platform-gcp-setup)
4. [Part 2: BigQuery Configuration](#part-2-bigquery-configuration)
5. [Part 3: Node.js Installation (CLI Only)](#part-3-nodejs-installation-cli-only)
6. [Part 4: Anthropic Account & API Key](#part-4-anthropic-account--api-key)
7. [Part 5: Git Installation & Configuration](#part-5-git-installation--configuration)
8. [Part 6: GitHub Account & Repository](#part-6-github-account--repository)
9. [Part 7: Claude Code Installation](#part-7-claude-code-installation)
10. [Part 8: Running Claude Code](#part-8-running-claude-code)
11. [Part 9: Level Data Grow API Integration](#part-9-level-data-grow-api-integration)
12. [Quick Reference Commands](#quick-reference-commands)
13. [Troubleshooting](#troubleshooting)

---

## Overview

This guide walks you through setting up a complete development environment to:

- **Query and analyze data** in Google BigQuery
- **Build interactive web dashboards** using Claude Code
- **Connect external APIs** (like Level Data Grow) to BigQuery
- **Version control your work** with Git and GitHub
- **Deploy web applications** to Google Cloud Run

**Two Paths to Claude Code:** You can access Claude Code either through the command line (CLI) or through the Claude Desktop app. The CLI offers maximum flexibility and is ideal for developers. The Desktop app provides a friendlier graphical interface and is easier to set up — no terminal experience required. Both options provide the same core capabilities. This guide covers both.

**What You'll Build:**

- BigQuery datasets and views
- Interactive web applications (salary calculators, bonus guides, trackers)
- Automated data pipelines from APIs to BigQuery

---

## Prerequisites

Before starting, ensure you have:

- A computer with Windows 10/11 (or Mac)
- Administrator access to install software
- A Google account (preferably your work email)
- Internet access
- About 2–3 hours for initial setup

---

## Part 1: Google Cloud Platform (GCP) Setup

### Step 1.1: Access Google Cloud Console

1. Open your web browser
2. Go to: **https://console.cloud.google.com**
3. Sign in with your work Google account (e.g., yourname@yourorg.org)

### Step 1.2: Create or Select a Project

1. Look at the **top of the page** for the project selector dropdown
2. Click on it
3. Either:
   - **Select an existing project** if your organization has one, OR
   - Click **"New Project"** to create one

#### If Creating a New Project:

- **Project name:** Something descriptive (e.g., talent-dashboards)
- **Organization:** Select your organization if available
- **Location:** Your organization folder or "No organization"
- Click **"Create"**
- Wait 30 seconds for the project to be created

### Step 1.3: Note Your Project ID

Your **Project ID** is critical — you'll use it everywhere.

1. Click the project selector at the top
2. Look for your project
3. Note the **Project ID** (e.g., talent-demo-482004)
   - This is different from the project name!
   - The ID is usually the name with numbers appended

**Write this down:** Project ID: ________________________

### Step 1.4: Enable Required APIs

1. In the left sidebar, click **"APIs & Services"** → **"Library"**
2. Search for and enable each of these APIs:
   - **BigQuery API** — Click → Enable
   - **BigQuery Storage API** — Click → Enable
   - **Cloud Run API** — Click → Enable (for deploying web apps)
   - **Cloud Build API** — Click → Enable (for deployments)

---

## Part 2: BigQuery Configuration

### Step 2.1: Access BigQuery

1. In Google Cloud Console, click the **search bar** at the top
2. Type **"BigQuery"**
3. Click **"BigQuery"** or **"BigQuery Studio"**

### Step 2.2: Create Your First Dataset

A **dataset** is a container for your tables and views.

1. In the **Explorer panel** (left side), find your project name
2. **Hover over your project name** — three dots (⋮) will appear
3. Click the **three dots**
4. Select **"Create dataset"**

#### Fill out the form:

- **Dataset ID:** talent_grow_observations (or your preferred name)
  - Rules: letters, numbers, underscores only; no spaces
- **Data location:** US (multiple regions in United States)
- **Default table expiration:** Leave blank
- Click **"Create Dataset"**

### Step 2.3: Connect a Google Sheet to BigQuery

To import data from Google Sheets:

1. In Explorer, find your new dataset
2. Click the **three dots** next to it
3. Select **"Create table"**

#### Configure the table:

- **Create table from:** Select **"Drive"**
- **Select Drive URI:** Paste your Google Sheet URL
- **File format:** Select **"Google Sheets"**
- **Sheet range:** Leave blank for entire sheet, or specify like Sheet1!A1:Z1000
- **Table name:** Give it a descriptive name (e.g., observations)
- **Schema:** Check **"Auto detect"**
- Click **"Create Table"**

#### Important: Share Your Sheet

Make sure your Google Sheet is shared with your GCP service account or set to "Anyone with the link can view."

### Step 2.4: Test Your Connection

Run a simple query to verify:

```sql
SELECT *
FROM `your-project-id.your_dataset.your_table`
LIMIT 10
```

Replace with your actual project ID, dataset, and table names.

---

## Part 3: Node.js Installation (CLI Only)

> **Note:** Node.js is only required if you plan to install Claude Code via the CLI (Option A in Part 7). If you plan to use the Claude Desktop app instead (Option B), you can skip this section.

### Step 3.1: Download Node.js

1. Open your browser
2. Go to: **https://nodejs.org**
3. Click the **LTS** button (recommended version)
4. Download the installer (.msi file for Windows)

### Step 3.2: Install Node.js

1. Find the downloaded file (usually in Downloads folder)
2. Double-click the .msi file
3. Click **"Next"** on the welcome screen
4. Accept the license agreement → Next
5. Use default installation location → Next
6. Keep default features → Next
7. Click **"Install"**
8. Wait for installation to complete
9. Click **"Finish"**

### Step 3.3: Verify Installation

1. **Close any open Command Prompt windows**
2. Open a **NEW** Command Prompt:
   - Press Windows + R
   - Type `cmd`
   - Press Enter
3. Run these commands:

```
node --version
```

You should see something like: v20.11.0

```
npm --version
```

You should see something like: 10.2.4

**If you see version numbers, Node.js is installed! ✅**

#### Troubleshooting: "not recognized"

If you see "node is not recognized":

1. Restart your computer
2. Open a new Command Prompt
3. Try again

---

## Part 4: Anthropic Account & API Key

Claude Code needs an Anthropic account to function.

### Step 4.1: Create an Anthropic Account

1. Go to: **https://console.anthropic.com**
2. Click **"Sign Up"** or **"Get Started"**
3. Sign up with your email (work or personal)
4. Verify your email address
5. Complete any required onboarding

### Step 4.2: Choose a Payment Method (Required)

There are two ways to pay for Claude Code:

**Option 1 – Claude Pro or Max Subscription (Recommended):** Subscribe to a Claude Pro ($20/month) or Max plan at claude.ai. This is the simplest option and includes access to Claude Code in both the CLI and the Claude Desktop app. No API key needed — just log in with your Claude account.

**Option 2 – Anthropic Console (Pay-As-You-Go):** Add a credit card in the Anthropic Console under Settings → Billing. API usage is pay-as-you-go (typically $5–20/month for normal use). You'll need an API key for this method (see Step 4.3).

### Step 4.3: Create an API Key (Console Users Only)

> **Skip this step if you're using a Claude Pro or Max subscription.**

1. In the Anthropic Console, click **"API Keys"** in the left menu
2. Click **"+ Create Key"**
3. Give it a name: `Claude Code - Work`
4. Click **"Create Key"**
5. **IMPORTANT:** Copy the key immediately!
   - It starts with `sk-ant-api03-...`
   - You won't be able to see it again!
6. Save this key somewhere secure (password manager, secure note)

**Write this down securely:** API Key: sk-ant-api03-________________________

---

## Part 5: Git Installation & Configuration

Git is version control software that tracks changes to your code.

### Step 5.1: Download Git

1. Go to: **https://git-scm.com/download/win**
2. The download should start automatically
3. If not, click the download link for Windows

### Step 5.2: Install Git

1. Run the downloaded installer
2. Click through the installer:
   - Accept the license
   - Use default installation location
   - Use default components
   - Choose your default editor (Notepad is fine for beginners)
   - Let Git decide the default branch name
   - Git from the command line and 3rd-party software
   - Use bundled OpenSSH
   - Use the OpenSSL library
   - Checkout Windows-style, commit Unix-style line endings
   - Use MinTTY
   - Default pull behavior (fast-forward or merge)
   - Use Git Credential Manager
   - Enable file system caching
   - Click **"Install"**
3. Click **"Finish"**

### Step 5.3: Verify Git Installation

Open a **NEW** Command Prompt and run:

```
git --version
```

You should see something like: git version 2.43.0.windows.1

### Step 5.4: Configure Git Identity

Tell Git who you are (this appears in your commit history):

```
git config --global user.name "Your Name"
git config --global user.email "your.email@yourorg.org"
```

### Step 5.5: Verify Configuration

```
git config --list
```

You should see your name and email in the output.

---

## Part 6: GitHub Account & Repository

GitHub is where your code is stored online.

### Step 6.1: Create a GitHub Account

1. Go to: **https://github.com**
2. Click **"Sign Up"**
3. Enter your email, create a password, choose a username
4. Complete the verification
5. Select the free plan

### Step 6.2: Create a Repository

1. Once logged in, click the **"+"** icon (top right)
2. Select **"New repository"**
3. Fill out:
   - **Repository name:** bigquery_dashboards (or your preferred name)
   - **Description:** "BigQuery dashboards and data tools"
   - **Public** or **Private:** Your choice (Private recommended for work)
   - Check **"Add a README file"**
   - Click **"Create repository"**

### Step 6.3: Clone the Repository to Your Computer

1. On your repository page, click the green **"Code"** button
2. Copy the HTTPS URL (looks like `https://github.com/yourusername/bigquery_dashboards.git`)
3. Open Command Prompt
4. Navigate to where you want the project:

```
cd C:\Users\YourUsername
```

5. Clone the repository:

```
git clone https://github.com/yourusername/bigquery_dashboards.git
```

6. Enter the project folder:

```
cd bigquery_dashboards
```

### Step 6.4: Verify Git Connection

```
git status
```

You should see: `On branch main` and `nothing to commit, working tree clean`

---

## Part 7: Claude Code Installation

Now we install Claude Code itself. There are two ways to access Claude Code: via the command line (CLI) or via the Claude Desktop app. Choose the option that works best for you.

### Option A: Install Claude Code via CLI (Command Line)

This is the original, most flexible way to use Claude Code. It runs in your terminal. The native installer is now the recommended method (npm install is deprecated).

**For Windows (PowerShell):**

```powershell
irm https://claude.ai/install.ps1 | iex
```

**For Mac/Linux:**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

> **Note:** Windows also requires [Git for Windows](https://git-scm.com/download/win) to be installed. The native installer does not require Node.js, but Node.js is still useful for running JavaScript-based projects.

After installation, verify by running:

```
claude --version
```

You should see the Claude Code version number.

### Option B: Use the Claude Desktop App (Easier Setup)

Claude Code is now available directly inside the Claude Desktop app. This is the easiest way to get started — no terminal commands, no Node.js, no npm required. It provides the same core capabilities as the CLI, with a graphical interface and visual session management.

1. Download the Claude Desktop app from **claude.ai/download** for your platform (Windows or Mac)
2. Install and open the app
3. Sign in with your Claude Pro or Max account
4. Click the **"Code"** tab in the app to access Claude Code
5. Point it to your project folder when starting a session

The Desktop app requires a Claude Pro or Max subscription (it does not work with Console API keys alone). It includes features like running multiple sessions in parallel, visual diff viewing, and automatic updates.

---

## Part 8: Running Claude Code

Follow the steps below for whichever installation method you chose in Part 7.

### If Using the CLI (Option A)

#### Step 8.1: Navigate to Your Project

```
cd C:\Users\YourUsername\bigquery_dashboards
```

(Replace with your actual path)

#### Step 8.2: Start Claude Code

```
claude
```

#### Step 8.3: First-Time Authentication

The first time you run Claude Code in the terminal, it will ask for authentication. It may open a browser window for OAuth login, or ask you to paste your API key. If using a Pro/Max subscription, choose the OAuth login option. If using a Console account, paste your API key (starts with `sk-ant-api03-...`).

### If Using Claude Desktop App (Option B)

1. Open the Claude Desktop app and sign in with your Claude Pro or Max account
2. Click the **"Code"** tab at the top of the app
3. Start a new session and point it at your project folder (e.g., your bigquery_dashboards folder)
4. You can now type natural language prompts just like in the CLI. Claude Code can read your files, make edits, and run commands
5. The Desktop app shows real-time diffs as Claude edits files, and you can accept or reject each change

### Step 8.4: Verify Claude Code is Working

Once connected, you'll see a prompt. Try:

```
create a file called test.txt with "Hello from Claude Code!"
```

Claude Code should create the file. Check with:

```
dir
```

You should see test.txt in the list.

### Step 8.5: Exit Claude Code

To exit Claude Code:

- CLI: Type `exit` and press Enter, or press Ctrl + C
- Desktop app: Close the session or the app window

---

## Part 9: Level Data Grow API Integration

This section covers connecting the Level Data Grow (Whetstone) API to BigQuery.

### Step 9.1: Get API Credentials from Level Data Grow

Contact Level Data Grow support to request:

1. **API access** for your organization
2. **Client ID** and **Client Secret**
3. **API documentation**

### Step 9.2: Test API Connection in Postman

1. Download Postman: **https://www.postman.com/downloads/**
2. Install and open Postman
3. Create a new request:
   - **Method:** GET
   - **URL:** `https://grow-api.leveldata.com/external/assignments?type=actionStep`
4. Add Authentication:
   - Go to **Authorization** tab
   - Type: **Bearer Token**
   - Paste your access token
5. Click **Send**
6. Verify you receive JSON data

### Step 9.3: Get a Bearer Token

Tokens expire (usually 24 hours). To get a new one:

1. In Postman, create a POST request to the auth endpoint:
   - **URL:** (Ask Level Data Grow for the exact token endpoint)
   - **Body:** Your client_id and client_secret
2. The response will include an access_token
3. Use this token in your API calls

### Step 9.4: Create the BigQuery Pipeline

Use Claude Code to build the pipeline:

```
Build a Python script to pull Level Data Grow API data into BigQuery.

API Details:
- Endpoint: https://grow-api.leveldata.com/external/assignments?type=actionStep
- Auth: Bearer token in header
- Token: [your token]

BigQuery Details:
- Project: [your-project-id]
- Dataset: talent_grow_observations
- Table name: ldg_action_steps

Requirements:
1. Create the BigQuery table if it doesn't exist
2. Handle pagination (may have thousands of records)
3. Strip HTML from text fields
4. Parse nested objects
5. Add error handling and logging
```

### Step 9.5: Set Up Daily Automation

Once the script works:

1. **For Google Cloud:**
   - Use Cloud Scheduler to trigger the script daily
   - Deploy as a Cloud Function or Cloud Run job

2. **For local automation:**
   - Use Windows Task Scheduler
   - Set it to run daily at a specific time

### Step 9.6: Handle Token Refresh

Since tokens expire, you'll need to either:

- **Manual:** Update the token in your config when it expires
- **Automated:** Create a token refresh script that runs before data pulls

Contact Level Data Grow for the token refresh endpoint details.

---

## Quick Reference Commands

### Opening Command Prompt

Windows + R → type "cmd" → Enter

### Navigate to Project Folder

```
cd C:\Users\YourUsername\bigquery_dashboards
```

### Start Claude Code (CLI)

```
claude
```

Or open the Claude Desktop app → Code tab → select your project folder

### Git Commands

```bash
# Check status
git status

# Stage changes
git add .

# Commit changes
git commit -m "Your message here"

# Push to GitHub
git push

# Pull latest changes
git pull
```

### Node.js Commands

```bash
# Check Node version
node --version

# Check npm version
npm --version

# Install a package globally
npm install -g package-name
```

### BigQuery Commands (in Cloud Shell)

```bash
# Run a query
bq query --use_legacy_sql=false 'SELECT * FROM dataset.table LIMIT 10'

# List datasets
bq ls

# List tables in a dataset
bq ls dataset_name
```

---

## Troubleshooting

### "node is not recognized"

- Restart your computer
- Open a NEW Command Prompt
- If still not working, reinstall Node.js

### "git is not recognized"

- Restart your computer
- Open a NEW Command Prompt
- If still not working, reinstall Git

### Claude Code won't connect

- **CLI:** Check your API key is correct, or try re-authenticating with OAuth
- **Desktop app:** Make sure you are signed in with a Pro or Max subscription
- Verify you have billing set up in Anthropic Console (if using Console)
- Check your internet connection

### BigQuery permission denied

- Make sure you're using the correct project ID
- Check that APIs are enabled
- Verify your Google account has BigQuery access

### Google Sheets not loading to BigQuery

- Ensure the sheet is shared (at least "Anyone with link can view")
- Check the URL is correct
- Try removing `/edit#gid=0` from the end of the URL

### CLI installer or "npm install" fails with permission error

- Run Command Prompt / PowerShell as Administrator:
  - Search for "cmd" or "PowerShell"
  - Right-click → "Run as administrator"
  - Try the install command again

### Git push rejected

- Pull first: `git pull`
- Then try pushing again: `git push`

---

## Next Steps

Once your environment is set up, you can:

1. **Build BigQuery Views** — Create SQL views to summarize your data
2. **Create Web Dashboards** — Use Claude Code to build interactive tools
3. **Connect More Data Sources** — Add APIs, Google Sheets, CSV files
4. **Deploy Applications** — Host your tools on Google Cloud Run

---

## Resources

- **Anthropic Console:** https://console.anthropic.com
- **Claude Desktop Download:** https://claude.ai/download
- **Claude Code Docs:** https://code.claude.com/docs
- **Google Cloud Console:** https://console.cloud.google.com
- **BigQuery Documentation:** https://cloud.google.com/bigquery/docs
- **GitHub Guides:** https://guides.github.com
- **Git Documentation:** https://git-scm.com/doc

---

## Disaster Recovery

If your computer crashes, here's how to get back up and running:

### 1. Install Tools
- **Python 3.12**: python.org
- **Git**: git-scm.com
- **Google Cloud SDK**: cloud.google.com/sdk
- **VS Code** (optional): code.visualstudio.com

### 2. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project talent-demo-482004
```

### 3. Clone Your Projects

**From sshirey-png (original repos):**
```bash
git clone https://github.com/sshirey-png/bigquery-dashboards.git
git clone https://github.com/sshirey-png/sabbatical-program.git
git clone https://github.com/sshirey-png/position-control.git
```

**Or from sshirey-cpc (all in one repo, different branches):**
```bash
git clone -b bigquery-dashboards https://github.com/sshirey-cpc/firstline-schools.git bigquery-dashboards
git clone -b sabbatical-program https://github.com/sshirey-cpc/firstline-schools.git sabbatical-program
git clone -b position-control https://github.com/sshirey-cpc/firstline-schools.git position-control
```

### 4. Install Python Dependencies
```bash
cd bigquery-dashboards && pip install -r requirements.txt
cd ../sabbatical-program && pip install -r requirements.txt
cd ../position-control && pip install -r requirements.txt
```

### 5. You're Back!
- All code is in GitHub
- All data is in BigQuery (unchanged)
- All apps are live on Cloud Run (unchanged)

The only thing you'd lose is local uncommitted changes. Everything else is safely in the cloud.

---

## Support

For questions about this setup:

- **Internal:** Contact the Talent Team
- **Anthropic:** https://support.anthropic.com
- **Google Cloud:** https://cloud.google.com/support
