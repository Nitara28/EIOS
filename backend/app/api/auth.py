from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.models.domain import User, Organization, OrganizationMember, RoleEnum
from app.schemas.schemas import UserRegister, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired authentication token.")
    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")
    return user

def get_current_organization(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Organization:
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to any organization.")
    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    return org

@router.post("/register", response_model=TokenResponse)
def register(req: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    # Create Organization
    slug = req.organization_name.lower().replace(" ", "-") + "-org"
    org = Organization(name=req.organization_name, slug=slug)
    db.add(org)
    db.flush()

    # Create User
    hashed_pwd = get_password_hash(req.password)
    user = User(email=req.email, hashed_password=hashed_pwd, full_name=req.full_name)
    db.add(user)
    db.flush()

    # Create Membership
    membership = OrganizationMember(organization_id=org.id, user_id=user.id, role=RoleEnum.OWNER)
    db.add(membership)
    db.commit()

    token = create_access_token(data={"sub": user.id, "org_id": org.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": RoleEnum.OWNER},
        "organization": {"id": org.id, "name": org.name, "slug": org.slug}
    }

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    email = None
    password = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email") or body.get("username")
        password = body.get("password")
    else:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password.")

    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )

    org_id = membership.organization_id if membership else None

    org = (
        db.query(Organization)
        .filter(Organization.id == org_id)
        .first()
        if org_id
        else None
    )

    token = create_access_token(
        data={"sub": user.id, "org_id": org_id}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": membership.role if membership else "EMPLOYEE"
        },
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug
        } if org else {
            "id": "",
            "name": "Default Org"
        }
    }

@router.get("/me")
def get_me(user: User = Depends(get_current_user), org: Organization = Depends(get_current_organization)):
    return {
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
        "organization": {"id": org.id, "name": org.name, "slug": org.slug, "currency": org.currency}
    }
