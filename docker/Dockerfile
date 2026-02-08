FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers for browser-use
RUN pip install --no-cache-dir playwright && playwright install --with-deps chromium

# Python deps
COPY jeph2sworm-core/pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source
COPY jeph2sworm-core/ ./

# Expose server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["python", "-m", "jeph2sworm.main"]
