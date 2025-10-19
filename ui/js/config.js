/**
 * ATS MAFIA UI Configuration
 * Environment-based configuration that can be injected at deployment time
 * 
 * This file can be generated/replaced by build scripts or environment variable substitution
 */

(function() {
    // Default configuration
    window.ATS_CONFIG = {
        // API Configuration
        apiBaseURL: 'http://localhost:8000/api/v1',
        websocketURL: 'ws://localhost:8080/ws',
        
        // UI Settings
        theme: 'dark',
        autoRefresh: true,
        refreshInterval: 30000,
        
        // Feature Flags
        enableVoiceControl: true,
        enableNotifications: true,
        enableAnalytics: true,
        
        // Environment
        environment: 'development',
        version: '1.0.0'
    };

    // Override with environment variables if available (injected by server/build)
    if (typeof window.ENV !== 'undefined') {
        if (window.ENV.API_HOST && window.ENV.API_PORT) {
            const protocol = window.ENV.API_PROTOCOL || 'http';
            window.ATS_CONFIG.apiBaseURL = `${protocol}://${window.ENV.API_HOST}:${window.ENV.API_PORT}/api/v1`;
        }
        
        if (window.ENV.WEBSOCKET_HOST && window.ENV.WEBSOCKET_PORT) {
            const wsProtocol = window.ENV.WEBSOCKET_PROTOCOL || 'ws';
            window.ATS_CONFIG.websocketURL = `${wsProtocol}://${window.ENV.WEBSOCKET_HOST}:${window.ENV.WEBSOCKET_PORT}/ws`;
        }
        
        if (window.ENV.ENVIRONMENT) {
            window.ATS_CONFIG.environment = window.ENV.ENVIRONMENT;
        }
    }

    // Log configuration in development
    if (window.ATS_CONFIG.environment === 'development') {
        console.log('ATS MAFIA Configuration loaded:', window.ATS_CONFIG);
    }
})();