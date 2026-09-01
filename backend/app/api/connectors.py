import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.domain import Organization, DataSource, SyncJob
from app.api.auth import get_current_organization
from app.connectors.excel_connector import ExcelConnector
from app.connectors.gmail_connector import GmailConnector
from app.connectors.whatsapp_connector import WhatsAppConnector
from app.schemas.schemas import WhatsAppConfigureRequest, WhatsAppSendRequest

router = APIRouter(prefix="/connectors", tags=["Data Sources & Connectors"])

@router.get("")
def list_connectors(org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    sources = db.query(DataSource).filter(DataSource.organization_id == org.id).all()
    source_map = {s.source_type: s for s in sources}

    excel_ds = source_map.get("EXCEL")
    gmail_ds = source_map.get("GMAIL")
    wa_ds = source_map.get("WHATSAPP")
    tally_ds = source_map.get("TALLY")

    wa_status_data = WhatsAppConnector.get_status(org.id, db)

    return [
        {
            "id": excel_ds.id if excel_ds else "ds-excel",
            "source_type": "EXCEL",
            "name": "Excel / CSV Import Wizard",
            "status": "ACTIVE",
            "description": "Upload spreadsheet files (.xlsx, .csv) with schema mapping.",
            "last_synced_at": excel_ds.last_synced_at if excel_ds else None
        },
        {
            "id": gmail_ds.id if gmail_ds else "ds-gmail",
            "source_type": "GMAIL",
            "name": "Gmail Business Communications",
            "status": gmail_ds.status if gmail_ds else "CONFIGURATION_READY",
            "description": "Sync customer email communication threads via Google OAuth 2.0 API.",
            "last_synced_at": gmail_ds.last_synced_at if gmail_ds else None,
            "configured": bool(gmail_ds and gmail_ds.config and gmail_ds.config.get("access_token"))
        },
        {
            "id": wa_ds.id if wa_ds else "ds-whatsapp",
            "source_type": "WHATSAPP",
            "name": "WhatsApp Business API",
            "status": wa_status_data["status"],
            "description": "Official Meta Cloud API connector for automated alerts, customer messages & templates.",
            "last_synced_at": wa_status_data["last_synced_at"],
            "configured": wa_status_data["configured"]
        },
        {
            "id": tally_ds.id if tally_ds else "ds-tally",
            "source_type": "TALLY",
            "name": "Tally Prime Sync",
            "status": tally_ds.status if tally_ds else "CONFIGURATION_READY",
            "description": "Direct XML/ODBC sync connector for Tally accounting software.",
            "last_synced_at": tally_ds.last_synced_at if tally_ds else None
        }
    ]

@router.post("/preview")
async def preview_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Invalid file type. Upload .csv, .xlsx, or .xls.")

    content = await file.read()
    preview_data = ExcelConnector.parse_and_preview(content, file.filename)
    return preview_data

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    column_mapping: str = Form("{}"),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    content = await file.read()
    try:
        mapping = json.loads(column_mapping)
    except Exception:
        mapping = {}

    if not mapping:
        preview = ExcelConnector.parse_and_preview(content, file.filename)
        mapping = preview.get("suggested_mapping", {})

    result = ExcelConnector.import_data(
        file_bytes=content,
        filename=file.filename,
        column_mapping=mapping,
        organization_id=org.id,
        db=db
    )
    return result

@router.get("/history")
def get_import_history(org: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    jobs = db.query(SyncJob).filter(SyncJob.organization_id == org.id).order_by(SyncJob.created_at.desc()).all()
    return jobs

# --- Gmail Connector OAuth & Sync Endpoints ---

@router.get("/gmail/auth-url")
def get_gmail_auth_url(org: Organization = Depends(get_current_organization)):
    return GmailConnector.get_authorization_url(org.id)

@router.get("/gmail/callback")
async def gmail_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        await GmailConnector.exchange_code_for_tokens(code=code, organization_id=state, db=db)
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        return RedirectResponse(url=f"{frontend_url}/data-sources?status=gmail_connected")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth Authorization failed: {e}")

@router.post("/gmail/sync")
async def sync_gmail(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    result = await GmailConnector.sync_gmail_messages(org.id, db)
    return result

@router.post("/gmail/disconnect")
def disconnect_gmail(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    result = GmailConnector.revoke_credentials(org.id, db)
    return result

# --- WhatsApp Business Cloud API Endpoints ---

@router.get("/whatsapp/status")
def get_whatsapp_status(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    return WhatsAppConnector.get_status(org.id, db)

@router.post("/whatsapp/configure")
def configure_whatsapp(
    req: WhatsAppConfigureRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    result = WhatsAppConnector.configure(org.id, req.model_dump(), db)
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result
        )
    return result

@router.get("/whatsapp/webhook")
def verify_whatsapp_webhook(
    request: Request,
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
    organization_id: str = Query(default=""),
    db: Session = Depends(get_db)
):
    if not hub_mode or not hub_verify_token or not hub_challenge:
        raise HTTPException(status_code=400, detail="Missing Meta webhook verification parameters.")

    challenge_val = WhatsAppConnector.verify_webhook(
        mode=hub_mode,
        verify_token=hub_verify_token,
        challenge=hub_challenge,
        organization_id=organization_id,
        db=db
    )

    if challenge_val is not None:
        return PlainTextResponse(content=str(challenge_val))
    else:
        raise HTTPException(
            status_code=403,
            detail={"error_code": "WEBHOOK_VERIFICATION_FAILED", "message": "Meta Webhook verification failed. Invalid verify token."}
        )

@router.post("/whatsapp/webhook")
async def receive_whatsapp_webhook(
    request: Request,
    organization_id: str = Query(default=""),
    db: Session = Depends(get_db)
):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_WEBHOOK", "message": "Invalid JSON payload."})

    target_org_id = organization_id
    if not target_org_id:
        ds = db.query(DataSource).filter(DataSource.source_type == "WHATSAPP", DataSource.status == "ACTIVE").first()
        target_org_id = ds.organization_id if ds else None

    if not target_org_id:
        from app.models.domain import Organization as OrgModel
        first_org = db.query(OrgModel).first()
        target_org_id = first_org.id if first_org else ""

    result = WhatsAppConnector.process_incoming_webhook(body, target_org_id, db)
    return result

@router.post("/whatsapp/send")
async def send_whatsapp_message(
    req: WhatsAppSendRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    result = await WhatsAppConnector.send_message(
        organization_id=org.id,
        recipient_phone=req.recipient_phone,
        message_body=req.message,
        db=db,
        template_name=req.template_name
    )

    if not result.get("success") and result.get("error_code") == "WHATSAPP_NOT_CONFIGURED":
        raise HTTPException(status_code=400, detail=result)

    return result

@router.post("/whatsapp/disconnect")
def disconnect_whatsapp(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    return WhatsAppConnector.disconnect(org.id, db)
