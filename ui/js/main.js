/**
 * ATS MAFIA Main JavaScript
 * Main application entry point and initialization
 */

class ATSApplication {
    constructor() {
        this.version = '1.0.0';
        this.isInitialized = false;
        this.modules = new Map();
        
        // Load config from window.ATS_CONFIG (set by config.js from env.js) with fallbacks
        const baseConfig = (typeof window !== 'undefined' && window.ATS_CONFIG) ? window.ATS_CONFIG : {};
        
        this.config = {
            apiBaseURL: baseConfig.apiBaseURL || 'http://localhost:8000/api/v1',
            websocketURL: baseConfig.websocketURL || 'ws://localhost:8080/ws',
            autoRefresh: baseConfig.autoRefresh !== undefined ? baseConfig.autoRefresh : true,
            refreshInterval: baseConfig.refreshInterval || 30000,
            enableVoiceControl: baseConfig.enableVoiceControl !== undefined ? baseConfig.enableVoiceControl : true,
            enableNotifications: baseConfig.enableNotifications !== undefined ? baseConfig.enableNotifications : true,
            theme: baseConfig.theme || 'dark'
        };
        
        console.log('ATSApplication: loaded config with apiBaseURL =', this.config.apiBaseURL);
        
        this.init();
    }

    /**
     * Initialize application
     */
    async init() {
        console.log(`ATS MAFIA v${this.version} - Initializing...`);
        
        try {
            // Load configuration
            await this.loadConfiguration();
            
            // Initialize modules
            await this.initializeModules();
            
            // Set up global error handling
            this.setupErrorHandling();
            
            // Set up keyboard shortcuts
            this.setupKeyboardShortcuts();
            
            // Initialize theme
            this.initializeTheme();
            
            // Check authentication
            await this.checkAuthentication();
            
            // Show welcome message
            this.showWelcomeMessage();
            
            this.isInitialized = true;
            console.log('ATS MAFIA initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize ATS MAFIA:', error);
            this.showCriticalError(error);
        }
    }

    /**
     * Load configuration
     */
    async loadConfiguration() {
        try {
            // Load from localStorage
            const storedConfig = localStorage.getItem('ats_config');
            if (storedConfig) {
                this.config = { ...this.config, ...JSON.parse(storedConfig) };
            }
            
            // Load from API if available
            if (window.atsAPI) {
                try {
                    const apiConfig = await window.atsAPI.getConfiguration();
                    this.config = { ...this.config, ...apiConfig };
                } catch (error) {
                    console.warn('Failed to load configuration from API:', error);
                }
            }
            
            // Update API client configuration
            if (window.atsAPI) {
                window.atsAPI.baseURL = this.config.apiBaseURL;
            }
            
            // Update WebSocket client configuration
            if (window.atsWebSocket) {
                window.atsWebSocket.url = this.config.websocketURL;
            }
            
        } catch (error) {
            console.error('Failed to load configuration:', error);
        }
    }

    /**
     * Save configuration
     */
    async saveConfiguration() {
        try {
            localStorage.setItem('ats_config', JSON.stringify(this.config));
            
            if (window.atsAPI) {
                await window.atsAPI.updateConfiguration(this.config);
            }
        } catch (error) {
            console.error('Failed to save configuration:', error);
        }
    }

    /**
     * Initialize modules
     */
    async initializeModules() {
        console.log('Initializing modules...');
        
        // Initialize WebSocket connection
        if (window.atsWebSocket) {
            try {
                await window.atsWebSocket.connect();
                console.log('WebSocket connected');
            } catch (error) {
                console.warn('Failed to connect WebSocket:', error);
            }
        }
        
        // Initialize dashboard
        if (window.atsDashboard) {
            console.log('Dashboard initialized');
        }
        
        // Initialize components
        if (window.atsComponents) {
            console.log('Components initialized');
        }
        
        // Set up periodic tasks
        this.setupPeriodicTasks();
    }

