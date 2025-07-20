// Canvas Tools and Utilities
class CanvasTools {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupSelectionBox();
        this.setupKeyboardShortcuts();
        this.setupDragAndDrop();
    }
    
    setupSelectionBox() {
        let isSelecting = false;
        let selectionStart = { x: 0, y: 0 };
        let selectionBox = null;
        
        const workspace = document.getElementById('canvas-workspace');
        
        workspace.addEventListener('mousedown', (e) => {
            if (e.target === workspace && window.canvasCore.currentTool === 'select') {
                isSelecting = true;
                selectionStart = { x: e.clientX, y: e.clientY };
                
                // Create selection box
                selectionBox = document.createElement('div');
                selectionBox.className = 'selection-box';
                selectionBox.style.left = selectionStart.x + 'px';
                selectionBox.style.top = selectionStart.y + 'px';
                selectionBox.style.width = '0px';
                selectionBox.style.height = '0px';
                document.body.appendChild(selectionBox);
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (isSelecting && selectionBox) {
                const currentX = e.clientX;
                const currentY = e.clientY;
                
                const left = Math.min(selectionStart.x, currentX);
                const top = Math.min(selectionStart.y, currentY);
                const width = Math.abs(currentX - selectionStart.x);
                const height = Math.abs(currentY - selectionStart.y);
                
                selectionBox.style.left = left + 'px';
                selectionBox.style.top = top + 'px';
                selectionBox.style.width = width + 'px';
                selectionBox.style.height = height + 'px';
                
                // Highlight elements within selection
                this.highlightElementsInSelection(left, top, width, height);
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (isSelecting) {
                isSelecting = false;
                if (selectionBox) {
                    selectionBox.remove();
                    selectionBox = null;
                }
            }
        });
    }
    
    highlightElementsInSelection(left, top, width, height) {
        const elements = document.querySelectorAll('.canvas-element');
        const selectionRect = { left, top, right: left + width, bottom: top + height };
        
        elements.forEach(element => {
            const elementRect = element.getBoundingClientRect();
            
            // Check if element intersects with selection box
            if (this.rectsIntersect(selectionRect, elementRect)) {
                element.classList.add('selected');
                window.canvasCore.selectedElements.add(element.dataset.elementId);
            } else {
                element.classList.remove('selected');
                window.canvasCore.selectedElements.delete(element.dataset.elementId);
            }
        });
    }
    
    rectsIntersect(rect1, rect2) {
        return !(rect1.right < rect2.left || 
                rect1.left > rect2.right || 
                rect1.bottom < rect2.top || 
                rect1.top > rect2.bottom);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Tool shortcuts
            if (!e.ctrlKey && !e.metaKey && !e.altKey) {
                switch (e.key) {
                    case 'v':
                    case 'V':
                        if (document.activeElement.tagName !== 'INPUT' && 
                            document.activeElement.tagName !== 'TEXTAREA') {
                            window.canvasCore.setTool('select');
                            e.preventDefault();
                        }
                        break;
                    case 't':
                    case 'T':
                        if (document.activeElement.tagName !== 'INPUT' && 
                            document.activeElement.tagName !== 'TEXTAREA') {
                            window.canvasCore.setTool('text');
                            e.preventDefault();
                        }
                        break;
                    case 's':
                    case 'S':
                        if (document.activeElement.tagName !== 'INPUT' && 
                            document.activeElement.tagName !== 'TEXTAREA') {
                            window.canvasCore.setTool('shape');
                            e.preventDefault();
                        }
                        break;
                }
            }
            
            // Zoom shortcuts
            if (e.ctrlKey || e.metaKey) {
                if (e.key === '=' || e.key === '+') {
                    e.preventDefault();
                    window.canvasCore.zoomIn();
                } else if (e.key === '-') {
                    e.preventDefault();
                    window.canvasCore.zoomOut();
                } else if (e.key === '0') {
                    e.preventDefault();
                    window.canvasCore.zoom = 1;
                    window.canvasCore.updateZoom();
                }
            }
        });
    }
    
    setupDragAndDrop() {
        const workspace = document.getElementById('canvas-workspace');
        
        workspace.addEventListener('dragover', (e) => {
            e.preventDefault();
            workspace.classList.add('drag-over');
        });
        
        workspace.addEventListener('dragleave', (e) => {
            if (!workspace.contains(e.relatedTarget)) {
                workspace.classList.remove('drag-over');
            }
        });
        
        workspace.addEventListener('drop', (e) => {
            e.preventDefault();
            workspace.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                const rect = workspace.getBoundingClientRect();
                const x = (e.clientX - rect.left) / window.canvasCore.zoom;
                const y = (e.clientY - rect.top) / window.canvasCore.zoom;
                
                files.forEach((file, index) => {
                    this.uploadAndCreateElement(file, x + (index * 20), y + (index * 20));
                });
            }
        });
    }
    
    async uploadAndCreateElement(file, x, y) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`/canvas/api/canvas/${window.canvasData.canvasId}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (file.type.startsWith('image/')) {
                    window.canvasCore.createImageElement(x, y, data.url, file.name);
                } else {
                    window.canvasCore.createDocumentElement(x, y, data.file);
                }
            } else {
                console.error('Upload failed:', data.message);
            }
        } catch (error) {
            console.error('Upload error:', error);
        }
    }
    
    // Utility functions
    static getElementCenter(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        };
    }
    
    static getDistance(point1, point2) {
        const dx = point2.x - point1.x;
        const dy = point2.y - point1.y;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    static snapToGrid(value, gridSize = 20) {
        return Math.round(value / gridSize) * gridSize;
    }
    
    static clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }
    
    // Element alignment tools
    static alignElements(elements, alignment) {
        if (elements.length < 2) return;
        
        const rects = elements.map(el => ({
            element: el,
            rect: el.getBoundingClientRect(),
            data: window.canvasCore.elements.get(el.dataset.elementId)
        }));
        
        switch (alignment) {
            case 'left':
                const leftMost = Math.min(...rects.map(r => r.rect.left));
                rects.forEach(({ element, data }) => {
                    data.x = leftMost;
                    element.style.left = leftMost + 'px';
                });
                break;
                
            case 'right':
                const rightMost = Math.max(...rects.map(r => r.rect.right));
                rects.forEach(({ element, data }) => {
                    data.x = rightMost - data.width;
                    element.style.left = (rightMost - data.width) + 'px';
                });
                break;
                
            case 'top':
                const topMost = Math.min(...rects.map(r => r.rect.top));
                rects.forEach(({ element, data }) => {
                    data.y = topMost;
                    element.style.top = topMost + 'px';
                });
                break;
                
            case 'bottom':
                const bottomMost = Math.max(...rects.map(r => r.rect.bottom));
                rects.forEach(({ element, data }) => {
                    data.y = bottomMost - data.height;
                    element.style.top = (bottomMost - data.height) + 'px';
                });
                break;
                
            case 'center-horizontal':
                const centerX = rects.reduce((sum, r) => sum + r.rect.left + r.rect.width / 2, 0) / rects.length;
                rects.forEach(({ element, data }) => {
                    data.x = centerX - data.width / 2;
                    element.style.left = (centerX - data.width / 2) + 'px';
                });
                break;
                
            case 'center-vertical':
                const centerY = rects.reduce((sum, r) => sum + r.rect.top + r.rect.height / 2, 0) / rects.length;
                rects.forEach(({ element, data }) => {
                    data.y = centerY - data.height / 2;
                    element.style.top = (centerY - data.height / 2) + 'px';
                });
                break;
        }
        
        window.canvasCore.autoSave();
    }
    
    // Element distribution tools
    static distributeElements(elements, distribution) {
        if (elements.length < 3) return;
        
        const rects = elements.map(el => ({
            element: el,
            rect: el.getBoundingClientRect(),
            data: window.canvasCore.elements.get(el.dataset.elementId)
        }));
        
        switch (distribution) {
            case 'horizontal':
                rects.sort((a, b) => a.rect.left - b.rect.left);
                const totalWidth = rects[rects.length - 1].rect.right - rects[0].rect.left;
                const elementWidths = rects.reduce((sum, r) => sum + r.rect.width, 0);
                const spacing = (totalWidth - elementWidths) / (rects.length - 1);
                
                let currentX = rects[0].rect.left;
                rects.forEach(({ element, data }, index) => {
                    if (index > 0) {
                        data.x = currentX;
                        element.style.left = currentX + 'px';
                    }
                    currentX += data.width + spacing;
                });
                break;
                
            case 'vertical':
                rects.sort((a, b) => a.rect.top - b.rect.top);
                const totalHeight = rects[rects.length - 1].rect.bottom - rects[0].rect.top;
                const elementHeights = rects.reduce((sum, r) => sum + r.rect.height, 0);
                const vSpacing = (totalHeight - elementHeights) / (rects.length - 1);
                
                let currentY = rects[0].rect.top;
                rects.forEach(({ element, data }, index) => {
                    if (index > 0) {
                        data.y = currentY;
                        element.style.top = currentY + 'px';
                    }
                    currentY += data.height + vSpacing;
                });
                break;
        }
        
        window.canvasCore.autoSave();
    }
}

// Initialize tools when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.canvasTools = new CanvasTools();
});
