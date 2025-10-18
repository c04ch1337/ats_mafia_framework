/**
 * ATS MAFIA UI Components
 * Reusable UI components and utilities
 */

class ATSComponents {
    constructor() {
        this.modals = new Map();
        this.tooltips = new Map();
        this.notifications = [];
        this.init();
    }

    /**
     * Initialize components
     */
    init() {
        this.setupModals();
        this.setupTooltips();
        this.setupNotifications();
        this.setupFormValidation();
    }

    /**
     * Setup modal system
     */
    setupModals() {
        // Modal close buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close')) {
                this.closeModal(e.target.closest('.modal-overlay'));
            }
        });

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeModal(e.target);
            }
        });

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal-overlay.active');
                if (openModal) {
                    this.closeModal(openModal);
                }
            }
        });
    }

    /**
     * Open modal
     */
    openModal(modalId, title, content, options = {}) {
        const modal = document.getElementById(modalId) || this.createModal(modalId);
        const modalTitle = modal.querySelector('.modal-title');
        const modalContent = modal.querySelector('.modal-content');

        if (title) modalTitle.textContent = title;
        if (content) modalContent.innerHTML = content;

        // Apply options
        if (options.size) {
            modal.classList.add(`modal-${options.size}`);
        }
        if (options.backdrop !== false) {
            modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        }

        modal.classList.add('active');
        this.modals.set(modalId, { modal, options });

        // Focus management
        const focusableElements = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }

        return modal;
    }

    /**
     * Close modal
     */
    closeModal(modal) {
        if (!modal) return;

        modal.classList.remove('active');
        
        // Remove custom classes
        modal.className = modal.className.replace(/modal-\w+/g, '').trim();
        
        const modalId = modal.id;
        if (this.modals.has(modalId)) {
            this.modals.delete(modalId);
        }

        // Return focus to trigger
        const trigger = document.querySelector(`[data-modal-target="${modalId}"]`);
        if (trigger) {
            trigger.focus();
        }
    }

    /**
     * Create modal dynamically
     */
    createModal(modalId) {
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-container">
                <div class="modal-header">
                    <h3 class="modal-title">Modal Title</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-content">
                    <!-- Dynamic content -->
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        return modal;
    }

    /**
     * Setup tooltips
     */
    setupTooltips() {
        document.addEventListener('mouseenter', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.showTooltip(target);
            }
        }, true);

        document.addEventListener('mouseleave', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.hideTooltip(target);
            }
        }, true);
    }

    /**
     * Show tooltip
     */
    showTooltip(element) {
        const text = element.dataset.tooltip;
        const position = element.dataset.tooltipPosition || 'top';
        
        const tooltip = document.createElement('div');
        tooltip.className = `ats-tooltip tooltip-${position}`;
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        // Position tooltip
        switch (position) {
            case 'top':
                tooltip.style.left = rect.left + (rect.width / 2) - (tooltipRect.width / 2) + 'px';
                tooltip.style.top = rect.top - tooltipRect.height - 10 + 'px';
                break;
            case 'bottom':
                tooltip.style.left = rect.left + (rect.width / 2) - (tooltipRect.width / 2) + 'px';
                tooltip.style.top = rect.bottom + 10 + 'px';
                break;
            case 'left':
                tooltip.style.left = rect.left - tooltipRect.width - 10 + 'px';
                tooltip.style.top = rect.top + (rect.height / 2) - (tooltipRect.height / 2) + 'px';
                break;
            case 'right':
                tooltip.style.left = rect.right + 10 + 'px';
                tooltip.style.top = rect.top + (rect.height / 2) - (tooltipRect.height / 2) + 'px';
                break;
        }
        
        this.tooltips.set(element, tooltip);
        
        // Fade in
        setTimeout(() => tooltip.classList.add('active'), 10);
    }

    /**
     * Hide tooltip
     */
    hideTooltip(element) {
        const tooltip = this.tooltips.get(element);
        if (tooltip) {
            tooltip.classList.remove('active');
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
                this.tooltips.delete(element);
            }, 200);
        }
    }

    /**
     * Setup notifications
     */
    setupNotifications() {
        // Create notification container
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info', options = {}) {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `ats-notification notification-${type}`;
        
        if (options.autoHide !== false) {
            notification.dataset.autoHide = options.autoHide || 5000;
        }

        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas ${this.getNotificationIcon(type)}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">${options.title || type.charAt(0).toUpperCase() + type.slice(1)}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(notification);

        // Auto hide
        if (options.autoHide !== false) {
            setTimeout(() => {
                this.hideNotification(notification);
            }, parseInt(notification.dataset.autoHide));
        }

        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });

        // Click to close
        if (options.clickToClose !== false) {
            notification.addEventListener('click', () => {
                this.hideNotification(notification);
            });
        }

        this.notifications.push(notification);
        return notification;
    }

    /**
     * Hide notification
     */
    hideNotification(notification) {
        if (!notification || !notification.parentNode) return;

        notification.classList.add('hiding');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }

    /**
     * Get notification icon
     */
    getNotificationIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    /**
     * Setup form validation
     */
    setupFormValidation() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.classList.contains('ats-form')) {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            }
        });

        // Real-time validation
        document.addEventListener('blur', (e) => {
            if (e.target.classList.contains('ats-form-input')) {
                this.validateField(e.target);
            }
        }, true);
    }

    /**
     * Validate form
     */
    validateForm(form) {
        const fields = form.querySelectorAll('.ats-form-input[required]');
        let isValid = true;

        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Validate field
     */
    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        let isValid = true;
        let errorMessage = '';

        // Required validation
        if (required && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Type-specific validation
        if (value && isValid) {
            switch (type) {
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid email address';
                    }
                    break;
                case 'url':
                    try {
                        new URL(value);
                    } catch {
                        isValid = false;
                        errorMessage = 'Please enter a valid URL';
                    }
                    break;
                case 'tel':
                    const phoneRegex = /^[\d\s\-\+\(\)]+$/;
                    if (!phoneRegex.test(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid phone number';
                    }
                    break;
            }
        }

        // Custom validation
        if (value && isValid && field.dataset.validation) {
            try {
                const regex = new RegExp(field.dataset.validation);
                if (!regex.test(value)) {
                    isValid = false;
                    errorMessage = field.dataset.validationMessage || 'Invalid format';
                }
            } catch (error) {
                console.error('Invalid validation regex:', error);
            }
        }

        // Update field UI
        this.updateFieldValidation(field, isValid, errorMessage);

        return isValid;
    }

    /**
     * Update field validation UI
     */
    updateFieldValidation(field, isValid, errorMessage) {
        const formGroup = field.closest('.ats-form-group');
        if (!formGroup) return;

        // Remove existing validation states
        field.classList.remove('valid', 'invalid');
        const existingError = formGroup.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        if (isValid) {
            field.classList.add('valid');
        } else {
            field.classList.add('invalid');
            
            const errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            errorElement.textContent = errorMessage;
            formGroup.appendChild(errorElement);
        }
    }

    /**
     * Create loading spinner
     */
    createSpinner(size = 'medium') {
        const spinner = document.createElement('div');
        spinner.className = `ats-spinner spinner-${size}`;
        spinner.innerHTML = '<div class="spinner-circle"></div>';
        return spinner;
    }

    /**
     * Show loading state
     */
    showLoading(element, message = 'Loading...') {
        const spinner = this.createSpinner();
        const loadingText = document.createElement('div');
        loadingText.className = 'loading-text';
        loadingText.textContent = message;

        const container = document.createElement('div');
        container.className = 'loading-container';
        container.appendChild(spinner);
        container.appendChild(loadingText);

        element.appendChild(container);
        element.classList.add('loading');
    }

    /**
     * Hide loading state
     */
    hideLoading(element) {
        const loadingContainer = element.querySelector('.loading-container');
        if (loadingContainer) {
            loadingContainer.remove();
        }
        element.classList.remove('loading');
    }

    /**
     * Create progress bar
     */
    createProgressBar(value = 0, max = 100, options = {}) {
        const progressBar = document.createElement('div');
        progressBar.className = `ats-progress-bar ${options.className || ''}`;
        
        const progressFill = document.createElement('div');
        progressFill.className = 'progress-fill';
        progressFill.style.width = `${(value / max) * 100}%`;
        
        if (options.animated) {
            progressFill.classList.add('animated');
        }
        
        if (options.striped) {
            progressFill.classList.add('striped');
        }
        
        progressBar.appendChild(progressFill);
        
        if (options.showLabel) {
            const label = document.createElement('div');
            label.className = 'progress-label';
            label.textContent = `${Math.round((value / max) * 100)}%`;
            progressBar.appendChild(label);
        }
        
        return progressBar;
    }

    /**
     * Update progress bar
     */
    updateProgressBar(progressBar, value, max = 100) {
        const progressFill = progressBar.querySelector('.progress-fill');
        const label = progressBar.querySelector('.progress-label');
        
        if (progressFill) {
            progressFill.style.width = `${(value / max) * 100}%`;
        }
        
        if (label) {
            label.textContent = `${Math.round((value / max) * 100)}%`;
        }
    }

    /**
     * Create card component
     */
    createCard(title, content, options = {}) {
        const card = document.createElement('div');
        card.className = `ats-card ${options.className || ''}`;
        
        if (title) {
            const header = document.createElement('div');
            header.className = 'ats-card-header';
            header.innerHTML = `<h3 class="ats-card-title">${title}</h3>`;
            
            if (options.actions) {
                const actions = document.createElement('div');
                actions.className = 'card-actions';
                actions.innerHTML = options.actions;
                header.appendChild(actions);
            }
            
            card.appendChild(header);
        }
        
        if (content) {
            const cardContent = document.createElement('div');
            cardContent.className = 'ats-card-content';
            cardContent.innerHTML = content;
            card.appendChild(cardContent);
        }
        
        return card;
    }

    /**
     * Create badge component
     */
    createBadge(text, type = 'default', options = {}) {
        const badge = document.createElement('span');
        badge.className = `ats-badge badge-${type} ${options.className || ''}`;
        badge.textContent = text;
        
        if (options.pill) {
            badge.classList.add('badge-pill');
        }
        
        return badge;
    }

    /**
     * Create button component
     */
    createButton(text, type = 'primary', options = {}) {
        const button = document.createElement('button');
        button.className = `ats-btn btn-${type} ${options.className || ''}`;
        button.textContent = text;
        
        if (options.icon) {
            const icon = document.createElement('i');
            icon.className = `fas ${options.icon}`;
            button.insertBefore(icon, button.firstChild);
        }
        
        if (options.disabled) {
            button.disabled = true;
        }
        
        if (options.loading) {
            button.classList.add('btn-loading');
            const spinner = this.createSpinner('small');
            button.appendChild(spinner);
        }
        
        if (options.onclick) {
            button.addEventListener('click', options.onclick);
        }
        
        return button;
    }

    /**
     * Format date
     */
    formatDate(date, format = 'short') {
        const d = new Date(date);
        
        switch (format) {
            case 'short':
                return d.toLocaleDateString();
            case 'long':
                return d.toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                });
            case 'time':
                return d.toLocaleTimeString();
            case 'datetime':
                return d.toLocaleString();
            default:
                return d.toLocaleDateString();
        }
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Initialize components when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.atsComponents = new ATSComponents();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ATSComponents;
}