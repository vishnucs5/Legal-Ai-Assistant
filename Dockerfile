FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]

