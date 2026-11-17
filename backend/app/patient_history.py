import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Appointment, MedicalRecord, Invoice


router = APIRouter(
    prefix="/api/history",
    tags=["Patient History"]
)


# Xem lich su kham cua benh nhan (chi de demo local)
@router.get("/{patient_username}")
def get_patient_history(
    patient_username: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Chi bat API demo khi duoc cho phep
    if os.getenv("ENABLE_DEMO_HISTORY") != "1":
        raise HTTPException(
            status_code=403,
            detail="API demo chua duoc bat"
        )

    username = patient_username.strip()

    if not username:
        raise HTTPException(
            status_code=422,
            detail="Ten benh nhan khong hop le"
        )

    if current_user["role"] != "admin" and (
        username != current_user["username"]
    ):
        raise HTTPException(403, "Khong co quyen xem lich su nay")

    appointments = db.scalars(
        select(Appointment)
        .where(Appointment.patient_username == username)
        .order_by(Appointment.appointment_time.desc())
    ).all()

    history = []

    for appointment in appointments:
        record = db.scalar(
            select(MedicalRecord).where(
                MedicalRecord.appointment_id == appointment.id
            )
        )

        invoice = db.scalar(
            select(Invoice).where(
                Invoice.appointment_id == appointment.id
            )
        )

        history.append({
            "appointment_id": appointment.id,
            "doctor_id": appointment.doctor_id,
            "appointment_time": appointment.appointment_time,
            "status": appointment.status,
            "diagnosis": record.diagnosis if record else None,
            "treatment": record.treatment if record else None,
            "invoice_amount": (
                str(invoice.total_amount) if invoice else None
            ),
            "payment_status": invoice.status if invoice else None
        })

    return {
        "patient_username": username,
        "total_appointments": len(history),
        "history": history
    }
