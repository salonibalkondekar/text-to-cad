// Viewport Component - 3D Scene Display

class ViewportComponent {
    constructor(threeManager) {
        this.threeManager = threeManager;
        this.measurementMode = false; // Measurement mode state
    }

    render() {
        const viewportHTML = `
            <div class="viewport" id="viewport">
                <!-- 3D Software Style Controls -->
                <div class="viewport-overlay">
                    <!-- Top toolbar -->
                    <div class="viewport-toolbar">
                        <div class="view-controls">
                            <button class="view-btn" id="frontView" title="Front View">Front</button>
                            <button class="view-btn" id="rightView" title="Right View">Right</button>
                            <button class="view-btn" id="topView" title="Top View">Top</button>
                            <button class="view-btn" id="perspectiveView" title="Perspective View">Persp</button>
                        </div>
                        <div class="status-indicators">
                            <span class="status-item" id="renderMode">🎨 Solid</span>
                            <span class="status-item" id="projectionMode">📐 Perspective</span>
                        </div>
                        <div class="display-controls">
                            <button class="display-btn active" id="gridToggle" title="Toggle Grid">Grid</button>
                            <button class="display-btn active" id="axesToggle" title="Toggle Axes">Axes</button>
                            <button class="display-btn" id="polarGridToggle" title="Toggle Polar Grid">Polar</button>
                            <button class="display-btn" id="xyGridToggle" title="Toggle XY Plane">XY</button>
                            <button class="display-btn" id="yzGridToggle" title="Toggle YZ Plane">YZ</button>
                            <button class="display-btn" id="measureToggle" title="Measurement Tool">📏 Measure</button>
                        </div>
                    </div>
                    
                    <!-- Bottom info panel -->
                    <div class="viewport-info">
                        <div class="coordinates-display">
                            <span id="mouseCoords">X: 0.00, Y: 0.00, Z: 0.00</span>
                        </div>
                        <div class="view-info">
                            <span id="viewMode">Perspective</span> | 
                            <span id="gridInfo">Grid: ON</span> | 
                            <span id="scaleInfo">Scale: 1:1</span> |
                            <span id="animStatus">Animation: OFF</span>
                        </div>
                    </div>
                    
                    <!-- Scale Reference (like CAD software) -->
                    <div class="scale-reference">
                        <div class="scale-line"></div>
                        <span class="scale-text" id="scaleReference">1 unit</span>
                    </div>
                    
                    <!-- Navigation cube (3D software style) -->
                    <div class="navigation-cube">
                        <div class="cube-face front" data-view="front">F</div>
                        <div class="cube-face back" data-view="back">B</div>
                        <div class="cube-face right" data-view="right">R</div>
                        <div class="cube-face left" data-view="left">L</div>
                        <div class="cube-face top" data-view="top">T</div>
                        <div class="cube-face bottom" data-view="bottom">Bot</div>
                    </div>
                    
                    <!-- Measurement Tool Overlay -->
                    <div class="measurement-overlay" id="measurementOverlay" style="display: none;">
                        <div class="measurement-instruction">
                            Click two points to measure distance
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('main-content').innerHTML = viewportHTML;
        
        // Initialize Three.js scene in the viewport
        setTimeout(() => {
            this.threeManager.init('viewport');
            this.setupResizeHandler();
            this.setupViewportControls();
        }, 100);
    }

    setupResizeHandler() {
        window.addEventListener('resize', () => {
            this.threeManager.resizeRenderer();
        });
    }

    setupViewportControls() {
        // Grid and display toggles
        document.getElementById('gridToggle')?.addEventListener('click', (e) => {
            const gridOn = this.threeManager.toggleGrid();
            e.target.classList.toggle('active', gridOn);
            document.getElementById('gridInfo').textContent = `Grid: ${gridOn ? 'ON' : 'OFF'}`;
        });

        document.getElementById('axesToggle')?.addEventListener('click', (e) => {
            const axesOn = this.threeManager.toggleAxes();
            e.target.classList.toggle('active', axesOn);
        });

        document.getElementById('polarGridToggle')?.addEventListener('click', (e) => {
            const polarOn = this.threeManager.togglePolarGrid();
            e.target.classList.toggle('active', polarOn);
        });

        document.getElementById('xyGridToggle')?.addEventListener('click', (e) => {
            const xyOn = this.threeManager.toggleXYGrid();
            e.target.classList.toggle('active', xyOn);
        });

        document.getElementById('yzGridToggle')?.addEventListener('click', (e) => {
            const yzOn = this.threeManager.toggleYZGrid();
            e.target.classList.toggle('active', yzOn);
        });

        // Measurement tool
        document.getElementById('measureToggle')?.addEventListener('click', (e) => {
            const measureOn = this.toggleMeasurementMode();
            e.target.classList.toggle('active', measureOn);
        });

        // View controls
        document.getElementById('frontView')?.addEventListener('click', () => {
            this.setOrthographicView('front');
        });

        document.getElementById('rightView')?.addEventListener('click', () => {
            this.setOrthographicView('right');
        });

        document.getElementById('topView')?.addEventListener('click', () => {
            this.setOrthographicView('top');
        });

        document.getElementById('perspectiveView')?.addEventListener('click', () => {
            this.threeManager.resetView();
            document.getElementById('viewMode').textContent = 'Perspective';
        });

        // Navigation cube
        document.querySelectorAll('.cube-face').forEach(face => {
            face.addEventListener('click', () => {
                const view = face.getAttribute('data-view');
                this.setOrthographicView(view);
            });
        });

        // Mouse coordinate tracking
        const viewport = document.getElementById('viewport');
        if (viewport) {
            viewport.addEventListener('mousemove', (e) => {
                this.updateMouseCoordinates(e);
            });
        }
    }

    setOrthographicView(view) {
        const camera = this.threeManager.getCamera();
        const distance = 10;
        
        switch(view) {
            case 'front':
                camera.position.set(0, 0, distance);
                camera.lookAt(0, 0, 0);
                document.getElementById('viewMode').textContent = 'Front View';
                break;
            case 'back':
                camera.position.set(0, 0, -distance);
                camera.lookAt(0, 0, 0);
                document.getElementById('viewMode').textContent = 'Back View';
                break;
            case 'right':
                camera.position.set(distance, 0, 0);
                camera.lookAt(0, 0, 0);
                document.getElementById('viewMode').textContent = 'Right View';
                break;
            case 'left':
                camera.position.set(-distance, 0, 0);
                camera.lookAt(0, 0, 0);
                document.getElementById('viewMode').textContent = 'Left View';
                break;
            case 'top':
                camera.position.set(0, distance, 0);
                camera.lookAt(0, 0, 0);
                document.getElementById('viewMode').textContent = 'Top View';
                break;
            case 'bottom':
                camera.position.set(0, -distance, 0);
                camera.lookAt(0, 0, 0);
                document.getElementById('viewMode').textContent = 'Bottom View';
                break;
        }
    }

    updateMouseCoordinates(event) {
        const rect = event.target.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        // Convert to world coordinates (simplified)
        const worldX = x * 10;
        const worldY = y * 10;
        const worldZ = 0; // Assuming ground plane
        
        document.getElementById('mouseCoords').textContent = 
            `X: ${worldX.toFixed(2)}, Y: ${worldY.toFixed(2)}, Z: ${worldZ.toFixed(2)}`;
    }

    toggleMeasurementMode() {
        this.measurementMode = !this.measurementMode;
        const overlay = document.getElementById('measurementOverlay');
        if (overlay) {
            overlay.style.display = this.measurementMode ? 'block' : 'none';
        }
        return this.measurementMode;
    }

}