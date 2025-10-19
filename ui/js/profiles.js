/**
 * ATS MAFIA Profiles Management
 * Handles profile creation, editing, and management
 */

class ATSProfiles {
    constructor() {
        this.profiles = [];
        this.filteredProfiles = [];
        this.currentProfile = null;
        this.isLoading = false;
        
        this.init();
    }

    /**
     * Initialize profiles management
     */
    init() {
        console.log('Initializing ATS Profiles...');
        
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
                    // Use current hostname for network accessibility (not hardcoded localhost)
                    const apiHost = (servedFromHttp && window.location.hostname) ? window.location.hostname : 'localhost';
                    const apiPort = '8000';
                    const basePath = isRelative ? b : '/api/v1';
                    window.atsAPI.baseURL = `http://${apiHost}:${apiPort}${basePath}`;
                    console.log('ATS Profiles: normalized API baseURL to', window.atsAPI.baseURL);
                }
            }
        } catch (_) {}

        // Set up event listeners
        this.setupEventListeners();
        
        // Load profiles
        this.loadProfiles();
        
        console.log('ATS Profiles initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Create profile button
        const createBtn = document.getElementById('createProfileBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.showCreateProfileModal();
            });
        }

        // Import profile button
        const importBtn = document.getElementById('importProfileBtn');
        if (importBtn) {
            importBtn.addEventListener('click', () => {
                this.importProfile();
            });
        }

        // Search input
        const searchInput = document.getElementById('profileSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.filterProfiles();
            }, 300));
        }

        // Filter dropdowns
        const typeFilter = document.getElementById('profileTypeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', () => {
                this.filterProfiles();
            });
        }

        const statusFilter = document.getElementById('profileStatusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                this.filterProfiles();
            });
        }

        // Profile form submission
        const profileForm = document.getElementById('profileForm');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleProfileSubmit(e);
            });
        }

        // Avatar input
        const avatarInput = document.getElementById('avatarInput');
        if (avatarInput) {
            avatarInput.addEventListener('change', (e) => {
                this.handleAvatarChange(e);
            });
        }

        // Profile action button delegation
        document.addEventListener('click', (e) => {
            const target = e.target;
            if (!target) return;

            // Find actual button (might click icon inside button)
            const button = target.closest('button');
            if (!button) return;

            // View profile
            if (button.classList.contains('profile-view-btn')) {
                const profileId = button.dataset.profileId;
                if (profileId) this.viewProfile(profileId);
            }
            // Edit profile
            else if (button.classList.contains('profile-edit-btn')) {
                const profileId = button.dataset.profileId;
                if (profileId) this.editProfile(profileId);
            }
            // Toggle status
            else if (button.classList.contains('profile-toggle-btn')) {
                const profileId = button.dataset.profileId;
                if (profileId) this.toggleProfileStatus(profileId);
            }
            // Delete profile
            else if (button.classList.contains('profile-delete-btn')) {
                const profileId = button.dataset.profileId;
                if (profileId) this.deleteProfile(profileId);
            }
        });

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
     * Load profiles from API
     */
    async loadProfiles() {
        this.setLoadingState(true);
        
        try {
            this.profiles = await window.atsAPI.getProfiles();
            this.filteredProfiles = [...this.profiles];
            this.renderProfiles();
        } catch (error) {
            console.error('Failed to load profiles:', error);
            this.showError('Failed to load profiles. Ensure backend is running on ' + (window.atsAPI ? window.atsAPI.baseURL : 'port 8000'));
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Render profiles grid
     */
    renderProfiles() {
        const grid = document.getElementById('profilesGrid');
        const emptyState = document.getElementById('emptyState');
        
        if (!grid) return;

        grid.innerHTML = '';

        if (this.filteredProfiles.length === 0) {
            emptyState.style.display = 'block';
            grid.style.display = 'none';
            return;
        }

        emptyState.style.display = 'none';
        grid.style.display = 'grid';

        this.filteredProfiles.forEach(profile => {
            const profileCard = this.createProfileCard(profile);
            grid.appendChild(profileCard);
        });
    }

    /**
     * Create profile card element
     */
    createProfileCard(profile) {
        const card = document.createElement('div');
        card.className = 'profile-card';
        card.dataset.profileId = profile.id;
        card.innerHTML = `
            <div class="profile-header">
                <div class="profile-avatar">
                    <img src="${profile.avatar || 'assets/images/default-avatar.png'}" alt="${profile.name}">
                    <div class="profile-status status-${profile.status}"></div>
                </div>
                <div class="profile-info">
                    <h3 class="profile-name">${profile.name}</h3>
                    <p class="profile-type">${this.formatProfileType(profile.type)}</p>
                </div>
            </div>
            <div class="profile-body">
                <p class="profile-description">${profile.description || 'No description available'}</p>
                <div class="profile-stats">
                    <div class="stat-item">
                        <span class="stat-label">Skill Level</span>
                        <span class="stat-value">${this.formatSkillLevel(profile.skill_level)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Specialization</span>
                        <span class="stat-value">${profile.specialization || 'General'}</span>
                    </div>
                </div>
            </div>
            <div class="profile-actions">
                <button class="ats-btn btn-sm btn-primary profile-view-btn" data-profile-id="${profile.id}">
                    <i class="fas fa-eye"></i>
                    View
                </button>
                <button class="ats-btn btn-sm btn-secondary profile-edit-btn" data-profile-id="${profile.id}">
                    <i class="fas fa-edit"></i>
                    Edit
                </button>
                <button class="ats-btn btn-sm ${profile.status === 'active' ? 'btn-danger' : 'btn-success'} profile-toggle-btn"
                        data-profile-id="${profile.id}" data-current-status="${profile.status}">
                    <i class="fas ${profile.status === 'active' ? 'fa-stop' : 'fa-play'}"></i>
                    ${profile.status === 'active' ? 'Stop' : 'Start'}
                </button>
                <button class="ats-btn btn-sm btn-danger profile-delete-btn" data-profile-id="${profile.id}">
                    <i class="fas fa-trash"></i>
                    Delete
                </button>
            </div>
        `;

        return card;
    }

    /**
     * Filter profiles based on search and filters
     */
    filterProfiles() {
        const searchTerm = document.getElementById('profileSearch').value.toLowerCase();
        const typeFilter = document.getElementById('profileTypeFilter').value;
        const statusFilter = document.getElementById('profileStatusFilter').value;

        this.filteredProfiles = this.profiles.filter(profile => {
            const matchesSearch = !searchTerm || 
                profile.name.toLowerCase().includes(searchTerm) ||
                profile.description?.toLowerCase().includes(searchTerm) ||
                profile.specialization?.toLowerCase().includes(searchTerm);

            const matchesType = !typeFilter || profile.type === typeFilter;
            const matchesStatus = !statusFilter || profile.status === statusFilter;

            return matchesSearch && matchesType && matchesStatus;
        });

        this.renderProfiles();
    }

    /**
     * Show create profile modal
     */
    showCreateProfileModal() {
        const modal = document.getElementById('profileModal');
        const form = document.getElementById('profileForm');
        
        if (form) {
            form.reset();
            form.dataset.mode = 'create';
            form.dataset.profileId = '';
        }
        
        if (modal) {
            modal.classList.add('active');
        }
    }

    /**
     * Show edit profile modal
     */
    async editProfile(profileId) {
        try {
            const profile = await window.atsAPI.getProfile(profileId);
            this.currentProfile = profile;
            
            const modal = document.getElementById('profileModal');
            const form = document.getElementById('profileForm');
            
            if (form) {
                form.dataset.mode = 'edit';
                form.dataset.profileId = profileId;
                
                // Populate form fields
                form.name.value = profile.name || '';
                form.type.value = profile.type || '';
                form.description.value = profile.description || '';
                form.skill_level.value = profile.skill_level || 'beginner';
                form.specialization.value = profile.specialization || '';
                form.configuration.value = JSON.stringify(profile.configuration || {}, null, 2);
                
                // Update avatar preview
                this.updateAvatarPreview(profile.avatar);
            }
            
            if (modal) {
                modal.classList.add('active');
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
            this.showError('Failed to load profile');
        }
    }

    /**
     * View profile details
     */
    async viewProfile(profileId) {
        try {
            const profile = await window.atsAPI.getProfile(profileId);
            this.showProfileDetails(profile);
        } catch (error) {
            console.error('Failed to load profile:', error);
            this.showError('Failed to load profile');
        }
    }

    /**
     * Show profile details modal
     */
    showProfileDetails(profile) {
        const modal = document.getElementById('profileDetailsModal');
        const content = document.getElementById('profileDetailsContent');
        
        if (content) {
            content.innerHTML = `
                <div class="profile-details">
                    <div class="profile-header-details">
                        <div class="profile-avatar-large">
                            <img src="${profile.avatar || 'assets/images/default-avatar.png'}" alt="${profile.name}">
                            <div class="profile-status status-${profile.status}"></div>
                        </div>
                        <div class="profile-info-details">
                            <h2>${profile.name}</h2>
                            <p class="profile-type">${this.formatProfileType(profile.type)}</p>
                            <p class="profile-description">${profile.description || 'No description available'}</p>
                        </div>
                    </div>
                    
                    <div class="profile-stats-grid">
                        <div class="stat-card">
                            <h4>Status</h4>
                            <span class="status-badge status-${profile.status}">${profile.status}</span>
                        </div>
                        <div class="stat-card">
                            <h4>Skill Level</h4>
                            <span>${this.formatSkillLevel(profile.skill_level)}</span>
                        </div>
                        <div class="stat-card">
                            <h4>Specialization</h4>
                            <span>${profile.specialization || 'General'}</span>
                        </div>
                        <div class="stat-card">
                            <h4>Created</h4>
                            <span>${this.formatDate(profile.created_at)}</span>
                        </div>
                    </div>
                    
                    <div class="profile-configuration">
                        <h3>Configuration</h3>
                        <pre><code>${JSON.stringify(profile.configuration || {}, null, 2)}</code></pre>
                    </div>
                    
                    <div class="profile-actions-details">
                        <button class="ats-btn btn-primary" onclick="atsProfiles.editProfile('${profile.id}')">
                            <i class="fas fa-edit"></i>
                            Edit Profile
                        </button>
                        <button class="ats-btn btn-success" onclick="atsProfiles.launchProfile('${profile.id}')">
                            <i class="fas fa-play"></i>
                            Launch Profile
                        </button>
                        <button class="ats-btn btn-secondary" onclick="atsProfiles.exportProfile('${profile.id}')">
                            <i class="fas fa-download"></i>
                            Export Profile
                        </button>
                    </div>
                </div>
            `;
        }
        
        if (modal) {
            modal.classList.add('active');
        }
    }

    /**
     * Handle profile form submission
     */
    async handleProfileSubmit(e) {
        const form = e.target;
        const formData = new FormData(form);
        const mode = form.dataset.mode;
        const profileId = form.dataset.profileId;

        // Basic required field validation
        const name = (formData.get('name') || '').toString().trim();
        const type = (formData.get('type') || '').toString().trim();
        if (!name || !type) {
            this.showError('Name and Type are required');
            return;
        }

        // Parse configuration safely
        let configuration = {};
        const cfgRaw = formData.get('configuration');
        if (cfgRaw && cfgRaw.toString().trim().length > 0) {
            try {
                configuration = JSON.parse(cfgRaw);
            } catch (parseErr) {
                console.error('Invalid configuration JSON:', parseErr);
                this.showError('Configuration must be valid JSON');
                return;
            }
        }

        // Log final base URL before submission for debugging
        try {
            if (typeof window !== 'undefined' && window.atsAPI) {
                console.log('ATS Profiles: submitting to API at', window.atsAPI.baseURL);
            }
        } catch (_) {}

        try {
            const profileData = {
                name,
                type,
                description: formData.get('description'),
                skill_level: formData.get('skill_level'),
                specialization: formData.get('specialization'),
                configuration
            };

            // Disable submit to prevent double submissions
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;

            if (mode === 'create') {
                await window.atsAPI.createProfile(profileData);
                this.showSuccess('Profile created successfully');
            } else if (mode === 'edit') {
                await window.atsAPI.updateProfile(profileId, profileData);
                this.showSuccess('Profile updated successfully');
            }

            this.closeModal(document.getElementById('profileModal'));
            await this.loadProfiles();
        } catch (error) {
            console.error('Failed to save profile:', error);
            const msg = (error && error.message) ? error.message : 'Failed to save profile';
            this.showError(msg);
        } finally {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = false;
        }
    }

    /**
     * Toggle profile status
     */
    async toggleProfileStatus(profileId) {
        try {
            const profile = this.profiles.find(p => p.id === profileId);
            if (!profile) return;

            if (profile.status === 'active') {
                await window.atsAPI.deactivateProfile(profileId);
                this.showSuccess('Profile deactivated');
            } else {
                await window.atsAPI.activateProfile(profileId);
                this.showSuccess('Profile activated');
            }

            await this.loadProfiles();
            
        } catch (error) {
            console.error('Failed to toggle profile status:', error);
            this.showError('Failed to update profile status');
        }
    }

    /**
     * Delete profile
     */
    async deleteProfile(profileId) {
        if (!confirm('Are you sure you want to delete this profile? This action cannot be undone.')) {
            return;
        }

        try {
            await window.atsAPI.deleteProfile(profileId);
            this.showSuccess('Profile deleted successfully');
            await this.loadProfiles();
            
        } catch (error) {
            console.error('Failed to delete profile:', error);
            this.showError('Failed to delete profile');
        }
    }

    /**
     * Launch profile
     */
    async launchProfile(profileId) {
        try {
            await window.atsAPI.activateProfile(profileId);
            this.showSuccess('Profile launched successfully');
            await this.loadProfiles();
            
        } catch (error) {
            console.error('Failed to launch profile:', error);
            this.showError('Failed to launch profile');
        }
    }

    /**
     * Export profile
     */
    async exportProfile(profileId) {
        try {
            const profile = await window.atsAPI.getProfile(profileId);
            const dataStr = JSON.stringify(profile, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `${profile.name.replace(/\s+/g, '_')}_profile.json`;
            link.click();
            
            this.showSuccess('Profile exported successfully');
            
        } catch (error) {
            console.error('Failed to export profile:', error);
            this.showError('Failed to export profile');
        }
    }

    /**
     * Import profile
     */
    importProfile() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                const profileData = JSON.parse(text);
                
                await window.atsAPI.createProfile(profileData);
                this.showSuccess('Profile imported successfully');
                await this.loadProfiles();
                
            } catch (error) {
                console.error('Failed to import profile:', error);
                this.showError('Failed to import profile. Please check the file format.');
            }
        });
        
        input.click();
    }

    /**
     * Handle avatar change
     */
    handleAvatarChange(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            this.updateAvatarPreview(e.target.result);
        };
        reader.readAsDataURL(file);
    }

    /**
     * Update avatar preview
     */
    updateAvatarPreview(src) {
        const preview = document.getElementById('avatarPreview');
        if (preview) {
            if (src) {
                preview.innerHTML = `<img src="${src}" alt="Avatar Preview">`;
            } else {
                preview.innerHTML = '<i class="fas fa-user"></i>';
            }
        }
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
        const grid = document.getElementById('profilesGrid');
        
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
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        if (window.atsComponents) {
            window.atsComponents.showNotification(message, 'error');
        }
    }

    /**
     * Format profile type
     */
    formatProfileType(type) {
        const types = {
            'red_team': 'Red Team',
            'blue_team': 'Blue Team',
            'social_engineer': 'Social Engineer'
        };
        return types[type] || type;
    }

    /**
     * Format skill level
     */
    formatSkillLevel(level) {
        const levels = {
            'beginner': 'Beginner',
            'intermediate': 'Intermediate',
            'advanced': 'Advanced',
            'expert': 'Expert'
        };
        return levels[level] || level;
    }

    /**
     * Format date
     */
    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        return new Date(dateString).toLocaleDateString();
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

// Initialize profiles when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.atsProfiles = new ATSProfiles();
});