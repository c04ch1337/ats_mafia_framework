/**
 * ATS MAFIA Scenarios Management
 * Handles scenario creation, editing, and management
 */

class ATSScenarios {
    constructor() {
        this.scenarios = [];
        this.filteredScenarios = [];
        this.currentScenario = null;
        this.isLoading = false;
        
        this.init();
    }

    /**
     * Initialize scenarios management
     */
    init() {
        console.log('Initializing ATS Scenarios...');
        
        // Ensure API baseURL is absolute with correct hostname for network accessibility
        try {
            if (typeof window !== 'undefined' && window.atsAPI && typeof window.atsAPI.baseURL === 'string') {
                const b = window.atsAPI.baseURL || '';
                const isAbsolute = /^https?:/i.test(b);
                const isRelative = b.startsWith('/');
                const servedFromHttp = window.location.protocol.startsWith('http');
                const differentPort = servedFromHttp && window.location.port && window.location.port !== '8000';
                const fromFile = window.location.protocol === 'file:';
                
                if (!isAbsolute || (differentPort && isRelative) || fromFile) {
                    // Use current hostname for network accessibility
                    const apiHost = (servedFromHttp && window.location.hostname) ? window.location.hostname : 'localhost';
                    const apiPort = '8000';
                    const basePath = isRelative ? b : '/api/v1';
                    window.atsAPI.baseURL = `http://${apiHost}:${apiPort}${basePath}`;
                    console.log('ATS Scenarios: normalized API baseURL to', window.atsAPI.baseURL);
                }
            }
        } catch (_) {}
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load scenarios
        this.loadScenarios();
        
        console.log('ATS Scenarios initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Create scenario button
        const createBtn = document.getElementById('createScenarioBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.showCreateScenarioModal();
            });
        }

        // Import scenario button
        const importBtn = document.getElementById('importScenarioBtn');
        if (importBtn) {
            importBtn.addEventListener('click', () => {
                this.importScenario();
            });
        }

