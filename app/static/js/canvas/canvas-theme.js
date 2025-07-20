// Canvas Theme Management
class CanvasTheme {
    constructor() {
        this.currentTheme = localStorage.getItem('canvas-theme') || 'light';
        this.init();
    }
    
    init() {
        this.themeToggle = document.getElementById('theme-toggle');
        this.setupEventListeners();
        this.applyTheme(this.currentTheme);
    }
    
    setupEventListeners() {
        this.themeToggle.addEventListener('click', () => {
            this.toggleTheme();
        });
    }
    
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('canvas-theme', this.currentTheme);
        
        // Auto-save theme preference
        if (window.CanvasAutoSave) {
            window.CanvasAutoSave.save();
        }
    }
    
    applyTheme(theme) {
        document.documentElement.dataset.theme = theme;
        
        // Update theme toggle icon
        const icon = this.themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            this.themeToggle.title = 'Switch to Light Mode';
        } else {
            icon.className = 'fas fa-moon';
            this.themeToggle.title = 'Switch to Dark Mode';
        }
        
        // Update canvas background
        this.updateCanvasBackground(theme);
    }
    
    updateCanvasBackground(theme) {
        const canvasContainer = document.getElementById('canvas-container');
        const canvasWorkspace = document.getElementById('canvas-workspace');
        
        if (theme === 'dark') {
            canvasContainer.style.background = '#1a1a1a';
            canvasContainer.style.color = '#ffffff';
            if (canvasWorkspace) {
                canvasWorkspace.style.background = '#1a1a1a';
            }
        } else {
            canvasContainer.style.background = '#ffffff';
            canvasContainer.style.color = '#333333';
            if (canvasWorkspace) {
                canvasWorkspace.style.background = '#ffffff';
            }
        }
        
        // Update grid pattern
        this.updateGridPattern(theme);
    }
    
    updateGridPattern(theme) {
        const grid = document.getElementById('canvas-grid');
        if (grid) {
            const dotColor = theme === 'dark' ? '#404040' : '#dee2e6';
            grid.style.backgroundImage = `radial-gradient(circle, ${dotColor} 1px, transparent 1px)`;
        }
    }
    
    // Get current theme
    getTheme() {
        return this.currentTheme;
    }
    
    // Set theme programmatically
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.currentTheme = theme;
            this.applyTheme(theme);
            localStorage.setItem('canvas-theme', theme);
        }
    }
}

// Initialize theme management when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.canvasTheme = new CanvasTheme();
});
