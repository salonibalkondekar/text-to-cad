// Sidebar Component - AI Prompt, Examples, and Code Editor

class SidebarComponent {
    constructor(aiGenerator, threeManager, consoleComponent) {
        this.aiGenerator = aiGenerator;
        this.threeManager = threeManager;
        this.consoleComponent = consoleComponent;
        this.authState = null;
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
                        <div class="auth-notice" id="authNotice" style="display: none;">
                            <div class="notice-content">
                                <span class="notice-icon">📧</span>
                                <span class="notice-text">Enter your email to generate AI models</span>
                            </div>
                        </div>
                        <div class="usage-notice" id="usageNotice" style="display: none;">
                            <div class="notice-content">
                                <span class="notice-icon">⚠️</span>
                                <span class="notice-text">Model generation limit reached (10/10)</span>
                            </div>
                        </div>
                        <textarea class="prompt-input" id="promptInput" placeholder="Describe the 3D model you want to create..."></textarea>
                        <button class="generate-button" id="generateModel">
                            <span id="generateText">🚀 Generate 3D Model</span>
                        </button>
                    </div>

                    <!-- Generated CAD Code Section -->
                    <div class="code-section">
                        <div class="section-title">💻 Generated CAD Code</div>
                        <textarea class="code-editor" id="codeEditor">${projects.basicShapes}</textarea>
                        <div class="button-row">
                            <button class="build-button" id="buildModel">🔨 BUILD MODEL</button>
                            <button class="download-button" id="downloadModelSTL">💾 Download STL</button>
                        </div>
                    </div>
                </div>

                <!-- Console will be rendered here with its own resize handle -->
                <div id="console-container" style="height: 150px;"></div>
            </div>
        `;
        
        document.getElementById('sidebar').innerHTML = sidebarHTML;
        this.attachEventListeners();
        this.initializeResizers();
        this.setupAuthListener();
    }

    attachEventListeners() {
        // AI Generate button
        document.getElementById('generateModel').addEventListener('click', () => {
            this.generateFromPrompt();
        });

        // Build button
        document.getElementById('buildModel').addEventListener('click', () => {
            this.buildModel();
        });

        // Download STL button
        document.getElementById('downloadModelSTL').addEventListener('click', () => {
            this.consoleComponent.log('💾 STL download only available for BadCAD models generated via backend', 'info');
        });

        // Enter key for prompt input
        document.getElementById('promptInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.generateFromPrompt();
            }
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

        // Check authentication
        if (!this.authState || !this.authState.isSignedIn) {
            this.consoleComponent.log('📧 Please enter your email to generate models', 'error');
            return;
        }

        // Check usage limits
        if (!this.authState.canGenerate) {
            this.consoleComponent.log('⚠️ Model generation limit reached (10/10). Please contact support for more models.', 'error');
            return;
        }

        const generateBtn = document.getElementById('generateModel');
        const generateText = document.getElementById('generateText');
        
        // Show loading state
        generateBtn.disabled = true;
        generateText.innerHTML = '<span class="loading-spinner"></span> Generating...';

        try {
            this.consoleComponent.log(`🤖 Sending prompt to backend: "${prompt}"`, 'ai');
            
            // Include user ID in the request
            const response = await fetch(`${window.API_URL || 'http://localhost:8000'}/api/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    prompt: prompt,
                    user_id: this.authState.user?.id
                })
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

                // Update auth state (user count should be incremented)
                if (window.authService) {
                    await window.authService.loadUserData();
                }
                
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
            const stlUrl = `${window.API_URL || 'http://localhost:8000'}/api/download/${modelId}`;
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
                this.consoleComponent.log('⚠️ Code not recognized. Please use CAD functions (cad.cube, etc.) or BadCAD syntax', 'error');
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
            // Check authentication for BadCAD execution
            if (!this.authState || !this.authState.isSignedIn) {
                this.consoleComponent.log('🔐 Please sign in with Google to execute BadCAD code', 'error');
                return;
            }

            // Check usage limits
            if (!this.authState.canGenerate) {
                this.consoleComponent.log('⚠️ Model generation limit reached (10/10). Please contact support for more models.', 'error');
                return;
            }

            // Call backend to execute BadCAD code
            const response = await fetch(`${window.API_URL || 'http://localhost:8000'}/api/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    code: code,
                    user_id: this.authState.user?.id
                })
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.consoleComponent.log(`✅ ${result.message}`, 'success');
                
                // Load and display the STL model
                await this.loadSTLModel(result.model_id);

                // Update auth state (user count should be incremented)
                if (window.authService) {
                    await window.authService.loadUserData();
                }
                
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

    setupAuthListener() {
        // Wait for auth service to be available
        const waitForAuth = () => {
            if (window.authService) {
                window.authService.setAuthStateListener((authState) => {
                    this.authState = authState;
                    this.updateAuthUI(authState);
                });
            } else {
                setTimeout(waitForAuth, 100);
            }
        };
        waitForAuth();
    }

    updateAuthUI(authState) {
        const authNotice = document.getElementById('authNotice');
        const usageNotice = document.getElementById('usageNotice');
        const generateBtn = document.getElementById('generateModel');
        const promptInput = document.getElementById('promptInput');

        if (!authState.isSignedIn) {
            // Show auth notice, hide usage notice
            authNotice.style.display = 'block';
            usageNotice.style.display = 'none';
            generateBtn.disabled = true;
            promptInput.disabled = true;
            promptInput.placeholder = 'Enter your email to generate AI models...';
        } else if (!authState.canGenerate) {
            // Show usage limit notice
            authNotice.style.display = 'none';
            usageNotice.style.display = 'block';
            generateBtn.disabled = true;
            promptInput.disabled = true;
            promptInput.placeholder = 'Model generation limit reached...';
        } else {
            // User can generate models
            authNotice.style.display = 'none';
            usageNotice.style.display = 'none';
            generateBtn.disabled = false;
            promptInput.disabled = false;
            promptInput.placeholder = `Describe the 3D model you want to create... (${authState.remaining} more generations left :)`;
        }
    }
}