// Console Component - System Messages and Logs

class ConsoleComponent {
    constructor() {
        this.outputElement = null;
    }

    render() {
        const consoleHTML = `
            <div class="console-section">
                <div class="console-resize-handle" id="consoleResizeHandle"></div>
                <div class="console-header">🤖 AI Console</div>
                <div class="console-output" id="consoleOutput">AI CAD system ready. Describe your 3D model to get started...</div>
            </div>
        `;
        
        document.getElementById('console-container').innerHTML = consoleHTML;
        this.outputElement = document.getElementById('consoleOutput');
        this.initializeConsoleResizer();
    }

    initializeConsoleResizer() {
        const resizeHandle = document.getElementById('consoleResizeHandle');
        const consoleContainer = document.getElementById('console-container');
        const sidebarContent = document.getElementById('sidebarContent');
        let isResizing = false;
        let startY = 0;
        let startHeight = 0;

        resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startY = e.clientY;
            startHeight = parseInt(window.getComputedStyle(consoleContainer).height, 10);
            document.body.style.cursor = 'ns-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            const deltaY = startY - e.clientY; // Inverted because we're resizing from top
            const newHeight = startHeight + deltaY;
            
            const minHeight = 80;
            const maxHeight = window.innerHeight - 200; // Leave space for sidebar content
            
            if (newHeight >= minHeight && newHeight <= maxHeight) {
                consoleContainer.style.height = newHeight + 'px';
                // Adjust sidebar content height accordingly
                const sidebarHeight = window.innerHeight - 60; // Account for header
                const remainingHeight = sidebarHeight - newHeight;
                sidebarContent.style.height = remainingHeight + 'px';
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    log(message, type = 'info') {
        if (!this.outputElement) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const className = type === 'error' ? 'console-error' : 
                         type === 'success' ? 'console-success' : 
                         type === 'ai' ? 'console-ai' : '';
        
        this.outputElement.innerHTML += `<div class="${className}">[${timestamp}] ${message}</div>`;
        this.outputElement.scrollTop = this.outputElement.scrollHeight;
    }

    clear() {
        if (this.outputElement) {
            this.outputElement.innerHTML = '';
        }
    }

    info(message) {
        this.log(message, 'info');
    }

    success(message) {
        this.log(message, 'success');
    }

    error(message) {
        this.log(message, 'error');
    }

    ai(message) {
        this.log(message, 'ai');
    }
} 