    /**
     * Setup error handling
     */
    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.logError('Global Error', event.error);
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.logError('Unhandled Promise Rejection', event.reason);
        });

        // API error handling
        if (window.atsAPI) {
            const originalRequest = window.atsAPI.request.bind(window.atsAPI);
            window.atsAPI.request = async (endpoint, options) => {
                try {
                    return await originalRequest(endpoint, options);
                } catch (error) {
                    this.handleAPIError(error, endpoint, options);
                    throw error;
                }
            };
        }
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K: Quick search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.showQuickSearch();
            }
            
            // Ctrl/Cmd + /: Show shortcuts
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.showKeyboardShortcuts();
            }
            
            // F11: Toggle fullscreen
            if (e.key === 'F11') {
                e.preventDefault();
                this.toggleFullscreen();
            }
            
            // Ctrl/Cmd + Shift + V: Toggle voice control
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'V') {
                e.preventDefault();
                this.toggleVoiceControl();
            }
        });
    }

    /**
     * Initialize theme
     */
    initializeTheme() {
        const theme = this.config.theme || 'dark';
        document.body.setAttribute('data-theme', theme);
        
        // Watch for system theme changes
        if (window.matchMedia) {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            darkModeQuery.addListener((e) => {
                if (this.config.theme === 'system') {
                    document.body.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    /**
     * Check authentication
     */
    async checkAuthentication() {
        try {
            if (window.atsAPI) {
                // Try to get user info to verify authentication
                await window.atsAPI.getSystemStatus();
            }
        } catch (error) {
            console.warn('Authentication check failed:', error);
            // Redirect to login if needed
            // this.redirectToLogin();
        }
    }

    /**
     * Setup periodic tasks
     */
    setupPeriodicTasks() {
        if (this.config.autoRefresh) {
            setInterval(() => {
                this.performPeriodicUpdate();
            }, this.config.refreshInterval);
        }
    }

    /**
     * Perform periodic update
     */
    async performPeriodicUpdate() {
        try {
            // Update system status
            if (window.atsDashboard && window.atsAPI) {
                await window.atsDashboard.loadSystemStatus();
            }
        } catch (error) {
            console.error('Periodic update failed:', error);
        }
    }

    /**
     * Show welcome message
     */
    showWelcomeMessage() {
        const lastVisit = localStorage.getItem('ats_last_visit');
        const now = new Date().toISOString();
        
        if (!lastVisit || this.isNewDay(lastVisit, now)) {
            if (window.atsComponents) {
                window.atsComponents.showNotification(
                    'Welcome to ATS MAFIA Headquarters',
                    'success',
                    {
                        title: 'Welcome',
                        autoHide: 8000
                    }
                );
            }
        }
        
        localStorage.setItem('ats_last_visit', now);
    }

    /**
     * Check if it's a new day
     */
    isNewDay(lastVisit, now) {
        const last = new Date(lastVisit);
        const current = new Date(now);
        return last.toDateString() !== current.toDateString();
    }

    /**
     * Show critical error
     */
    showCriticalError(error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'critical-error';
        errorDiv.innerHTML = `
            <div class="error-content">
                <h2>Critical Error</h2>
                <p>ATS MAFIA failed to initialize properly.</p>
                <p><strong>Error:</strong> ${error.message}</p>
                <button onclick="location.reload()">Reload Application</button>
            </div>
        `;
        document.body.appendChild(errorDiv);
    }

    /**
     * Log error
     */
    logError(type, error) {
        const errorLog = {
            type,
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        console.error('Error logged:', errorLog);
        
        // Send to server if available
        if (window.atsAPI) {
            window.atsAPI.request('/errors', {
                method: 'POST',
                body: JSON.stringify(errorLog)
            }).catch(() => {
                // Ignore logging errors
            });
        }
    }

    /**
     * Handle API error
     */
    handleAPIError(error, endpoint, options) {
        console.error(`API Error (${endpoint}):`, error);
        
        if (window.atsComponents) {
            let message = 'API request failed';
            
            if (error.message.includes('401')) {
                message = 'Authentication required';
            } else if (error.message.includes('403')) {
                message = 'Access denied';
            } else if (error.message.includes('404')) {
                message = 'Resource not found';
            } else if (error.message.includes('500')) {
                message = 'Server error';
            }
            
            window.atsComponents.showNotification(message, 'error');
        }
    }

    /**
     * Show quick search
     */
    showQuickSearch() {
        if (window.atsComponents) {
            const modal = window.atsComponents.openModal(
                'quick-search-modal',
                'Quick Search',
                `
                    <div class="search-container">
                        <input type="text" class="ats-form-input" placeholder="Search profiles, scenarios, sessions..." id="quick-search-input">
                        <div class="search-results" id="quick-search-results"></div>
                    </div>
                `,
                { size: 'large' }
            );
            
            const input = modal.querySelector('#quick-search-input');
            const results = modal.querySelector('#quick-search-results');
            
            input.focus();
            
            input.addEventListener('input', this.debounce(async (e) => {
                const query = e.target.value.trim();
                if (query.length < 2) {
                    results.innerHTML = '';
                    return;
                }
                
                try {
                    const [profiles, scenarios] = await Promise.all([
                        window.atsAPI.searchProfiles(query),
                        window.atsAPI.searchScenarios(query)
                    ]);
                    
                    results.innerHTML = this.renderSearchResults(profiles, scenarios, query);
                } catch (error) {
                    results.innerHTML = '<p>Search failed</p>';
                }
            }, 300));
        }
    }

    /**
     * Render search results
     */
    renderSearchResults(profiles, scenarios, query) {
        let html = '';
        
        if (profiles.length > 0) {
            html += '<h4>Profiles</h4>';
            profiles.forEach(profile => {
                html += `<div class="search-result-item">
                    <strong>${profile.name}</strong>
                    <p>${profile.description}</p>
                </div>`;
            });
        }
        
        if (scenarios.length > 0) {
            html += '<h4>Scenarios</h4>';
            scenarios.forEach(scenario => {
                html += `<div class="search-result-item">
                    <strong>${scenario.name}</strong>
                    <p>${scenario.description}</p>
                </div>`;
            });
        }
        
        if (!html) {
            html = '<p>No results found</p>';
        }
        
        return html;
    }

    /**
     * Show keyboard shortcuts
     */
    showKeyboardShortcuts() {
        if (window.atsComponents) {
            window.atsComponents.openModal(
                'keyboard-shortcuts-modal',
                'Keyboard Shortcuts',
                `
                    <div class="shortcuts-list">
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd> + <kbd>K</kbd>
                            <span>Quick search</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd> + <kbd>/</kbd>
                            <span>Show shortcuts</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>F11</kbd>
                            <span>Toggle fullscreen</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd>
                            <span>Toggle voice control</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Esc</kbd>
                            <span>Close modal</span>
                        </div>
                    </div>
                `
            );
        }
    }

    /**
     * Toggle fullscreen
     */
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }

    /**
     * Toggle voice control
     */
    toggleVoiceControl() {
        if (window.atsDashboard) {
            window.atsDashboard.toggleVoiceControl();
        }
    }

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Get application info
     */
    getInfo() {
        return {
            version: this.version,
            initialized: this.isInitialized,
            config: this.config,
            modules: Array.from(this.modules.keys())
        };
    }

    /**
     * Restart application
     */
    async restart() {
        console.log('Restarting ATS MAFIA...');
        
        // Cleanup
        this.cleanup();
        
        // Wait a moment
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Reload page
        location.reload();
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        // Disconnect WebSocket
        if (window.atsWebSocket) {
            window.atsWebSocket.disconnect();
        }
        
        // Clear intervals
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Clear modules
        this.modules.clear();
        
        this.isInitialized = false;
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    window.atsApp = new ATSApplication();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ATSApplication;
}