# Use Python 3.15 slim image
FROM python:3.14-slim

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
RUN mkdir -p photos /cache

# Create a script to run the application
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Run the application based on MODE environment variable\n\
if [ "$MODE" = "cron" ]; then\n\
    # Build the command with cron options\n\
    CMD="python -m src --cron"\n\
    \n\
    # Use cron expression if provided, otherwise use schedule\n\
    if [ -n "$CRON_EXPRESSION" ]; then\n\
        echo "Starting in CRON mode with cron expression: $CRON_EXPRESSION"\n\
        CMD="$CMD --cron-expression \"$CRON_EXPRESSION\""\n\
    else\n\
        echo "Starting in CRON mode with schedule: ${SCHEDULE:-daily}"\n\
        CMD="$CMD --schedule \"${SCHEDULE:-daily}\""\n\
    fi\n\
    \n\
    # Add run-immediately flag if set\n\
    if [ "$RUN_IMMEDIATELY" = "true" ]; then\n\
        echo "Will run immediately on startup"\n\
        CMD="$CMD --run-immediately"\n\
    fi\n\
    \n\
    eval "exec $CMD"\n\
else\n\
    echo "Starting in CLI mode (run once)"\n\
    exec python -m src\n\
fi\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Environment variables (can be overridden)
ENV MODE=cron \
    SCHEDULE=daily \
    OUTPUT_DIR=/photos \
    CACHE_DIR=/cache \
    PYTHONUNBUFFERED=1
# Optional: CRON_EXPRESSION - takes precedence over SCHEDULE (e.g., "0 2 * * *")
# Optional: RUN_IMMEDIATELY - set to "true" to run immediately on startup

# Volume for photos and cache
VOLUME ["/photos", "/cache"]

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
