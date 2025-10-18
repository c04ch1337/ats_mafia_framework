/**
 * ATS MAFIA Tools Controller
 * Manages tool browsing, details, and execution
 */

class ToolsController {
    constructor() {
        this.apiClient = window.atsAPI;
        this.tools = [];
        this.filteredTools = [];
        this.selectedTool = null;
        this.executionHistory = [];
        this.currentCategory = 'all';
        this.currentStatus = 'all';
        this.searchQuery = '';

        this.init();
    }

    /**
     * Initialize the controller
     */
    async init() {
        console.log('Initializing Tools Controller...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load tools
        await this.loadTools();
        
        // Load execution history
        await this.loadExecutionHistory();
        
        console.log('Tools Controller initialized successfully');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Filter controls
        document.getElementById('categoryFilter')?.addEventListener('change', (e) => {
            this.currentCategory = e.target.value;
            this.filterTools();
        });

        document.getElementById('statusFilter')?.addEventListener('change', (e) => {
            this.currentStatus = e.target.value;
            this.filterTools();
        });

        document.getElementById('searchTools')?.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase();
            this.filterTools();
        });

        // Action buttons
        document.getElementById('refreshToolsBtn')?.addEventListener('click', () => {
            this.loadTools();
        });

        document.getElementById('validateAllToolsBtn')?.addEventListener('click', () => {
            this.validateAllTools();
        });

        document.getElementById('clearHistoryBtn')?.addEventListener('click', () => {
            this.clearExecutionHistory();
        });

        // Modal controls
        document.getElementById('closeToolDetailsModal')?.addEventListener('click', () => {
            this.closeToolDetailsModal();
        });

        document.getElementById('closeToolDetailsBtn')?.addEventListener('click', () => {
            this.closeToolDetailsModal();
        });

        document.getElementById('executeToolBtn')?.addEventListener('click', () => {
            this.showExecutionModal();
        });

        document.getElementById('closeExecutionModal')?.addEventListener('click', () => {
            this.closeExecutionModal();
        });

        document.getElementById('cancelExecutionBtn')?.addEventListener('click', () => {
            this.closeExecutionModal();
        });

