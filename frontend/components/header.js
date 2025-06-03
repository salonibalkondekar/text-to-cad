// Header Component - Top Navigation Bar

class HeaderComponent {
    constructor(threeManager) {
        this.threeManager = threeManager;
    }

    render() {
        const headerHTML = `
            <div class="header">
                <div class="logo">🤖 AI CAD.js</div>
                <div class="tagline">AI-Powered 3D Model Generation from Text</div>
                <div class="toolbar">
                    <button id="resetView">🔄 Reset View</button>
                    <button id="wireframe">📐 Wireframe</button>
                    <button id="animate">🎬 Animate</button>
                    <button id="axes">📍 Axes</button>
                </div>
            </div>
        `;
        
        document.getElementById('header').innerHTML = headerHTML;
        this.attachEventListeners();
    }

    attachEventListeners() {
        // Reset View button
        document.getElementById('resetView').addEventListener('click', () => {
            this.threeManager.resetView();
            console.log('🔄 View reset');
        });

        // Wireframe toggle
        document.getElementById('wireframe').addEventListener('click', (e) => {
            const wireframeMode = this.threeManager.toggleWireframe();
            e.target.classList.toggle('active', wireframeMode);
            console.log(`📐 Wireframe: ${wireframeMode ? 'ON' : 'OFF'}`);
        });

        // Animation toggle
        document.getElementById('animate').addEventListener('click', (e) => {
            const animationEnabled = this.threeManager.toggleAnimation();
            e.target.classList.toggle('active', animationEnabled);
            
            // Update animation status in viewport
            const animStatus = document.getElementById('animStatus');
            if (animStatus) {
                animStatus.textContent = animationEnabled ? 'ON' : 'OFF';
            }
            
            console.log(`🎬 Animation: ${animationEnabled ? 'ON' : 'OFF'}`);
        });

        // Axes toggle
        document.getElementById('axes').addEventListener('click', (e) => {
            const axesVisible = this.threeManager.toggleAxes();
            e.target.classList.toggle('active', axesVisible);
            console.log(`📍 Axes: ${axesVisible ? 'ON' : 'OFF'}`);
        });
    }
}