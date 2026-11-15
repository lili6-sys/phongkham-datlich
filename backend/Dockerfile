
FROM python:3.13-slim

WORKDIR /app

# Cai dat thu vien Python
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Sao chep ma nguon Backend
COPY app ./app

# Cong chay FastAPI
EXPOSE 8000

# Khoi dong ung dung
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
