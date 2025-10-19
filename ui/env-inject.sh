#!/bin/sh
# Environment Variable Injection Script for ATS MAFIA UI
# This script generates a JavaScript file with environment configuration from docker-compose

cat > /app/ats_mafia_framework/ui/js/env.js <<EOF
/**
 * ATS MAFIA Environment Configuration
 * Auto-generated from environment variables
 * DO NOT EDIT MANUALLY - This file is generated at container startup
 */

window.ENV = {
    API_HOST: '${API_HOST:-localhost}',
    API_PORT: '${API_PORT:-8000}',
    API_PROTOCOL: '${API_PROTOCOL:-http}',
    WEBSOCKET_HOST: '${WEBSOCKET_HOST:-localhost}',
    WEBSOCKET_PORT: '${WEBSOCKET_PORT:-8080}',
    WEBSOCKET_PROTOCOL: '${WEBSOCKET_PROTOCOL:-ws}',
    ENVIRONMENT: '${FRAMEWORK_ENV:-production}',
    UI_PORT: '${UI_PORT:-8501}'
};

console.log('Environment configuration loaded:', window.ENV);
EOF

echo "Generated env.js with API_HOST=${API_HOST:-localhost}, API_PORT=${API_PORT:-8000}"