        // Search input
        const searchInput = document.getElementById('scenarioSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => {
                this.filterScenarios();
            }, 300));
        }

        // Filter dropdowns
        const typeFilter = document.getElementById('scenarioTypeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', () => {
                this.filterScenarios();
            });
        }

        const difficultyFilter = document.getElementById('scenarioDifficultyFilter');
        if (difficultyFilter) {
            difficultyFilter.addEventListener('change', () => {
                this.filterScenarios();
            });
        }

        // Modal close buttons
        document.addEventListener('click', (e) => {
            if (e.target && e.target.classList && e.target.classList.contains('modal-close')) {
                const modal = e.target.closest('.modal-overlay');
                if (modal) {
                    this.closeModal(modal);
                }
            }
        });
    }

    /**
     * Load scenarios from API
     */
    async loadScenarios() {
        this.setLoadingState(true);
        
        try {
            this.scenarios = await window.atsAPI.getScenarios();
            this.filteredScenarios = [...this.scenarios];
            this.renderScenarios();
        } catch (error) {
            console.error('Failed to load scenarios:', error);
            this.showError('Failed to load scenarios. Ensure backend is running on ' + (window.atsAPI ? window.atsAPI.baseURL : 'port 8000'));
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Render scenarios grid
     */
    renderScenarios() {
        const grid = document.getElementById('scenariosGrid');
        const emptyState = document.getElementById('emptyState');
        
        if (!grid) return;

        grid.innerHTML = '';

        if (this.filteredScenarios.length === 0) {
            if (emptyState) emptyState.style.display = 'block';
            grid.style.display = 'none';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';
        grid.style.display = 'grid';

        this.filteredScenarios.forEach(scenario => {
            const scenarioCard = this.createScenarioCard(scenario);
            grid.appendChild(scenarioCard);
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
                <h3 class="scenario-name">${scenario.name || 'Unnamed Scenario'}</h3>
                <span class="difficulty-badge ${scenario.difficulty || 'intermediate'}">${scenario.difficulty || 'Intermediate'}</span>
            </div>
            <div class="scenario-body">
                <p class="scenario-description">${scenario.description || 'No description available'}</p>
                <div class="scenario-meta">
                    <span class="meta-item">
                        <i class="fas fa-clock"></i> ${scenario.estimated_duration || 'N/A'}
                    </span>
                    <span class="meta-item">
                        <i class="fas fa-flag"></i> ${scenario.objectives?.length || 0} objectives
                    </span>
                </div>
            </div>
            <div class="scenario-actions">
                <button class="ats-btn btn-sm btn-primary" onclick="atsScenarios.viewScenario('${scenario.id}')">
                    <i class="fas fa-eye"></i>
                    View
                </button>
                <button class="ats-btn btn-sm btn-success" onclick="atsScenarios.launchScenario('${scenario.id}')">
                    <i class="fas fa-play"></i>
                    Launch
                </button>
                <button class="ats-btn btn-sm btn-secondary" onclick="atsScenarios.editScenario('${scenario.id}')">
                    <i class="fas fa-edit"></i>
                    Edit
                </button>
            </div>
        `;

        return card;
    }

    /**
     * Filter scenarios
     */
    filterScenarios() {
        const searchTerm = (document.getElementById('scenarioSearch')?.value || '').toLowerCase();
        const typeFilter = document.getElementById('scenarioTypeFilter')?.value || '';
        const difficultyFilter = document.getElementById('scenarioDifficultyFilter')?.value || '';

        this.filteredScenarios = this.scenarios.filter(scenario => {
            const matchesSearch = !searchTerm || 
                (scenario.name || '').toLowerCase().includes(searchTerm) ||
                (scenario.description || '').toLowerCase().includes(searchTerm);

            const matchesType = !typeFilter || scenario.scenario_type === typeFilter;
            const matchesDifficulty = !difficultyFilter || scenario.difficulty === difficultyFilter;

            return matchesSearch && matchesType && matchesDifficulty;
        });

        this.renderScenarios();
    }

    /**
     * Show create scenario modal
     */
    showCreateScenarioModal() {
        if (window.atsComponents) {
            window.atsComponents.showNotification('Scenario creation UI coming soon', 'info');
        } else {
            alert('Scenario creation UI is under development');
        }
    }

    /**
     * View scenario details
     */
    async viewScenario(scenarioId) {
        try {
            const scenario = await window.atsAPI.getScenario(scenarioId);
            this.showScenarioDetails(scenario);
        } catch (error) {
            console.error('Failed to load scenario:', error);
            this.showError('Failed to load scenario');
        }
    }

    /**
     * Show scenario details modal
     */
    showScenarioDetails(scenario) {
        if (window.atsComponents) {
            const content = `
                <div class="scenario-details">
                    <h3>${scenario.name}</h3>
                    <p class="difficulty">Difficulty: <span class="${scenario.difficulty}">${scenario.difficulty}</span></p>
                    <p class="description">${scenario.description || ''}</p>
                    <h4>Objectives:</h4>
                    <ul>
                        ${(scenario.objectives || []).map(obj => `<li>${obj}</li>`).join('') || '<li>No objectives specified</li>'}
                    </ul>
                    <p class="estimated-time">Estimated Duration: ${scenario.estimated_duration || 'N/A'}</p>
                </div>
            `;
            window.atsComponents.openModal('scenario-details-modal', 'Scenario Details', content, { size: 'large' });
        }
    }

    /**
     * Launch scenario
     */
    async launchScenario(scenarioId) {
        try {
            const config = { scenario_id: scenarioId };
            const session = await window.atsAPI.startTrainingSession(config);
            this.showSuccess(`Scenario launched successfully! Session ID: ${session.id}`);
        } catch (error) {
            console.error('Failed to launch scenario:', error);
            this.showError('Failed to launch scenario');
        }
    }

    /**
     * Edit scenario (placeholder)
     */
    editScenario(scenarioId) {
        if (window.atsComponents) {
            window.atsComponents.showNotification('Scenario editing UI coming soon', 'info');
        }
    }

    /**
     * Import scenario
     */
    importScenario() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                const scenarioData = JSON.parse(text);
                
                await window.atsAPI.createScenario(scenarioData);
                this.showSuccess('Scenario imported successfully');
                await this.loadScenarios();
            } catch (error) {
                console.error('Failed to import scenario:', error);
                this.showError('Failed to import scenario. Please check the file format.');
            }
        });
        
        input.click();
    }

    /**
     * Close modal
     */
    closeModal(modal) {
        if (modal) {
            modal.classList.remove('active');
        }
    }

    /**
     * Set loading state
     */
    setLoadingState(loading) {
        this.isLoading = loading;
        const loadingState = document.getElementById('loadingState');
        const grid = document.getElementById('scenariosGrid');
        
        if (loading) {
            if (loadingState) loadingState.style.display = 'block';
            if (grid) grid.style.display = 'none';
        } else {
            if (loadingState) loadingState.style.display = 'none';
            if (grid) grid.style.display = 'grid';
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        if (window.atsComponents) {
            window.atsComponents.showNotification(message, 'success');
        } else {
            console.log('SUCCESS:', message);
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        if (window.atsComponents) {
            window.atsComponents.showNotification(message, 'error');
        } else {
            console.error('ERROR:', message);
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
}

// Initialize scenarios when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.atsScenarios = new ATSScenarios();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ATSScenarios;
}