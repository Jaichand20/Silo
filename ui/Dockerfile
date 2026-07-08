FROM python:3.12-slim

WORKDIR /app

COPY static/ ./static

CMD ["python", "-m", "http.server", "8501", "--directory", "static"]
