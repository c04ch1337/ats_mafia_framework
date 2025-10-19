/**
 * ATS MAFIA Dashboard JavaScript
 * Handles dashboard functionality and real-time updates
 */

class ATSDashboard {
    constructor() {
        this.currentPage = 'dashboard';
        this.trainingSessions = new Map();
        this.performanceChart = null;
        this.systemStatus = null;
        this.notifications = [];
        this.refreshInterval = null;
        
        this.init();
    }

    /**
     * Initialize dashboard
     */
    async init() {
        console.log('Initializing ATS Dashboard...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Set up WebSocket listeners
        this.setupWebSocketListeners();
        
        // Load initial data
        await this.loadInitialData();
        
        // Start auto-refresh
        this.startAutoRefresh();
        
        // Initialize performance chart
        this.initPerformanceChart();
        
        console.log('ATS Dashboard initialized successfully');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const page = link.dataset.page;
                if (page) {
                    e.preventDefault();
                    this.navigateToPage(page);
                }
                // If no data-page attribute, allow the browser to follow the href normally
            });
        });

        // Quick action buttons
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.dataset.action;
                this.handleQuickAction(action);
            });
        });

        // Voice control button
        const voiceBtn = document.getElementById('voiceControlBtn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => {
                this.toggleVoiceControl();
            });
        }

        // Session action buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('session-monitor-btn')) {
                const sessionId = e.target.dataset.sessionId;
                this.monitorSession(sessionId);
            } else if (e.target.classList.contains('session-stop-btn')) {
                const sessionId = e.target.dataset.sessionId;
                this.stopSession(sessionId);
            }
        });

        // Performance filter
        const performanceFilter = document.querySelector('.performance-filter');
        if (performanceFilter) {
            performanceFilter.addEventListener('change', (e) => {
                this.updatePerformanceChart(e.target.value);
            });
        }
    }

    /**
     * Set up WebSocket listeners
     */
    setupWebSocketListeners() {
        if (window.atsWebSocket) {
            // Connection events
            window.atsWebSocket.subscribe('connected', () => {
                this.showNotification('Connected to ATS Server', 'success');
                this.loadSystemStatus();
            });

            window.atsWebSocket.subscribe('disconnected', () => {
                this.showNotification('Disconnected from ATS Server', 'error');
            });

            // Training updates
            window.atsWebSocket.subscribe('training_update', (data) => {
                this.updateTrainingSession(data);
            });

            // System status updates
            window.atsWebSocket.subscribe('system_status', (data) => {
                this.updateSystemStatus(data);
            });

            // Voice events
            window.atsWebSocket.subscribe('voice_event', (data) => {
                this.handleVoiceEvent(data);
            });

            // Error handling
            window.atsWebSocket.subscribe('server_error', (data) => {
                this.showNotification(`Server Error: ${data.message}`, 'error');
            });
        }
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        try {
            // Load training sessions
            await this.loadTrainingSessions();
            
            // Load system status
            await this.loadSystemStatus();
            
            // Load performance data
            await this.loadPerformanceData();
            
            // Load profiles count
            await this.loadProfilesCount();
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }

    /**
     * Load training sessions
     */
    async loadTrainingSessions() {
        try {
            const sessions = await window.atsAPI.getTrainingSessions();
            this.updateSessionsList(sessions);
        } catch (error) {
            console.error('Failed to load training sessions:', error);
        }
    }

    /**
     * Load system status
     */
    async loadSystemStatus() {
        try {
            this.systemStatus = await window.atsAPI.getSystemStatus();
            this.updateSystemStatusDisplay();
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    }

    /**
     * Load performance data
     */
    async loadPerformanceData() {
        try {
            const analytics = await window.atsAPI.getAnalytics('7d');
            this.updatePerformanceChart(analytics);
        } catch (error) {
            console.error('Failed to load performance data:', error);
        }
    }

    /**
     * Load profiles count
     */
    async loadProfilesCount() {
        try {
            const profiles = await window.atsAPI.getProfiles();
            this.updateStatsDisplay('profiles', profiles.length);
        } catch (error) {
            console.error('Failed to load profiles count:', error);
        }
    }

    /**
     * Navigate to page
     */
    navigateToPage(page) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-page="${page}"]`).closest('.nav-item').classList.add('active');

        // Update page content
        document.querySelectorAll('.page-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${page}-page`).classList.add('active');

        this.currentPage = page;

        // Load page-specific data
        this.loadPageData(page);
    }

    /**
     * Load page-specific data
     */
    async loadPageData(page) {
        switch (page) {
            case 'dashboard':
                await this.loadInitialData();
                break;
            case 'profiles':
                await this.loadProfilesPage();
                break;
            case 'scenarios':
                await this.loadScenariosPage();
                break;
            case 'training':
                await this.loadTrainingPage();
                break;
            case 'reports':
                await this.loadReportsPage();
                break;
        }
    }

    /**
     * Handle quick actions
     */
    handleQuickAction(action) {
        switch (action) {
            case 'launch-profile':
                // TODO: Temporary redirect until SPA profile creation is implemented
                window.location.href = 'profiles.html';
                break;
            case 'create-scenario':
                this.showCreateScenarioModal();
                break;
            case 'view-reports':
                this.navigateToPage('reports');
                break;
            case 'system-status':
                this.showSystemStatusModal();
                break;
        }
    }

    /**
     * Toggle voice control
     */
    toggleVoiceControl() {
        const voiceBtn = document.getElementById('voiceControlBtn');
        const isActive = voiceBtn.classList.contains('active');

        if (isActive) {
            // Stop voice control
            voiceBtn.classList.remove('active');
            this.showNotification('Voice control deactivated', 'info');
            
            if (window.atsWebSocket) {
                window.atsWebSocket.sendVoiceCommand('stop');
            }
        } else {
            // Start voice control
            voiceBtn.classList.add('active');
            this.showNotification('Voice control activated', 'success');
            
            if (window.atsWebSocket) {
                window.atsWebSocket.sendVoiceCommand('start');
            }
        }
    }

    /**
     * Monitor training session
     */
    monitorSession(sessionId) {
        // Join WebSocket room for session updates
        if (window.atsWebSocket) {
            window.atsWebSocket.joinTrainingSession(sessionId);
        }
        
        // Navigate to training page
        this.navigateToPage('training');
        
        this.showNotification(`Monitoring session ${sessionId}`, 'info');
    }

    /**
     * Stop training session
     */
    async stopSession(sessionId) {
        try {
            await window.atsAPI.stopTrainingSession(sessionId);
            this.showNotification(`Session ${sessionId} stopped`, 'success');
            await this.loadTrainingSessions();
        } catch (error) {
            console.error('Failed to stop session:', error);
            this.showNotification('Failed to stop session', 'error');
        }
    }

    /**
     * Update sessions list
     */
    updateSessionsList(sessions) {
        const sessionList = document.querySelector('.session-list');
        if (!sessionList) return;

        sessionList.innerHTML = '';

        sessions.forEach(session => {
            const sessionItem = this.createSessionItem(session);
            sessionList.appendChild(sessionItem);
        });
    }

    /**
     * Create session item element
     */
    createSessionItem(session) {
        const div = document.createElement('div');
        div.className = 'session-item';
        div.innerHTML = `
            <div class="session-info">
                <h4>${session.scenario_name}</h4>
                <p>${session.profile_name}</p>
            </div>
            <div class="session-status">
                <span class="status-badge ${session.status}">${session.status}</span>
                <span class="session-time">${this.formatDuration(session.duration)}</span>
            </div>
            <div class="session-actions">
                <button class="btn btn-sm btn-secondary session-monitor-btn" data-session-id="${session.id}">
                    Monitor
                </button>
                ${session.status === 'active' ? `
                    <button class="btn btn-sm btn-danger session-stop-btn" data-session-id="${session.id}">
                        Stop
                    </button>
                ` : ''}
            </div>
        `;
        return div;
    }

    /**
     * Update system status display
     */
    updateSystemStatusDisplay() {
        if (!this.systemStatus) return;

        // Update status indicators
        const statusElement = document.querySelector('.system-status-indicator');
        if (statusElement) {
            statusElement.className = `status-indicator ${this.systemStatus.status}`;
            statusElement.innerHTML = `
                <span class="status-dot ${this.systemStatus.status}"></span>
                ${this.systemStatus.status}
            `;
        }
    }

    /**
     * Update system status
     */
    updateSystemStatus(status) {
        this.systemStatus = status;
        this.updateSystemStatusDisplay();
    }

    /**
     * Update training session
     */
    updateTrainingSession(sessionData) {
        this.trainingSessions.set(sessionData.id, sessionData);
        
        // Update UI if on dashboard
        if (this.currentPage === 'dashboard') {
            this.loadTrainingSessions();
        }
        
        // Update metrics if on training page
        if (this.currentPage === 'training') {
            this.updateTrainingMetrics(sessionData);
        }
    }

    /**
     * Initialize performance chart
     */
    initPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Success Rate',
                    data: [],
                    borderColor: '#ffd700',
                    backgroundColor: 'rgba(255, 215, 0, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Completion Time',
                    data: [],
                    borderColor: '#b71c1c',
                    backgroundColor: 'rgba(183, 28, 28, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f5f5f5'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#9e9e9e'
                        },
                        grid: {
                            color: 'rgba(158, 158, 158, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#9e9e9e'
                        },
                        grid: {
                            color: 'rgba(158, 158, 158, 0.1)'
                        }
                    }
                }
            }
        });
    }

    /**
     * Update performance chart
     */
    updatePerformanceChart(data) {
        if (!this.performanceChart) return;

        this.performanceChart.data.labels = data.labels || [];
        this.performanceChart.data.datasets[0].data = data.success_rates || [];
        this.performanceChart.data.datasets[1].data = data.completion_times || [];
        this.performanceChart.update();
    }

    /**
     * Update stats display
     */
    updateStatsDisplay(type, value) {
        const statElements = document.querySelectorAll('.stat-value');
        statElements.forEach(element => {
            const label = element.nextElementSibling?.textContent.toLowerCase();
            if (label && label.includes(type)) {
                element.textContent = value;
            }
        });
    }

    /**
     * Handle voice events
     */
    handleVoiceEvent(event) {
        switch (event.type) {
            case 'transcription':
                console.log('Voice transcription:', event.text);
                break;
            case 'command':
                this.handleVoiceCommand(event.command);
                break;
            case 'error':
                this.showNotification(`Voice error: ${event.message}`, 'error');
                break;
        }
    }

    /**
     * Handle voice command
     */
    handleVoiceCommand(command) {
        this.showNotification(`Voice command: ${command}`, 'info');
        // Implement voice command handling
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `dashboard-notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="notification-message">${message}</div>
            <button class="notification-close">&times;</button>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);

        // Close button handler
        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadSystemStatus();
                this.loadTrainingSessions();
            }
        }, 30000); // Refresh every 30 seconds
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Format duration
     */
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    /**
     * Show modal (placeholder)
     */
    showModal(title, content) {
        const modal = document.getElementById('modal-overlay');
        const modalTitle = modal.querySelector('.modal-title');
        const modalContent = modal.querySelector('.modal-content');

        modalTitle.textContent = title;
        modalContent.innerHTML = content;
        modal.classList.add('active');

        // Close button handler
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.classList.remove('active');
        });

        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    }

    /**
     * Show launch profile modal (placeholder)
     */
    showLaunchProfileModal() {
        this.showModal('Launch Profile', '<p>Profile launch interface coming soon...</p>');
    }

    /**
     * Show create scenario modal (placeholder)
     */
    showCreateScenarioModal() {
        this.showModal('Create Scenario', '<p>Scenario creation interface coming soon...</p>');
    }

    /**
     * Show system status modal (placeholder)
     */
    showSystemStatusModal() {
        const content = this.systemStatus ? `
            <div class="system-status-details">
                <p><strong>Status:</strong> ${this.systemStatus.status}</p>
                <p><strong>CPU Usage:</strong> ${this.systemStatus.cpu_usage}%</p>
                <p><strong>Memory Usage:</strong> ${this.systemStatus.memory_usage}%</p>
                <p><strong>Active Sessions:</strong> ${this.systemStatus.active_sessions}</p>
            </div>
        ` : '<p>Loading system status...</p>';
        
        this.showModal('System Status', content);
    }

    /**
     * Placeholder methods for page loading
     */
    async loadProfilesPage() {
        console.log('Loading profiles page...');
        try {
            const container = document.getElementById('profiles-page');
            if (container) {
                if (!container.querySelector('.profiles-grid')) {
                    container.innerHTML = `
                        <div class="page-header">
                            <h1 class="page-title">Profile Management</h1>
                            <p class="page-subtitle">Manage your specialized training profiles</p>
                        </div>
                        <div class="profiles-grid"></div>
                        <div class="empty-state" style="display:none;">
                            <i class="fas fa-users"></i>
                            <h3>No Profiles Found</h3>
                        </div>
                    `;
                }
            }
            const profiles = await window.atsAPI.getProfiles();
            const grid = container ? container.querySelector('.profiles-grid') : null;
            if (grid) {
                grid.innerHTML = '';
                if (!profiles || profiles.length === 0) {
                    const empty = container.querySelector('.empty-state');
                    if (empty) empty.style.display = 'block';
                    grid.style.display = 'none';
                } else {
                    const empty = container.querySelector('.empty-state');
                    if (empty) empty.style.display = 'none';
                    grid.style.display = 'grid';
                    profiles.forEach(p => {
                        const card = document.createElement('div');
                        card.className = 'profile-card';
                        card.innerHTML = `
                            <div class="profile-header">
                                <div class="profile-avatar">
                                    <img src="${p.avatar || 'assets/images/default-avatar.png'}" alt="${p.name || ''}">
                                    <div class="profile-status status-${p.status || 'inactive'}"></div>
                                </div>
                                <div class="profile-info">
                                    <h3 class="profile-name">${p.name || 'Unnamed'}</h3>
                                    <p class="profile-type">${p.type || ''}</p>
                                </div>
                            </div>
                            <div class="profile-body">
                                <p class="profile-description">${p.description || ''}</p>
                            </div>
                        `;
                        grid.appendChild(card);
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load profiles:', error);
            this.showNotification('Failed to load profiles', 'error');
        }
    }

    /**
     * Load scenarios page with real data
     */
    async loadScenariosPage() {
        console.log('Loading scenarios page...');
        try {
            const container = document.getElementById('scenarios-page');
            if (container && !container.querySelector('.scenarios-grid')) {
                container.innerHTML = `
                    <div class="page-header">
                        <h1 class="page-title">Scenario Management</h1>
                        <p class="page-subtitle">Design and manage training scenarios</p>
                    </div>
                    <div class="scenarios-grid"></div>
                `;
            }
            const scenarios = await window.atsAPI.getScenarios();
            this.renderScenarios(scenarios);
        } catch (error) {
            console.error('Failed to load scenarios:', error);
            this.showNotification('Failed to load scenarios', 'error');
        }
    }

    /**
     * Render scenarios grid
     */
    renderScenarios(scenarios) {
        const scenariosGrid = document.querySelector('.scenarios-grid');
        if (!scenariosGrid) return;

        scenariosGrid.innerHTML = '';

        scenarios.forEach(scenario => {
            const scenarioCard = this.createScenarioCard(scenario);
            scenariosGrid.appendChild(scenarioCard);
        });
    }

    /**
     * Create scenario card element
     */
    createScenarioCard(scenario) {
        const card = document.createElement('div');
        card.className = 'scenario-card';
        card.innerHTML = `
            <div class="scenario-header">
                <h3>${scenario.name}</h3>
                <span class="difficulty-badge ${scenario.difficulty}">${scenario.difficulty}</span>
            </div>
            <p class="scenario-description">${scenario.description}</p>
            <div class="scenario-meta">
                <span class="meta-item">
                    <i class="icon-clock"></i> ${scenario.estimated_duration || 'N/A'}
                </span>
                <span class="meta-item">
                    <i class="icon-users"></i> ${scenario.required_profiles?.length || 0} profiles
                </span>
            </div>
            <div class="scenario-actions">
                <button class="btn btn-primary launch-scenario-btn" data-scenario-id="${scenario.id}">
                    Launch Scenario
                </button>
                <button class="btn btn-secondary view-details-btn" data-scenario-id="${scenario.id}">
                    View Details
                </button>
            </div>
        `;

        // Add event listeners
        card.querySelector('.launch-scenario-btn').addEventListener('click', () => {
            this.launchScenario(scenario.id);
        });

        card.querySelector('.view-details-btn').addEventListener('click', () => {
            this.showScenarioDetails(scenario);
        });

        return card;
    }

    /**
     * Launch scenario
     */
    async launchScenario(scenarioId) {
        try {
            // Show launch modal with configuration options
            const config = await this.showLaunchScenarioModal(scenarioId);
            if (!config) return; // User cancelled

            // Start training session with the scenario
            const session = await window.atsAPI.startTrainingSession({
                scenario_id: scenarioId,
                ...config
            });

            this.showNotification(`Scenario launched successfully! Session ID: ${session.id}`, 'success');
            
            // Navigate to training page to monitor
            this.monitorSession(session.id);
        } catch (error) {
            console.error('Failed to launch scenario:', error);
            this.showNotification('Failed to launch scenario', 'error');
        }
    }

    /**
     * Show scenario details modal
     */
    showScenarioDetails(scenario) {
        const content = `
            <div class="scenario-details">
                <h3>${scenario.name}</h3>
                <p class="difficulty">Difficulty: <span class="${scenario.difficulty}">${scenario.difficulty}</span></p>
                <p class="description">${scenario.description}</p>
                <h4>Objectives:</h4>
                <ul>
                    ${scenario.objectives?.map(obj => `<li>${obj}</li>`).join('') || '<li>No objectives specified</li>'}
                </ul>
                <h4>Required Profiles:</h4>
                <ul>
                    ${scenario.required_profiles?.map(profile => `<li>${profile}</li>`).join('') || '<li>No profiles required</li>'}
                </ul>
                <p class="estimated-time">Estimated Duration: ${scenario.estimated_duration || 'N/A'}</p>
            </div>
        `;
        this.showModal('Scenario Details', content);
    }

    /**
     * Show launch scenario modal
     */
    async showLaunchScenarioModal(scenarioId) {
        return new Promise((resolve) => {
            const scenario = null; // Would fetch scenario details
            const content = `
                <form id="launchScenarioForm" class="launch-scenario-form">
                    <div class="form-group">
                        <label for="sessionName">Session Name</label>
                        <input type="text" id="sessionName" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label for="modelSelector">LLM Model</label>
                        <select id="modelSelector" class="form-control">
                            <option value="auto">Auto-Select (Recommended)</option>
                            <option value="gpt-4">GPT-4</option>
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                            <option value="claude-3-opus">Claude 3 Opus</option>
                            <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="budgetInput">Budget (USD)</label>
                        <input type="number" id="budgetInput" class="form-control" value="10" step="1" min="1">
                    </div>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Launch</button>
                        <button type="button" class="btn btn-secondary cancel-btn">Cancel</button>
                    </div>
                </form>
            `;

            this.showModal('Launch Scenario', content);

            const form = document.getElementById('launchScenarioForm');
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                resolve({
                    name: document.getElementById('sessionName').value,
                    model: document.getElementById('modelSelector').value,
                    budget: parseFloat(document.getElementById('budgetInput').value)
                });
                document.getElementById('modal-overlay').classList.remove('active');
            });

            document.querySelector('.cancel-btn').addEventListener('click', () => {
                resolve(null);
                document.getElementById('modal-overlay').classList.remove('active');
            });
        });
    }

    async loadTrainingPage() {
        console.log('Loading training page...');
        try {
            const container = document.getElementById('training-page');
            if (container && !container.querySelector('.training-sessions-container')) {
                container.innerHTML = `
                    <div class="page-header">
                        <h1 class="page-title">Situation Room</h1>
                        <p class="page-subtitle">Live training session monitoring and control</p>
                    </div>
                    <div class="training-sessions-container"></div>
                `;
            }
            const sessions = await window.atsAPI.getTrainingSessions();
            this.renderTrainingSessions(sessions);
        } catch (error) {
            console.error('Failed to load training sessions:', error);
            this.showNotification('Failed to load training sessions', 'error');
        }
    }

    renderTrainingSessions(sessions) {
        const sessionsContainer = document.querySelector('.training-sessions-container');
        if (!sessionsContainer) return;
        sessionsContainer.innerHTML = '';
        sessions.forEach(session => {
            const sessionCard = this.createSessionItem(session);
            sessionsContainer.appendChild(sessionCard);
        });
    }

    async loadReportsPage() {
        console.log('Loading reports page...');
        try {
            const container = document.getElementById('reports-page');
            if (container && !container.querySelector('.reports-container')) {
                container.innerHTML = `
                    <div class="page-header">
                        <h1 class="page-title">After-Action Reports</h1>
                        <p class="page-subtitle">Training performance analysis and reporting</p>
                    </div>
                    <div class="reports-container"></div>
                `;
            }
            const reports = await window.atsAPI.getReports();
            this.renderReports(reports);
        } catch (error) {
            console.error('Failed to load reports:', error);
            this.showNotification('Failed to load reports', 'error');
        }
    }

    renderReports(reports) {
        const reportsContainer = document.querySelector('.reports-container');
        if (!reportsContainer) return;
        reportsContainer.innerHTML = '';
        reports.forEach(report => {
            const reportCard = this.createReportCard(report);
            reportsContainer.appendChild(reportCard);
        });
    }

    createReportCard(report) {
        const card = document.createElement('div');
        card.className = 'report-card';
        card.innerHTML = `
            <div class="report-header">
                <h3>${report.title}</h3>
                <span class="report-date">${new Date(report.created_at).toLocaleDateString()}</span>
            </div>
            <p class="report-type">${report.type}</p>
            <div class="report-actions">
                <button class="btn btn-sm btn-primary view-report-btn" data-report-id="${report.id}">
                    View Report
                </button>
                <button class="btn btn-sm btn-secondary download-report-btn" data-report-id="${report.id}">
                    Download
                </button>
            </div>
        `;
        return card;
    }

    updateTrainingMetrics(sessionData) {
        console.log('Updating training metrics:', sessionData);
        const sessionStats = document.querySelector('.session-stats');
        if (sessionStats && sessionData.metrics) {
            sessionStats.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">Success Rate</span>
                    <span class="stat-value">${sessionData.metrics.success_rate}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Duration</span>
                    <span class="stat-value">${this.formatDuration(sessionData.duration)}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Actions</span>
                    <span class="stat-value">${sessionData.metrics.action_count}</span>
                </div>
            `;
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.atsDashboard = new ATSDashboard();
});