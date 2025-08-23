# Use Python 3.11 slim for smaller image size and better performance
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Configure Gunicorn for Cloud Run
# - Single worker to avoid memory issues on small instances
# - Multiple threads for I/O bound operations
# - Timeout 0 for long-running ffmpeg operations
# - Preload app for better performance
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --preload app:app
