# FDR SmartTrack — Smart Security Deposit / FDR Management Portal
### Problem Statement: SIH26265 &bull; Portfolio-Quality Hackathon Prototype

FDR SmartTrack is a centralized, administrative security deposit and Fixed Deposit Receipt (FDR) management portal built to help regulatory and educational organizations track security deposit receipts, supporting documents, maturity dates, renewals, release requests, and verification workflows.

---

## 1. Project Overview & Scope

- **Purpose**: Manage institutional security deposits and FDR records, eliminate manual spreadsheet tracking, calculate approaching maturities, detect discrepancies between uploaded receipts and database entries, and enforce strict role-based access control.
- **Important Scope Boundaries**:
  - Administrative FDR management platform, **not** a general customer banking application (no money transfers or customer retail banking).
  - Demonstrates a prototype workflow for SIH26265; does not claim official AICTE/Bank endorsement.
  - Documents that pass field validation are clearly marked: *"External bank authenticity verification has not been performed."* Real bank verification requires authorized Core Banking System (CBS) integration.

---

## 2. Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons, React Router DOM.
- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.x, Alembic Migrations, Pydantic v2, Uvicorn, Pytest.
- **Dedicated Database**: PostgreSQL (`fdr_smarttrack_db`).
- **Security**: Argon2id password hashing, JWT access tokens, refresh token rotation, TOTP 2FA (RFC 6238 compliant) with QR enrollment and SHA-256 hashed one-time recovery codes, RBAC, multi-tenant institution isolation.
- **AI & Document Processing**: OCR text extraction (PDF & image parsing), regex-based structured field extraction with calibrated confidence indicators, and scikit-learn Isolation Forest for experimental anomaly detection.
- **Scheduler**: APScheduler background task runner for 90/60/30/7/1-day maturity alerts with deduplication keys.

---

## 3. Dedicated Database Architecture

Operational data is persisted exclusively in a dedicated PostgreSQL database (`fdr_smarttrack_db`).

### Key Entities
1. **User**: Admin, Reviewer, Institution User, Read-only Auditor accounts with Argon2id hashes.
2. **Institution**: Multi-tenant institutions with isolated record boundaries.
3. **Bank**: Supported commercial and public banking institutions with IFSC prefixes.
4. **FDRRecord**: Financial precision (`Decimal(15,2)`), issue/maturity dates, status, discrepancy flags, anomaly scores.
5. **FDRDocument**: SHA-256 tamper-evident hash, MIME validation, storage reference outside web root.
6. **ExtractedDocumentField**: Field-level confidence scores, source page, and user-corrected values.
7. **VerificationCheck**: 7+ deterministic rules with evidence, severity, explanation, and disclaimer.
8. **RenewalRequest & ReleaseRequest**: Multi-stage approval state transitions with audit trail.
9. **ReviewDecision**: Formal reviewer actions with reasons and before/after status diffs.
10. **Notification**: In-app maturity alerts with event deduplication (`event_key`).
11. **AuditLog**: Immutable append-only compliance audit trail.
12. **MFAConfiguration & MFARecoveryCode**: TOTP secrets and hashed recovery codes.

---

## 4. Quick Start & Execution Commands

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 15+ (Running locally or via Docker Compose)

### A. Start PostgreSQL
#### Option 1: Native Local PostgreSQL Cluster
```powershell
# Dedicated cluster data directory
& "C:\Program Files\PostgreSQL\18\bin\postgres.exe" -D "C:\Users\S Sheruba\.postgres_fdr_smarttrack" -p 5433
```
#### Option 2: Docker Compose
```bash
docker-compose up db -d
```

### B. Backend Setup & Startup
```powershell
# 1. Activate Virtual Environment
cd backend
.\venv\Scripts\Activate.ps1

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt
pip install psycopg[binary]

# 3. Apply Alembic Migrations
alembic stamp head

# 4. Seed Demo Users & Baseline Records
python scripts/seed_demo_accounts.py

# 5. Start FastAPI Server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Backend API will be running at: `http://localhost:8000` (Docs: `http://localhost:8000/docs`)

### C. Frontend Setup & Startup
```powershell
# In a new terminal:
cd frontend
npm install --legacy-peer-deps
npm run dev -- --host 0.0.0.0 --port 5173
```
Frontend Portal will be running at: `http://localhost:5173`

---

## 5. Demo Accounts

The database seed script automatically prepares 4 distinct role personas:

