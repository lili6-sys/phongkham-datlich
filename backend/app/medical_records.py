from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .models import Appointment, MedicalRecord


router = APIRouter(
    prefix="/api/medical-records",
    tags=["Medical Records"]
)


class MedicalRecordCreate(BaseModel):
    appointment_id: int = Field(gt=0)
    diagnosis: str = Field(min_length=2)
    treatment: str | None = None


class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    diagnosis: str
    treatment: str | None
    created_at: datetime


# 1. Lay danh sach ket qua kham
@router.get("/", response_model=list[MedicalRecordResponse])
def get_medical_records(db: Session = Depends(get_db)):
    return db.scalars(
        select(MedicalRecord).order_by(MedicalRecord.id)
    ).all()


# 2. Xem chi tiet ket qua kham
@router.get("/{record_id}", response_model=MedicalRecordResponse)
def get_medical_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    record = db.get(MedicalRecord, record_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay ket qua kham"
        )

    return record


# 3. Luu ket qua kham
@router.post(
    "/",
    response_model=MedicalRecordResponse,
    status_code=201
)
def create_medical_record(
    data: MedicalRecordCreate,
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

    if appointment.status != "checked_in":
        raise HTTPException(
            status_code=409,
            detail="Benh nhan chua check-in"
        )

    existing = db.scalar(
        select(MedicalRecord).where(
            MedicalRecord.appointment_id == data.appointment_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Lich hen da co ket qua kham"
        )

    record = MedicalRecord(
        appointment_id=data.appointment_id,
        diagnosis=data.diagnosis,
        treatment=data.treatment
    )

    db.add(record)
    appointment.status = "completed"

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Khong the luu ket qua kham"
        )

    db.refresh(record)

    return record
