// Authentication Service - Session-based with Analytics Backend

class AuthService {
    constructor() {
        console.log('🚀 AuthService constructor called (Email Collection Mode)');
        this.user = null;
        this.isSignedIn = false;
        this.modelCount = 0;
        this.maxModels = 10;
        this.onAuthStateChanged = null;
        this.csrfToken = null;
        
        // Check for existing session
        this.checkExistingSession();
    }

    async checkExistingSession() {
        try {
            const response = await fetch('/analytics/auth/current-user', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const userData = await response.json();
                this.user = {
                    id: userData.id,
                    name: userData.name,
                    email: userData.email,
                    imageUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(userData.name)}&background=random`
                };
                this.isSignedIn = true;
                this.modelCount = userData.model_count;
                console.log('✅ Existing session found:', userData);
            }
        } catch (error) {
            console.log('📊 No existing session');
        }
        
        // Notify listeners
        setTimeout(() => this.notifyAuthStateChanged(), 100);
    }

    loadLocalUserData() {
        const userData = localStorage.getItem('tempUserData');
        if (userData) {
            const parsedData = JSON.parse(userData);
            this.user = parsedData.user;
            this.isSignedIn = true;
            this.modelCount = parsedData.modelCount || 0;
            console.log('📊 Loaded user data from localStorage:', this.user);
        }
    }

    saveLocalUserData() {
        const userData = {
            user: this.user,
            modelCount: this.modelCount
        };
        localStorage.setItem('tempUserData', JSON.stringify(userData));
    }

    async promptForEmail() {
        return new Promise((resolve) => {
            // Create modal overlay
            const overlay = document.createElement('div');
            overlay.className = 'auth-modal-overlay';
            
            const modal = document.createElement('div');
            modal.className = 'auth-modal';
            
            modal.innerHTML = `
                <div class="auth-modal-header">
                    <div class="auth-modal-icon">✉️</div>
                    <h2 class="auth-modal-title">Enter Your Email to Continue</h2>
                    <p class="auth-modal-subtitle">We need your email to save your creations and track your usage</p>
                </div>
                
                <form class="auth-modal-form" id="authModalForm">
                    <div class="auth-input-group">
                        <label class="auth-input-label">
                            Email Address <span class="auth-input-required">*</span>
                        </label>
                        <input 
                            type="email" 
                            class="auth-input" 
                            id="authEmailInput" 
                            placeholder="your@email.com"
                            required
                            autocomplete="email"
                        >
                        <div class="auth-error-message" id="emailError" style="display: none;"></div>
                    </div>
                    
                    <div class="auth-input-group">
                        <label class="auth-input-label">
                            Your Name <span style="color: #666;">(optional)</span>
                        </label>
                        <input 
                            type="text" 
                            class="auth-input" 
                            id="authNameInput" 
                            placeholder="John Doe"
                            autocomplete="name"
                        >
                    </div>
                    
                    <button type="submit" class="auth-continue-btn" id="authContinueBtn">
                        Continue to Text-to-CAD
                    </button>
                </form>
                
                <div class="auth-benefits">
                    <div class="auth-benefits-title">Why we need your email:</div>
                    <ul class="auth-benefits-list">
                        <li>Track your model generation history</li>
                        <li>Save your projects for later</li>
                        <li>Get support if something goes wrong</li>
                        <li>Free usage up to 10 models</li>
                    </ul>
                </div>
            `;
            
            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            
            // Focus email input
            setTimeout(() => {
                document.getElementById('authEmailInput').focus();
            }, 100);
            
            // Handle form submission
            const form = document.getElementById('authModalForm');
            const emailInput = document.getElementById('authEmailInput');
            const nameInput = document.getElementById('authNameInput');
            const emailError = document.getElementById('emailError');
            const continueBtn = document.getElementById('authContinueBtn');
            
            // Email validation
            const validateEmail = (email) => {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return emailRegex.test(email);
            };
            
            // Real-time email validation
            emailInput.addEventListener('input', () => {
                const email = emailInput.value.trim();
                if (email && !validateEmail(email)) {
                    emailInput.classList.add('error');
                    emailError.textContent = 'Please enter a valid email address';
                    emailError.style.display = 'block';
                    continueBtn.disabled = true;
                } else {
                    emailInput.classList.remove('error');
                    emailError.style.display = 'none';
                    continueBtn.disabled = !email;
                }
            });
            
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                
                const email = emailInput.value.trim();
                const name = nameInput.value.trim() || 'Anonymous User';
                
                if (!validateEmail(email)) {
                    emailInput.classList.add('error');
                    emailError.textContent = 'Please enter a valid email address';
                    emailError.style.display = 'block';
                    return;
                }
                
                // Remove modal
                document.body.removeChild(overlay);
                
                // Return user info
                resolve({
                    email: email,
                    name: name,
                    id: btoa(email).replace(/[^a-zA-Z0-9]/g, '') // Simple ID from email
                });
            });
            
            // No way to close without entering email!
        });
    }

    async signIn() {
        try {
            console.log('📧 Email sign-in attempt started');
            
            // Get user email
            const userInfo = await this.promptForEmail();
            if (!userInfo) {
                return false;
            }
            
            // Create session with analytics backend
            const sessionResponse = await fetch('/analytics/auth/create-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `email=${encodeURIComponent(userInfo.email)}&name=${encodeURIComponent(userInfo.name)}`,
                credentials: 'include'
            });

            if (!sessionResponse.ok) {
                const errorData = await sessionResponse.json().catch(() => ({}));
                throw new Error(`Session creation failed: ${errorData.detail || 'Unknown error'}`);
            }

            const sessionData = await sessionResponse.json();
            this.csrfToken = sessionData.csrf_token;
            
            this.user = {
                id: sessionData.user.id,
                name: sessionData.user.name,
                email: sessionData.user.email,
                imageUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(sessionData.user.name)}&background=random`
            };
            this.isSignedIn = true;
            this.modelCount = sessionData.user.model_count;
            
            // Save to localStorage
            this.saveLocalUserData();
            
            console.log('✅ User signed in with analytics session:', this.getUserInfo());
            this.notifyAuthStateChanged();
            
            return true;
        } catch (error) {
            console.error('❌ Sign in failed:', error);
            alert(`Sign-in failed: ${error.message || 'Unknown error'}`);
            return false;
        }
    }

