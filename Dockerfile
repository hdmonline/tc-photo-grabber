# Use Python 3.15 slim image
FROM python:3.15-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    exiftool \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY .env.example /app/.env.example

# Create directories for photos and cache
RUN mkdir -p /app/photos /app/cache

# Create a script to run the application
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Run the application based on MODE environment variable\n\
if [ "$MODE" = "cron" ]; then\n\
    echo "Starting in CRON mode with schedule: ${SCHEDULE:-daily}"\n\
    exec python -m src --cron --schedule "${SCHEDULE:-daily}"\n\
else\n\
    echo "Starting in CLI mode (run once)"\n\
    exec python -m src\n\
fi\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Environment variables (can be overridden)
ENV MODE=cron \
    SCHEDULE=daily \
    OUTPUT_DIR=/app/photos \
    CACHE_DIR=/app/cache \
    PYTHONUNBUFFERED=1

# Volume for photos and cache
VOLUME ["/app/photos", "/app/cache"]

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
