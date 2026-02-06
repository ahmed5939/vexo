FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create data directory
RUN mkdir -p /app/data

# Environment
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/musicbot.db

# Run the bot
CMD ["python", "-m", "src.bot"]
