FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (build-essential and libpq-dev are needed for compiling psycopg2 or other C extensions if necessary, though asyncpg is pure python or precompiled)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure keys directory exists
RUN mkdir -p keys

# Expose microservice port
EXPOSE 8000

# Run FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
