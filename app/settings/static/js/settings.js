/**
 * Settings Hub JavaScript
 * Handles sidebar toggle, navigation, and interactive features
 */

class SettingsHub {
    constructor() {
        this.sidebar = document.querySelector('.settings-sidebar');
        this.toggleBtn = document.querySelector('.sidebar-toggle');
        this.mobileBreakpoint = 768;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setActiveNavItem();
        this.handleResponsive();
        
        // Load saved sidebar state
        this.loadSidebarState();
    }
    
    bindEvents() {
        // Sidebar toggle
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggleSidebar());
        }
        
        // Close sidebar on mobile when clicking outside
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= this.mobileBreakpoint) {
                if (!this.sidebar.contains(e.target) && this.sidebar.classList.contains('mobile-open')) {
                    this.closeMobileSidebar();
                }
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', () => this.handleResponsive());
        
        // Form submissions with loading states
        this.bindFormSubmissions();
        
        // Delete confirmations
        this.bindDeleteConfirmations();
    }
    
    toggleSidebar() {
        if (window.innerWidth <= this.mobileBreakpoint) {
            this.toggleMobileSidebar();
        } else {
            this.toggleDesktopSidebar();
        }
    }
    
    toggleDesktopSidebar() {
        this.sidebar.classList.toggle('collapsed');
        this.saveSidebarState();
    }
    
    toggleMobileSidebar() {
        this.sidebar.classList.toggle('mobile-open');
    }
    
    closeMobileSidebar() {
        this.sidebar.classList.remove('mobile-open');
    }
    
    handleResponsive() {
        if (window.innerWidth <= this.mobileBreakpoint) {
            this.sidebar.classList.remove('collapsed');
            this.sidebar.classList.remove('mobile-open');
        } else {
            this.sidebar.classList.remove('mobile-open');
        }
    }
    
    setActiveNavItem() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            
            const href = link.getAttribute('href');
            if (href && (currentPath === href || currentPath.startsWith(href + '/'))) {
                link.classList.add('active');
            }
        });
    }
    
    saveSidebarState() {
        const isCollapsed = this.sidebar.classList.contains('collapsed');
        localStorage.setItem('settings-sidebar-collapsed', isCollapsed);
    }
    
    loadSidebarState() {
        const isCollapsed = localStorage.getItem('settings-sidebar-collapsed') === 'true';
        if (isCollapsed && window.innerWidth > this.mobileBreakpoint) {
            this.sidebar.classList.add('collapsed');
        }
    }
    
    bindFormSubmissions() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('loading');
                    submitBtn.disabled = true;
                    
                    // Add spinner if not present
                    if (!submitBtn.querySelector('.spinner')) {
                        const spinner = document.createElement('span');
                        spinner.className = 'spinner';
                        submitBtn.insertBefore(spinner, submitBtn.firstChild);
                    }
                }
            });
        });
    }
    
    bindDeleteConfirmations() {
        const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                const itemName = button.getAttribute('data-item-name') || 'this item';
                const message = `Are you sure you want to delete "${itemName}"? This action cannot be undone.`;
                
                if (confirm(message)) {
                    // If it's a form, submit it
                    const form = button.closest('form');
                    if (form) {
                        form.submit();
                    } else {
                        // If it's a link, follow it
                        window.location.href = button.href;
                    }
                }
            });
        });
    }
    
    // Utility methods for dynamic content
    showLoading(element) {
        element.classList.add('loading');
    }
    
    hideLoading(element) {
        element.classList.remove('loading');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            this.removeNotification(notification);
        }, 5000);
        
        // Bind close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.removeNotification(notification);
        });
    }
    
    removeNotification(notification) {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
}

// AJAX utilities for dynamic content loading
class SettingsAPI {
    constructor() {
        this.baseUrl = '/settings/api';
    }
    
    async getCategories() {
        try {
            const response = await fetch(`${this.baseUrl}/categories`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching categories:', error);
            return [];
        }
    }
    
    async getMines() {
        try {
            const response = await fetch(`${this.baseUrl}/mines`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching mines:', error);
            return [];
        }
    }
    
    async getSubtypesByCategory(categoryId) {
        try {
            const response = await fetch(`${this.baseUrl}/subtypes/category/${categoryId}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching subtypes:', error);
            return [];
        }
    }
}

// Form utilities
class FormUtils {
    static populateSelect(selectElement, options, valueKey = 'id', textKey = 'name', placeholder = null) {
        // Clear existing options
        selectElement.innerHTML = '';
        
        // Add placeholder if provided
        if (placeholder) {
            const placeholderOption = document.createElement('option');
            placeholderOption.value = '';
            placeholderOption.textContent = placeholder;
            selectElement.appendChild(placeholderOption);
        }
        
        // Add options
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option[valueKey];
            optionElement.textContent = option[textKey];
            selectElement.appendChild(optionElement);
        });
    }
    
    static async updateSubtypesByCategory(categorySelect, subtypeSelect) {
        const categoryId = categorySelect.value;
        
        if (!categoryId) {
            FormUtils.populateSelect(subtypeSelect, [], 'id', 'name', '-- Select Category First --');
            return;
        }
        
        try {
            const api = new SettingsAPI();
            const subtypes = await api.getSubtypesByCategory(categoryId);
            FormUtils.populateSelect(subtypeSelect, subtypes, 'id', 'name', '-- Select Subtype --');
        } catch (error) {
            console.error('Error updating subtypes:', error);
            FormUtils.populateSelect(subtypeSelect, [], 'id', 'name', '-- Error Loading Subtypes --');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize main settings hub
    window.settingsHub = new SettingsHub();
    window.settingsAPI = new SettingsAPI();
    
    // Initialize form dependencies
    const categorySelects = document.querySelectorAll('[data-category-select]');
    categorySelects.forEach(categorySelect => {
        const subtypeSelectId = categorySelect.getAttribute('data-subtype-target');
        const subtypeSelect = document.getElementById(subtypeSelectId);
        
        if (subtypeSelect) {
            categorySelect.addEventListener('change', () => {
                FormUtils.updateSubtypesByCategory(categorySelect, subtypeSelect);
            });
        }
    });
    
    // Add animation classes to elements
    const animatedElements = document.querySelectorAll('.settings-card, .stat-card');
    animatedElements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add('animate-slide-in');
        }, index * 100);
    });
});

// Export for use in other scripts
window.SettingsHub = SettingsHub;
window.SettingsAPI = SettingsAPI;
window.FormUtils = FormUtils;

