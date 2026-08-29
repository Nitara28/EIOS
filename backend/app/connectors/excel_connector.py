import pandas as pd
import io
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.domain import Customer, Invoice, DataSource, SyncJob, ActivityLog

logger = logging.getLogger("eios_excel")

class ExcelConnector:
    """
    Data connector for Excel (.xlsx, .xls) and CSV file upload, mapping, and database import.
    """

    COLUMN_MAP_SUGGESTIONS = {
        "name": ["customer", "customer_name", "client", "client_name", "name"],
        "company_name": ["company", "company_name", "organization", "business"],
        "email": ["email", "e-mail", "email_address", "contact_email"],
        "phone": ["phone", "mobile", "contact_no", "phone_number"],
        "gstin": ["gst", "gstin", "tax_id"],
        "amount": ["amount", "invoice_amount", "total", "balance"],
        "due_date": ["due_date", "due", "payment_due"]
    }

    @classmethod
    def parse_and_preview(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Parses uploaded file bytes and returns header metadata, sample rows, and suggested mappings.
        """
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        headers = list(df.columns)
        sample_rows = df.head(5).fillna("").to_dict(orient="records")

        # Auto-detect column mapping
        detected_mapping = {}
        for std_field, aliases in cls.COLUMN_MAP_SUGGESTIONS.items():
            for col in headers:
                clean_col = str(col).strip().lower()
                if clean_col in aliases or any(alias in clean_col for alias in aliases):
                    detected_mapping[std_field] = col
                    break

        return {
            "filename": filename,
            "total_rows": len(df),
            "headers": headers,
            "sample_rows": sample_rows,
            "suggested_mapping": detected_mapping
        }

    @classmethod
    def import_data(cls, file_bytes: bytes, filename: str, column_mapping: Dict[str, str], organization_id: str, db: Session) -> Dict[str, Any]:
        """
        Imports data rows into Customer and Invoice tables based on mapped columns.
        """
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        records_processed = 0
        records_imported = 0
        duplicates_count = 0
        errors_count = 0

        name_col = column_mapping.get("name")
        company_col = column_mapping.get("company_name")
        email_col = column_mapping.get("email")
        phone_col = column_mapping.get("phone")
        gstin_col = column_mapping.get("gstin")
        amount_col = column_mapping.get("amount")
        due_col = column_mapping.get("due_date")

        for idx, row in df.iterrows():
            records_processed += 1
            try:
                c_name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else None
                if not c_name:
                    c_name = str(row[company_col]).strip() if company_col and pd.notna(row[company_col]) else f"Imported Client #{idx+1}"

                c_email = str(row[email_col]).strip() if email_col and pd.notna(row[email_col]) else None
                c_company = str(row[company_col]).strip() if company_col and pd.notna(row[company_col]) else c_name
                c_phone = str(row[phone_col]).strip() if phone_col and pd.notna(row[phone_col]) else None
                c_gstin = str(row[gstin_col]).strip() if gstin_col and pd.notna(row[gstin_col]) else None

                # Entity matching check
                existing_customer = db.query(Customer).filter(
                    Customer.organization_id == organization_id,
                    (Customer.name == c_name) | (Customer.email == c_email if c_email else False)
                ).first()

                if existing_customer:
                    customer = existing_customer
                    duplicates_count += 1
                else:
                    customer = Customer(
                        organization_id=organization_id,
                        name=c_name,
                        company_name=c_company,
                        email=c_email,
                        phone=c_phone,
                        gstin=c_gstin
                    )
                    db.add(customer)
                    db.flush()
                    records_imported += 1

                # If amount column mapped, create invoice
                if amount_col and pd.notna(row[amount_col]):
                    amt = float(row[amount_col])
                    due_date = datetime.now(timezone.utc)
                    if due_col and pd.notna(row[due_col]):
                        try:
                            due_date = pd.to_datetime(row[due_col]).to_pydatetime().replace(tzinfo=timezone.utc)
                        except Exception:
                            pass

                    invoice = Invoice(
                        organization_id=organization_id,
                        customer_id=customer.id,
                        invoice_number=f"INV-IMP-{records_processed:04d}",
                        amount=amt,
                        paid_amount=0.0,
                        status="PENDING" if due_date >= datetime.now(timezone.utc) else "OVERDUE",
                        issue_date=datetime.now(timezone.utc),
                        due_date=due_date
                    )
                    db.add(invoice)

            except Exception as e:
                logger.error(f"Row {idx} import error: {e}")
                errors_count += 1

        # Register data source if not exists
        data_source = db.query(DataSource).filter(
            DataSource.organization_id == organization_id,
            DataSource.source_type == "EXCEL"
        ).first()

        if not data_source:
            data_source = DataSource(
                organization_id=organization_id,
                source_type="EXCEL",
                name=f"Excel Import ({filename})",
                status="ACTIVE",
                last_synced_at=datetime.now(timezone.utc)
            )
            db.add(data_source)
            db.flush()
        else:
            data_source.last_synced_at = datetime.now(timezone.utc)

        # Log SyncJob
        sync_job = SyncJob(
            organization_id=organization_id,
            data_source_id=data_source.id,
            status="COMPLETED",
            records_processed=records_processed,
            records_imported=records_imported,
            errors_count=errors_count,
            summary=f"Imported {records_imported} customer/invoice records from '{filename}'. Duplicates matched: {duplicates_count}."
        )
        db.add(sync_job)

        # Activity log
        log_entry = ActivityLog(
            organization_id=organization_id,
            user_name="Admin",
            action=f"Uploaded and imported '{filename}'",
            source="Excel/CSV Connector",
            status="SUCCESS",
            details=f"Processed: {records_processed}, Imported: {records_imported}, Duplicates: {duplicates_count}, Errors: {errors_count}",
            risk_level="LOW"
        )
        db.add(log_entry)
        db.commit()

        return {
            "records_processed": records_processed,
            "records_imported": records_imported,
            "duplicates_matched": duplicates_count,
            "errors_count": errors_count,
            "summary": f"Import completed successfully from '{filename}'."
        }
