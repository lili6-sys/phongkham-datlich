from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import hashlib
import secrets
import jwt
import os
from datetime import datetime, timedelta, timezone
# Tao router cho Authentication
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# Luu tai khoan tam thoi trong bo nho
users = {}

# Tao Admin thu nghiem trong moi truong local
def create_demo_admin():
    if os.getenv("ENABLE_DEMO_ADMIN") != "1":
        return

    username = "admin_demo"
    password = os.getenv("DEMO_ADMIN_PASSWORD")

    if not password or len(password) < 8:
        raise RuntimeError(
            "Can cau hinh DEMO_ADMIN_PASSWORD it nhat 8 ky tu"
        )

    if username in users:
        return

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600000
    )

    users[username] = {
        "full_name": "Demo Admin",
        "password_hash": password_hash.hex(),
        "salt": salt.hex(),
        "role": "admin"
    }


create_demo_admin()

# Cau hinh JWT cho giai doan thuc hanh
SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(username: str, role: str):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# =====================================
# 1. MODEL DANG KY TAI KHOAN
# =====================================
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
    full_name: str


# =====================================
# 2. API DANG KY TAI KHOAN
# =====================================
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    username = data.username.strip()

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Ten dang nhap khong hop le"
        )

    if username in users:
        raise HTTPException(
            status_code=400,
            detail="Tai khoan da ton tai"
        )

    # Ma hoa mat khau bang PBKDF2
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        data.password.encode("utf-8"),
        salt,
        600000
    )

    # Luu thong tin nguoi dung
    users[username] = {
        "full_name": data.full_name,
        "password_hash": password_hash.hex(),
        "salt": salt.hex(),
        "role": "patient"
    }

    return {
        "message": "Dang ky thanh cong",
        "username": username,
        "full_name": data.full_name,
        "role": "patient"
    }


# =====================================
# 3. MODEL DANG NHAP
# =====================================
class LoginRequest(BaseModel):
    username: str
    password: str


# =====================================
# 4. API DANG NHAP TAI KHOAN
# =====================================
@router.post("/login")
def login(data: LoginRequest):
    username = data.username.strip()

    # Tim tai khoan
    user = users.get(username)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Sai ten dang nhap hoac mat khau"
        )

    # Kiem tra mat khau
    salt = bytes.fromhex(user["salt"])

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        data.password.encode("utf-8"),
        salt,
        600000
    )

    stored_hash = bytes.fromhex(
        user["password_hash"]
    )

    if not secrets.compare_digest(
        password_hash,
        stored_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Sai ten dang nhap hoac mat khau"
        )

    
    # Tao JWT Token khi dang nhap thanh cong
    access_token = create_access_token(
        username=username,
        role=user["role"]
    )

    return {
        "message": "Dang nhap thanh cong",
        "username": username,
        "full_name": user["full_name"],
        "role": user["role"],
        "access_token": access_token,
        "token_type": "bearer"
    }


# Kiem tra JWT Token
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")
        user = users.get(username) if isinstance(username, str) else None

        if user is None or payload.get("role") != user["role"]:
            raise HTTPException(
                status_code=401,
                detail="Token khong hop le"
            )

        return {
            "username": username,
            "full_name": user["full_name"],
            "role": user["role"]
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token da het han"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token khong hop le"
        )


# API lay thong tin nguoi dang nhap
@router.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

# =====================================
# 5. PHAN QUYEN NGUOI DUNG
# =====================================

def require_roles(*allowed_roles: str):
    def check_role(
        current_user: dict = Depends(get_current_user)
    ):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Ban khong co quyen truy cap"
            )

        return current_user

    return check_role


# API danh cho benh nhan
@router.get("/patient-area")
def patient_area(
    current_user: dict = Depends(
        require_roles("patient")
    )
):
    return {
        "message": "Truy cap khu vuc benh nhan thanh cong",
        "username": current_user["username"],
        "role": current_user["role"]
    }


# API danh cho Admin
@router.get("/admin-area")
def admin_area(
    current_user: dict = Depends(
        require_roles("admin")
    )
):
    return {
        "message": "Truy cap khu vuc Admin thanh cong",
        "username": current_user["username"],
        "role": current_user["role"]
    }
