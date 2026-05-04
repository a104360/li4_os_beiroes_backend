# --- STAGE 1: Build Stage ---
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install dependencies into a specific folder
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- STAGE 2: Runtime Stage ---
FROM python:3.11-slim-bookworm

# Security: Create a non-privileged user
RUN groupadd -r beiroes && useradd -r -g beiroes beiroes

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/app

WORKDIR /app

# Install ONLY the runtime library for Postgres (no headers/compilers)
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

# Copy only the installed python packages from the builder
COPY --from=builder /install /usr/local
COPY . .

# Change ownership to the non-root user
RUN chown -R beiroes:beiroes /app
USER beiroes

EXPOSE 8080

# Production Tip: Use Gunicorn instead of 'python app/main.py'
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app.main:app"]
# CMD ["python", "app/main.py"]