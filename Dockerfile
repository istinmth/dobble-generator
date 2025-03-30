FROM python:3.10-slim

WORKDIR /app

# Install required system packages
# Install required system packages
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    libpango1.0-dev \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    wget \
    curl \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/uploads/icons /app/uploads/exports /app/logs /app/static/default_icons

# Copy application files
COPY *.py /app/
COPY entrypoint.sh /app/
COPY templates/ /app/templates/
COPY static/ /app/static/

# Set permissions
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/*.py
RUN chmod -R 777 /app/uploads /app/logs

# Volume for persistent storage
VOLUME ["/app/uploads", "/app/logs"]

# Expose port for web UI
EXPOSE 8920

# Add Unraid-specific labels
LABEL \
    org.opencontainers.image.title="Dobble Card Generator" \
    org.opencontainers.image.description="Generate Dobble/Spot It cards from your own images" \
    org.opencontainers.image.version="1.0.0" \
    com.unraid.docker.icon="https://cdn-icons-png.flaticon.com/512/4696/4696624.png" \
    com.unraid.docker.webui="http://[IP]:[PORT:8920]/" \
    com.unraid.docker.defaultport="8920" \
    com.unraid.docker.support="https://github.com/istinmth/dobble-generator/issues" \
    com.unraid.docker.overview="Dobble Card Generator"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8920/health || exit 1

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]