from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String, Integer, Text, DateTime,
    ForeignKey, Numeric, Boolean, func
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


# 1. Bang chuyen khoa
class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )


# 2. Bang bac si
class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    full_name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )
    specialty_id: Mapped[int] = mapped_column(
        ForeignKey("specialties.id"), nullable=False
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


# 3. Bang lich hen kham
class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    patient_username: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"), nullable=False
    )
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False
    )
    note: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )


# 4. Bang ket qua kham
class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id"),
        unique=True,
        nullable=False
    )
    diagnosis: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    treatment: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


# 5. Bang hoa don
class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id"),
        unique=True,
        nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="unpaid", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
