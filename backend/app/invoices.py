from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .models import Appointment, Invoice


router = APIRouter(
    prefix="/api/invoices",
    tags=["Invoices"]
)


class InvoiceCreate(BaseModel):
    appointment_id: int = Field(gt=0)
    total_amount: Decimal = Field(
        gt=0, max_digits=12, decimal_places=2
    )


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    total_amount: Decimal
    status: str
    created_at: datetime


# 1. Lay danh sach hoa don
@router.get("/", response_model=list[InvoiceResponse])
def get_invoices(db: Session = Depends(get_db)):
    return db.scalars(
        select(Invoice).order_by(Invoice.id)
    ).all()


# 2. Xem chi tiet hoa don
@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    invoice = db.get(Invoice, invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay hoa don"
        )

    return invoice


# 3. Tao hoa don kham benh
@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=201
)
def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    appointment = db.get(
        Appointment, data.appointment_id
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay lich hen"
        )

    if appointment.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Lich hen chua hoan thanh kham"
        )

    existing = db.scalar(
        select(Invoice).where(
            Invoice.appointment_id == data.appointment_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Lich hen da co hoa don"
        )

    invoice = Invoice(
        appointment_id=data.appointment_id,
        total_amount=data.total_amount,
        status="unpaid"
    )

    db.add(invoice)

    try:
        db.commit()
        db.refresh(invoice)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Khong the tao hoa don"
        )

    return invoice
# 4. Xac nhan thanh toan hoa don
@router.patch(
    "/{invoice_id}/pay",
    response_model=InvoiceResponse
)
def pay_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    invoice = db.get(Invoice, invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay hoa don"
        )

    if invoice.status == "paid":
        raise HTTPException(
            status_code=409,
            detail="Hoa don da duoc thanh toan"
        )

    if invoice.status != "unpaid":
        raise HTTPException(
            status_code=409,
            detail="Trang thai hoa don khong hop le"
        )

    invoice.status = "paid"

    db.commit()
    db.refresh(invoice)

    return invoice
