from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.domain import Organization, Customer, Invoice, Project
from app.api.auth import get_current_organization
from app.schemas.schemas import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("")
def list_customers(search: Optional[str] = None, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    query = db.query(Customer).filter(Customer.organization_id == org.id)
    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%") | Customer.company_name.ilike(f"%{search}%"))

    customers = query.order_by(Customer.created_at.desc()).all()
    results = []
    for c in customers:
        outstanding = db.query(Invoice).filter(
            Invoice.customer_id == c.id,
            Invoice.amount > Invoice.paid_amount
        ).all()
        bal = sum(i.amount - i.paid_amount for i in outstanding)
        p_count = db.query(Project).filter(Project.customer_id == c.id).count()

        results.append({
            "id": c.id,
            "name": c.name,
            "company_name": c.company_name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "gstin": c.gstin,
            "status": c.status,
            "outstanding_balance": bal,
            "projects_count": p_count,
            "created_at": c.created_at
        })
    return results

@router.post("", response_model=CustomerResponse)
def create_customer(req: CustomerCreate, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    customer = Customer(
        organization_id=org.id,
        name=req.name,
        company_name=req.company_name,
        email=req.email,
        phone=req.phone,
        address=req.address,
        gstin=req.gstin
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.get("/{customer_id}")
def get_customer_profile(customer_id: str, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id, Customer.organization_id == org.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")

    invoices = db.query(Invoice).filter(Invoice.customer_id == c.id).all()
    projects = db.query(Project).filter(Project.customer_id == c.id).all()

    return {
        "customer": c,
        "invoices": invoices,
        "projects": projects
    }