        document.getElementById('runToolBtn')?.addEventListener('click', () => {
            this.executeSelectedTool();
        });
    }

    /**
     * Load tools from API
     */
    async loadTools(category = 'all') {
        try {
            const toolsGrid = document.getElementById('toolsGrid');
            toolsGrid.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading tools...</p></div>';

            this.tools = await this.apiClient.getTools(category);
            this.filteredTools = this.tools;
            
            this.renderTools();
            this.updateToolCount();
        } catch (error) {
            console.error('Failed to load tools:', error);
            this.showError('Failed to load tools');
        }
    }

    /**
     * Filter tools based on current filters
     */
    filterTools() {
        this.filteredTools = this.tools.filter(tool => {
            // Category filter
            if (this.currentCategory !== 'all' && tool.category !== this.currentCategory) {
                return false;
            }

            // Status filter
            if (this.currentStatus !== 'all' && tool.status !== this.currentStatus) {
                return false;
            }

            // Search filter
            if (this.searchQuery) {
                const searchFields = [
                    tool.name,
                    tool.description,
                    tool.category
                ].join(' ').toLowerCase();

                if (!searchFields.includes(this.searchQuery)) {
                    return false;
                }
            }

            return true;
        });

        this.renderTools();
        this.updateToolCount();
    }

    /**
     * Render tools grid
     */
    renderTools() {
        const toolsGrid = document.getElementById('toolsGrid');
        
        if (this.filteredTools.length === 0) {
            toolsGrid.innerHTML = '<div class="empty-state"><p>No tools found matching the current filters.</p></div>';
            return;
        }

        toolsGrid.innerHTML = '';

        this.filteredTools.forEach(tool => {
            const toolCard = this.createToolCard(tool);
            toolsGrid.appendChild(toolCard);
        });
    }

    /**
     * Create tool card element
     */
    createToolCard(tool) {
        const card = document.createElement('div');
        card.className = `tool-card ${tool.status}`;
        
        card.innerHTML = `
            <div class="tool-header">
                <h3 class="tool-name">${tool.name}</h3>
                <span class="tool-category-badge ${tool.category}">${tool.category}</span>
            </div>
            <p class="tool-description">${tool.description || 'No description available'}</p>
            <div class="tool-meta">
                <span class="meta-item">
                    <span class="meta-label">Version:</span>
                    <span class="meta-value">${tool.version || 'N/A'}</span>
                </span>
                <span class="meta-item">
                    <span class="meta-label">Status:</span>
                    <span class="meta-value status-${tool.status}">${tool.status || 'unknown'}</span>
                </span>
            </div>
            <div class="tool-actions">
                <button class="btn btn-sm btn-secondary view-tool-btn" data-tool-name="${tool.name}">
                    <span>ℹ️</span> Details
                </button>
                <button class="btn btn-sm btn-primary execute-tool-btn" data-tool-name="${tool.name}">
                    <span>▶️</span> Execute
                </button>
            </div>
        `;

        // Add event listeners
        card.querySelector('.view-tool-btn').addEventListener('click', () => {
            this.showToolDetails(tool.name);
        });

        card.querySelector('.execute-tool-btn').addEventListener('click', () => {
            this.selectedTool = tool;
            this.showExecutionModal();
        });

        return card;
    }

    /**
     * Show tool details modal
     */
    async showToolDetails(toolName) {
        try {
            const tool = await this.apiClient.getToolDetails(toolName);
            this.selectedTool = tool;

            const modal = document.getElementById('toolDetailsModal');
            const title = document.getElementById('toolDetailTitle');
            const content = document.getElementById('toolDetailContent');

            title.textContent = tool.name;
            content.innerHTML = this.renderToolDetails(tool);

            modal.classList.add('active');
        } catch (error) {
            console.error('Failed to load tool details:', error);
            this.showError('Failed to load tool details');
        }
    }

    /**
     * Render tool details content
     */
    renderToolDetails(tool) {
        let parametersHtml = '<p>No parameters required</p>';
        
        if (tool.parameters && tool.parameters.length > 0) {
            parametersHtml = '<ul class="parameters-list">';
            tool.parameters.forEach(param => {
                parametersHtml += `
                    <li class="parameter-item">
                        <strong>${param.name}</strong> 
                        ${param.required ? '<span class="required-badge">Required</span>' : '<span class="optional-badge">Optional</span>'}
                        <p class="param-description">${param.description || ''}</p>
                        <p class="param-type">Type: <code>${param.type}</code></p>
                        ${param.default ? `<p class="param-default">Default: <code>${param.default}</code></p>` : ''}
                    </li>
                `;
            });
            parametersHtml += '</ul>';
        }

        return `
            <div class="tool-details-content">
                <div class="detail-section">
                    <h4>Description</h4>
                    <p>${tool.description || 'No description available'}</p>
                </div>

                <div class="detail-section">
                    <h4>Category</h4>
                    <span class="category-badge ${tool.category}">${tool.category}</span>
                </div>

                <div class="detail-section">
                    <h4>Version</h4>
                    <p>${tool.version || 'Unknown'}</p>
                </div>

                <div class="detail-section">
                    <h4>Status</h4>
                    <span class="status-badge status-${tool.status}">${tool.status || 'unknown'}</span>
                </div>

                <div class="detail-section">
                    <h4>Parameters</h4>
                    ${parametersHtml}
                </div>

                ${tool.examples ? `
                    <div class="detail-section">
                        <h4>Examples</h4>
                        <pre class="code-block">${JSON.stringify(tool.examples, null, 2)}</pre>
                    </div>
                ` : ''}

                ${tool.documentation_url ? `
                    <div class="detail-section">
                        <h4>Documentation</h4>
                        <a href="${tool.documentation_url}" target="_blank" class="doc-link">View Documentation →</a>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Close tool details modal
     */
    closeToolDetailsModal() {
        document.getElementById('toolDetailsModal').classList.remove('active');
    }

    /**
     * Show execution modal
     */
    showExecutionModal() {
        if (!this.selectedTool) return;

        this.closeToolDetailsModal();

        const modal = document.getElementById('toolExecutionModal');
        const title = document.getElementById('executionModalTitle');
        const parametersContainer = document.getElementById('toolParametersContainer');

        title.textContent = `Execute: ${this.selectedTool.name}`;

        // Generate parameter inputs
        parametersContainer.innerHTML = this.renderParameterInputs(this.selectedTool);

        // Hide output initially
        document.getElementById('executionOutput').style.display = 'none';

        modal.classList.add('active');
    }

    /**
     * Render parameter input fields
     */
    renderParameterInputs(tool) {
        if (!tool.parameters || tool.parameters.length === 0) {
            return '<p class="no-params-message">This tool does not require any parameters.</p>';
        }

        let html = '';

        tool.parameters.forEach(param => {
            const inputId = `param_${param.name}`;
            const required = param.required ? 'required' : '';

            html += `
                <div class="form-group">
                    <label for="${inputId}">
                        ${param.name}
                        ${param.required ? '<span class="required-asterisk">*</span>' : ''}
                    </label>
                    ${param.description ? `<p class="param-help">${param.description}</p>` : ''}
                    ${this.renderParameterInput(param, inputId, required)}
                </div>
            `;
        });

        return html;
    }

    /**
     * Render specific parameter input based on type
     */
    renderParameterInput(param, inputId, required) {
        const defaultValue = param.default || '';

        switch (param.type) {
            case 'boolean':
                return `
                    <select id="${inputId}" class="form-control" ${required}>
                        <option value="true" ${defaultValue === true ? 'selected' : ''}>True</option>
                        <option value="false" ${defaultValue === false ? 'selected' : ''}>False</option>
                    </select>
                `;

            case 'select':
            case 'enum':
                let options = '';
                if (param.options) {
                    options = param.options.map(opt => 
                        `<option value="${opt}" ${opt === defaultValue ? 'selected' : ''}>${opt}</option>`
                    ).join('');
                }
                return `
                    <select id="${inputId}" class="form-control" ${required}>
                        <option value="">-- Select ${param.name} --</option>
                        ${options}
                    </select>
                `;

            case 'number':
            case 'integer':
                return `
                    <input type="number" 
                           id="${inputId}" 
                           class="form-control" 
                           value="${defaultValue}"
                           ${param.min !== undefined ? `min="${param.min}"` : ''}
                           ${param.max !== undefined ? `max="${param.max}"` : ''}
                           ${required}>
                `;

            case 'textarea':
            case 'text-long':
                return `
                    <textarea id="${inputId}" 
                              class="form-control" 
                              rows="4" 
                              ${required}>${defaultValue}</textarea>
                `;

            default:
                return `
                    <input type="text" 
                           id="${inputId}" 
                           class="form-control" 
                           value="${defaultValue}"
                           placeholder="Enter ${param.name}"
                           ${required}>
                `;
        }
    }

    /**
     * Execute selected tool
     */
    async executeSelectedTool() {
        if (!this.selectedTool) return;

        try {
            // Collect parameter values
            const parameters = {};
            const form = document.getElementById('toolExecutionForm');
            
            if (this.selectedTool.parameters) {
                this.selectedTool.parameters.forEach(param => {
                    const input = document.getElementById(`param_${param.name}`);
                    if (input) {
                        parameters[param.name] = input.value;
                    }
                });
            }

            // Disable run button
            const runBtn = document.getElementById('runToolBtn');
            const originalText = runBtn.textContent;
            runBtn.disabled = true;
            runBtn.textContent = 'Executing...';

            // Execute tool
            const result = await this.apiClient.executeTool(this.selectedTool.name, parameters);

            // Show output
            const outputDiv = document.getElementById('executionOutput');
            const outputContent = document.getElementById('executionOutputContent');
            outputContent.textContent = JSON.stringify(result, null, 2);
            outputDiv.style.display = 'block';

            // Add to execution history
            this.addToExecutionHistory({
                tool: this.selectedTool.name,
                parameters,
                result,
                timestamp: new Date().toISOString(),
                status: 'success'
            });

            // Re-enable run button
            runBtn.disabled = false;
            runBtn.textContent = originalText;

            this.showSuccess(`Tool executed successfully`);
        } catch (error) {
            console.error('Tool execution failed:', error);
            
            // Show error in output
            const outputDiv = document.getElementById('executionOutput');
            const outputContent = document.getElementById('executionOutputContent');
            outputContent.textContent = `Error: ${error.message}`;
            outputDiv.style.display = 'block';

            // Add to execution history
            this.addToExecutionHistory({
                tool: this.selectedTool.name,
                error: error.message,
                timestamp: new Date().toISOString(),
                status: 'error'
            });

            // Re-enable run button
            const runBtn = document.getElementById('runToolBtn');
            runBtn.disabled = false;
            runBtn.textContent = 'Run Tool';

            this.showError(`Tool execution failed: ${error.message}`);
        }
    }

    /**
     * Close execution modal
     */
    closeExecutionModal() {
        document.getElementById('toolExecutionModal').classList.remove('active');
    }

    /**
     * Load execution history
     */
    async loadExecutionHistory() {
        try {
            const history = await this.apiClient.getToolExecutionHistory();
            this.executionHistory = history;
            this.renderExecutionHistory();
        } catch (error) {
            console.error('Failed to load execution history:', error);
        }
    }

    /**
     * Add to execution history
     */
    addToExecutionHistory(execution) {
        this.executionHistory.unshift(execution);
        if (this.executionHistory.length > 50) {
            this.executionHistory = this.executionHistory.slice(0, 50);
        }
        this.renderExecutionHistory();
    }

    /**
     * Render execution history
     */
    renderExecutionHistory() {
        const historyContainer = document.getElementById('executionHistory');
        
        if (this.executionHistory.length === 0) {
            historyContainer.innerHTML = '<p class="empty-state">No recent executions</p>';
            return;
        }

        historyContainer.innerHTML = '';

        this.executionHistory.slice(0, 10).forEach(execution => {
            const item = document.createElement('div');
            item.className = `execution-item status-${execution.status}`;
            
            const timestamp = new Date(execution.timestamp).toLocaleString();
            
            item.innerHTML = `
                <div class="execution-header">
                    <span class="execution-tool">${execution.tool}</span>
                    <span class="execution-status ${execution.status}">${execution.status}</span>
                </div>
                <div class="execution-time">${timestamp}</div>
                ${execution.error ? `<div class="execution-error">${execution.error}</div>` : ''}
            `;

            historyContainer.appendChild(item);
        });
    }

    /**
     * Clear execution history
     */
    clearExecutionHistory() {
        if (confirm('Are you sure you want to clear the execution history?')) {
            this.executionHistory = [];
            this.renderExecutionHistory();
            this.showSuccess('Execution history cleared');
        }
    }

    /**
     * Validate all tools
     */
    async validateAllTools() {
        try {
            const validateBtn = document.getElementById('validateAllToolsBtn');
            validateBtn.disabled = true;
            validateBtn.textContent = 'Validating...';

            for (const tool of this.tools) {
                try {
                    await this.apiClient.validateTool(tool.name);
                } catch (error) {
                    console.error(`Validation failed for ${tool.name}:`, error);
                }
            }

            // Reload tools to get updated status
            await this.loadTools(this.currentCategory);

            validateBtn.disabled = false;
            validateBtn.textContent = '✓ Validate All';

            this.showSuccess('All tools validated');
        } catch (error) {
            console.error('Validation failed:', error);
            this.showError('Failed to validate tools');
        }
    }

    /**
     * Update tool count display
     */
    updateToolCount() {
        const countElement = document.getElementById('toolCount');
        if (countElement) {
            countElement.textContent = `${this.filteredTools.length} of ${this.tools.length} tools`;
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
}