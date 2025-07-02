// Sidebar Component - AI Prompt, Examples, and Code Editor

class SidebarComponent {
    constructor(aiGenerator, threeManager, consoleComponent) {
        this.aiGenerator = aiGenerator;
        this.threeManager = threeManager;
        this.consoleComponent = consoleComponent;
        this.authState = null;
        this.currentModelId = null; // Track the current model ID for downloads
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
                        <div class="section-title">AI Model Generator</div>
                        
                        <!-- Prominent Auth Banner -->
                        <div class="auth-notice-banner" id="authBanner" style="display: none;">
                            <div class="auth-notice-banner-icon">✉️</div>
                            <div class="auth-notice-banner-text">
                                <strong>Email Required!</strong>
                            </div>
                            <div class="auth-notice-banner-action">Sign In</div>
                        </div>
                        
                        <!-- Usage Notice -->
                        <div class="usage-notice" id="usageNotice" style="display: none;">
                            <div class="notice-content">
                                <span class="notice-icon">⚠️</span>
                                <span class="notice-text">Model generation limit reached (10/10)</span>
                            </div>
                        </div>
                        
                        <!-- Model Count Display -->
                        <div class="model-count" id="modelCount" style="display: none;">
                            <span class="model-count-icon">📊</span>
                            <span class="model-count-text">Models: <strong id="modelCountValue">0/10</strong></span>
                        </div>
                        
                        <textarea class="prompt-input" id="promptInput" placeholder="Describe the 3D model you want to create..."></textarea>
                        <button class="generate-button" id="generateModel">
                            <span id="generateText">🚀 Generate 3D Model</span>
                            <span class="email-required-badge" id="emailBadge" style="display: none;">✉️</span>
                        </button>
                    </div>

                    <!-- Generated CAD Code Section -->
                    <div class="code-section">
                        <div class="section-title">Generated CAD Code</div>
                        <textarea class="code-editor" id="codeEditor">${projects.basicShapes}</textarea>
                        <div class="button-row">
                            <button class="build-button" id="buildModel">🔨 BUILD MODEL</button>
                            <button class="download-button" id="downloadModelSTL">💾 Download STL</button>
                        </div>
                    </div>
                </div>

                <!-- Console will be rendered here with its own resize handle -->
                <div id="console-container"></div>
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
            this.downloadSTL();
        });

        // Enter key for prompt input (Enter = generate, Shift+Enter = new line)
        document.getElementById('promptInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.generateFromPrompt();
            }
            // Shift+Enter allows normal new line behavior
        });

        // Sidebar toggle
        document.getElementById('sidebarToggle').addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Auth banner click
        const authBanner = document.getElementById('authBanner');
        if (authBanner) {
            authBanner.addEventListener('click', async () => {
                if (window.authService) {
                    const success = await window.authService.signIn();
                    if (success) {
                        this.updateAuthUI(window.authService.getAuthState());
                    }
                }
            });
        }
    }

    async generateFromPrompt() {
        const prompt = document.getElementById('promptInput').value.trim();
        if (!prompt) {
            this.consoleComponent.log('⚠️ Please enter a prompt', 'error');
            return;
        }

        // Check authentication
        if (!this.authState || !this.authState.isSignedIn) {
            this.consoleComponent.log('📧 Please enter your email to generate models', 'info');
            // Trigger sign in
            if (window.authService) {
                const success = await window.authService.signIn();
                if (!success) {
                    return;
                }
                // Update auth state after sign in
                this.authState = window.authService.getAuthState();
            }
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

        // Reset current model ID for new generation
        this.currentModelId = null;

        try {
            this.consoleComponent.log(`🤖 Sending prompt to backend: "${prompt}"`, 'ai');
            
            // Include user ID in the request with session credentials
            const response = await fetch(`${window.API_URL || 'http://localhost:8000'}/api/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ 
                    prompt: prompt,
                    user_id: this.authState.user?.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`Backend error: ${response.status} - ${errorData.detail || 'Unknown error'}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.consoleComponent.log(`✅ ${result.message}`, 'success');
                
                // Store the model ID for download functionality
                this.currentModelId = result.model_id;
                
                // Display the BadCAD code in the editor
                document.getElementById('codeEditor').value = result.badcad_code;
                
                // Load and display the STL model
                await this.loadSTLModel(result.model_id);

                // Update auth state (user count should be incremented)
                if (window.authService) {
                    await window.authService.loadUserData();
                }
                
            } else {
                // Handle API-specific errors with helpful messages
                let errorMessage = result.message || 'Unknown error occurred';
                let actionMessage = '';
                
                switch (result.error_type) {
                    case 'invalid_api_key':
                        errorMessage = '🔑 API Configuration Error';
                        actionMessage = 'The server\'s Gemini API key is invalid. Please contact the administrator to fix the configuration.';
                        break;
                    case 'quota_exhausted':
                        errorMessage = '📊 API Quota Exceeded';
                        actionMessage = 'The Gemini API quota has been exceeded. Please try again later or contact support.';
                        break;
                    case 'permission_denied':
                        errorMessage = '🚫 API Access Denied';
                        actionMessage = 'Access to the Gemini API was denied. Please contact the administrator.';
                        break;
                    default:
                        actionMessage = result.error_details || 'Please try again or contact support.';
                }
                
                this.consoleComponent.log(`❌ ${errorMessage}`, 'error');
                this.consoleComponent.log(`💡 ${actionMessage}`, 'info');
                throw new Error(`${errorMessage}: ${actionMessage}`);
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
            const response = await fetch(stlUrl, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to download STL: ${response.status}`);
            }
            
            const stlData = await response.arrayBuffer();
            
            // Validate STL data before loading
            if (!stlData || stlData.byteLength === 0) {
                throw new Error('Downloaded STL file is empty');
            }
            
            this.consoleComponent.log(`📦 STL file downloaded: ${(stlData.byteLength / 1024).toFixed(2)} KB`, 'info');
            
            // Load STL into Three.js scene
            this.threeManager.loadSTL(stlData);
            
            this.consoleComponent.log('✅ STL model loaded successfully!', 'success');
            
        } catch (error) {
            this.consoleComponent.log(`❌ STL Loading Error: ${error.message}`, 'error');
            
            // Provide helpful error messages
            if (error.message.includes('offset is outside the bounds')) {
                this.consoleComponent.log('💡 The STL file appears to be corrupted or incomplete. Try regenerating the model.', 'warning');
            } else if (error.message.includes('triangle count')) {
                this.consoleComponent.log('💡 The STL file has an invalid format. This may be due to a server error.', 'warning');
            } else if (error.message.includes('Failed to download')) {
                this.consoleComponent.log('💡 Could not download the STL file. Check your network connection.', 'warning');
            }
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
                // Three.js CAD mode - no STL file available for download
                this.consoleComponent.log('🔧 Building CAD model...', 'info');
                this.currentModelId = null; // Clear model ID as this is local visualization only
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
                credentials: 'include',
                body: JSON.stringify({ 
                    code: code,
                    user_id: this.authState.user?.id
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`Backend error: ${response.status} - ${errorData.detail || 'Unknown error'}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.consoleComponent.log(`✅ ${result.message}`, 'success');
                
                // Store the model ID for download functionality
                this.currentModelId = result.model_id;
                
                // Load and display the STL model
                await this.loadSTLModel(result.model_id);

                // Update auth state (user count should be incremented)
                if (window.authService) {
                    await window.authService.loadUserData();
                }
                
            } else {
                throw new Error(result.error || 'Code execution failed');
            }

        } catch (error) {
            this.consoleComponent.log(`❌ BadCAD Execution Error: ${error.message}`, 'error');
        }
    }

    async downloadSTL() {
        try {
            if (!this.currentModelId) {
                this.consoleComponent.log('⚠️ No model available for download. Please generate or build a model first.', 'warning');
                return;
            }

            this.consoleComponent.log('📥 Downloading STL file...', 'info');

            // Create download URL
            const downloadUrl = `${window.API_URL || 'http://localhost:8000'}/api/download/${this.currentModelId}`;
            
            // Create temporary link element for download
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `model_${this.currentModelId}.stl`;
            link.style.display = 'none';
            
            // Add to document, click, and remove
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.consoleComponent.log('✅ STL download initiated!', 'success');
            
        } catch (error) {
            this.consoleComponent.log(`❌ Download Error: ${error.message}`, 'error');
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
        const authBanner = document.getElementById('authBanner');
        const usageNotice = document.getElementById('usageNotice');
        const modelCount = document.getElementById('modelCount');
        const modelCountValue = document.getElementById('modelCountValue');
        const generateBtn = document.getElementById('generateModel');
        const promptInput = document.getElementById('promptInput');

        if (!authState.isSignedIn) {
            // Show auth banner prominently
            if (authBanner) authBanner.style.display = 'flex';
            if (usageNotice) usageNotice.style.display = 'none';
            if (modelCount) modelCount.style.display = 'none';
            generateBtn.classList.add('auth-required');
            // Don't disable - let them click and get prompted
            generateBtn.disabled = false;
            promptInput.disabled = false;
            promptInput.placeholder = 'Describe the 3D model you want to create...';
        } else if (!authState.canGenerate) {
            // Show usage limit notice
            if (authBanner) authBanner.style.display = 'none';
            if (usageNotice) usageNotice.style.display = 'block';
            if (modelCount) modelCount.style.display = 'flex';
            if (modelCountValue) modelCountValue.textContent = `10/10`;
            generateBtn.disabled = true;
            promptInput.disabled = true;
            promptInput.placeholder = 'Model generation limit reached...';
        } else {
            // User can generate models
            if (authBanner) authBanner.style.display = 'none';
            if (usageNotice) usageNotice.style.display = 'none';
            if (modelCount) modelCount.style.display = 'flex';
            const count = authState.modelCount || 0;
            if (modelCountValue) modelCountValue.textContent = `${count}/10`;
            generateBtn.classList.remove('auth-required');
            generateBtn.disabled = false;
            promptInput.disabled = false;
            promptInput.placeholder = `Describe the 3D model you want to create...`;
        }
    }
}