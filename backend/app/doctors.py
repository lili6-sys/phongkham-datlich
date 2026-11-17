from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .models import Doctor, Specialty


router = APIRouter(
    prefix="/api/doctors",
    tags=["Doctors"]
)


class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    specialty_id: int = Field(gt=0)
    phone: str | None = Field(default=None, max_length=20)
    is_active: bool = True


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    specialty_id: int
    phone: str | None
    is_active: bool


# 1. Lay danh sach bac si
@router.get("/", response_model=list[DoctorResponse])
def get_doctors(db: Session = Depends(get_db)):
    return db.scalars(
        select(Doctor).order_by(Doctor.id)
    ).all()


# 2. Xem chi tiet bac si
@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    doctor = db.get(Doctor, doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay bac si"
        )

    return doctor


# 3. Them bac si
@router.post("/", response_model=DoctorResponse, status_code=201)
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db)
):
    specialty = db.get(Specialty, data.specialty_id)

    if not specialty:
        raise HTTPException(
            status_code=404,
            detail="Chuyen khoa khong ton tai"
        )

    doctor = Doctor(
        full_name=data.full_name.strip(),
        specialty_id=data.specialty_id,
        phone=data.phone,
        is_active=data.is_active
    )

    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return doctor


# 4. Cap nhat bac si
@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: int,
    data: DoctorCreate,
    db: Session = Depends(get_db)
):
    doctor = db.get(Doctor, doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay bac si"
        )

    specialty = db.get(Specialty, data.specialty_id)

    if not specialty:
        raise HTTPException(
            status_code=404,
            detail="Chuyen khoa khong ton tai"
        )

    doctor.full_name = data.full_name.strip()
    doctor.specialty_id = data.specialty_id
    doctor.phone = data.phone
    doctor.is_active = data.is_active

    db.commit()
    db.refresh(doctor)

    return doctor


# 5. Xoa bac si
@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    doctor = db.get(Doctor, doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay bac si"
        )

    try:
        db.delete(doctor)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Bac si dang co lich hen, khong the xoa"
        )

    return {"message": "Xoa bac si thanh cong"}
