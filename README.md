# EIOS — AI COO Business Operations Platform

> **"One AI. Your entire business operations."**

EIOS is an enterprise AI Chief Operating Officer platform designed for small and medium businesses. It connects fragmented business data across customers, projects, payments, tasks, and communications into a unified operational intelligence layer.

---

## 🚀 Key Features

* **Operational Intelligence Dashboard**: Executive KPI overview tracking collected revenue, pending receivables, overdue payments aging, delayed projects, and pending approvals. Includes daily AI COO briefings.
* **Natural Language Query Engine**: Execute natural language queries like *"Which customers have pending payments above ₹50,000?"* or *"Which projects are delayed?"* with strict intent classification, entity extraction, and SQL safety validation.
* **Safety & Policy Engine**: Structured intent validation preventing arbitrary LLM database execution. Assigns risk ratings (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
* **Human-in-the-Loop Approval Workflow**: Risk-gated action queue where managers approve or reject high-risk operational dispatches before execution.
* **Excel & CSV Data Connector**: File upload wizard with automatic column header detection, field mapping, data preview, entity matching, and database import history.
* **Immutable Activity Logs**: Traceable, tamper-proof audit trail capturing every AI query, user action, file upload, and execution status transition.
* **Multi-Tenant Architecture**: Complete data isolation enforced at the PostgreSQL/SQLAlchemy ORM layer using `organization_id`.

---

## 🛠️ Tech Stack

### Frontend
* **Framework**: Next.js 14 (App Router) with React & TypeScript
* **Styling**: Vanilla Tailwind CSS with custom SaaS dark visual design system
* **Charts & Icons**: Recharts & Lucide Icons

### Backend
* **API Framework**: FastAPI (Python 3.11+)
* **Database & ORM**: PostgreSQL / SQLite fallback with SQLAlchemy ORM & Alembic
* **Security & Auth**: JWT Bearer token authentication with bcrypt password hashing
* **AI Decision Layer**: Google Gemini API (`GEMINI_API_KEY`) integration with intent engine abstraction

---

## 📁 Monorepo Structure

```
EIOS/
├── frontend/             # Next.js App Router Frontend
│   ├── app/              # Dashboard, AI Assistant, Customers, Projects, Payments, Tasks, etc.
│   ├── components/       # AppLayout, Nav, Headers, Cards
│   ├── lib/              # API Client Utilities
│   └── public/
├── backend/              # FastAPI Backend Architecture
│   ├── app/
│   │   ├── main.py       # FastAPI Entrypoint & CORS
│   │   ├── api/          # Routers (Auth, Dashboard, AI, Customers, Payments, etc.)
│   │   ├── ai/           # AIService & Gemini intent engine
│   │   ├── actions/      # ActionEngine & SafetyEngine
│   │   ├── connectors/   # Excel/CSV parser and connector handlers
│   │   ├── core/         # Config, Database, Security
│   │   ├── models/       # SQLAlchemy Domain ORM Models
│   │   └── schemas/      # Pydantic Schemas
│   └── database/seeds/   # Realistic Seed Data Generator
├── docker-compose.yml    # PostgreSQL + Redis + Backend + Frontend
└── README.md
```

---

## ⚡ Quick Start & Running Locally

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
> The database will automatically initialize and populate with rich demo data (Acme Mfg, Vertex Tech, BlueStone Infra, 20 customers, 30 projects, 50 invoices, overdue payments, and pending approvals) on startup.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔑 Demo Credentials

* **Email**: `admin@eios.ai`
* **Password**: `password123`

---

## 📚 API Documentation

FastAPI automatically serves interactive Swagger documentation at:
* [http://localhost:8000/docs](http://localhost:8000/docs)
* [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🎯 Verification & Demo Scenario

1. **Dashboard Overview**: Sign in to view real-time KPIs, revenue trend chart, project health, and the AI Business Briefing card.
2. **Data Connector Upload**: Navigate to `/data-sources`, upload an Excel `.xlsx` or `.csv` customer list, map column headers, and confirm import.
3. **Ask EIOS AI Assistant**: Go to `/ai-assistant` and ask:
   > *"Which customers have pending payments above ₹50,000?"*
4. **Action & Approvals**: Click `[Prepare Reminders]` on the AI response -> action enters `/approvals` -> Click **Approve** -> check immutable audit log under `/activity-logs`.
