FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

EXPOSE 8000

# Run DB migrations (if any) then start the server
# Tables are also auto-created by SQLAlchemy on startup (main.py lifespan)
CMD ["sh", "-c", "alembic upgrade head 2>&1 || echo 'Alembic migration skipped'; exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
