from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.core.database import get_db
from app.models.domain import Organization, Customer, Project, Invoice, Payment, Task, Approval, ActivityLog, ApprovalStatusEnum
from app.api.auth import get_current_organization
from app.ai.ai_service import AIService, ensure_naive

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    now = datetime.now()
    org_id = org.id

    total_revenue = db.query(func.sum(Invoice.paid_amount)).filter(Invoice.organization_id == org_id).scalar() or 0.0
    pending_payments = db.query(func.sum(Invoice.amount - Invoice.paid_amount)).filter(
        Invoice.organization_id == org_id,
        Invoice.amount > Invoice.paid_amount
    ).scalar() or 0.0

    all_unpaid = db.query(Invoice).filter(
        Invoice.organization_id == org_id,
        Invoice.amount > Invoice.paid_amount
    ).all()

    overdue_payments = 0.0
    for inv in all_unpaid:
        due = ensure_naive(inv.due_date)
        if due and due < now:
            overdue_payments += (inv.amount - inv.paid_amount)

    active_projects = db.query(Project).filter(
        Project.organization_id == org_id,
        Project.status.in_(["PLANNED", "IN_PROGRESS", "AT_RISK", "DELAYED"])
    ).count()

    delayed_projects = db.query(Project).filter(
        Project.organization_id == org_id,
        Project.status.in_(["DELAYED", "AT_RISK"])
    ).count()

    open_tasks = db.query(Task).filter(
        Task.organization_id == org_id,
        Task.status.in_(["TODO", "IN_PROGRESS"])
    ).count()

    pending_approvals = db.query(Approval).filter(
        Approval.organization_id == org_id,
        Approval.status == ApprovalStatusEnum.PENDING
    ).count()

    briefing = AIService.generate_daily_briefing(org_id, db)

    revenue_chart = [
        {"month": "Apr", "revenue": total_revenue * 0.15, "overdue": overdue_payments * 0.3},
        {"month": "May", "revenue": total_revenue * 0.20, "overdue": overdue_payments * 0.25},
        {"month": "Jun", "revenue": total_revenue * 0.18, "overdue": overdue_payments * 0.20},
        {"month": "Jul", "revenue": total_revenue * 0.22, "overdue": overdue_payments * 0.15},
        {"month": "Aug", "revenue": total_revenue * 0.25, "overdue": overdue_payments * 0.10},
    ]

    project_dist = [
        {"name": "Completed", "value": db.query(Project).filter(Project.organization_id == org_id, Project.status == "COMPLETED").count()},
        {"name": "In Progress", "value": db.query(Project).filter(Project.organization_id == org_id, Project.status == "IN_PROGRESS").count()},
        {"name": "Delayed", "value": delayed_projects},
        {"name": "Planned", "value": db.query(Project).filter(Project.organization_id == org_id, Project.status == "PLANNED").count()},
    ]

    return {
        "kpis": {
            "total_revenue": total_revenue,
            "pending_payments": pending_payments,
            "overdue_payments": overdue_payments,
            "active_projects": active_projects,
            "delayed_projects": delayed_projects,
            "open_tasks": open_tasks,
            "pending_approvals": pending_approvals
        },
        "ai_summary": briefing,
        "revenue_chart": revenue_chart,
        "project_distribution": project_dist
    }
