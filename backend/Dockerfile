FROM python:3.11-slim

# ffmpeg is required by faster-whisper/whisper for audio decoding
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-postgres.txt .
RUN pip install --no-cache-dir -r requirements-postgres.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
