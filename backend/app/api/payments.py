from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.domain import Organization, Invoice, Payment, Customer
from app.api.auth import get_current_organization
from app.schemas.schemas import InvoiceCreate, PaymentCreate
from app.ai.ai_service import ensure_naive

router = APIRouter(prefix="/payments", tags=["Payments & Invoices"])

@router.get("/invoices")
def list_invoices(status: Optional[str] = None, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    query = db.query(Invoice).filter(Invoice.organization_id == org.id)
    if status:
        query = query.filter(Invoice.status == status)

    invoices = query.order_by(Invoice.due_date.asc()).all()
    results = []
    now = datetime.now()
    for inv in invoices:
        cust = db.query(Customer).filter(Customer.id == inv.customer_id, Customer.organization_id == org.id).first()
        due = ensure_naive(inv.due_date)
        days_overdue = (now - due).days if due and due < now and inv.amount > inv.paid_amount else 0
        results.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "customer_id": inv.customer_id,
            "customer_name": cust.name if cust else "Unknown Customer",
            "company_name": cust.company_name if cust else "",
            "amount": inv.amount,
            "paid_amount": inv.paid_amount,
            "outstanding_balance": inv.amount - inv.paid_amount,
            "status": inv.status,
            "issue_date": inv.issue_date,
            "due_date": inv.due_date,
            "days_overdue": max(0, days_overdue)
        })
    return results

@router.post("/invoices")
def create_invoice(req: InvoiceCreate, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    # Validate customer belongs to user's organization
    customer = db.query(Customer).filter(Customer.id == req.customer_id, Customer.organization_id == org.id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to your organization."
        )

    inv = Invoice(
        organization_id=org.id,
        customer_id=req.customer_id,
        invoice_number=req.invoice_number,
        amount=req.amount,
        paid_amount=0.0,
        status="PENDING",
        issue_date=datetime.now(),
        due_date=req.due_date
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv
