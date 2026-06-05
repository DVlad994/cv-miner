FROM python:3.11-slim

# системные зависимости: Tesseract (OCR, рус+англ) и poppler (pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# сначала зависимости, слой кешируется, пока requirements не меняются
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# затем код
COPY backend/ ./backend/

WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

# по умолчанию запускаем API через gunicorn; worker переопределяет команду в compose
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "app:app"]
