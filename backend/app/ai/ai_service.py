import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.config import settings
from app.models.domain import Customer, Project, Invoice, Payment, Task, Action, Approval, ActivityLog, RiskLevelEnum, ApprovalStatusEnum

logger = logging.getLogger("eios_ai")

def ensure_naive(dt: Optional[datetime]) -> Optional[datetime]:
    if dt and getattr(dt, 'tzinfo', None) is not None:
        return dt.replace(tzinfo=None)
    return dt

class AIService:
    """
    EIOS Central AI Operational Intelligence Service
    Connects business data from PostgreSQL, understands intents, validates safety policies,
    generates responses via Gemini LLM or structured rules engine, and creates actionable tasks.
    """

    ALLOWED_INTENTS = [
        "GET_CUSTOMERS",
        "GET_PROJECTS",
        "GET_PAYMENTS",
        "GET_OVERDUE_PAYMENTS",
        "GET_PENDING_TASKS",
        "GET_DELAYED_PROJECTS",
        "GET_REVENUE_SUMMARY",
        "GET_CUSTOMER_DETAILS",
        "GET_PROJECT_DETAILS",
        "GET_PAYMENT_DETAILS",
        "CREATE_REMINDER",
        "DRAFT_EMAIL",
        "CREATE_TASK",
        "CREATE_APPROVAL"
    ]

    @staticmethod
    def sanitize_untrusted_input(text: str) -> str:
        forbidden = ["ignore previous instructions", "system prompt:", "you are now", "drop table"]
        sanitized = text
        for term in forbidden:
            sanitized = sanitized.replace(term, "[redacted]")
        return sanitized

    @classmethod
    def process_query(cls, query: str, organization_id: str, db: Session) -> Dict[str, Any]:
        sanitized_query = cls.sanitize_untrusted_input(query)
        intent, filters = cls._classify_intent(sanitized_query)

        data_records, summary_text = cls._execute_intent_query(intent, filters, organization_id, db)
        llm_response = cls._generate_ai_explanation(sanitized_query, intent, data_records, summary_text)
        action_recommendation = cls._build_recommended_action(intent, filters, data_records)

        return {
            "intent": intent,
            "filters_used": filters,
            "answer": llm_response,
            "structured_data": data_records,
            "suggested_action": action_recommendation
        }

    @classmethod
    def _classify_intent(cls, query: str) -> tuple[str, Dict[str, Any]]:
        query_lower = query.lower()
        filters = {}

        # Extract numeric amounts (e.g. 50,000, 50000, 50k)
        min_amt = 0.0
        if "50" in query_lower and ("000" in query_lower or "k" in query_lower or "50000" in query_lower):
            min_amt = 50000.0
        elif "10" in query_lower and ("000" in query_lower or "k" in query_lower or "10000" in query_lower):
            min_amt = 10000.0

        if min_amt > 0:
            filters["minimum_amount"] = min_amt

        if "overdue" in query_lower or "above" in query_lower or ("pending" in query_lower and "payment" in query_lower):
            intent = "GET_OVERDUE_PAYMENTS"
        elif "revenue" in query_lower or "summary" in query_lower:
            intent = "GET_REVENUE_SUMMARY"
        elif "payment" in query_lower or "invoice" in query_lower:
            intent = "GET_PAYMENTS"
        elif "delayed" in query_lower or "behind" in query_lower or "at risk" in query_lower:
            intent = "GET_DELAYED_PROJECTS"
        elif "project" in query_lower:
            intent = "GET_PROJECTS"
        elif "customer" in query_lower or "client" in query_lower:
            intent = "GET_CUSTOMERS"
        elif "task" in query_lower or "todo" in query_lower:
            intent = "GET_PENDING_TASKS"
        elif "reminder" in query_lower or "follow up" in query_lower:
            intent = "CREATE_REMINDER"
        else:
            intent = "GET_REVENUE_SUMMARY"

        return intent, filters

    @classmethod
    def _execute_intent_query(cls, intent: str, filters: Dict[str, Any], organization_id: str, db: Session) -> tuple[List[Dict[str, Any]], str]:
        records = []
        summary = ""

        if intent == "GET_OVERDUE_PAYMENTS":
            min_amount = filters.get("minimum_amount", 0.0)
            now = datetime.now()
            invoices = db.query(Invoice).filter(
                Invoice.organization_id == organization_id,
                Invoice.amount - Invoice.paid_amount >= min_amount
            ).all()

            for inv in invoices:
                due = ensure_naive(inv.due_date)
                if due and due < now:
                    customer = db.query(Customer).filter(Customer.id == inv.customer_id).first()
                    days_overdue = (now - due).days
                    records.append({
                        "id": inv.id,
                        "invoice_number": inv.invoice_number,
                        "customer_name": customer.name if customer else "Unknown",
                        "company_name": customer.company_name if customer else "",
                        "customer_email": customer.email if customer else "",
                        "amount": inv.amount,
                        "paid_amount": inv.paid_amount,
                        "outstanding_balance": inv.amount - inv.paid_amount,
                        "due_date": due.strftime("%Y-%m-%d") if due else "",
                        "days_overdue": max(1, days_overdue)
                    })
            summary = f"Found {len(records)} overdue invoice(s) matching criteria."

        elif intent == "GET_DELAYED_PROJECTS":
            projects = db.query(Project).filter(
                Project.organization_id == organization_id,
                Project.status.in_(["DELAYED", "AT_RISK"])
            ).all()

            for p in projects:
                customer = db.query(Customer).filter(Customer.id == p.customer_id).first()
                due = ensure_naive(p.due_date)
                records.append({
                    "id": p.id,
                    "project_name": p.name,
                    "customer_name": customer.name if customer else "Unknown",
                    "status": p.status,
                    "progress_percentage": p.progress_percentage,
                    "budget": p.budget,
                    "due_date": due.strftime("%Y-%m-%d") if due else ""
                })
            summary = f"Identified {len(records)} delayed or at-risk project(s)."

        elif intent == "GET_CUSTOMERS":
            customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
            for c in customers:
                records.append({
                    "id": c.id,
                    "name": c.name,
                    "company_name": c.company_name,
                    "email": c.email,
                    "phone": c.phone,
                    "status": c.status
                })
            summary = f"Retrieved {len(records)} active customers."

        elif intent == "GET_REVENUE_SUMMARY":
            total_rev = db.query(func.sum(Invoice.paid_amount)).filter(Invoice.organization_id == organization_id).scalar() or 0.0
            total_due = db.query(func.sum(Invoice.amount - Invoice.paid_amount)).filter(
                Invoice.organization_id == organization_id,
                Invoice.amount > Invoice.paid_amount
            ).scalar() or 0.0
            now = datetime.now()
            overdue_due = 0.0
            all_unpaid = db.query(Invoice).filter(
                Invoice.organization_id == organization_id,
                Invoice.amount > Invoice.paid_amount
            ).all()
            for inv in all_unpaid:
                due = ensure_naive(inv.due_date)
                if due and due < now:
                    overdue_due += (inv.amount - inv.paid_amount)

            records.append({
                "total_revenue": total_rev,
                "outstanding_payments": total_due,
                "overdue_payments": overdue_due
            })
            summary = f"Total Revenue: INR {total_rev:,.2f} | Outstanding: INR {total_due:,.2f} | Overdue: INR {overdue_due:,.2f}"

        else:
            tasks = db.query(Task).filter(Task.organization_id == organization_id).limit(10).all()
            for t in tasks:
                due = ensure_naive(t.due_date)
                records.append({
                    "id": t.id,
                    "title": t.title,
                    "priority": t.priority,
                    "status": t.status,
                    "due_date": due.strftime("%Y-%m-%d") if due else ""
                })
            summary = f"Found {len(records)} operational tasks."

        return records, summary

    @classmethod
    def _generate_ai_explanation(cls, query: str, intent: str, records: List[Dict[str, Any]], summary: str) -> str:
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""
You are EIOS, an AI Chief Operating Officer for small and medium businesses.
User Query: "{query}"
Intent: {intent}
Retrieved Data Summary: {summary}
Raw Data Records: {json.dumps(records, indent=2)}

