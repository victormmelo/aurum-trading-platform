FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY apps/api ./apps/api
COPY services ./services
RUN pip install --no-cache-dir setuptools && \
    pip install --no-cache-dir --no-build-isolation -e ./apps/api

WORKDIR /workspace

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "/workspace/apps/api", "--host", "0.0.0.0", "--port", "8000"]
