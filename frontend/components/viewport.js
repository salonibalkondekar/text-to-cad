// Viewport Component - 3D Scene Display

class ViewportComponent {
    constructor(threeManager) {
        this.threeManager = threeManager;
    }

    render() {
        const viewportHTML = `
            <div class="viewport" id="viewport">
                <div class="animation-controls">
                    <span>Animation: <strong id="animStatus">OFF</strong></span>
                </div>
            </div>
        `;
        
        document.getElementById('main-content').innerHTML = viewportHTML;
        
        // Initialize Three.js scene in the viewport
        setTimeout(() => {
            this.threeManager.init('viewport');
            this.setupResizeHandler();
        }, 100);
    }

    setupResizeHandler() {
        window.addEventListener('resize', () => {
            this.threeManager.resizeRenderer();
        });
    }
} 