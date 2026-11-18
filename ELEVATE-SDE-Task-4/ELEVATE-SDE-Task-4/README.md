# ELEVATE-SDE-Task-4 — CredVault Full Stack Platform

This project implements the uploaded Task 4 PDF: connect citizen pages to backend APIs and a database. It supports certificate requests, application tracking, certificate verification, admin login, application approval/rejection, certificate issuance, and revocation.

## Requirements
- Python 3.10+
- VS Code (recommended)

## Run on Windows
1. Extract the ZIP and open this folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create a virtual environment:
   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   If activation is blocked:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```
4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
6. Open `.env`. Local demo login is username `admin`, password `ChangeMe123!`. Change these before public deployment.
7. Start the app:
   ```powershell
   python app.py
   ```
8. Open **http://127.0.0.1:5000**. Do not use Live Server; Flask serves the pages and API.
9. Stop the server with **Ctrl+C** in the terminal.

## Test the full workflow
1. Request page: submit applicant details and save the returned Application ID.
2. Track page: enter the ID and confirm status is Pending.
3. Admin portal: log in using credentials in `.env`.
4. Applications: approve a pending request. The system generates a Certificate ID. Or reject it.
5. Certificates: view issued certificates.
6. Verify page: enter Certificate ID; status should show Valid.
7. Admin Certificates: revoke it.
8. Verify again; status should now show Revoked.

The SQLite database `crevault.db` is created automatically on first run and stores all records. No preloaded dummy application/certificate records are used.

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/applications` | Submit certificate request |
| GET | `/api/applications/track/<applicationId>` | Track request |
| GET | `/api/certificates/verify/<certificateId>` | Verify certificate |
| POST | `/api/admin/login` | Admin login |
| POST | `/api/admin/logout` | Admin logout |
| GET | `/api/admin/me` | Current admin session |
| GET | `/api/admin/applications` | List applications (protected) |
| PATCH | `/api/admin/applications/<applicationId>/approve` | Approve and issue certificate |
| PATCH | `/api/admin/applications/<applicationId>/reject` | Reject application |
| GET | `/api/admin/certificates` | List certificates (protected) |
| PATCH | `/api/admin/certificates/<certificateId>/revoke` | Revoke certificate |

## Database
- `admins`: admin username and hashed password.
- `applications`: applicationId, name, phone, gender, city, state, status, submittedAt.
- `certificates`: certificateId, applicationId, issuedOn, status.

## Push to GitHub
Create a public repository named exactly `ELEVATE-SDE-Task-4`. From this folder run:
```bash
git init
git add .
git commit -m "Complete CredVault full stack certificate platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ELEVATE-SDE-Task-4.git
git push -u origin main
```
Replace `YOUR_USERNAME` with your GitHub username. `.gitignore` excludes `.env`, the virtual environment, and the local database.

## Screenshots / video required by the task
The PDF requires screenshots or a screen-recorded video of the entire website. After testing, create a `screenshots` folder and add your own captures:
1. Home page
2. Successful request showing Application ID
3. Track page showing Pending
4. Admin login
5. Applications dashboard
6. Approval success showing Certificate ID
7. Certificates dashboard
8. Verification showing Valid
9. Verification showing Revoked

Add them here, for example:
```markdown
![Home](screenshots/01-home.png)
![Request success](screenshots/02-request.png)
![Tracking](screenshots/03-track.png)
```
Add your real demo-video link under a `Demo video` heading. Do not submit placeholder screenshots as if they were real.

## Important
This is a local development implementation. Before production deployment use HTTPS, a strong random secret key, a strong admin password, secure cookie settings, backups, and rate limiting. The Task 4 PDF describes connecting your own Task 2 and Task 3 work; this ZIP is a self-contained implementation of the same specified workflow and API contract. You can merge your earlier design into `templates/` and `static/` if required.
