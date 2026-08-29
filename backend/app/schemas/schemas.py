from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    organization: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    organization_id: str

# --- Customer Schemas ---

class CustomerCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None

class CustomerResponse(BaseModel):
    id: str
    name: str
    company_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    gstin: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Project Schemas ---

class ProjectCreate(BaseModel):
    name: str
    customer_id: str
    description: Optional[str] = None
    status: str = "PLANNED"
    budget: float = 0.0
    due_date: Optional[datetime] = None

class ProjectResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: Optional[str] = None
    name: str
    description: Optional[str]
    status: str
    progress_percentage: int
    budget: float
    spent: float
    due_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Payment & Invoice Schemas ---

class InvoiceCreate(BaseModel):
    customer_id: str
    invoice_number: str
    amount: float
    due_date: datetime

class PaymentCreate(BaseModel):
    customer_id: str
    invoice_id: Optional[str] = None
    amount: float
    payment_mode: str = "UPI / Bank Transfer"
    reference_no: Optional[str] = None

class PaymentResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: Optional[str] = None
    invoice_id: Optional[str] = None
    amount: float
    payment_mode: str
    reference_no: Optional[str]
    payment_date: datetime
    status: str

    class Config:
        from_attributes = True

# --- Task Schemas ---

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: str = "MEDIUM"
    status: str = "TODO"
    due_date: Optional[datetime] = None
    customer_id: Optional[str] = None
    project_id: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    assigned_to: Optional[str]
    priority: str
    status: str
    due_date: Optional[datetime]
    customer_id: Optional[str]
    project_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- AI & Query Schemas ---

class AIQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class AIQueryResponse(BaseModel):
    answer: str
    intent: str
    filters_used: Dict[str, Any]
    structured_data: List[Dict[str, Any]]
    suggested_action: Optional[Dict[str, Any]] = None
    conversation_id: str

# --- Approval & Action Schemas ---

class ActionCreate(BaseModel):
    action_type: str
    payload: Dict[str, Any]
    risk_level: str = "MEDIUM"

class ApprovalReview(BaseModel):
    approved: bool
    comments: Optional[str] = None

class ApprovalResponse(BaseModel):
    id: str
    action_id: str
    title: str
    reason: Optional[str]
    risk_level: str
    status: str
    action_type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- WhatsApp Connector Schemas ---

class WhatsAppConfigureRequest(BaseModel):
    access_token: str
    phone_number_id: str
    business_account_id: Optional[str] = None
    verify_token: Optional[str] = "eios_whatsapp_verify_token"
    api_version: Optional[str] = "v18.0"

class WhatsAppSendRequest(BaseModel):
    recipient_phone: str
    message: str
    template_name: Optional[str] = None

# --- Standard API Response ---

class StandardResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
