// Main Application - Coordinates all components

class AICADApp {
    constructor() {
        this.threeManager = new ThreeJSManager();
        this.aiGenerator = new AICADGenerator();
        this.consoleComponent = new ConsoleComponent();
        this.headerComponent = new HeaderComponent(this.threeManager);
        this.viewportComponent = new ViewportComponent(this.threeManager);
        this.sidebarComponent = new SidebarComponent(
            this.aiGenerator, 
            this.threeManager, 
            this.consoleComponent
        );
    }

    async init() {
        try {
            // Render all components
            this.headerComponent.render();
            this.viewportComponent.render();
            this.sidebarComponent.render();
            this.consoleComponent.render();

            // Wait for Three.js to initialize
            await this.waitForThreeJS();

            // Build initial model
            setTimeout(() => {
                this.sidebarComponent.buildModel();
            }, 500);

            this.consoleComponent.success('🚀 AI CAD system initialized successfully');
            
        } catch (error) {
            this.consoleComponent.error(`❌ Initialization error: ${error.message}`);
            console.error('App initialization error:', error);
        }
    }

    waitForThreeJS() {
        return new Promise((resolve) => {
            const checkThreeJS = () => {
                if (this.threeManager.getScene()) {
                    resolve();
                } else {
                    setTimeout(checkThreeJS, 100);
                }
            };
            checkThreeJS();
        });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new AICADApp();
    app.init();
}); 