    async signOut() {
        try {
            // Destroy analytics session
            await fetch('/analytics/auth/destroy-session', {
                method: 'POST',
                credentials: 'include'
            });
            
            this.user = null;
            this.isSignedIn = false;
            this.modelCount = 0;
            this.csrfToken = null;
            
            // Clear localStorage
            localStorage.removeItem('tempUserData');
            
            console.log('✅ User signed out');
            this.notifyAuthStateChanged();
            
            return true;
        } catch (error) {
            console.error('❌ Sign out failed:', error);
            return false;
        }
    }

    async loadUserData() {
        if (!this.isSignedIn || !this.user) return;

        try {
            // Load current user data from analytics backend
            const response = await fetch('/analytics/auth/current-user', {
                credentials: 'include'
            });

            if (response.ok) {
                const userData = await response.json();
                this.modelCount = userData.model_count || 0;
                this.saveLocalUserData(); // Update localStorage
                console.log(`📊 User has generated ${this.modelCount}/${this.maxModels} models`);
                this.notifyAuthStateChanged();
            }
        } catch (error) {
            console.error('❌ Failed to load user data:', error);
        }
    }


    getUserInfo() {
        if (!this.user) return null;

        return {
            id: this.user.id,
            name: this.user.name,
            email: this.user.email,
            imageUrl: this.user.imageUrl
        };
    }

    canGenerateModel() {
        return this.isSignedIn && this.modelCount < this.maxModels;
    }

    getRemainingModels() {
        return this.maxModels - this.modelCount;
    }

    getUsagePercentage() {
        return (this.modelCount / this.maxModels) * 100;
    }

    getAuthState() {
        return {
            isSignedIn: this.isSignedIn,
            user: this.getUserInfo(),
            modelCount: this.modelCount,
            maxModels: this.maxModels,
            canGenerate: this.canGenerateModel(),
            remaining: this.getRemainingModels(),
            usagePercentage: this.getUsagePercentage()
        };
    }

    notifyAuthStateChanged() {
        const authState = {
            isSignedIn: this.isSignedIn,
            user: this.getUserInfo(),
            modelCount: this.modelCount,
            maxModels: this.maxModels,
            canGenerate: this.canGenerateModel(),
            remaining: this.getRemainingModels(),
            usagePercentage: this.getUsagePercentage()
        };
        
        console.log('🔔 Notifying auth state change:', authState);
        
        if (this.onAuthStateChanged) {
            this.onAuthStateChanged(authState);
        } else {
            console.warn('⚠️ No auth state listener registered');
        }
    }

    setAuthStateListener(callback) {
        this.onAuthStateChanged = callback;
    }
}

// Global auth service instance
window.authService = new AuthService();
