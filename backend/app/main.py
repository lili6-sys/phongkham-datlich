
from fastapi import FastAPI

# Authentication - Linh
from .auth import router as auth_router

# Backend - Hao
from .specialties import router as specialties_router
from .doctors import router as doctors_router
from .appointments import router as appointments_router
from .medical_records import router as medical_records_router
from .invoices import router as invoices_router
from .patient_history import router as history_router

app = FastAPI(
    title="He thong dat lich kham",
    description="DG2 - De tai 6 - Phong kham tu nhan",
    version="1.0.0"
)

# Ket noi JWT cua Linh
app.include_router(auth_router)

# Ket noi API cua Hao
app.include_router(specialties_router)
app.include_router(doctors_router)
app.include_router(appointments_router)
app.include_router(medical_records_router)
app.include_router(invoices_router)
app.include_router(history_router)


@app.get("/")
def home():
    return {
        "message": "Chao mung den voi he thong dat lich kham"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }
