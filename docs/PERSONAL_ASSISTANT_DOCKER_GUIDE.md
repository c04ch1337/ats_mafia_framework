# Personal Assistant Docker Deployment Guide

## 🐳 Docker Configuration

The Personal Assistant feature is fully containerized and ready to run in Docker! All necessary dependencies, directories, and configurations are included in the Docker image.

---

## 📦 What's Included in Docker

### System Dependencies
✅ **Audio Processing**
- portaudio19-dev (for PyAudio)
- espeak (text-to-speech engine)
- python3-pyaudio

✅ **Voice Libraries**
- speechrecognition
- pyttsx3
- pyaudio

✅ **Phone Providers**
- Twilio SDK
- Plivo SDK

✅ **Web Server**
- Flask (for webhook server)
- Flask-CORS

### Directory Structure in Container
```
/app/
├── ats_mafia_framework/          # Framework code
│   ├── voice/
│   │   ├── personal_assistant.py
│   │   ├── personal_assistant_tool.py
│   │   └── personal_assistant_config.py
│   ├── ui/
│   │   └── personal_assistant_ui.py
│   └── examples/
│       └── personal_assistant_examples.py
├── recordings/
│   └── personal_assistant/        # Call recordings (persistent)
├── transcripts/
│   └── personal_assistant/        # Call transcripts (persistent)
├── data/
│   └── personal_assistant/
│       └── tasks/                 # Task history (persistent)
├── config/
│   └── runtime.yaml               # Runtime configuration
└── logs/                          # Application logs
```

---

## 🚀 Quick Start with Docker

### Method 1: Docker Run (Simple)

```bash
# Build the image
docker build -t ats-mafia:latest -f ats_mafia_framework/Dockerfile ats_mafia_framework/

# Run with mock provider (testing)
docker run -d \
  --name ats-mafia \
  -p 8080:8080 \
  -p 5000:5000 \
  -e PERSONAL_ASSISTANT_ENABLED=true \
  -e PERSONAL_ASSISTANT_PHONE_PROVIDER=mock \
  -v $(pwd)/recordings:/app/recordings \
  -v $(pwd)/transcripts:/app/transcripts \
  -v $(pwd)/data:/app/data \
  ats-mafia:latest
```

### Method 2: Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ats-mafia:
    build:
      context: ./ats_mafia_framework
      dockerfile: Dockerfile
    container_name: ats-mafia
    ports:
      - "8080:8080"  # API
      - "5000:5000"  # Webhook server
      - "8501:8501"  # Web UI
    environment:
      # Personal Assistant Configuration
      - PERSONAL_ASSISTANT_ENABLED=true
      - PERSONAL_ASSISTANT_PHONE_PROVIDER=mock
      - PERSONAL_ASSISTANT_DEFAULT_PERSONA=professional_assistant
      - PERSONAL_ASSISTANT_AUTO_RECORD=true
      - PERSONAL_ASSISTANT_MAX_CALL_DURATION=10
      
      # Twilio (uncomment and configure if using)
      # - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      # - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      # - TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}
      
      # Plivo (uncomment and configure if using)
      # - PLIVO_AUTH_ID=${PLIVO_AUTH_ID}
      # - PLIVO_AUTH_TOKEN=${PLIVO_AUTH_TOKEN}
      # - PLIVO_PHONE_NUMBER=${PLIVO_PHONE_NUMBER}
    
    volumes:
      # Persist recordings and data
      - ./recordings:/app/recordings
      - ./transcripts:/app/transcripts
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  recordings:
  transcripts:
  data:
  logs:
  config:
```

Then run:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🔧 Configuration in Docker

### Option 1: Environment Variables (Recommended for Docker)

Create `.env` file:

```bash
# Personal Assistant Feature
PERSONAL_ASSISTANT_ENABLED=true
PERSONAL_ASSISTANT_PHONE_PROVIDER=mock

# Default Settings
PERSONAL_ASSISTANT_DEFAULT_PERSONA=professional_assistant
PERSONAL_ASSISTANT_AUTO_RECORD=true
PERSONAL_ASSISTANT_MAX_CALL_DURATION=10

# Twilio Configuration (uncomment if using)
# TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# TWILIO_AUTH_TOKEN=your_auth_token_here
# TWILIO_PHONE_NUMBER=+1234567890

# Plivo Configuration (uncomment if using)
# PLIVO_AUTH_ID=MAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# PLIVO_AUTH_TOKEN=your_auth_token_here
# PLIVO_PHONE_NUMBER=+1234567890

# Rate Limiting
PERSONAL_ASSISTANT_MAX_TASKS_PER_DAY=50
PERSONAL_ASSISTANT_MAX_ACTIVE_TASKS=5

# Notifications
PERSONAL_ASSISTANT_NOTIFY_ON_APPROVAL=true
PERSONAL_ASSISTANT_NOTIFY_ON_COMPLETED=true
PERSONAL_ASSISTANT_NOTIFY_ON_FAILED=true
```

Then reference in docker-compose.yml:

```yaml
services:
  ats-mafia:
    env_file:
      - .env
```

### Option 2: Mount Configuration File

Create `config/personal_assistant.yaml`:

```yaml
voice:
  personal_assistant:
    enabled: true
    phone_provider: mock
    default_persona: professional_assistant
    auto_record_calls: true
    max_call_duration_minutes: 10
```

Mount in docker-compose.yml:

```yaml
volumes:
  - ./config/personal_assistant.yaml:/app/config/personal_assistant.yaml
```

---

## 📞 Using Twilio/Plivo in Docker

### Twilio Setup with Docker

1. **Get Twilio Credentials** (see main guide)

2. **Set Environment Variables**:
```bash
# In .env file
PERSONAL_ASSISTANT_ENABLED=true
PERSONAL_ASSISTANT_PHONE_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

3. **Expose Webhook Server**:
```yaml
services:
  ats-mafia:
    ports:
      - "5000:5000"  # Webhook server
    environment:
      - WEBHOOK_URL=https://your-domain.com/voice/twiml
```

4. **Use ngrok for Development**:
```bash
# In a separate terminal
docker run -it --rm --net=host wernight/ngrok ngrok http 5000

# Use the ngrok URL in Twilio console
# Example: https://abc123.ngrok.io/voice/twiml
```

---

## 💾 Data Persistence

### Important: Use Volumes for Persistent Data

The following directories **must** be mounted as volumes to persist data:

```yaml
volumes:
  - ./recordings:/app/recordings          # Call recordings
  - ./transcripts:/app/transcripts        # Call transcripts
  - ./data:/app/data                      # Task history and user data
  - ./logs:/app/logs                      # Application logs
  - ./config:/app/config                  # Configuration files
```

Without volumes, all call recordings and task history will be lost when container restarts!

### Backup Strategy

```bash
# Backup recordings and data
docker run --rm \
  -v ats-mafia_recordings:/source \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/recordings-$(date +%Y%m%d).tar.gz -C /source .

# Restore from backup
docker run --rm \
  -v ats-mafia_recordings:/target \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/recordings-20251018.tar.gz -C /target
```

---

## 🏗️ Building Custom Docker Image

### Build with Specific Features

```bash
# Build with all features
docker build \
  -t ats-mafia:personal-assistant \
  -f ats_mafia_framework/Dockerfile \
  --build-arg ENABLE_VOICE=true \
  --build-arg ENABLE_PERSONAL_ASSISTANT=true \
  ats_mafia_framework/

# Build optimized image (production)
docker build \
  -t ats-mafia:prod \
  -f ats_mafia_framework/Dockerfile \
  --build-arg BUILD_ENV=production \
  ats_mafia_framework/
```

### Multi-Stage Build (Smaller Image)

Create `Dockerfile.optimized`:

```dockerfile
# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    espeak \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application
WORKDIR /app
COPY . /app/ats_mafia_framework/

# Setup directories
RUN mkdir -p /app/recordings /app/transcripts /app/data

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "ats_mafia_framework.cli"]
```

---

## 🧪 Testing in Docker

### Run Examples in Container

```bash
# Start container
docker-compose up -d

# Run example scripts
docker-compose exec ats-mafia python -m ats_mafia_framework.examples.personal_assistant_examples

# Run tests
docker-compose exec ats-mafia pytest ats_mafia_framework/tests/test_personal_assistant.py -v

# Check logs
docker-compose logs -f ats-mafia
```

### Interactive Shell

```bash
# Enter container
docker-compose exec ats-mafia /bin/bash

# Inside container, test manually
python
>>> from ats_mafia_framework.voice.personal_assistant import get_personal_assistant_manager
>>> pa = get_personal_assistant_manager()
>>> # Test commands...
```

---

## 🔒 Security in Docker

### Secrets Management

Use Docker secrets instead of environment variables for sensitive data:

```yaml
version: '3.8'

services:
  ats-mafia:
    secrets:
      - twilio_auth_token
      - plivo_auth_token
    environment:
      - TWILIO_ACCOUNT_SID=ACxxxx
      - TWILIO_AUTH_TOKEN_FILE=/run/secrets/twilio_auth_token

secrets:
  twilio_auth_token:
    file: ./secrets/twilio_auth_token.txt
  plivo_auth_token:
    file: ./secrets/plivo_auth_token.txt
```

