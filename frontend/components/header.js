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
                <div class="user-section" id="userSection">
                    <div class="auth-loading" id="authLoading">Loading...</div>
                    <div class="user-info" id="userInfo" style="display: none;">
                        <div class="user-avatar" id="userAvatar"></div>
                        <div class="user-details">
                            <div class="user-name" id="userName"></div>
                            <div class="user-usage" id="userUsage"></div>
                        </div>
                        <button class="sign-out-btn" id="signOutBtn">Sign Out</button>
                    </div>
                    <div class="sign-in-section" id="signInSection" style="display: none;">
                        <button class="sign-in-btn" id="signInBtn">
                            📧 Enter Email to Continue
                        </button>
                    </div>
                </div>
                <div class="toolbar">
                    <button id="resetView">🔄 Reset View</button>
                    <button id="wireframe">📐 Wireframe</button>
                    <button id="animate">🎬 Animate</button>
                    <button id="axes" class="active">📍 Axes</button>
                </div>
            </div>
        `;
        
        document.getElementById('header').innerHTML = headerHTML;
        this.attachEventListeners();
        this.setupAuthListener();
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

    setupAuthListener() {
        console.log('🔗 Setting up auth listener');
        
        // Wait for auth service to be available
        const waitForAuth = () => {
            if (window.authService) {
                console.log('✅ Auth service found, setting up listener');
                window.authService.setAuthStateListener((authState) => {
                    this.updateAuthUI(authState);
                });
            } else {
                console.log('⏳ Waiting for auth service...');
                setTimeout(waitForAuth, 100);
            }
        };
        waitForAuth();

        // Fallback: Show sign-in button after 3 seconds if auth service doesn't respond
        setTimeout(() => {
            const authLoading = document.getElementById('authLoading');
            const signInSection = document.getElementById('signInSection');
            
            if (authLoading && authLoading.style.display !== 'none') {
                console.log('⚠️ Auth service timeout - showing sign-in button');
                authLoading.style.display = 'none';
                if (signInSection) {
                    signInSection.style.display = 'block';
                }
            }
        }, 10000); // Increased timeout to 10 seconds

        // Sign in button
        document.getElementById('signInBtn').addEventListener('click', async () => {
            console.log('🖱️ Sign-in button clicked');
            if (window.authService) {
                await window.authService.signIn();
            } else {
                alert('Authentication service not available. Please refresh the page.');
            }
        });

        // Sign out button
        document.getElementById('signOutBtn').addEventListener('click', async () => {
            if (window.authService) {
                await window.authService.signOut();
            }
        });
    }

    updateAuthUI(authState) {
        console.log('🔍 Updating auth UI with state:', authState);
        
        const authLoading = document.getElementById('authLoading');
        const userInfo = document.getElementById('userInfo');
        const signInSection = document.getElementById('signInSection');

        // Hide loading
        if (authLoading) {
            authLoading.style.display = 'none';
        }

        if (authState.isSignedIn) {
            // Show user info
            userInfo.style.display = 'flex';
            signInSection.style.display = 'none';

            // Update user details
            const userAvatar = document.getElementById('userAvatar');
            const userName = document.getElementById('userName');
            const userUsage = document.getElementById('userUsage');

            if (authState.user) {
                userAvatar.innerHTML = `<img src="${authState.user.imageUrl}" alt="${authState.user.name}" width="32" height="32">`;
                userName.textContent = authState.user.name;
                
                const usageColor = authState.usagePercentage > 80 ? '#ff6b6b' : 
                                  authState.usagePercentage > 60 ? '#ffa726' : '#51cf66';
                
                userUsage.innerHTML = `
                    <div class="usage-bar">
                        <div class="usage-fill" style="width: ${authState.usagePercentage}%; background: ${usageColor};"></div>
                    </div>
                    <span class="usage-text">${authState.modelCount}/${authState.maxModels} models</span>
                `;
            }
        } else {
            // Show sign in button
            console.log('👤 User not signed in - showing sign-in button');
            userInfo.style.display = 'none';
            if (signInSection) {
                signInSection.style.display = 'block';
                console.log('✅ Sign-in section should now be visible');
            } else {
                console.error('❌ Sign-in section element not found');
            }
        }
    }
}