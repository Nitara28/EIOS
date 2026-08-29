import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.domain import (
    Organization, User, OrganizationMember, RoleEnum, Customer, Contact,
    Project, ProjectUpdate, ProjectStatusEnum, Invoice, Payment, PaymentStatusEnum,
    Task, TaskStatusEnum, Employee, DataSource, Approval, Action, ActivityLog, Notification, RiskLevelEnum, ApprovalStatusEnum
)

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded
        existing_org = db.query(Organization).first()
        if existing_org:
            print("Database already contains data. Skipping seed.")
            return existing_org.id

        print("Seeding EIOS database with realistic business operations data...")
        now = datetime.now(timezone.utc)

        # 1. Create Organization
        org = Organization(
            name="Apex Global Operations",
            slug="apex-global",
            industry="Industrial Manufacturing & Tech Services",
            currency="INR"
        )
        db.add(org)
        db.flush()

        # 2. Create Admin User & Member
        admin_user = User(
            email="admin@eios.ai",
            hashed_password=get_password_hash("password123"),
            full_name="Rajesh Sharma",
            is_active=True,
            is_superuser=True
        )
        db.add(admin_user)
        db.flush()

        member = OrganizationMember(
            organization_id=org.id,
            user_id=admin_user.id,
            role=RoleEnum.OWNER
        )
        db.add(member)

        # 3. Create 20 Realistic Customers
        customer_data = [
            ("ABC Industries", "Acme Manufacturing Pvt Ltd", "finance@acme.com", "+91 98765 43210", "GSTIN27AAACA1234A1Z1"),
            ("XYZ Solutions", "Vertex Technologies", "accounts@vertextech.in", "+91 98111 22334", "GSTIN27BBBCB5678B1Z2"),
            ("BlueStone Infra", "BlueStone Infrastructure Ltd", "contact@bluestoneinfra.com", "+91 99000 88776", "GSTIN27CCCC19012C1Z3"),
            ("Nova Retail", "Nova Retail Chains India", "info@novaretail.co.in", "+91 98222 33445", "GSTIN27DDDD3456D1Z4"),
            ("GreenGrid Energy", "GreenGrid Energy Solutions", "billing@greengrid.org", "+91 97333 44556", "GSTIN27EEEE7890E1Z5"),
            ("Zenith Logistics", "Zenith Supply Chain Services", "ops@zenithlog.com", "+91 96444 55667", "GSTIN27FFFF1122F1Z6"),
            ("Nexus Pharma", "Nexus Healthcare & Life Sciences", "payables@nexuspharma.in", "+91 95555 66778", "GSTIN27GGGG3344G1Z7"),
            ("Quantum Soft", "Quantum Enterprise Software", "finance@quantumsoft.io", "+91 94666 77889", "GSTIN27HHHH5566H1Z8"),
            ("Orion Metals", "Orion Precision Forge", "orders@orionmetals.com", "+91 93777 88990", "GSTIN27IIII7788I1Z9"),
            ("Starlight Media", "Starlight Digital Entertainment", "invoices@starlight.net", "+91 92888 99001", "GSTIN27JJJJ9900J1Z0"),
            ("Horizon Real Estate", "Horizon Urban Developers", "accounts@horizonreal.com", "+91 91999 00112", "GSTIN27KKKK1133K1Z1"),
            ("Vanguard Security", "Vanguard Defense Systems", "billing@vanguardsec.in", "+91 90000 11223", "GSTIN27LLLL2244L1Z2"),
            ("Echo Systems", "Echo Robotics & Electronics", "contact@echosystems.io", "+91 89111 22334", "GSTIN27MMMM3355M1Z3"),
            ("Titanium Automotive", "Titanium Auto Components", "procurement@titanauto.com", "+91 88222 33445", "GSTIN27NNNN4466N1Z4"),
            ("Solaris Foods", "Solaris Agro & Beverages", "finance@solarisfoods.in", "+91 87333 44556", "GSTIN27OOOO5577O1Z5"),
            ("Pinnacle Construction", "Pinnacle Highrise Projects", "payables@pinnaclecon.com", "+91 86444 55667", "GSTIN27PPPP6688P1Z6"),
            ("AeroTech Spares", "AeroTech Dynamics India", "invoices@aerotech.in", "+91 85555 66778", "GSTIN27QQQQ7799Q1Z7"),
            ("CyberPulse Networks", "CyberPulse Telecommunications", "billing@cyberpulse.net", "+91 84666 77889", "GSTIN27RRRR8800R1Z8"),
            ("Velox Medical", "Velox Diagnostic Equipment", "accounts@veloxmed.org", "+91 83777 88990", "GSTIN27SSSS9911S1Z9"),
            ("Matrix Heavy Equip", "Matrix Heavy Machinery Ltd", "finance@matrixheavy.com", "+91 82888 99001", "GSTIN27TTTT0022T1Z0"),
        ]

        customers_db = []
        for name, comp, email, phone, gstin in customer_data:
            c = Customer(
                organization_id=org.id,
                name=name,
                company_name=comp,
                email=email,
                phone=phone,
                gstin=gstin,
                status="ACTIVE"
            )
            db.add(c)
            customers_db.append(c)
        db.flush()

        # 4. Create 30 Projects
        project_names = [
            ("SCADA Automation Upgrade", ProjectStatusEnum.IN_PROGRESS, 65, 450000.0, 250000.0),
            ("Warehouse ERP Migration", ProjectStatusEnum.DELAYED, 35, 800000.0, 520000.0),
            ("Factory IoT Sensor Network", ProjectStatusEnum.AT_RISK, 40, 350000.0, 210000.0),
            ("Pan-India POS Integration", ProjectStatusEnum.DELAYED, 20, 1200000.0, 750000.0),
            ("Solar Roof Panel Installation", ProjectStatusEnum.COMPLETED, 100, 600000.0, 580000.0),
            ("Fleet Management Telematics", ProjectStatusEnum.IN_PROGRESS, 80, 280000.0, 200000.0),
            ("Cleanroom HVAC Commissioning", ProjectStatusEnum.DELAYED, 45, 950000.0, 600000.0),
            ("Cloud Migration Phase 2", ProjectStatusEnum.IN_PROGRESS, 50, 400000.0, 180000.0),
            ("High-Speed Stamping Line", ProjectStatusEnum.PLANNED, 0, 1500000.0, 0.0),
            ("OTT Video Streaming Platform", ProjectStatusEnum.COMPLETED, 100, 700000.0, 690000.0),
            ("Residential Tower Smart Metering", ProjectStatusEnum.IN_PROGRESS, 70, 1100000.0, 800000.0),
            ("Perimeter Radar Surveillance", ProjectStatusEnum.IN_PROGRESS, 85, 500000.0, 420000.0),
            ("AGV Automated Guided Vehicles", ProjectStatusEnum.AT_RISK, 30, 850000.0, 400000.0),
            ("BS-VI Engine Test Bench", ProjectStatusEnum.COMPLETED, 100, 1300000.0, 1250000.0),
            ("Cold Chain Logistics Tracking", ProjectStatusEnum.IN_PROGRESS, 60, 320000.0, 190000.0),
            ("Steel Structure Pre-Fabrication", ProjectStatusEnum.PLANNED, 10, 900000.0, 50000.0),
            ("Avionics Harness Fabrication", ProjectStatusEnum.COMPLETED, 100, 450000.0, 440000.0),
            ("5G Core Network Upgrade", ProjectStatusEnum.IN_PROGRESS, 75, 1800000.0, 1300000.0),
            ("MRI Machine Calibration", ProjectStatusEnum.COMPLETED, 100, 250000.0, 240000.0),
            ("Hydraulic Excavator Refurbish", ProjectStatusEnum.IN_PROGRESS, 55, 650000.0, 350000.0),
            ("Substation Transformer Testing", ProjectStatusEnum.PLANNED, 0, 380000.0, 0.0),
            ("Biometric Access Control Deployment", ProjectStatusEnum.IN_PROGRESS, 90, 220000.0, 190000.0),
            ("Custom CRM Workflow Engine", ProjectStatusEnum.COMPLETED, 100, 500000.0, 490000.0),
            ("Effluent Treatment Plant Monitoring", ProjectStatusEnum.IN_PROGRESS, 40, 750000.0, 300000.0),
            ("Cold Storage Expansion Phase 1", ProjectStatusEnum.DELAYED, 25, 1400000.0, 600000.0),
            ("Automated Packaging Line", ProjectStatusEnum.IN_PROGRESS, 70, 880000.0, 600000.0),
            ("Foundry Temperature Sensors", ProjectStatusEnum.COMPLETED, 100, 300000.0, 295000.0),
            ("Fiber Optic Backbone Ring", ProjectStatusEnum.IN_PROGRESS, 80, 1250000.0, 950000.0),
            ("UL-Certified Control Panels", ProjectStatusEnum.COMPLETED, 100, 420000.0, 410000.0),
            ("Diesel Generator Sync System", ProjectStatusEnum.PLANNED, 5, 550000.0, 20000.0),
        ]

        projects_db = []
        for idx, (p_name, p_status, p_prog, p_bud, p_spent) in enumerate(project_names):
            cust = customers_db[idx % len(customers_db)]
            proj = Project(
                organization_id=org.id,
                customer_id=cust.id,
                name=p_name,
                description=f"Operational project deployment for {cust.company_name}",
                status=p_status,
                progress_percentage=p_prog,
                budget=p_bud,
                spent=p_spent,
                due_date=now + timedelta(days=random.randint(-15, 60))
            )
            db.add(proj)
            projects_db.append(proj)
        db.flush()

        # 5. Create 50 Invoices & Payments (Including specific prompt invoice amounts)
        # ABC Industries — ₹80,000 — 15 days overdue
        inv_abc = Invoice(
            organization_id=org.id,
            customer_id=customers_db[0].id,
            invoice_number="INV-1024",
            amount=80000.0,
            paid_amount=0.0,
            status=PaymentStatusEnum.OVERDUE,
            issue_date=now - timedelta(days=45),
            due_date=now - timedelta(days=15)
        )
        db.add(inv_abc)

        # XYZ Solutions — ₹65,000 — 8 days overdue
        inv_xyz = Invoice(
            organization_id=org.id,
            customer_id=customers_db[1].id,
            invoice_number="INV-1028",
            amount=65000.0,
            paid_amount=0.0,
            status=PaymentStatusEnum.OVERDUE,
            issue_date=now - timedelta(days=38),
            due_date=now - timedelta(days=8)
        )
        db.add(inv_xyz)

        # Generate 48 additional invoices
        for i in range(1, 49):
            cust = customers_db[i % len(customers_db)]
            is_overdue = (i % 4 == 0)
            is_paid = (i % 2 == 1 and not is_overdue)
            amt = float(random.randint(15, 120) * 1000)

            if is_paid:
                paid = amt
                status = PaymentStatusEnum.PAID
                due = now - timedelta(days=random.randint(5, 30))
            elif is_overdue:
                paid = 0.0
                status = PaymentStatusEnum.OVERDUE
                due = now - timedelta(days=random.randint(2, 25))
            else:
                paid = float(random.choice([0, amt * 0.5]))
                status = PaymentStatusEnum.PARTIALLY_PAID if paid > 0 else PaymentStatusEnum.PENDING
                due = now + timedelta(days=random.randint(5, 45))

            inv = Invoice(
                organization_id=org.id,
                customer_id=cust.id,
                invoice_number=f"INV-{2000 + i}",
                amount=amt,
                paid_amount=paid,
                status=status,
                issue_date=now - timedelta(days=random.randint(30, 90)),
                due_date=due
            )
            db.add(inv)

            if paid > 0:
                pmt = Payment(
                    organization_id=org.id,
                    customer_id=cust.id,
                    invoice_id=inv.id,
                    amount=paid,
                    payment_mode="UPI / NEFT",
                    reference_no=f"TXN-{random.randint(100000, 999999)}",
                    payment_date=now - timedelta(days=random.randint(1, 20)),
                    status="COMPLETED"
                )
                db.add(pmt)
        db.flush()

        # 6. Create Tasks
        task_titles = [
            ("Send payment reminder to ABC Industries for INV-1024", "HIGH", TaskStatusEnum.TODO, customers_db[0].id),
            ("Follow up with XYZ Solutions regarding ₹65,000 overdue invoice", "HIGH", TaskStatusEnum.TODO, customers_db[1].id),
            ("Review milestone delays on Warehouse ERP Migration", "HIGH", TaskStatusEnum.IN_PROGRESS, customers_db[1].id),
            ("Confirm delivery of IoT sensors for Factory Project", "MEDIUM", TaskStatusEnum.TODO, customers_db[2].id),
            ("Draft Q3 revenue statement for executive board", "MEDIUM", TaskStatusEnum.COMPLETED, None),
            ("Sync CSV client ledger from Tally exports", "LOW", TaskStatusEnum.COMPLETED, None)
        ]
        for t_title, prio, stat, c_id in task_titles:
            t = Task(
                organization_id=org.id,
                customer_id=c_id,
                title=t_title,
                priority=prio,
                status=stat,
                due_date=now + timedelta(days=random.randint(1, 10))
            )
            db.add(t)

        # 7. Create Pending Approvals & Actions
        action_1 = Action(
            organization_id=org.id,
            action_type="SEND_REMINDER",
            payload={
                "customers": ["ABC Industries", "XYZ Solutions"],
                "total_overdue": 145000.0,
                "invoice_numbers": ["INV-1024", "INV-1028"]
            },
            risk_level=RiskLevelEnum.HIGH,
            status=ApprovalStatusEnum.PENDING,
            created_by="EIOS AI Assistant"
        )
        db.add(action_1)
        db.flush()

        app_1 = Approval(
            organization_id=org.id,
            action_id=action_1.id,
            title="Overdue Payment Reminder Dispatch (₹1.45L)",
            reason="High risk customer communication action requiring manager confirmation.",
            risk_level=RiskLevelEnum.HIGH,
            status=ApprovalStatusEnum.PENDING
        )
        db.add(app_1)

        # 8. Create Data Sources
        ds_excel = DataSource(
            organization_id=org.id,
            source_type="EXCEL",
            name="Excel / CSV Data Import",
            status="ACTIVE",
            last_synced_at=now - timedelta(hours=2)
        )
        ds_gmail = DataSource(
            organization_id=org.id,
            source_type="GMAIL",
            name="Gmail Connector (OAuth)",
            status="CONFIGURATION_READY",
            config={"scopes": ["https://www.googleapis.com/auth/gmail.readonly"]}
        )
        ds_wa = DataSource(
            organization_id=org.id,
            source_type="WHATSAPP",
            name="WhatsApp Business API",
            status="CONFIGURATION_READY",
            config={"provider": "Meta WhatsApp Cloud API"}
        )
        ds_tally = DataSource(
            organization_id=org.id,
            source_type="TALLY",
            name="Tally Prime Direct Sync",
            status="CONFIGURATION_READY",
            config={"port": 9000}
        )
        db.add_all([ds_excel, ds_gmail, ds_wa, ds_tally])

        # 9. Create Activity Logs
        logs = [
            ("Admin", "Uploaded Customers_August2026.xlsx", "Excel Connector", "SUCCESS", "Imported 12 customer records and 8 invoices.", "LOW"),
            ("EIOS AI COO", "Generated Daily Business Briefing", "AI Engine", "SUCCESS", "Identified 3 delayed projects and ₹2.4L overdue payments.", "LOW"),
            ("EIOS AI COO", "Classified Intent GET_OVERDUE_PAYMENTS", "AI Assistant", "SUCCESS", "Query: 'Which customers have pending payments above ₹50,000?'", "LOW"),
            ("System AI", "Created Action Request SEND_REMINDER", "Action Engine", "SUCCESS", "Pending approval created for 2 overdue customers.", "HIGH"),
        ]
        for u_name, act, src, stat, det, r_lvl in logs:
            log = ActivityLog(
                organization_id=org.id,
                user_name=u_name,
                action=act,
                source=src,
                status=stat,
                details=det,
                risk_level=r_lvl
            )
            db.add(log)

        db.commit()
        print("Database successfully seeded with 20 customers, 30 projects, 50 invoices, approvals & activity logs!")
        return org.id

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
