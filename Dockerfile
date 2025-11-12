# ============================================
# Multi-stage Dockerfile for RAG API
# ============================================

# Stage 1: Base image with dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    tesseract-ocr \
    tesseract-ocr-vie \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development image
FROM base AS development

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed data/vectorstores logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "scripts/run_api.py"]

# Stage 3: Production image (optimized)
FROM base AS production

# Copy only necessary files
COPY src ./src
COPY config ./config
COPY scripts ./scripts
COPY .env.example ./.env

# Create necessary directories
RUN mkdir -p data/raw data/processed data/vectorstores logs && \
    # Remove unnecessary files
    find . -type d -name "__pycache__" -exec rm -rf {} + && \
    find . -type f -name "*.pyc" -delete

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn directly for better performance
CMD ["uvicorn", "src.sgk_rag.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]