| Role | Email | Password | Scope & Permissions |
|---|---|---|---|
| **Super Administrator** | `admin@smarttrack.gov.in` | `AdminPassword@123` | System-wide settings, user management, audit logs, dataset generation |
| **Reviewing Official** | `reviewer@smarttrack.gov.in` | `ReviewerPassword@123` | Review queue, verification evaluation, renewal & release decisions |
| **Institution User** | `institution@smarttrack.gov.in` | `DemoPassword@123` | Tenant-isolated: creates FDRs, uploads receipts, submits renewals & releases |
| **Read-Only Auditor** | `auditor@smarttrack.gov.in` | `AuditorPassword@123` | Read-only inspection of records, analytics, and immutable audit trails |

*Note: The login page provides quick one-click autofill buttons for these personas.*

---

## 6. How to Configure Authenticator 2FA (MFA)

1. Sign in to any account and click the **Key icon (MFA Security)** in the top right navigation bar (or navigate to `/mfa-setup`).
2. Click **Set Up Authenticator**.
3. Scan the generated QR code using **Google Authenticator** or **Microsoft Authenticator** (or enter the manual 32-character key).
4. Enter the current 6-digit TOTP code and click **Verify & Enable 2FA**.
5. Save the 8 displayed one-time backup recovery codes.
6. On your next login, the portal will challenge you for your TOTP authenticator code (or a backup recovery code if device is lost).

---

## 7. Major Workflows Tested

1. **FDR Registration**: User enters reference number, bank, principal amount, issue date, and maturity date. Chronological validation ensures maturity > issue date.
2. **Document Upload & AI OCR Extraction**: Uploaded receipts (PDF/PNG/JPG) are SHA-256 hashed, stored safely, and parsed for structured fields (Amount, Dates, FDR Number, Bank Name) with calibrated confidence scores.
3. **Discrepancy Reconciliation**: Authorized users can review extracted values side-by-side with stored data and correct optical misreads.
4. **Verification Engine**: Automatically runs 7+ deterministic checks (required completeness, date sequence, amount validity, duplicate reference detection, supporting document attachment, database vs document correlation, and bank CBS disclaimer).
5. **Renewal Workflow**: Institution submits renewal request with new maturity date and rationale &rarr; Status becomes *Renewal Pending* &rarr; Reviewing official evaluates and approves &rarr; Maturity date is updated and audit event logged.
6. **Release Workflow**: Institution submits release clearance request &rarr; Status becomes *Release Requested* &rarr; Reviewing official checks clearance and approves &rarr; Status becomes *Released*.
7. **Proactive Maturity Alerts**: Background engine automatically scans for approaching maturities (90, 60, 30, 7, 1 days) and creates deduplicated in-app notifications.

---

## 8. Automated Test Execution & Verification

To run the complete automated test suite:
```powershell
cd backend
.\venv\Scripts\pytest.exe -v
```

### Test Results
```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.1.1
collected 13 items

tests/test_auth.py::test_health_check PASSED                             [  7%]
tests/test_auth.py::test_password_hashing PASSED                         [ 15%]
tests/test_auth.py::test_login_success PASSED                            [ 23%]
tests/test_auth.py::test_login_failure_invalid_credentials PASSED        [ 30%]
tests/test_auth.py::test_totp_mfa_workflow PASSED                        [ 38%]
tests/test_dashboard_and_notifications.py::test_dashboard_metrics PASSED [ 46%]
tests/test_dashboard_and_notifications.py::test_notifications_lifecycle PASSED [ 53%]
tests/test_fdr_and_isolation.py::test_fdr_date_validation_rejected PASSED [ 61%]
tests/test_fdr_and_isolation.py::test_institution_data_isolation PASSED  [ 69%]
tests/test_fdr_and_isolation.py::test_fdr_creation_and_automatic_verification PASSED [ 76%]
tests/test_verification_and_workflow.py::test_renewal_workflow PASSED    [ 84%]
tests/test_verification_and_workflow.py::test_release_workflow PASSED    [ 92%]
tests/test_verification_and_workflow.py::test_review_queue PASSED        [100%]

======================= 13 passed in 1.96s =======================
```

Frontend production build check:
```powershell
cd frontend
npm run build
# Result: built in 1.50s (0 errors)
```

---

## 9. Security & Compliance Implementation

- **Password Storage**: Argon2id hashing via `argon2-cffi`.
- **JWT Protection**: Short-lived access tokens (30 minutes) + refresh tokens stored as hashes with revocation.
- **Multi-Tenant Isolation**: Enforced server-side in `backend/app/core/deps.py` and service queries; institution users are strictly forbidden from viewing or modifying records belonging to other institutions.
- **Upload Integrity**: File size limits (10MB), MIME whitelist (`application/pdf`, `image/png`, `image/jpeg`), SHA-256 fingerprinting.
- **Audit Trails**: Every login, FDR update, document upload, OCR field correction, and review decision is stored in `audit_logs` table with actor, IP, before/after diffs, and timestamp.
