FROM python:3.11-slim

COPY requirements.txt /requirements.txt

WORKDIR /app

RUN apt update && apt install -y \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
&& rm -f -r /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /requirements.txt

COPY app .
COPY data /data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