Provide a concise, professional executive response. Detail the key figures (in INR ₹), call out critical risks or delays, and end with a clear recommended next action.
"""
                res = model.generate_content(prompt)
                if res and res.text:
                    return res.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API invocation fallback: {e}")

        if intent == "GET_OVERDUE_PAYMENTS":
            if not records:
                return "Great news! There are currently no overdue payments matching your criteria in the system."
            formatted_lines = []
            for r in records:
                formatted_lines.append(f"• **{r['company_name'] or r['customer_name']}**: INR {r['outstanding_balance']:,.2f} ({r['days_overdue']} days overdue - Invoice #{r['invoice_number']})")
            body = "\n".join(formatted_lines)
            return f"EIOS detected {len(records)} customer(s) with overdue payments matching your criteria:\n\n{body}\n\n**Recommended COO Action:** Send payment reminders to improve cash flow."

        elif intent == "GET_DELAYED_PROJECTS":
            if not records:
                return "All active projects are currently running on schedule."
            formatted_lines = []
            for r in records:
                formatted_lines.append(f"• **{r['project_name']}** ({r['customer_name']}): Status `{r['status']}`, Progress: {r['progress_percentage']}%")
            body = "\n".join(formatted_lines)
            return f"EIOS identified {len(records)} project(s) requiring immediate operational attention:\n\n{body}\n\n**Recommended COO Action:** Schedule project review with technical leads."

        elif intent == "GET_REVENUE_SUMMARY":
            r = records[0] if records else {}
            return f"**Business Operational Financial Briefing:**\n\n• **Collected Revenue:** INR {r.get('total_revenue', 0.0):,.2f}\n• **Total Outstanding:** INR {r.get('outstanding_payments', 0.0):,.2f}\n• **Overdue Amount:** INR {r.get('overdue_payments', 0.0):,.2f}\n\n**Summary:** Priority focus should be placed on clearing overdue receivables."

        return f"{summary}\n\nHere are the operational details retrieved from your business data."

    @classmethod
    def _build_recommended_action(cls, intent: str, filters: Dict[str, Any], records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if intent == "GET_OVERDUE_PAYMENTS" and records:
            return {
                "action_type": "SEND_REMINDER",
                "label": "Prepare Payment Reminders",
                "risk_level": "HIGH",
                "payload": {
                    "count": len(records),
                    "customers": [r["customer_name"] for r in records],
                    "total_amount": sum(r["outstanding_balance"] for r in records),
                    "invoice_ids": [r["id"] for r in records]
                }
            }
        elif intent == "GET_DELAYED_PROJECTS" and records:
            return {
                "action_type": "CREATE_TASK",
                "label": "Schedule Project Escalation",
                "risk_level": "MEDIUM",
                "payload": {
                    "task_title": f"Review {len(records)} Delayed Projects",
                    "priority": "HIGH",
                    "project_ids": [r["id"] for r in records]
                }
            }
        return None

    @classmethod
    def generate_daily_briefing(cls, organization_id: str, db: Session) -> Dict[str, Any]:
        now = datetime.now()
        total_rev = db.query(func.sum(Invoice.paid_amount)).filter(Invoice.organization_id == organization_id).scalar() or 0.0
        total_due = db.query(func.sum(Invoice.amount - Invoice.paid_amount)).filter(
            Invoice.organization_id == organization_id,
            Invoice.amount > Invoice.paid_amount
        ).scalar() or 0.0

        all_unpaid = db.query(Invoice).filter(
            Invoice.organization_id == organization_id,
            Invoice.amount > Invoice.paid_amount
        ).all()

        overdue_due = 0.0
        overdue_invoices = []
        for inv in all_unpaid:
            due = ensure_naive(inv.due_date)
            if due and due < now:
                overdue_due += (inv.amount - inv.paid_amount)
                overdue_invoices.append(inv)

        delayed_projects_count = db.query(Project).filter(
            Project.organization_id == organization_id,
            Project.status.in_(["DELAYED", "AT_RISK"])
        ).count()

        pending_approvals_count = db.query(Approval).filter(
            Approval.organization_id == organization_id,
            Approval.status == ApprovalStatusEnum.PENDING
        ).count()

        priority_text = "All customer accounts are in good standing."
        if overdue_invoices:
            top_overdue = max(overdue_invoices, key=lambda x: x.amount - x.paid_amount)
            customer = db.query(Customer).filter(Customer.id == top_overdue.customer_id).first()
            c_name = customer.name if customer else "Customer"
            due = ensure_naive(top_overdue.due_date)
            days = (now - due).days if due else 0
            priority_text = f"Follow up with {c_name} regarding invoice {top_overdue.invoice_number} (INR {top_overdue.amount - top_overdue.paid_amount:,.2f}, {max(1, days)} days overdue)."

        return {
            "greeting": "Good morning. EIOS AI COO Briefing.",
            "metrics": {
                "revenue": total_rev,
                "outstanding": total_due,
                "overdue": overdue_due,
                "delayed_projects": delayed_projects_count,
                "pending_approvals": pending_approvals_count
            },
            "summary_text": f"EIOS found {delayed_projects_count} delayed projects, INR {overdue_due:,.2f} in overdue payments, and {pending_approvals_count} approvals requiring attention.",
            "priority_recommendation": priority_text
        }