### Network Isolation

```yaml
services:
  ats-mafia:
    networks:
      - internal
      - external

networks:
  internal:
    internal: true
  external:
    driver: bridge
```

---

## 📊 Monitoring in Docker

### Health Checks

The container includes a health check endpoint:

```bash
# Check health
curl http://localhost:5000/health

# View health status
docker inspect --format='{{.State.Health.Status}}' ats-mafia
```

### Logging

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f ats-mafia

# Filter by service
docker-compose logs personal-assistant

# Last 100 lines
docker-compose logs --tail=100 ats-mafia
```

### Metrics

Access metrics endpoint:

```bash
# Get statistics
curl http://localhost:5000/api/personal-assistant/statistics

# Get active tasks
curl http://localhost:5000/api/personal-assistant/tasks/active
```

---

## 🔄 Updates and Maintenance

### Update Container

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Or force recreate
docker-compose up -d --force-recreate --build
```

### Cleanup Old Data

```bash
# Enter container
docker-compose exec ats-mafia /bin/bash

# Inside container
cd /app/recordings/personal_assistant
find . -type f -mtime +30 -delete  # Delete recordings older than 30 days

cd /app/transcripts/personal_assistant
find . -type f -mtime +30 -delete  # Delete transcripts older than 30 days
```

---

## 🌐 Production Deployment

### With Reverse Proxy (nginx)

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - ats-mafia
  
  ats-mafia:
    build: ./ats_mafia_framework
    environment:
      - PERSONAL_ASSISTANT_ENABLED=true
      - WEBHOOK_URL=https://your-domain.com/voice/twiml
    volumes:
      - recordings:/app/recordings
      - transcripts:/app/transcripts
      - data:/app/data
    networks:
      - internal

networks:
  internal:
    driver: bridge

volumes:
  recordings:
  transcripts:
  data:
```

### SSL Configuration (nginx.conf)

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location /voice/ {
        proxy_pass http://ats-mafia:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://ats-mafia:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🐛 Troubleshooting Docker

### Common Issues

**Issue**: "Audio device not found"
```bash
# Solution: Audio in Docker containers can be tricky
# For text-to-speech without audio output:
docker run -e AUDIO_OUTPUT=file ...
```

**Issue**: "Permission denied on /app/recordings"
```bash
# Solution: Check volume permissions
docker-compose exec ats-mafia ls -la /app/recordings
# If needed, fix ownership:
docker-compose exec -u root ats-mafia chown -R ats:ats /app/recordings
```

**Issue**: "Twilio webhook not reachable"
```bash
# Solution: Container needs public internet access
# Check webhook URL is publicly accessible:
curl https://your-webhook-url.com/health

# For local dev, use ngrok:
docker run -it --rm --network=host wernight/ngrok ngrok http 5000
```

**Issue**: "Module not found errors"
```bash
# Solution: Rebuild with --no-cache
docker-compose build --no-cache
docker-compose up -d
```

### Debug Mode

Run container in debug mode:

```bash
docker run -it --rm \
  -e DEBUG=true \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/recordings:/app/recordings \
  ats-mafia:latest \
  python -m ats_mafia_framework.examples.personal_assistant_examples
```

---

## 📋 Docker Compose Full Example

Complete `docker-compose.yml` with all features:

```yaml
version: '3.8'

