/**
 * ATS MAFIA API Client
 * Handles communication with the backend framework
 */

class ATSAPIClient {
    constructor(baseURL = '/api/v1') {
        this.baseURL = baseURL;

        // Normalize base URL for local dev when UI is served from a different origin/port or file://
        try {
            if (typeof window !== 'undefined') {
                const isAbsolute = typeof this.baseURL === 'string' && /^https?:/i.test(this.baseURL);
                const isRelative = typeof this.baseURL === 'string' && this.baseURL.startsWith('/');
                const servedFromHttp = window.location.protocol.startsWith('http');
                const differentPort = servedFromHttp && window.location.port && window.location.port !== '8000';
                const fromFile = window.location.protocol === 'file:';
                if ((!isAbsolute && isRelative && (differentPort || fromFile)) || (fromFile && !isAbsolute)) {
                    this.baseURL = 'http://localhost:8000' + this.baseURL;
                    try { console.log('ATSAPIClient: normalized baseURL to', this.baseURL); } catch (_) {}
                }
            }
        } catch (_) {}

        this.token = localStorage.getItem('ats_token');
        this.refreshToken = localStorage.getItem('ats_refresh_token');
    }

    /**
     * Set authentication tokens
     */
    setTokens(accessToken, refreshToken) {
        this.token = accessToken;
        this.refreshToken = refreshToken;
        localStorage.setItem('ats_token', accessToken);
        localStorage.setItem('ats_refresh_token', refreshToken);
    }

    /**
     * Clear authentication tokens
     */
    clearTokens() {
        this.token = null;
        this.refreshToken = null;
        localStorage.removeItem('ats_token');
        localStorage.removeItem('ats_refresh_token');
    }

