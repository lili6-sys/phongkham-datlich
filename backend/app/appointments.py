from .auth import require_roles, get_current_user
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Appointment, Doctor


router = APIRouter(
    prefix="/api/appointments",
    tags=["Appointments"]
)


class AppointmentCreate(BaseModel):
    patient_username: str = Field(min_length=3)
    doctor_id: int = Field(gt=0)
    appointment_time: datetime
    note: str | None = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_username: str
    doctor_id: int
    appointment_time: datetime
    status: str
    note: str | None


# 1. Lay danh sach lich hen
@router.get("/", response_model=list[AppointmentResponse],
    dependencies=[Depends(require_roles('admin'))]
)
def get_appointments(db: Session = Depends(get_db)):
    return db.scalars(
        select(Appointment).order_by(Appointment.id)
    ).all()


# 2. Xem chi tiet lich hen
@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    appointment = db.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay lich hen"
        )

    if current_user["role"] != "admin" and (
        appointment.patient_username != current_user["username"]
    ):
        raise HTTPException(403, "Khong co quyen truy cap lich hen")

    return appointment


# 3. Dat lich kham
@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=201
)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin" and (
        current_user["role"] != "patient"
        or data.patient_username.strip() != current_user["username"]
    ):
        raise HTTPException(403, "Chi duoc dat lich cho chinh minh")

    doctor = db.get(Doctor, data.doctor_id)

    if not doctor or not doctor.is_active:
        raise HTTPException(
            status_code=404,
            detail="Bac si khong ton tai hoac ngung hoat dong"
        )

    appointment_time = data.appointment_time

    if appointment_time.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="Thoi gian can co mui gio"
        )

    appointment_time = appointment_time.astimezone(
        timezone.utc
    )

    if appointment_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Phai dat lich trong tuong lai"
        )

    existing = db.scalar(
        select(Appointment).where(
            Appointment.doctor_id == data.doctor_id,
            Appointment.appointment_time == appointment_time,
            Appointment.status.in_(
                ["pending", "confirmed", "checked_in"]
            )
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Bac si da co lich hen vao thoi gian nay"
        )

    appointment = Appointment(
        patient_username=data.patient_username.strip(),
        doctor_id=data.doctor_id,
        appointment_time=appointment_time,
        status="pending",
        note=data.note
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
# 4. Huy lich kham
@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse
)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    appointment = db.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay lich hen"
        )

    if current_user["role"] != "admin" and (
        appointment.patient_username != current_user["username"]
    ):
        raise HTTPException(403, "Khong co quyen truy cap lich hen")

    if appointment.status not in ["pending", "confirmed"]:
        raise HTTPException(
            status_code=409,
            detail="Lich hen khong the huy"
        )

    appointment.status = "cancelled"

    db.commit()
    db.refresh(appointment)

    return appointment
# 5. Model doi lich kham
class AppointmentReschedule(BaseModel):
    appointment_time: datetime


# 6. API doi lich kham
@router.patch(
    "/{appointment_id}/reschedule",
    response_model=AppointmentResponse
)
def reschedule_appointment(
    appointment_id: int,
    data: AppointmentReschedule,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    appointment = db.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay lich hen"
        )

    if current_user["role"] != "admin" and (
        appointment.patient_username != current_user["username"]
    ):
        raise HTTPException(403, "Khong co quyen truy cap lich hen")

    if appointment.status not in ["pending", "confirmed"]:
        raise HTTPException(
            status_code=409,
            detail="Lich hen khong the doi"
        )

    new_time = data.appointment_time

    if new_time.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="Thoi gian can co mui gio"
        )

    new_time = new_time.astimezone(timezone.utc)

    if new_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Phai chon thoi gian trong tuong lai"
        )

    existing = db.scalar(
        select(Appointment).where(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.id != appointment_id,
            Appointment.appointment_time == new_time,
            Appointment.status.in_(
                ["pending", "confirmed", "checked_in"]
            )
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Bac si da co lich hen vao thoi gian nay"
        )

    appointment.appointment_time = new_time
    appointment.status = "pending"

    db.commit()
    db.refresh(appointment)

    return appointment
# 7. Xac nhan lich hen
@router.patch(
    "/{appointment_id}/confirm",
    response_model=AppointmentResponse
,
    dependencies=[Depends(require_roles('admin'))]
)
def confirm_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay lich hen"
        )

    if appointment.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Lich hen khong o trang thai cho xac nhan"
        )

    appointment.status = "confirmed"

    db.commit()
    db.refresh(appointment)

    return appointment
# 8. Check-in benh nhan
@router.patch(
    "/{appointment_id}/check-in",
    response_model=AppointmentResponse
,
    dependencies=[Depends(require_roles('admin'))]
)
def check_in_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = db.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay lich hen"
        )

    if appointment.status != "confirmed":
        raise HTTPException(
            status_code=409,
            detail="Lich hen chua duoc xac nhan hoac da check-in"
        )

    appointment.status = "checked_in"

    db.commit()
    db.refresh(appointment)

    return appointment
