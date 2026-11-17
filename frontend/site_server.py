
from pathlib import Path
import sys

from fastapi.staticfiles import StaticFiles

# Duong dan thu muc du an
ROOT = Path(__file__).resolve().parents[1]

# Su dung Backend da co cua nhom
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app

# Ket noi giao dien cua Quynh voi API
app.mount(
    "/web",
    StaticFiles(
        directory=str(ROOT / "frontend"),
        html=True
    ),
    name="frontend"
)
