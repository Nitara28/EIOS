from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.domain import Organization, Project, Customer, ProjectUpdate
from app.api.auth import get_current_organization
from app.schemas.schemas import ProjectCreate

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("")
def list_projects(status: Optional[str] = None, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    query = db.query(Project).filter(Project.organization_id == org.id)
    if status:
        query = query.filter(Project.status == status)

    projects = query.order_by(Project.created_at.desc()).all()
    results = []
    for p in projects:
        cust = db.query(Customer).filter(Customer.id == p.customer_id, Customer.organization_id == org.id).first()
        results.append({
            "id": p.id,
            "customer_id": p.customer_id,
            "customer_name": cust.name if cust else "Unknown Customer",
            "company_name": cust.company_name if cust else "",
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "progress_percentage": p.progress_percentage,
            "budget": p.budget,
            "spent": p.spent,
            "due_date": p.due_date,
            "created_at": p.created_at
        })
    return results

@router.post("")
def create_project(req: ProjectCreate, org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    # Validate customer belongs to user's organization
    customer = db.query(Customer).filter(Customer.id == req.customer_id, Customer.organization_id == org.id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to your organization."
        )

    proj = Project(
        organization_id=org.id,
        customer_id=req.customer_id,
        name=req.name,
        description=req.description,
        status=req.status,
        budget=req.budget,
        due_date=req.due_date
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj
