from fastapi import FastAPI

app = FastAPI(
    title="He thong dat lich kham",
    description="DG2 - De tai 6 - Phong kham tu nhan",
    version="1.0.0"
)

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