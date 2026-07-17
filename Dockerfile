FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY socratic_tutor/ ./socratic_tutor/

RUN python -m pip install --no-cache-dir .

CMD ["sh", "-c", "python -m uvicorn socratic_tutor.web_app:app --host 0.0.0.0 --port ${PORT}"]
