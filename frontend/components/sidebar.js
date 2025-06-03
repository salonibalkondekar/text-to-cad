// Sidebar Component - AI Prompt, Examples, and Code Editor

class SidebarComponent {
    constructor(aiGenerator, threeManager, consoleComponent) {
        this.aiGenerator = aiGenerator;
        this.threeManager = threeManager;
        this.consoleComponent = consoleComponent;
    }

    render() {
        const sidebarHTML = `
            <div class="sidebar" id="sidebar-panel">
                <!-- Sidebar Toggle Button -->
                <button class="sidebar-toggle" id="sidebarToggle" title="Toggle Sidebar">
                    <span class="toggle-icon">◀</span>
                </button>
                
                <!-- Horizontal Resize Handle -->
                <div class="resize-handle-horizontal" id="horizontalResizer"></div>
                
                <div class="sidebar-content" id="sidebarContent">
                    <!-- AI Prompt Section -->
                    <div class="ai-prompt-section">
                        <div class="section-title" style="color: white; margin-bottom: 15px;">🤖 AI Model Generator</div>
                        <textarea class="prompt-input" id="promptInput" placeholder="Describe the 3D model you want to create..."></textarea>
                        <button class="generate-button" id="generateModel">
                            <span id="generateText">🚀 Generate 3D Model</span>
                        </button>
                    </div>

                    <!-- Generated CAD Code Section -->
                    <div class="code-section">
                        <div class="section-title">💻 Generated CAD Code</div>
                        <div class="mode-indicator" id="modeIndicator">
                            <span class="mode-badge" id="modeBadge">🔧 CAD Mode</span>
                            <span class="mode-description" id="modeDescription">Using CSG operations (cad.cube, cad.cylinder, etc.)</span>
                        </div>
                        <textarea class="code-editor" id="codeEditor">${projects.basicShapes}</textarea>
                        <button class="build-button" id="buildModel">🔨 BUILD MODEL</button>
                    </div>

                    <!-- Pre-defined Examples - Collapsible -->
                    <div class="predefined-examples-section">
                        <div class="section-title collapsible-header" id="predefinedExamplesToggle">
                            <span class="toggle-arrow">▶</span>
                            <span>📁 Pre-defined Examples</span>
                        </div>
                        <div class="collapsible-content" id="predefinedExamplesContainer" style="display: none;">
                            <div id="projectsContainer"></div>
                        </div>
                    </div>

                    <!-- Collapsible Example Prompts - Moved to bottom -->
                    <div class="example-prompts-section">
                        <div class="section-title collapsible-header" id="examplePromptsToggle">
                            <span class="toggle-arrow">▶</span>
                            <span>💡 Example Prompts</span>
                        </div>
                        <div class="collapsible-content" id="examplePromptsContainer" style="display: none;"></div>
                    </div>
                </div>

                <!-- Console will be rendered here with its own resize handle -->
                <div id="console-container" style="height: 150px;"></div>
            </div>
        `;
        
        document.getElementById('sidebar').innerHTML = sidebarHTML;
        this.renderExamplePrompts();
        this.renderProjects();
        this.attachEventListeners();
        this.initializeResizers();
        
        // Initialize mode indicator
        this.updateModeIndicator();
    }

    renderExamplePrompts() {
        const container = document.getElementById('examplePromptsContainer');
        container.innerHTML = examplePrompts.map(example => 
            `<div class="example-prompt" data-prompt="${example.prompt}">${example.text}</div>`
        ).join('');
    }

    renderProjects() {
        const projectItems = [
            // BadCAD Examples
            { key: 'badcadCross', icon: '➕', name: 'BadCAD: Cross Shape' },
            { key: 'badcadSimpleBox', icon: '📦', name: 'BadCAD: Simple Box' },
            { key: 'badcadCylinder', icon: '🔵', name: 'BadCAD: Cylinder with Hole' },
            { key: 'badcadGear', icon: '⚙️', name: 'BadCAD: Simple Gear' },
            // Three.js CAD Examples
            { key: 'basicShapes', icon: '🔲', name: 'Three.js: Basic Shapes' },
            { key: 'coffeeMug', icon: '☕', name: 'Three.js: Professional Mug' },
            { key: 'professionalGear', icon: '⚙️', name: 'Three.js: Professional Gear' },
            { key: 'mechanicalBearing', icon: '⚙️', name: 'Three.js: Mechanical Bearing' },
            { key: 'simpleTable', icon: '🪑', name: 'Three.js: Simple Table' },
            { key: 'hexBolt', icon: '🔧', name: 'Three.js: Hex Bolt' },
        ];

        const container = document.getElementById('projectsContainer');
        container.innerHTML = projectItems.map(item => 
            `<div class="project-item" data-project="${item.key}">
                <span class="project-icon">${item.icon}</span>
                ${item.name}
            </div>`
        ).join('');
    }

