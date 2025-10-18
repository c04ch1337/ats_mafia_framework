/**
 * ATS MAFIA WebSocket Client
 * Handles real-time communication with the backend
 */

class ATSWebSocketClient {
    constructor(url = null, options = {}) {
        this.url = url || this.getWebSocketURL();
        this.options = {
            reconnectInterval: 5000,
            maxReconnectAttempts: 10,
            heartbeatInterval: 30000,
            ...options
        };
        
        this.ws = null;
        this.reconnectAttempts = 0;
        this.heartbeatTimer = null;
        this.isConnected = false;
        this.messageQueue = [];
        this.eventHandlers = new Map();
        this.connectionPromise = null;
    }

    /**
     * Get WebSocket URL based on current location
     */
    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws`;
    }

    /**
     * Connect to WebSocket server
     */
    async connect() {
        if (this.connectionPromise) {
            return this.connectionPromise;
        }

        this.connectionPromise = new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);
                
                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.startHeartbeat();
                    this.processMessageQueue();
                    this.emit('connected');
                    resolve(undefined);
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event);
                };

                this.ws.onclose = (event) => {
                    console.log('WebSocket disconnected:', event.code, event.reason);
                    this.isConnected = false;
                    this.stopHeartbeat();
                    this.emit('disconnected', { code: event.code, reason: event.reason });
                    
                    if (!event.wasClean && this.reconnectAttempts < this.options.maxReconnectAttempts) {
                        this.scheduleReconnect();
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.emit('error', error);
                    reject(error);
                };

            } catch (error) {
                console.error('Failed to create WebSocket connection:', error);
                reject(error);
            }
        });

        return this.connectionPromise;
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        this.options.maxReconnectAttempts = 0; // Prevent reconnection
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.stopHeartbeat();
        this.isConnected = false;
        this.emit('disconnected');
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        this.reconnectAttempts++;
        console.log(`Scheduling reconnection attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts}`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect().catch(error => {
                    console.error('Reconnection failed:', error);
                });
            }
        }, this.options.reconnectInterval);
    }

    /**
     * Start heartbeat to keep connection alive
     */
    startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected && this.ws) {
                this.send({ type: 'heartbeat', timestamp: Date.now() });
            }
        }, this.options.heartbeatInterval);
    }

    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.emit('message', message);
            
            // Handle specific message types
            switch (message.type) {
                case 'heartbeat':
                    this.emit('heartbeat', message);
                    break;
                case 'training_update':
                    this.emit('training_update', message.data);
                    break;
                case 'profile_update':
                    this.emit('profile_update', message.data);
                    break;
                case 'system_status':
                    this.emit('system_status', message.data);
                    break;
                case 'voice_event':
                    this.emit('voice_event', message.data);
                    break;
                case 'error':
                    this.emit('server_error', message.data);
                    break;
                default:
                    this.emit('unknown_message', message);
            }
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
            this.emit('parse_error', { data: event.data, error });
        }
    }

    /**
     * Send message to WebSocket server
     */
    send(message) {
        if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
                this.ws.send(messageStr);
                return true;
            } catch (error) {
                console.error('Failed to send WebSocket message:', error);
                return false;
            }
        } else {
            // Queue message for later sending
            this.messageQueue.push(message);
            return false;
        }
    }

    /**
     * Process queued messages
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }

    /**
     * Subscribe to specific events
     */
    subscribe(eventType, callback) {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, []);
        }
        this.eventHandlers.get(eventType).push(callback);
        
        // Send subscription message to server
        this.send({
            type: 'subscribe',
            event: eventType,
            timestamp: Date.now()
        });
    }

    /**
     * Unsubscribe from specific events
     */
    unsubscribe(eventType, callback) {
        if (this.eventHandlers.has(eventType)) {
            const handlers = this.eventHandlers.get(eventType);
            const index = handlers.indexOf(callback);
            if (index > -1) {
                handlers.splice(index, 1);
            }
            
            if (handlers.length === 0) {
                this.eventHandlers.delete(eventType);
            }
        }
        
        // Send unsubscribe message to server
        this.send({
            type: 'unsubscribe',
            event: eventType,
            timestamp: Date.now()
        });
    }

    /**
     * Emit event to all subscribers
     */
    emit(eventType, data = null) {
        if (this.eventHandlers.has(eventType)) {
            this.eventHandlers.get(eventType).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventType}:`, error);
                }
            });
        }
    }

    /**
     * Send training session command
     */
    sendTrainingCommand(sessionId, command, data = {}) {
        this.send({
            type: 'training_command',
            session_id: sessionId,
            command,
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Send profile command
     */
    sendProfileCommand(profileId, command, data = {}) {
        this.send({
            type: 'profile_command',
            profile_id: profileId,
            command,
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Send voice command
     */
    sendVoiceCommand(command, data = {}) {
        this.send({
            type: 'voice_command',
            command,
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Request system status
     */
    requestSystemStatus() {
        this.send({
            type: 'get_system_status',
            timestamp: Date.now()
        });
    }

    /**
     * Request training session updates
     */
    requestTrainingUpdates(sessionId) {
        this.send({
            type: 'get_training_updates',
            session_id: sessionId,
            timestamp: Date.now()
        });
    }

    /**
     * Join training session room
     */
    joinTrainingSession(sessionId) {
        this.send({
            type: 'join_training_session',
            session_id: sessionId,
            timestamp: Date.now()
        });
    }

    /**
     * Leave training session room
     */
    leaveTrainingSession(sessionId) {
        this.send({
            type: 'leave_training_session',
            session_id: sessionId,
            timestamp: Date.now()
        });
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.options.maxReconnectAttempts,
            queuedMessages: this.messageQueue.length
        };
    }

    /**
     * Clear all event handlers
     */
    clearEventHandlers() {
        this.eventHandlers.clear();
    }

    /**
     * Set authentication token
     */
    setAuthToken(token) {
        if (this.isConnected) {
            this.send({
                type: 'auth',
                token,
                timestamp: Date.now()
            });
        }
    }
}

// Create global WebSocket client instance
if (typeof window !== 'undefined') {
    window['atsWebSocket'] = new ATSWebSocketClient();
}

// Auto-connect when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (typeof window !== 'undefined' && window['atsWebSocket']) {
        window['atsWebSocket'].connect().catch(error => {
            console.error('Failed to connect WebSocket:', error);
        });
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ATSWebSocketClient;
}