services:
  ats-mafia:
    build:
      context: ./ats_mafia_framework
      dockerfile: Dockerfile
    container_name: ats-mafia
    hostname: ats-mafia
    
    ports:
      - "8080:8080"  # API server
      - "5000:5000"  # Webhook server
      - "8501:8501"  # Web UI
    
    environment:
      # Core Framework
      - FRAMEWORK_ENV=production
      - LOG_LEVEL=INFO
      - DEBUG=false
      
      # Personal Assistant
      - PERSONAL_ASSISTANT_ENABLED=true
      - PERSONAL_ASSISTANT_PHONE_PROVIDER=${PHONE_PROVIDER:-mock}
      - PERSONAL_ASSISTANT_DEFAULT_PERSONA=professional_assistant
      - PERSONAL_ASSISTANT_AUTO_RECORD=true
      - PERSONAL_ASSISTANT_MAX_CALL_DURATION=10
      
      # Phone Provider (Twilio)
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID:-}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN:-}
      - TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER:-}
      
      # Phone Provider (Plivo)
      - PLIVO_AUTH_ID=${PLIVO_AUTH_ID:-}
      - PLIVO_AUTH_TOKEN=${PLIVO_AUTH_TOKEN:-}
      - PLIVO_PHONE_NUMBER=${PLIVO_PHONE_NUMBER:-}
      
      # Paths
      - RECORDING_PATH=/app/recordings/personal_assistant/
      - TRANSCRIPT_PATH=/app/transcripts/personal_assistant/
      - TASK_HISTORY_PATH=/app/data/personal_assistant/tasks/
      
      # Rate Limiting
      - MAX_TASKS_PER_DAY=50
      - MAX_ACTIVE_TASKS=5
      
      # Notifications
      - NOTIFY_ON_TASK_AWAITING_APPROVAL=true
      - NOTIFY_ON_CALL_COMPLETED=true
      - NOTIFY_ON_TASK_FAILED=true
      
      # Webhook
      - WEBHOOK_URL=${WEBHOOK_URL:-http://localhost:5000/voice/twiml}
    
    volumes:
      # Persistent data
      - recordings:/app/recordings
      - transcripts:/app/transcripts
      - task_data:/app/data
      - logs:/app/logs
      
      # Configuration (optional)
      - ./config:/app/config:ro
    
    networks:
      - ats-network
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    labels:
      - "com.atsmafia.service=main"
      - "com.atsmafia.personal-assistant=enabled"

  # Optional: Webhook server (if separate)
  webhook-server:
    build:
      context: ./webhook
      dockerfile: Dockerfile
    container_name: ats-webhook
    ports:
      - "5001:5000"
    environment:
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
    networks:
      - ats-network
    depends_on:
      - ats-mafia

networks:
  ats-network:
    driver: bridge

volumes:
  recordings:
    driver: local
  transcripts:
    driver: local
  task_data:
    driver: local
  logs:
    driver: local
```

---

## 🚀 Production Deployment Checklist

### Pre-Deployment
- [ ] All code files present in image
- [ ] Dependencies installed correctly
- [ ] Configuration validated
- [ ] Volumes configured for persistence
- [ ] Environment variables set
- [ ] Secrets properly managed
- [ ] Network configured correctly

### Phone Provider Setup
- [ ] Provider credentials configured
- [ ] Phone number activated
- [ ] Webhook server accessible
- [ ] Webhook URL configured in provider console
- [ ] Test call successful
- [ ] Recording working
- [ ] Transcription working

### Security
- [ ] Using secrets for credentials (not env vars in production)
- [ ] HTTPS enabled for webhooks
- [ ] Network isolation configured
- [ ] Container runs as non-root user
- [ ] Volume permissions correct
- [ ] Firewall rules configured

### Monitoring
- [ ] Health check endpoint working
- [ ] Logging configured
- [ ] Metrics accessible
- [ ] Alerts configured
- [ ] Backup strategy in place

---

## 📦 Docker Commands Reference

### Build
```bash
# Build image
docker build -t ats-mafia:latest -f ats_mafia_framework/Dockerfile ats_mafia_framework/

# Build with docker-compose
docker-compose build

# Build without cache
docker-compose build --no-cache
```

### Run
```bash
# Start services
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up ats-mafia
```

### Manage
```bash
# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

### Debug
```bash
# View logs
docker-compose logs -f

# Enter container
docker-compose exec ats-mafia /bin/bash

# Run command in container
docker-compose exec ats-mafia python -m ats_mafia_framework.cli --help

# Check container status
docker-compose ps

# Inspect container
docker inspect ats-mafia
```

---

## ✅ Verification Steps

After deployment, verify everything works:

```bash
# 1. Check container is running
docker-compose ps

# 2. Check health
curl http://localhost:5000/health

# 3. Check Personal Assistant status
docker-compose exec ats-mafia python -c "
from ats_mafia_framework.voice.personal_assistant import get_personal_assistant_manager
pa = get_personal_assistant_manager()
print('Enabled:', pa.enabled if pa else 'Not initialized')
print('Statistics:', pa.get_statistics() if pa else 'N/A')
"

# 4. Run test task
docker-compose exec ats-mafia python -m ats_mafia_framework.examples.personal_assistant_examples

# 5. Check recordings directory
docker-compose exec ats-mafia ls -la /app/recordings/personal_assistant/
```

---

## 🎯 Summary

Yes, **everything is Docker-ready!** ✅

The Personal Assistant feature is fully containerized with:
- All dependencies installed
- Audio libraries configured
- Phone provider SDKs included
- Directories created and permissions set
- Volume mounts for persistence
- Health checks configured
- Environment variable support
- Docker Compose ready

Just use the provided docker-compose.yml and configure your phone provider credentials!