    attachEventListeners() {
        // AI Generate button
        document.getElementById('generateModel').addEventListener('click', () => {
            this.generateFromPrompt();
        });

        // Example prompts toggle
        document.getElementById('examplePromptsToggle').addEventListener('click', () => {
            this.toggleExamplePrompts();
        });
        
        // Predefined examples toggle
        document.getElementById('predefinedExamplesToggle').addEventListener('click', () => {
            this.togglePredefinedExamples();
        });

        // Example prompts
        document.querySelectorAll('.example-prompt').forEach(prompt => {
            prompt.addEventListener('click', () => {
                document.getElementById('promptInput').value = prompt.dataset.prompt;
                this.consoleComponent.log(`📝 Loaded example: "${prompt.dataset.prompt}"`, 'ai');
            });
        });

        // Manual projects
        document.querySelectorAll('.project-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.project-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                const code = projects[item.dataset.project];
                if (code) {
                    document.getElementById('codeEditor').value = code;
                    this.updateModeIndicator();
                    this.buildModel();
                }
            });
        });

        // Build button
        document.getElementById('buildModel').addEventListener('click', () => {
            this.buildModel();
        });

        // Enter key for prompt input
        document.getElementById('promptInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.generateFromPrompt();
            }
        });

        // Code editor change detection for mode indicator
        document.getElementById('codeEditor').addEventListener('input', () => {
            this.updateModeIndicator();
        });

        // Sidebar toggle
        document.getElementById('sidebarToggle').addEventListener('click', () => {
            this.toggleSidebar();
        });
    }

    async generateFromPrompt() {
        const prompt = document.getElementById('promptInput').value.trim();
        if (!prompt) {
            this.consoleComponent.log('⚠️ Please enter a prompt', 'error');
            return;
        }

        const generateBtn = document.getElementById('generateModel');
        const generateText = document.getElementById('generateText');
        
        // Show loading state
        generateBtn.disabled = true;
        generateText.innerHTML = '<span class="loading-spinner"></span> Generating...';

        try {
            this.consoleComponent.log(`🤖 Sending prompt to backend: "${prompt}"`, 'ai');
            
            // Call backend API
            const response = await fetch('http://localhost:8000/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt: prompt })
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.consoleComponent.log(`✅ ${result.message}`, 'success');
                
                // Display the BadCAD code in the editor
                document.getElementById('codeEditor').value = result.badcad_code;
                
                // Load and display the STL model
                await this.loadSTLModel(result.model_id);
                
            } else {
                throw new Error(result.error || 'Unknown backend error');
            }

        } catch (error) {
            this.consoleComponent.log(`❌ Generation Error: ${error.message}`, 'error');
            // Log error when backend is not available
            if (error.message.includes('fetch')) {
                this.consoleComponent.log('❌ Backend unavailable. Please ensure the backend server is running.', 'error');
            }
        } finally {
            // Reset button state
            generateBtn.disabled = false;
            generateText.innerHTML = '🚀 Generate 3D Model';
        }
    }

    async loadSTLModel(modelId) {
        try {
            this.consoleComponent.log('📥 Loading STL model...', 'info');
            
            // Download STL file from backend
            const stlUrl = `http://localhost:8000/api/download/${modelId}`;
            const response = await fetch(stlUrl);
            
            if (!response.ok) {
                throw new Error(`Failed to download STL: ${response.status}`);
            }
            
            const stlData = await response.arrayBuffer();
            
            // Load STL into Three.js scene
            this.threeManager.loadSTL(stlData);
            
            this.consoleComponent.log('✅ STL model loaded successfully!', 'success');
            
        } catch (error) {
            this.consoleComponent.log(`❌ STL Loading Error: ${error.message}`, 'error');
        }
    }

    async buildModel() {
        try {
            const code = document.getElementById('codeEditor').value;
            
            if (!code.trim()) {
                this.consoleComponent.log('⚠️ No code to build', 'error');
                return;
            }

            // Detect code type based on content
            const isBadCAD = this.isBadCADCode(code);
            this.consoleComponent.log(`🔍 Code detection - BadCAD: ${isBadCAD}, CAD: ${/cad\./.test(code)}`, 'info');
            
            if (/cad\./.test(code)) {
                // Three.js CAD mode
                this.consoleComponent.log('🔧 Building CAD model...', 'info');
                const result = this.threeManager.buildModel(code);
                
                if (result) {
                    this.consoleComponent.log('✅ Model built successfully!', 'success');
                }
            } else if (isBadCAD) {
                // BadCAD mode - send to backend
                this.consoleComponent.log('⚙️ Executing BadCAD code...', 'info');
                await this.executeBadCADCode(code);
            } else {
                // Raw Three.js mode
                this.consoleComponent.log('🎮 Running Three.js code...', 'info');
                const result = this.threeManager.buildRawThreeJS(code);
                
                if (result && result.success) {
                    this.consoleComponent.log('✅ Three.js code executed!', 'success');
                }
            }

        } catch (error) {
            this.consoleComponent.log(`❌ Error: ${error.message}`, 'error');
        }
    }

    isBadCADCode(code) {
        // Check for BadCAD-specific functions
        const badcadPatterns = [
            /square\s*\(/,
            /circle\s*\(/,
            /polygon\s*\(/,
            /\.offset\s*\(/,
            /\.extrude/,
            /\.revolve/,
            /extrude_to\s*\(/,
            /from badcad/,
            /import.*badcad/
        ];
        
        const matches = badcadPatterns.filter(pattern => pattern.test(code));
        console.log('BadCAD pattern matches:', matches.map(p => p.toString()));
        
        return badcadPatterns.some(pattern => pattern.test(code));
    }

    async executeBadCADCode(code) {
        try {
            // Call backend to execute BadCAD code
            const response = await fetch('http://localhost:8000/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code: code })
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.consoleComponent.log(`✅ ${result.message}`, 'success');
                
                // Load and display the STL model
                await this.loadSTLModel(result.model_id);
                
            } else {
                throw new Error(result.error || 'Unknown backend error');
            }

        } catch (error) {
            this.consoleComponent.log(`❌ BadCAD Execution Error: ${error.message}`, 'error');
        }
    }

    initializeResizers() {
        this.initializeHorizontalResizer();
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar-panel');
        const toggleIcon = document.querySelector('.toggle-icon');
        const isCollapsed = sidebar.classList.contains('collapsed');
        
        if (isCollapsed) {
            sidebar.classList.remove('collapsed');
            toggleIcon.textContent = '◀';
            sidebar.style.width = sidebar.dataset.lastWidth || '350px';
        } else {
            sidebar.dataset.lastWidth = sidebar.style.width || '350px';
            sidebar.classList.add('collapsed');
            toggleIcon.textContent = '▶';
            sidebar.style.width = '40px';
        }
    }
    
    initializeHorizontalResizer() {
        const resizer = document.getElementById('horizontalResizer');
        const sidebar = document.getElementById('sidebar-panel');
        let isResizing = false;

        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'ew-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const newWidth = e.clientX;
            if (newWidth >= 250 && newWidth <= 600) {
                sidebar.style.width = newWidth + 'px';
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

    updateModeIndicator() {
        const code = document.getElementById('codeEditor').value;
        const modeBadge = document.getElementById('modeBadge');
        const modeDescription = document.getElementById('modeDescription');
        
        if (/cad\./.test(code)) {
            modeBadge.textContent = '🔧 CAD Mode';
            modeBadge.className = 'mode-badge cad-mode';
            modeDescription.textContent = 'Using CSG operations (cad.cube, cad.cylinder, etc.)';
        } else if (this.isBadCADCode(code)) {
            modeBadge.textContent = '⚙️ BadCAD Mode';
            modeBadge.className = 'mode-badge badcad-mode';
            modeDescription.textContent = 'Professional CAD using BadCAD (square, circle, extrude, etc.)';
        } else {
            modeBadge.textContent = '🎮 Three.js Playground';
            modeBadge.className = 'mode-badge threejs-mode';
            modeDescription.textContent = 'Full Three.js access (THREE, scene, camera, renderer, controls)';
        }
    }
    
    togglePredefinedExamples() {
        const container = document.getElementById('predefinedExamplesContainer');
        const header = document.getElementById('predefinedExamplesToggle');
        const arrow = header.querySelector('.toggle-arrow');
        
        if (container.style.display === 'none') {
            container.style.display = 'block';
            arrow.textContent = '▼';
        } else {
            container.style.display = 'none';
            arrow.textContent = '▶';
        }
    }
    
    toggleExamplePrompts() {
        const container = document.getElementById('examplePromptsContainer');
        const header = document.getElementById('examplePromptsToggle');
        const arrow = header.querySelector('.toggle-arrow');
        
        if (container.style.display === 'none') {
            container.style.display = 'block';
            arrow.textContent = '▼';
        } else {
            container.style.display = 'none';
            arrow.textContent = '▶';
        }
    }
} 