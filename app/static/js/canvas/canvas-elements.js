// Canvas Elements Management
class CanvasElements {
    constructor() {
        this.resizeHandles = [];
        this.isResizing = false;
        this.resizeStart = { x: 0, y: 0, width: 0, height: 0 };
        this.currentResizeElement = null;
        
        this.init();
    }
    
    init() {
        this.setupResizeHandles();
        this.setupElementInteractions();
    }
    
    setupResizeHandles() {
        // Create resize handles
        const handles = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
        
        handles.forEach(direction => {
            const handle = document.createElement('div');
            handle.className = `resize-handle resize-${direction}`;
            handle.dataset.direction = direction;
            handle.style.display = 'none';
            document.body.appendChild(handle);
            
            this.resizeHandles.push(handle);
            
            handle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                this.startResize(e, direction);
            });
        });
        
        // Hide handles when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!e.target.classList.contains('canvas-element') && 
                !e.target.classList.contains('resize-handle')) {
                this.hideResizeHandles();
            }
        });
    }
    
    setupElementInteractions() {
        // Double-click to edit text elements
        document.addEventListener('dblclick', (e) => {
            if (e.target.classList.contains('text-element')) {
                this.editTextElement(e.target);
            }
        });
        
        // Element selection with resize handles
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('canvas-element')) {
                this.showResizeHandles(e.target);
            }
        });
    }
    
    showResizeHandles(element) {
        this.hideResizeHandles();
        this.currentResizeElement = element;
        
        const rect = element.getBoundingClientRect();
        const handleSize = 8;
        
        // Position handles around the element
        const positions = {
            nw: { left: rect.left - handleSize/2, top: rect.top - handleSize/2, cursor: 'nw-resize' },
            n:  { left: rect.left + rect.width/2 - handleSize/2, top: rect.top - handleSize/2, cursor: 'n-resize' },
            ne: { left: rect.right - handleSize/2, top: rect.top - handleSize/2, cursor: 'ne-resize' },
            e:  { left: rect.right - handleSize/2, top: rect.top + rect.height/2 - handleSize/2, cursor: 'e-resize' },
            se: { left: rect.right - handleSize/2, top: rect.bottom - handleSize/2, cursor: 'se-resize' },
            s:  { left: rect.left + rect.width/2 - handleSize/2, top: rect.bottom - handleSize/2, cursor: 's-resize' },
            sw: { left: rect.left - handleSize/2, top: rect.bottom - handleSize/2, cursor: 'sw-resize' },
            w:  { left: rect.left - handleSize/2, top: rect.top + rect.height/2 - handleSize/2, cursor: 'w-resize' }
        };
        
        this.resizeHandles.forEach(handle => {
            const direction = handle.dataset.direction;
            const pos = positions[direction];
            
            handle.style.left = pos.left + 'px';
            handle.style.top = pos.top + 'px';
            handle.style.cursor = pos.cursor;
            handle.style.display = 'block';
        });
    }
    
    hideResizeHandles() {
        this.resizeHandles.forEach(handle => {
            handle.style.display = 'none';
        });
        this.currentResizeElement = null;
    }
    
    startResize(e, direction) {
        if (!this.currentResizeElement) return;
        
        this.isResizing = true;
        const element = this.currentResizeElement;
        const elementData = window.canvasCore.elements.get(element.dataset.elementId);
        
        this.resizeStart = {
            x: e.clientX,
            y: e.clientY,
            width: elementData.width,
            height: elementData.height,
            left: elementData.x,
            top: elementData.y
        };
        
        document.addEventListener('mousemove', (e) => this.handleResize(e, direction));
        document.addEventListener('mouseup', () => this.endResize());
        
        e.preventDefault();
    }
    
    handleResize(e, direction) {
        if (!this.isResizing || !this.currentResizeElement) return;
        
        const element = this.currentResizeElement;
        const elementData = window.canvasCore.elements.get(element.dataset.elementId);
        
        const dx = e.clientX - this.resizeStart.x;
        const dy = e.clientY - this.resizeStart.y;
        
        let newWidth = this.resizeStart.width;
        let newHeight = this.resizeStart.height;
        let newLeft = this.resizeStart.left;
        let newTop = this.resizeStart.top;
        
        // Calculate new dimensions based on resize direction
        switch (direction) {
            case 'nw':
                newWidth = this.resizeStart.width - dx;
                newHeight = this.resizeStart.height - dy;
                newLeft = this.resizeStart.left + dx;
                newTop = this.resizeStart.top + dy;
                break;
            case 'n':
                newHeight = this.resizeStart.height - dy;
                newTop = this.resizeStart.top + dy;
                break;
            case 'ne':
                newWidth = this.resizeStart.width + dx;
                newHeight = this.resizeStart.height - dy;
                newTop = this.resizeStart.top + dy;
                break;
            case 'e':
                newWidth = this.resizeStart.width + dx;
                break;
            case 'se':
                newWidth = this.resizeStart.width + dx;
                newHeight = this.resizeStart.height + dy;
                break;
            case 's':
                newHeight = this.resizeStart.height + dy;
                break;
            case 'sw':
                newWidth = this.resizeStart.width - dx;
                newHeight = this.resizeStart.height + dy;
                newLeft = this.resizeStart.left + dx;
                break;
            case 'w':
                newWidth = this.resizeStart.width - dx;
                newLeft = this.resizeStart.left + dx;
                break;
        }
        
        // Apply minimum size constraints
        const minSize = 20;
        newWidth = Math.max(minSize, newWidth);
        newHeight = Math.max(minSize, newHeight);
        
        // Update element
        elementData.width = newWidth;
        elementData.height = newHeight;
        elementData.x = newLeft;
        elementData.y = newTop;
        
        element.style.width = newWidth + 'px';
        element.style.height = newHeight + 'px';
        element.style.left = newLeft + 'px';
        element.style.top = newTop + 'px';
        
        // Update resize handles position
        this.showResizeHandles(element);
    }
    
    endResize() {
        if (this.isResizing) {
            this.isResizing = false;
            document.removeEventListener('mousemove', this.handleResize);
            document.removeEventListener('mouseup', this.endResize);
            
            // Save changes
            window.canvasCore.autoSave();
            window.canvasCore.saveToHistory();
        }
    }
    
    editTextElement(textElement) {
        textElement.focus();
        textElement.select();
        
        // Add editing class for styling
        textElement.classList.add('editing');
        
        const finishEditing = () => {
            textElement.classList.remove('editing');
            textElement.blur();
            window.canvasCore.autoSave();
        };
        
        // Finish editing on Enter or blur
        textElement.addEventListener('blur', finishEditing, { once: true });
        textElement.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                finishEditing();
            }
        }, { once: true });
    }
    
    // Element grouping functionality
    groupElements(elements) {
        if (elements.length < 2) return;
        
        const groupId = 'group_' + Date.now();
        const groupData = {
            id: groupId,
            type: 'group',
            elements: elements.map(el => el.dataset.elementId),
            x: Math.min(...elements.map(el => window.canvasCore.elements.get(el.dataset.elementId).x)),
            y: Math.min(...elements.map(el => window.canvasCore.elements.get(el.dataset.elementId).y)),
            width: 0,
            height: 0
        };
        
        // Calculate group bounds
        const bounds = this.calculateGroupBounds(elements);
        groupData.width = bounds.width;
        groupData.height = bounds.height;
        
        // Create group element
        const groupElement = document.createElement('div');
        groupElement.className = 'canvas-element canvas-group';
        groupElement.dataset.elementId = groupId;
        groupElement.style.left = groupData.x + 'px';
        groupElement.style.top = groupData.y + 'px';
        groupElement.style.width = groupData.width + 'px';
        groupElement.style.height = groupData.height + 'px';
        groupElement.style.border = '2px dashed #007bff';
        groupElement.style.background = 'rgba(0, 123, 255, 0.1)';
        
        // Add elements to group
        elements.forEach(element => {
            groupElement.appendChild(element);
            element.style.position = 'absolute';
            // Adjust positions relative to group
            const elementData = window.canvasCore.elements.get(element.dataset.elementId);
            element.style.left = (elementData.x - groupData.x) + 'px';
            element.style.top = (elementData.y - groupData.y) + 'px';
        });
        
        document.getElementById('canvas-elements').appendChild(groupElement);
        window.canvasCore.elements.set(groupId, groupData);
        
        window.canvasCore.autoSave();
        window.canvasCore.saveToHistory();
    }
    
    ungroupElements(groupElement) {
        const groupData = window.canvasCore.elements.get(groupElement.dataset.elementId);
        if (!groupData || groupData.type !== 'group') return;
        
        const elementsContainer = document.getElementById('canvas-elements');
        
        // Move elements back to main container
        Array.from(groupElement.children).forEach(element => {
            const elementData = window.canvasCore.elements.get(element.dataset.elementId);
            
            // Adjust positions back to absolute
            elementData.x = groupData.x + parseInt(element.style.left);
            elementData.y = groupData.y + parseInt(element.style.top);
            
            element.style.left = elementData.x + 'px';
            element.style.top = elementData.y + 'px';
            element.style.position = 'absolute';
            
            elementsContainer.appendChild(element);
        });
        
        // Remove group
        groupElement.remove();
        window.canvasCore.elements.delete(groupElement.dataset.elementId);
        
        window.canvasCore.autoSave();
        window.canvasCore.saveToHistory();
    }
    
    calculateGroupBounds(elements) {
        const bounds = {
            left: Infinity,
            top: Infinity,
            right: -Infinity,
            bottom: -Infinity
        };
        
        elements.forEach(element => {
            const data = window.canvasCore.elements.get(element.dataset.elementId);
            bounds.left = Math.min(bounds.left, data.x);
            bounds.top = Math.min(bounds.top, data.y);
            bounds.right = Math.max(bounds.right, data.x + data.width);
            bounds.bottom = Math.max(bounds.bottom, data.y + data.height);
        });
        
        return {
            x: bounds.left,
            y: bounds.top,
            width: bounds.right - bounds.left,
            height: bounds.bottom - bounds.top
        };
    }
    
    // Element layering
    bringToFront(element) {
        const elementData = window.canvasCore.elements.get(element.dataset.elementId);
        const maxZ = Math.max(...Array.from(window.canvasCore.elements.values()).map(e => e.zIndex || 1));
        elementData.zIndex = maxZ + 1;
        element.style.zIndex = elementData.zIndex;
        window.canvasCore.autoSave();
    }
    
    sendToBack(element) {
        const elementData = window.canvasCore.elements.get(element.dataset.elementId);
        const minZ = Math.min(...Array.from(window.canvasCore.elements.values()).map(e => e.zIndex || 1));
        elementData.zIndex = Math.max(1, minZ - 1);
        element.style.zIndex = elementData.zIndex;
        window.canvasCore.autoSave();
    }
    
    // Element locking
    lockElement(element) {
        element.classList.add('locked');
        element.style.pointerEvents = 'none';
        const elementData = window.canvasCore.elements.get(element.dataset.elementId);
        elementData.locked = true;
        window.canvasCore.autoSave();
    }
    
    unlockElement(element) {
        element.classList.remove('locked');
        element.style.pointerEvents = 'auto';
        const elementData = window.canvasCore.elements.get(element.dataset.elementId);
        elementData.locked = false;
        window.canvasCore.autoSave();
    }
}

// Add CSS for resize handles
const style = document.createElement('style');
style.textContent = `
    .resize-handle {
        position: fixed;
        width: 8px;
        height: 8px;
        background: #007bff;
        border: 1px solid white;
        border-radius: 50%;
        z-index: 1000;
        pointer-events: auto;
    }
    
    .resize-handle:hover {
        background: #0056b3;
        transform: scale(1.2);
    }
    
    .canvas-element.locked {
        opacity: 0.7;
        border-color: #6c757d !important;
    }
    
    .canvas-element.locked::after {
        content: '🔒';
        position: absolute;
        top: -20px;
        right: -10px;
        font-size: 12px;
        background: white;
        padding: 2px 4px;
        border-radius: 3px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    .text-element.editing {
        background: rgba(0, 123, 255, 0.1) !important;
        border: 1px solid #007bff !important;
    }
    
    .canvas-group {
        pointer-events: none;
    }
    
    .canvas-group > .canvas-element {
        pointer-events: auto;
    }
    
    .drag-over {
        background: rgba(0, 123, 255, 0.1) !important;
    }
`;
document.head.appendChild(style);

// Initialize elements management when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.canvasElements = new CanvasElements();
});
