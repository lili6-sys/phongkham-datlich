from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .models import Specialty


router = APIRouter(
    prefix="/api/specialties",
    tags=["Specialties"]
)


class SpecialtyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None


class SpecialtyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


# 1. Lay danh sach chuyen khoa
@router.get("/", response_model=list[SpecialtyResponse])
def get_specialties(db: Session = Depends(get_db)):
    return db.scalars(
        select(Specialty).order_by(Specialty.id)
    ).all()


# 2. Xem chi tiet chuyen khoa
@router.get("/{specialty_id}", response_model=SpecialtyResponse)
def get_specialty(
    specialty_id: int,
    db: Session = Depends(get_db)
):
    specialty = db.get(Specialty, specialty_id)

    if not specialty:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay chuyen khoa"
        )

    return specialty


# 3. Them chuyen khoa
@router.post("/", response_model=SpecialtyResponse, status_code=201)
def create_specialty(
    data: SpecialtyCreate,
    db: Session = Depends(get_db)
):
    name = data.name.strip()

    if len(name) < 2:
        raise HTTPException(
            status_code=422,
            detail="Ten chuyen khoa khong hop le"
        )

    specialty = Specialty(
        name=name,
        description=data.description
    )

    db.add(specialty)

    try:
        db.commit()
        db.refresh(specialty)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Chuyen khoa da ton tai"
        )

    return specialty


# 4. Cap nhat chuyen khoa
@router.put("/{specialty_id}", response_model=SpecialtyResponse)
def update_specialty(
    specialty_id: int,
    data: SpecialtyCreate,
    db: Session = Depends(get_db)
):
    specialty = db.get(Specialty, specialty_id)

    if not specialty:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay chuyen khoa"
        )

    name = data.name.strip()

    if len(name) < 2:
        raise HTTPException(
            status_code=422,
            detail="Ten chuyen khoa khong hop le"
        )

    specialty.name = name
    specialty.description = data.description

    try:
        db.commit()
        db.refresh(specialty)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Chuyen khoa da ton tai"
        )

    return specialty


# 5. Xoa chuyen khoa
@router.delete("/{specialty_id}")
def delete_specialty(
    specialty_id: int,
    db: Session = Depends(get_db)
):
    specialty = db.get(Specialty, specialty_id)
    if not specialty:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay chuyen khoa"
        )

    try:
        db.delete(specialty)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Chuyen khoa dang duoc su dung"
        )

    return {"message": "Xoa chuyen khoa thanh cong"}
