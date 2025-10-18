/**
 * ATS MAFIA Real-Time WebSocket Manager
 * Enhanced version with automatic reconnection, event handling, and latency tracking
 */

class ATSRealtimeManager {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 5000;
        this.heartbeatInterval = 30000;
        this.heartbeatTimer = null;
        this.messageQueue = [];
        this.subscriptions = new Map();
        this.latency = 0;
        this.lastPingTime = null;
        this.updateCount = 0;
        
        // Connection state callbacks
        this.onConnected = null;
        this.onDisconnected = null;
        this.onReconnecting = null;
        this.onError = null;
        
        this.init();
    }

    /**
     * Initialize real-time connection
     */
    init() {
        // Use existing WebSocket client if available
        if (window.atsWebSocket) {
            this.ws = window.atsWebSocket;
            this.setupExistingClient();
        } else {
            this.connect();
        }
        
        this.updateConnectionUI();
    }

    /**
     * Setup listeners for existing WebSocket client
     */
    setupExistingClient() {
        // Subscribe to connection events
        this.ws.subscribe('connected', () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionUI('connected');
            this.startHeartbeat();
            this.processMessageQueue();
            
            if (this.onConnected) {
                this.onConnected();
            }
        });

        this.ws.subscribe('disconnected', (data) => {
            this.connected = false;
            this.updateConnectionUI('disconnected');
            this.stopHeartbeat();
            
            if (this.onDisconnected) {
                this.onDisconnected(data);
            }
            
            // Attempt reconnection
            this.scheduleReconnect();
        });

        this.ws.subscribe('error', (error) => {
            console.error('WebSocket error:', error);
            if (this.onError) {
                this.onError(error);
            }
        });

        // Subscribe to heartbeat responses
        this.ws.subscribe('heartbeat', (data) => {
            if (this.lastPingTime) {
                this.latency = Date.now() - this.lastPingTime;
                this.updateLatencyUI();
            }
        });

        // Check initial connection status
        if (this.ws.isConnected) {
            this.connected = true;
            this.updateConnectionUI('connected');
            this.startHeartbeat();
        }
    }

    /**
     * Connect to WebSocket server
     */
    async connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            // Generate unique client ID
            const clientId = this.generateClientId();
            const wsUrl = `${protocol}//${host}/ws?client_id=${clientId}`;

            this.ws = new WebSocket(wsUrl);
            this.clientId = clientId;

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionUI('connected');
                this.startHeartbeat();
                this.processMessageQueue();

                if (this.onConnected) {
                    this.onConnected();
                }
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event);
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.connected = false;
                this.updateConnectionUI('disconnected');
                this.stopHeartbeat();

                if (this.onDisconnected) {
                    this.onDisconnected({ code: event.code, reason: event.reason });
                }

                // Attempt reconnection if not a clean close
                if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                if (this.onError) {
                    this.onError(error);
                }
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.showToast('Connection lost. Please refresh the page.', 'error');
            return;
        }

        this.reconnectAttempts++;
        this.updateConnectionUI('reconnecting');

        if (this.onReconnecting) {
            this.onReconnecting(this.reconnectAttempts);
        }

        console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectDelay}ms`);

        setTimeout(() => {
            if (!this.connected) {
                this.connect();
            }
        }, this.reconnectDelay);
    }

    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.stopHeartbeat();
        
        this.heartbeatTimer = setInterval(() => {
            if (this.connected) {
                this.lastPingTime = Date.now();
                this.send({ type: 'ping', timestamp: this.lastPingTime });
            }
        }, this.heartbeatInterval);
    }

    /**
     * Stop heartbeat timer
     */
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * Handle incoming messages
     */
    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.updateCount++;
            this.updateCountUI();

            // Handle pong responses
            if (message.type === 'pong') {
                if (this.lastPingTime) {
                    this.latency = Date.now() - this.lastPingTime;
                    this.updateLatencyUI();
                }
                return;
            }

            // Emit to subscribers
            const eventType = message.type || 'message';
            this.emit(eventType, message.data || message);

            // Also emit generic message event
            this.emit('message', message);

        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    /**
     * Send message to server
     */
    send(message) {
        if (this.connected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
                this.ws.send(messageStr);
                return true;
            } catch (error) {
                console.error('Failed to send message:', error);
                return false;
            }
        } else {
            // Queue message for later
            this.messageQueue.push(message);
            return false;
        }
    }

    /**
     * Process queued messages
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.connected) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }

    /**
     * Subscribe to events
     */
    subscribe(eventType, callback) {
        if (!this.subscriptions.has(eventType)) {
            this.subscriptions.set(eventType, []);
        }
        this.subscriptions.get(eventType).push(callback);

        // If using existing client, also subscribe there
        if (this.ws && this.ws.subscribe) {
            this.ws.subscribe(eventType, callback);
        }
    }

    /**
     * Unsubscribe from events
     */
    unsubscribe(eventType, callback) {
        if (this.subscriptions.has(eventType)) {
            const callbacks = this.subscriptions.get(eventType);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }

        // If using existing client, also unsubscribe there
        if (this.ws && this.ws.unsubscribe) {
            this.ws.unsubscribe(eventType, callback);
        }
    }

    /**
     * Emit event to subscribers
     */
    emit(eventType, data) {
        if (this.subscriptions.has(eventType)) {
            this.subscriptions.get(eventType).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventType}:`, error);
                }
            });
        }
    }

    /**
     * Join a session room for updates
     */
    joinSession(sessionId) {
        if (this.ws && this.ws.joinTrainingSession) {
            this.ws.joinTrainingSession(sessionId);
        } else {
            this.send({
                type: 'join_session',
                session_id: sessionId,
                timestamp: Date.now()
            });
        }
    }

    /**
     * Leave a session room
     */
    leaveSession(sessionId) {
        if (this.ws && this.ws.leaveTrainingSession) {
            this.ws.leaveTrainingSession(sessionId);
        } else {
            this.send({
                type: 'leave_session',
                session_id: sessionId,
                timestamp: Date.now()
            });
        }
    }

    /**
     * Request session updates
     */
    requestSessionUpdate(sessionId) {
        if (this.ws && this.ws.requestTrainingUpdates) {
            this.ws.requestTrainingUpdates(sessionId);
        } else {
            this.send({
                type: 'request_update',
                session_id: sessionId,
                timestamp: Date.now()
            });
        }
    }

    /**
     * Update connection status in UI
     */
    updateConnectionUI(status = 'connecting') {
        const statusElement = document.getElementById('connectionStatus');
        if (!statusElement) return;

        const dot = statusElement.querySelector('.status-dot');
        const text = statusElement.querySelector('.status-text');

        // Remove all status classes
        statusElement.classList.remove('connected', 'connecting', 'disconnected');

        switch (status) {
            case 'connected':
                statusElement.classList.add('connected');
                if (text) text.textContent = 'Connected';
                break;
            case 'connecting':
            case 'reconnecting':
                statusElement.classList.add('connecting');
                if (text) text.textContent = this.reconnectAttempts > 0 ? 'Reconnecting...' : 'Connecting...';
                break;
            case 'disconnected':
                statusElement.classList.add('disconnected');
                if (text) text.textContent = 'Disconnected';
                break;
        }
    }

    /**
     * Update latency display in UI
     */
    updateLatencyUI() {
        const latencyElement = document.getElementById('wsLatency');
        if (latencyElement) {
            latencyElement.textContent = this.latency;
        }
    }

    /**
     * Update message count in UI
     */
    updateCountUI() {
        const countElement = document.getElementById('updateCount');
        if (countElement) {
            countElement.textContent = this.updateCount;
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };

        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas fa-${iconMap[type] || 'info-circle'}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">&times;</button>
        `;

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOutRight 0.3s ease-out';
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }
        }, 5000);

        // Close button handler
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                toast.remove();
            }, 300);
        });
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.connected,
            reconnectAttempts: this.reconnectAttempts,
            latency: this.latency,
            updateCount: this.updateCount,
            queuedMessages: this.messageQueue.length
        };
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        this.stopHeartbeat();
        
        if (this.ws) {
            if (this.ws.disconnect) {
                this.ws.disconnect();
            } else if (this.ws.close) {
                this.ws.close();
            }
        }
        
        this.connected = false;
        this.updateConnectionUI('disconnected');
    }

    /**
     * Reconnect to server
     */
    reconnect() {
        this.disconnect();
        this.reconnectAttempts = 0;
        setTimeout(() => this.connect(), 1000);
    }

    /**
     * Generate unique client ID
     */
    generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    /**
     * Send voice command
     */
    sendVoiceCommand(command) {
        this.send({
            type: 'voice_command',
            command: command,
            timestamp: Date.now()
        });
    }

    /**
     * Subscribe to topic
     */
    subscribeTopic(topic) {
        this.send({
            type: 'subscribe',
            topic: topic,
            timestamp: Date.now()
        });
    }

    /**
     * Unsubscribe from topic
     */
    unsubscribeTopic(topic) {
        this.send({
            type: 'unsubscribe',
            topic: topic,
            timestamp: Date.now()
        });
    }

    /**
     * Join training session
     */
    joinTrainingSession(sessionId) {
        this.joinSession(sessionId);
    }

    /**
     * Leave training session
     */
    leaveTrainingSession(sessionId) {
        this.leaveSession(sessionId);
    }

    /**
     * Request training updates
     */
    requestTrainingUpdates(sessionId) {
        this.requestSessionUpdate(sessionId);
    }

    /**
     * Check if connected
     */
    get isConnected() {
        return this.connected;
    }
}

// Add slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// Create global instance
window.atsRealtime = new ATSRealtimeManager();

// Auto-cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.atsRealtime) {
        window.atsRealtime.disconnect();
    }
});