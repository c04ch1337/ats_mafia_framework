# ATS MAFIA Framework Dockerfile
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app:/app/ats_mafia_framework

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    netcat-openbsd \
    nmap \
    libpcap-dev \
    portaudio19-dev \
    python3-pyaudio \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    && rm -rf /var/lib/apt/lists/*

# Create the ats_mafia_framework directory
RUN mkdir -p /app/ats_mafia_framework

# Copy requirements first for better caching
COPY requirements.txt /app/ats_mafia_framework/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r /app/ats_mafia_framework/requirements.txt && \
    pip install python-nmap scapy websockets fastapi uvicorn

# Copy the framework files
COPY . /app/ats_mafia_framework/

# Copy tools separately to ensure they're available at /app/tools/
COPY ./tools /app/tools

# Install the framework in development mode
RUN cd /app/ats_mafia_framework && pip install -e .

# Create necessary directories
RUN mkdir -p /app/logs /app/config /app/profiles /app/scenarios \
    /app/recordings/personal_assistant \
    /app/transcripts/personal_assistant \
    /app/data/personal_assistant/tasks

# Copy default configuration if it exists
RUN if [ -f /app/ats_mafia_framework/config/default.yaml ]; then \
        cp /app/ats_mafia_framework/config/default.yaml /app/config/runtime.yaml; \
    fi

# Create a non-root user
RUN useradd --create-home --shell /bin/bash ats && \
    chown -R ats:ats /app && \
    chown -R ats:ats /app/recordings && \
    chown -R ats:ats /app/transcripts && \
    chown -R ats:ats /app/data
USER ats

# Expose ports
EXPOSE 8080 8501 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command - run the FastAPI container management server
CMD ["uvicorn", "ats_mafia_framework.api.container_app_example:app", "--host", "0.0.0.0", "--port", "5000"]