    /**
     * Make API request with authentication
     */
    async request(endpoint, options = {}) {
        // Ensure endpoint always concatenates correctly (leading slash)
        const path = (typeof endpoint === 'string' && endpoint.startsWith('/')) ? endpoint : `/${endpoint}`;
        const url = `${this.baseURL}${path}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (response.status === 401 && this.refreshToken) {
                // Try to refresh token
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.token}`;
                    return fetch(url, { ...options, headers });
                }
            }

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    /**
     * Refresh access token
     */
    async refreshAccessToken() {
        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access_token, data.refresh_token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }

        this.clearTokens();
        return false;
    }

    /**
     * Authentication methods
     */
    async login(credentials) {
        const response = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
        
        this.setTokens(response.access_token, response.refresh_token);
        return response;
    }

    async logout() {
        try {
            await this.request('/auth/logout', { method: 'POST' });
        } finally {
            this.clearTokens();
        }
    }

    /**
     * Profile management
     */
    async getProfiles() {
        return this.request('/profiles');
    }

    async getProfile(profileId) {
        return this.request(`/profiles/${profileId}`);
    }

    async createProfile(profileData) {
        return this.request('/profiles', {
            method: 'POST',
            body: JSON.stringify(profileData),
        });
    }

    async updateProfile(profileId, profileData) {
        return this.request(`/profiles/${profileId}`, {
            method: 'PUT',
            body: JSON.stringify(profileData),
        });
    }

    async deleteProfile(profileId) {
        return this.request(`/profiles/${profileId}`, {
            method: 'DELETE',
        });
    }

    async activateProfile(profileId) {
        return this.request(`/profiles/${profileId}/activate`, {
            method: 'POST',
        });
    }

    async deactivateProfile(profileId) {
        return this.request(`/profiles/${profileId}/deactivate`, {
            method: 'POST',
        });
    }

    /**
     * Scenario management
     */
    async getScenarios() {
        return this.request('/scenarios');
    }

    async getScenario(scenarioId) {
        return this.request(`/scenarios/${scenarioId}`);
    }

    async createScenario(scenarioData) {
        return this.request('/scenarios', {
            method: 'POST',
            body: JSON.stringify(scenarioData),
        });
    }

    async updateScenario(scenarioId, scenarioData) {
        return this.request(`/scenarios/${scenarioId}`, {
            method: 'PUT',
            body: JSON.stringify(scenarioData),
        });
    }

    async deleteScenario(scenarioId) {
        return this.request(`/scenarios/${scenarioId}`, {
            method: 'DELETE',
        });
    }

    /**
     * Training session management
     */
    async getTrainingSessions() {
        return this.request('/training/sessions');
    }

    async getTrainingSession(sessionId) {
        return this.request(`/training/sessions/${sessionId}`);
    }

    async startTrainingSession(sessionData) {
        return this.request('/training/sessions', {
            method: 'POST',
            body: JSON.stringify(sessionData),
        });
    }

    async stopTrainingSession(sessionId) {
        return this.request(`/training/sessions/${sessionId}/stop`, {
            method: 'POST',
        });
    }

    async pauseTrainingSession(sessionId) {
        return this.request(`/training/sessions/${sessionId}/pause`, {
            method: 'POST',
        });
    }

    async resumeTrainingSession(sessionId) {
        return this.request(`/training/sessions/${sessionId}/resume`, {
            method: 'POST',
        });
    }

    async getTrainingSessionLogs(sessionId) {
        return this.request(`/training/sessions/${sessionId}/logs`);
    }

    async getTrainingSessionMetrics(sessionId) {
        return this.request(`/training/sessions/${sessionId}/metrics`);
    }

    /**
     * Reports and analytics
     */
    async getReports(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        return this.request(`/reports?${queryParams}`);
    }

    async getReport(reportId) {
        return this.request(`/reports/${reportId}`);
    }

    async generateReport(reportData) {
        return this.request('/reports/generate', {
            method: 'POST',
            body: JSON.stringify(reportData),
        });
    }

    async getAnalytics(timeRange = '7d') {
        return this.request(`/analytics?time_range=${timeRange}`);
    }

    async getPerformanceMetrics(profileId, timeRange = '30d') {
        return this.request(`/analytics/performance/${profileId}?time_range=${timeRange}`);
    }

    /**
     * System status and health
     */
    async getSystemStatus() {
        return this.request('/system/status');
    }

    async getSystemHealth() {
        return this.request('/system/health');
    }

    async getSystemMetrics() {
        return this.request('/system/metrics');
    }

    /**
     * Voice system integration
     */
    async getVoiceStatus() {
        return this.request('/voice/status');
    }

    async startVoiceSession(sessionData) {
        return this.request('/voice/sessions', {
            method: 'POST',
            body: JSON.stringify(sessionData),
        });
    }

    async stopVoiceSession(sessionId) {
        return this.request(`/voice/sessions/${sessionId}`, {
            method: 'DELETE',
        });
    }

    async getVoiceSessions() {
        return this.request('/voice/sessions');
    }

    /**
     * Configuration management
     */
    async getConfiguration() {
        return this.request('/config');
    }

    async updateConfiguration(configData) {
        return this.request('/config', {
            method: 'PUT',
            body: JSON.stringify(configData),
        });
    }

    async resetConfiguration() {
        return this.request('/config/reset', {
            method: 'POST',
        });
    }

    /**
     * File upload/download
     */
    async uploadFile(file, type = 'general') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', type);

        const response = await fetch(`${this.baseURL}/files/upload`, {
            method: 'POST',
            headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {},
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        return response.json();
    }

    async downloadFile(fileId) {
        const response = await fetch(`${this.baseURL}/files/${fileId}`, {
            headers: this.token ? { 'Authorization': `Bearer ${this.token}` } : {},
        });

        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }

        return response.blob();
    }

    /**
     * Utility methods
     */
    async validateProfile(profileData) {
        return this.request('/profiles/validate', {
            method: 'POST',
            body: JSON.stringify(profileData),
        });
    }

    async validateScenario(scenarioData) {
        return this.request('/scenarios/validate', {
            method: 'POST',
            body: JSON.stringify(scenarioData),
        });
    }

    async searchProfiles(query) {
        return this.request(`/profiles/search?q=${encodeURIComponent(query)}`);
    }

    async searchScenarios(query) {
        return this.request(`/scenarios/search?q=${encodeURIComponent(query)}`);
    }
    /**
     * LLM Management methods
     */
    async getModels(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        return this.request(`/llm/models?${queryParams}`);
    }

    async getModelDetails(provider, modelName) {
        return this.request(`/llm/models/${provider}/${modelName}`);
    }

    async recommendModel(taskType) {
        return this.request('/llm/recommend', {
            method: 'POST',
            body: JSON.stringify({ task_type: taskType }),
        });
    }

    async getSessionCosts(sessionId) {
        return this.request(`/training/sessions/${sessionId}/costs`);
    }

    async setSessionBudget(sessionId, budget) {
        return this.request(`/training/sessions/${sessionId}/budget`, {
            method: 'PUT',
            body: JSON.stringify({ budget }),
        });
    }

    async getCostSummary(timeframe = '30d') {
        return this.request(`/llm/costs/summary?timeframe=${timeframe}`);
    }

    /**
     * Tool Management methods
     */
    async getTools(category = 'all') {
        return this.request(`/tools?category=${category}`);
    }

    async getToolDetails(toolName) {
        return this.request(`/tools/${toolName}`);
    }

    async executeTool(toolName, parameters) {
        return this.request(`/tools/${toolName}/execute`, {
            method: 'POST',
            body: JSON.stringify({ parameters }),
        });
    }

    async validateTool(toolName) {
        return this.request(`/tools/${toolName}/validate`, {
            method: 'POST',
        });
    }

    async getToolCategories() {
        return this.request('/tools/categories');
    }

    async getToolExecutionHistory(toolName = null) {
        const endpoint = toolName 
            ? `/tools/${toolName}/history` 
            : '/tools/history';
        return this.request(endpoint);
    }

    /**
     * Analytics methods
     */
    async getOperatorPerformance(operatorId, timeframe = '30d') {
        return this.request(`/analytics/operators/${operatorId}/performance?timeframe=${timeframe}`);
    }

    async getSessionAnalysis(sessionId) {
        return this.request(`/analytics/sessions/${sessionId}`);
    }

    async getCostBreakdown(timeframe = '30d') {
        return this.request(`/analytics/costs/breakdown?timeframe=${timeframe}`);
    }

    async getLeaderboard(category = 'xp', limit = 10) {
        return this.request(`/analytics/leaderboard?category=${category}&limit=${limit}`);
    }

    async getSuccessRateMetrics(timeframe = '30d') {
        return this.request(`/analytics/success-rate?timeframe=${timeframe}`);
    }

    async getScenarioStatistics(scenarioId = null) {
        const endpoint = scenarioId 
            ? `/analytics/scenarios/${scenarioId}/statistics` 
            : '/analytics/scenarios/statistics';
        return this.request(endpoint);
    }

}

// Create global API client instance
if (typeof window !== 'undefined') {
    window['atsAPI'] = new ATSAPIClient();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ATSAPIClient;
}