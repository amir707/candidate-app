# Built by Cloud Build via `gcloud run deploy --source` (no local Docker).
FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY flags.json .

# Cloud Run injects PORT; default for local runs.
ENV PORT=8080
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
