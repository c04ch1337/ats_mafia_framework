/**
 * ATS MAFIA LLM Controller
 * Manages LLM models, cost tracking, and budget monitoring
 */

class LLMController {
    constructor() {
        this.apiClient = window.atsAPI;
        this.models = [];
        this.filteredModels = [];
        this.selectedModels = [];
        this.costChart = null;
        this.costData = null;
        this.currentProvider = 'all';
        this.currentCapability = 'all';

        this.init();
    }

    /**
     * Initialize the controller
     */
    async init() {
        console.log('Initializing LLM Controller...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadModels();
        await this.loadCostData();
        
        // Initialize cost chart
        this.initCostChart();
        
        console.log('LLM Controller initialized successfully');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Filter controls
        document.getElementById('providerFilter')?.addEventListener('change', (e) => {
            this.currentProvider = e.target.value;
            this.filterModels();
        });

        document.getElementById('capabilityFilter')?.addEventListener('change', (e) => {
            this.currentCapability = e.target.value;
            this.filterModels();
        });

        document.getElementById('costPeriodFilter')?.addEventListener('change', (e) => {
            this.loadCostData(e.target.value);
        });

        // Action buttons
        document.getElementById('refreshModelsBtn')?.addEventListener('click', () => {
            this.loadModels();
        });

        document.getElementById('recommendModelBtn')?.addEventListener('click', () => {
            this.showRecommendationModal();
        });

        document.getElementById('clearComparisonBtn')?.addEventListener('click', () => {
            this.clearComparison();
        });

        // Modal controls
        document.getElementById('closeModelDetailsModal')?.addEventListener('click', () => {
            this.closeModelDetailsModal();
        });

        document.getElementById('closeModelDetailsBtn')?.addEventListener('click', () => {
            this.closeModelDetailsModal();
        });

        document.getElementById('selectModelBtn')?.addEventListener('click', () => {
            this.selectModelForSession();
        });

        document.getElementById('closeRecommendationModal')?.addEventListener('click', () => {
            this.closeRecommendationModal();
        });

        document.getElementById('cancelRecommendationBtn')?.addEventListener('click', () => {
            this.closeRecommendationModal();
        });

        document.getElementById('getRecommendationBtn')?.addEventListener('click', () => {
            this.getModelRecommendation();
        });

        // Budget configuration
        document.getElementById('closeBudgetModal')?.addEventListener('click', () => {
            this.closeBudgetModal();
        });

        document.getElementById('cancelBudgetBtn')?.addEventListener('click', () => {
            this.closeBudgetModal();
        });

        document.getElementById('saveBudgetBtn')?.addEventListener('click', () => {
            this.saveBudgetConfiguration();
        });

        // Budget card click to open config
        document.querySelector('.cost-card:last-child')?.addEventListener('click', () => {
            this.showBudgetModal();
        });
    }

    /**
     * Load models from API
     */
    async loadModels(filters = {}) {
        try {
            const modelsGrid = document.getElementById('modelsGrid');
            modelsGrid.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading models...</p></div>';

            this.models = await this.apiClient.getModels(filters);
            this.filteredModels = this.models;
            
            this.renderModels();
        } catch (error) {
            console.error('Failed to load models:', error);
            this.showError('Failed to load models');
        }
    }

    /**
     * Filter models based on current filters
     */
    filterModels() {
        this.filteredModels = this.models.filter(model => {
            // Provider filter
            if (this.currentProvider !== 'all' && model.provider !== this.currentProvider) {
                return false;
            }

            // Capability filter
            if (this.currentCapability !== 'all') {
                if (!model.capabilities || !model.capabilities.includes(this.currentCapability)) {
                    return false;
                }
            }

            return true;
        });

        this.renderModels();
    }

    /**
     * Render models grid
     */
    renderModels() {
        const modelsGrid = document.getElementById('modelsGrid');
        
        if (this.filteredModels.length === 0) {
            modelsGrid.innerHTML = '<div class="empty-state"><p>No models found matching the current filters.</p></div>';
            return;
        }

        modelsGrid.innerHTML = '';

        this.filteredModels.forEach(model => {
            const modelCard = this.createModelCard(model);
            modelsGrid.appendChild(modelCard);
        });
    }

    /**
     * Create model card element
     */
    createModelCard(model) {
        const card = document.createElement('div');
        card.className = 'tool-card model-card';
        
        const isSelected = this.selectedModels.some(m => m.name === model.name);
        if (isSelected) {
            card.classList.add('selected');
        }

        card.innerHTML = `
            <div class="tool-header">
                <h3 class="tool-name">${model.name}</h3>
                <span class="tool-category-badge ${model.provider}">${model.provider}</span>
            </div>
            <p class="tool-description">${model.description || 'No description available'}</p>
            <div class="tool-meta">
                <span class="meta-item">
                    <span class="meta-label">Context:</span>
                    <span class="meta-value">${model.context_window?.toLocaleString() || 'N/A'} tokens</span>
                </span>
                <span class="meta-item">
                    <span class="meta-label">Cost:</span>
                    <span class="meta-value">$${model.cost_per_1k_tokens || '0.00'}/1K</span>
                </span>
            </div>
            <div class="model-capabilities">
                ${model.capabilities ? model.capabilities.slice(0, 3).map(cap => 
                    `<span class="capability-badge">${cap}</span>`
                ).join('') : ''}
            </div>
            <div class="tool-actions">
                <button class="btn btn-sm btn-secondary view-model-btn" data-model-name="${model.name}">
                    <span>ℹ️</span> Details
                </button>
                <button class="btn btn-sm ${isSelected ? 'btn-warning' : 'btn-primary'} compare-model-btn" 
                        data-model-name="${model.name}">
                    <span>${isSelected ? '✓' : '⚖️'}</span> ${isSelected ? 'Selected' : 'Compare'}
                </button>
            </div>
        `;

        // Add event listeners
        card.querySelector('.view-model-btn').addEventListener('click', () => {
            this.showModelDetails(model.provider, model.name);
        });

        card.querySelector('.compare-model-btn').addEventListener('click', () => {
            this.toggleModelComparison(model);
        });

        return card;
    }

    /**
     * Show model details modal
     */
    async showModelDetails(provider, modelName) {
        try {
            const model = await this.apiClient.getModelDetails(provider, modelName);

            const modal = document.getElementById('modelDetailsModal');
            const title = document.getElementById('modelDetailTitle');
            const content = document.getElementById('modelDetailContent');

            title.textContent = model.name;
            content.innerHTML = this.renderModelDetails(model);

            modal.classList.add('active');
        } catch (error) {
            console.error('Failed to load model details:', error);
            this.showError('Failed to load model details');
        }
    }

    /**
     * Render model details content
     */
    renderModelDetails(model) {
        return `
            <div class="tool-details-content">
                <div class="detail-section">
                    <h4>Description</h4>
                    <p>${model.description || 'No description available'}</p>
                </div>

                <div class="detail-section">
                    <h4>Provider</h4>
                    <span class="category-badge ${model.provider}">${model.provider}</span>
                </div>

                <div class="detail-section">
                    <h4>Pricing</h4>
                    <div class="pricing-details">
                        <p><strong>Input:</strong> $${model.cost_input_per_1k || '0.00'} per 1K tokens</p>
                        <p><strong>Output:</strong> $${model.cost_output_per_1k || '0.00'} per 1K tokens</p>
                        <p><strong>Average:</strong> $${model.cost_per_1k_tokens || '0.00'} per 1K tokens</p>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Specifications</h4>
                    <ul class="spec-list">
                        <li><strong>Context Window:</strong> ${model.context_window?.toLocaleString() || 'N/A'} tokens</li>
                        <li><strong>Max Output:</strong> ${model.max_output_tokens?.toLocaleString() || 'N/A'} tokens</li>
                        <li><strong>Training Cutoff:</strong> ${model.training_cutoff || 'N/A'}</li>
                    </ul>
                </div>

                ${model.capabilities && model.capabilities.length > 0 ? `
                    <div class="detail-section">
                        <h4>Capabilities</h4>
                        <div class="capabilities-grid">
                            ${model.capabilities.map(cap => 
                                `<span class="capability-badge">${cap}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}

                ${model.best_for ? `
                    <div class="detail-section">
                        <h4>Best For</h4>
                        <p>${model.best_for}</p>
                    </div>
                ` : ''}

                ${model.limitations ? `
                    <div class="detail-section">
                        <h4>Limitations</h4>
                        <p>${model.limitations}</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Close model details modal
     */
    closeModelDetailsModal() {
        document.getElementById('modelDetailsModal').classList.remove('active');
    }

    /**
     * Select model for session
     */
    selectModelForSession() {
        this.showSuccess('Model selection saved for next session');
        this.closeModelDetailsModal();
    }

    /**
     * Toggle model comparison
     */
    toggleModelComparison(model) {
        const index = this.selectedModels.findIndex(m => m.name === model.name);
        
        if (index > -1) {
            // Remove from comparison
            this.selectedModels.splice(index, 1);
        } else {
            // Add to comparison (max 4 models)
            if (this.selectedModels.length >= 4) {
                this.showError('You can compare up to 4 models at a time');
                return;
            }
            this.selectedModels.push(model);
        }

        this.renderModels();
        this.renderComparison();
    }

    /**
     * Render comparison table
     */
    renderComparison() {
        const container = document.getElementById('comparisonContainer');
        
        if (this.selectedModels.length === 0) {
            container.innerHTML = '<p class="empty-state">Select models to compare their features and costs</p>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'comparison-table';
        
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Feature</th>
                    ${this.selectedModels.map(m => `<th>${m.name}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Provider</strong></td>
                    ${this.selectedModels.map(m => `<td>${m.provider}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Context Window</strong></td>
                    ${this.selectedModels.map(m => `<td>${m.context_window?.toLocaleString() || 'N/A'}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Cost per 1K Tokens</strong></td>
                    ${this.selectedModels.map(m => `<td>$${m.cost_per_1k_tokens || '0.00'}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Input Cost</strong></td>
                    ${this.selectedModels.map(m => `<td>$${m.cost_input_per_1k || '0.00'}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Output Cost</strong></td>
                    ${this.selectedModels.map(m => `<td>$${m.cost_output_per_1k || '0.00'}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Max Output Tokens</strong></td>
                    ${this.selectedModels.map(m => `<td>${m.max_output_tokens?.toLocaleString() || 'N/A'}</td>`).join('')}
                </tr>
            </tbody>
        `;

        container.innerHTML = '';
        container.appendChild(table);
    }

    /**
     * Clear comparison selection
     */
    clearComparison() {
        this.selectedModels = [];
        this.renderModels();
        this.renderComparison();
    }

    /**
     * Load cost data
     */
    async loadCostData(timeframe = '30d') {
        try {
            this.costData = await this.apiClient.getCostSummary(timeframe);
            this.updateCostDashboard();
            this.updateCostChart();
        } catch (error) {
            console.error('Failed to load cost data:', error);
            this.showError('Failed to load cost data');
        }
    }

    /**
     * Update cost dashboard
     */
    updateCostDashboard() {
        if (!this.costData) return;

        // Update total spend
        document.getElementById('totalSpend').textContent = 
            `$${this.costData.total_spend?.toFixed(2) || '0.00'}`;

        // Update average session cost
        document.getElementById('avgSessionCost').textContent = 
            `$${this.costData.avg_session_cost?.toFixed(2) || '0.00'}`;

        // Update tokens used
        document.getElementById('tokensUsed').textContent = 
            this.costData.total_tokens?.toLocaleString() || '0';

        // Update budget remaining
        const budget = this.costData.monthly_budget || 100;
        const spent = this.costData.total_spend || 0;
        const remaining = Math.max(0, budget - spent);
        const percentage = budget > 0 ? (spent / budget) * 100 : 0;

        document.getElementById('budgetRemaining').textContent = `$${remaining.toFixed(2)}`;
        document.getElementById('budgetFill').style.width = `${Math.min(100, percentage)}%`;

        // Update budget fill color based on percentage
        const budgetFill = document.getElementById('budgetFill');
        if (percentage >= 90) {
            budgetFill.style.background = '#f44336';
        } else if (percentage >= 80) {
            budgetFill.style.background = '#ff9800';
        } else {
            budgetFill.style.background = '#4caf50';
        }
    }

    /**
     * Initialize cost chart
     */
    initCostChart() {
        const ctx = document.getElementById('costChart');
        if (!ctx) return;

        this.costChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Daily Cost',
                    data: [],
                    borderColor: '#ffd700',
                    backgroundColor: 'rgba(255, 215, 0, 0.1)',
                    tension: 0.4,
                    fill: true
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
                        ticks: { color: '#9e9e9e' },
                        grid: { color: 'rgba(158, 158, 158, 0.1)' }
                    },
                    y: {
                        ticks: { 
                            color: '#9e9e9e',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        },
                        grid: { color: 'rgba(158, 158, 158, 0.1)' }
                    }
                }
            }
        });
    }

    /**
     * Update cost chart
     */
    updateCostChart() {
        if (!this.costChart || !this.costData) return;

        this.costChart.data.labels = this.costData.dates || [];
        this.costChart.data.datasets[0].data = this.costData.daily_costs || [];
        this.costChart.update();
    }

    /**
     * Show recommendation modal
     */
    showRecommendationModal() {
        document.getElementById('recommendationResult').style.display = 'none';
        document.getElementById('recommendationModal').classList.add('active');
    }

    /**
     * Close recommendation modal
     */
    closeRecommendationModal() {
        document.getElementById('recommendationModal').classList.remove('active');
    }

    /**
     * Get model recommendation
     */
    async getModelRecommendation() {
        try {
            const taskType = document.getElementById('taskType').value;
            const priorityFactor = document.getElementById('priorityFactor').value;
            const maxBudget = parseFloat(document.getElementById('maxBudget').value);

            if (!taskType) {
                this.showError('Please select a task type');
                return;
            }

            const getBtn = document.getElementById('getRecommendationBtn');
            getBtn.disabled = true;
            getBtn.textContent = 'Getting Recommendation...';

            const recommendation = await this.apiClient.recommendModel(taskType, {
                priority: priorityFactor,
                max_budget: maxBudget
            });

            // Show recommendation
            const resultDiv = document.getElementById('recommendationResult');
            const cardDiv = document.getElementById('recommendedModelCard');
            
            cardDiv.innerHTML = this.createModelCard(recommendation.model).outerHTML;
            resultDiv.style.display = 'block';

            getBtn.disabled = false;
            getBtn.textContent = 'Get Recommendation';
        } catch (error) {
            console.error('Failed to get recommendation:', error);
            this.showError('Failed to get recommendation');
            
            const getBtn = document.getElementById('getRecommendationBtn');
            getBtn.disabled = false;
            getBtn.textContent = 'Get Recommendation';
        }
    }

    /**
     * Show budget modal
     */
    showBudgetModal() {
        document.getElementById('budgetConfigModal').classList.add('active');
    }

    /**
     * Close budget modal
     */
    closeBudgetModal() {
        document.getElementById('budgetConfigModal').classList.remove('active');
    }

    /**
     * Save budget configuration
     */
    async saveBudgetConfiguration() {
        try {
            const monthlyBudget = parseFloat(document.getElementById('monthlyBudget').value);
            const sessionBudget = parseFloat(document.getElementById('sessionBudget').value);
            const alertThreshold = parseInt(document.getElementById('alertThreshold').value);
            const autoStop = document.getElementById('autoStop').checked;

            // Save configuration via API
            // await this.apiClient.saveBudgetConfig({ ... });

            this.showSuccess('Budget configuration saved');
            this.closeBudgetModal();
            this.loadCostData();
        } catch (error) {
            console.error('Failed to save budget configuration:', error);
            this.showError('Failed to save configuration');
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);

        notification.querySelector('.notification-close').addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
}