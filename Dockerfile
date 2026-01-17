# Dockerfile for loco
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better caching
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source
COPY src/ src/

# Install the package
RUN pip install --no-cache-dir -e .

# Set working directory for mounted projects
WORKDIR /workspace

ENTRYPOINT ["loco"]
