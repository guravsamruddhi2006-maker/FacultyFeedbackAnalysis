FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY database/ ./database/
COPY ml/ ./ml/

ENV APP_ENV=production \
    DB_HOST=db \
    DB_PORT=5432 \
    DB_NAME=faculty_feedback \
    DB_USER=postgres \
    DB_PASSWORD=postgres

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
