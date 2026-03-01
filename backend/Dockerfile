FROM python:3.11-slim

# Create a non-root user for security
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Secure file permissions globally
COPY app ./app
COPY ml ./ml

COPY . .
RUN chown -R appuser:appuser /app

# Switch to standard environment user
USER appuser

# Start Uvicorn bound natively via uvloop and httptools with keeping alive connection pooling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop", "--http", "httptools", "--timeout-keep-alive", "30"]
