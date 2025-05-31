FROM python:3.10.1-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ✅ 把整個 backend 複製到容器的 /app/backend
COPY backend /app/backend

# ✅ 設定為工作目錄
WORKDIR /app/backend

ENV PYTHONPATH=/app/backend
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5001

CMD ["python", "init_db.py", "&&", "python", "app.py"]
