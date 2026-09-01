# EIOS — AI COO Business Operations Platform

> **"One AI. Your entire business operations."**

EIOS is an enterprise AI Chief Operating Officer platform designed for small and medium businesses. It connects fragmented business data across customers, projects, payments, tasks, and communications into a unified operational intelligence layer.

---

## 🚀 Key Features

* **Operational Intelligence Dashboard**: Executive KPI overview tracking collected revenue, pending receivables, overdue payments aging, delayed projects, and pending approvals. Includes daily AI COO briefings.
* **Natural Language Query Engine**: Execute natural language queries like *"Which customers have pending payments above ₹50,000?"* or *"Which projects are delayed?"* with strict intent classification, entity extraction, and SQL safety validation.
* **Safety & Policy Engine**: Structured intent validation preventing arbitrary LLM database execution. Assigns risk ratings (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
* **Human-in-the-Loop Approval Workflow**: Risk-gated action queue where managers approve or reject high-risk operational dispatches before execution.
* **Gmail Business OAuth 2.0 Integration**: Sync customer email threads, extract senders, match against customer database, and store communication logs safely.
* **WhatsApp Business Cloud API Connector**: Official Meta Cloud API connector for incoming webhook events, phone number normalization, customer matching, and outbound messaging with delivery confirmation.
* **Excel & CSV Data Connector**: File upload wizard with automatic column header detection, field mapping, data preview, entity matching, and database import history.
* **Immutable Activity Logs**: Traceable, tamper-proof audit trail capturing every AI query, user action, file upload, and execution status transition.
* **Multi-Tenant Architecture**: Complete data isolation enforced at the database layer using `organization_id`.

---

## 🛠️ Tech Stack

### Frontend
* **Framework**: Next.js 14 (App Router) with React & TypeScript
* **Styling**: Vanilla Tailwind CSS with custom SaaS dark visual design system
* **Charts & Icons**: Recharts & Lucide Icons

### Backend
* **API Framework**: FastAPI (Python 3.11+)
* **Database & ORM**: PostgreSQL (Production) / SQLite fallback (Development) with SQLAlchemy ORM
* **Security & Auth**: JWT Bearer token authentication with salted password hashing
* **AI Decision Layer**: Google Gemini API (`GEMINI_API_KEY`) integration with intent engine abstraction

---

## 📁 Monorepo Structure

```
EIOS/
├── frontend/             # Next.js App Router Frontend
│   ├── app/              # Dashboard, AI Assistant, Customers, Projects, Payments, Tasks, etc.
│   ├── components/       # AppLayout, Nav, Headers, Cards
│   ├── lib/              # API Client Utilities
│   ├── Dockerfile        # Next.js Production Dockerfile
│   └── .env.example
├── backend/              # FastAPI Backend Architecture
│   ├── app/
│   │   ├── main.py       # FastAPI Entrypoint & CORS
│   │   ├── api/          # Routers (Auth, Dashboard, AI, Customers, Payments, Connectors, etc.)
│   │   ├── ai/           # AIService & Gemini intent engine
│   │   ├── actions/      # ActionEngine & SafetyEngine
│   │   ├── connectors/   # Gmail, WhatsApp, and Excel connector handlers
│   │   ├── core/         # Config, Database, Security
│   │   ├── models/       # SQLAlchemy Domain ORM Models
│   │   └── schemas/      # Pydantic Schemas
│   ├── database/seeds/   # Realistic Seed Data Generator
│   ├── Dockerfile        # FastAPI Production Dockerfile
│   └── .env.example
├── docker-compose.yml    # Development Docker Compose
├── docker-compose.production.yml # Production Docker Compose
└── README.md
```

---

## ⚡ Quick Start & Local Development

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run FastAPI Dev Server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser. Login with `admin@eios.ai` / `password123`.

---

## 🌐 Production Deployment Guide

### 1. Requirements
* Docker & Docker Compose (or Node.js 20+ & Python 3.11+)
* PostgreSQL 14+ database instance
* SSL Certificates / Domain for HTTPS (`https://YOUR-BACKEND-DOMAIN` & `https://YOUR-FRONTEND-DOMAIN`)

### 2. Environment Variables

Create environment configuration files using provided templates:

**Backend (`backend/.env`)**:
```env
ENVIRONMENT="production"
PROJECT_NAME="EIOS AI COO"
SECRET_KEY="replace_with_a_secure_random_32_byte_secret_key_in_production"
DATABASE_URL="postgresql://user:password@postgresql-host:5432/eios_db"
FRONTEND_URL="https://YOUR-FRONTEND-DOMAIN"
CORS_ORIGINS="https://YOUR-FRONTEND-DOMAIN"
GEMINI_API_KEY="your_production_gemini_key"
GOOGLE_CLIENT_ID="your_google_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your_google_client_secret"
GOOGLE_REDIRECT_URI="https://YOUR-BACKEND-DOMAIN/api/v1/connectors/gmail/callback"
WHATSAPP_ACCESS_TOKEN="your_meta_permanent_access_token"
WHATSAPP_PHONE_NUMBER_ID="your_meta_phone_number_id"
WHATSAPP_BUSINESS_ACCOUNT_ID="your_meta_business_account_id"
WHATSAPP_VERIFY_TOKEN="your_custom_webhook_verify_token"
```

**Frontend (`frontend/.env.local`)**:
```env
NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-DOMAIN
```

### 3. Database Setup (PostgreSQL)
Ensure your PostgreSQL database is reachable via `DATABASE_URL`. Tables will automatically be initialized on backend startup via SQLAlchemy. Automatic seed data execution is disabled when `ENVIRONMENT="production"`.

### 4. Containerized Production Deployment
Deploy using `docker-compose.production.yml`:
```bash
docker compose -f docker-compose.production.yml up -d --build
```

### 5. Google Gmail OAuth Configuration
In [Google Cloud Console](https://console.cloud.google.com/):
1. Add `https://YOUR-BACKEND-DOMAIN/api/v1/connectors/gmail/callback` under **Authorized redirect URIs**.
2. Add your frontend domain `https://YOUR-FRONTEND-DOMAIN` under **Authorized JavaScript origins**.

### 6. Meta WhatsApp Webhook Configuration
In [Meta for Developers Console](https://developers.facebook.com/):
1. Set **Callback URL** to `https://YOUR-BACKEND-DOMAIN/api/v1/connectors/whatsapp/webhook`.
2. Set **Verify Token** to your configured `WHATSAPP_VERIFY_TOKEN`.
3. Subscribe to the `messages` webhook field.

### 7. Health & Readiness Checks
- **App Health**: `GET https://YOUR-BACKEND-DOMAIN/health` -> `{"status": "ok"}`
- **Database Readiness**: `GET https://YOUR-BACKEND-DOMAIN/health/db` -> `{"status": "ok", "database": "connected"}`

### 8. Production Troubleshooting
- **CORS Errors**: Verify `CORS_ORIGINS` in backend matches the exact origin of your frontend (`https://YOUR-FRONTEND-DOMAIN`).
- **Database Connection Failed**: Ensure `DATABASE_URL` format starts with `postgresql://` and port 5432 is open.
- **Gmail Redirect Mismatch**: Ensure `GOOGLE_REDIRECT_URI` exactly matches the URI registered in Google Cloud Console.
