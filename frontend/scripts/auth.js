// Authentication Service - Email Collection Management (Temporary)

class AuthService {
    constructor() {
        console.log('🚀 AuthService constructor called (Email Collection Mode)');
        this.user = null;
        this.isSignedIn = false;
        this.modelCount = 0;
        this.maxModels = 10;
        this.onAuthStateChanged = null;
        
        // Load user data from localStorage if available
        this.loadLocalUserData();
        
        // Initialize without Google API
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
        const email = prompt('Please enter your email address to continue:\n(This is temporary - we will implement proper authentication soon)');
        
        if (!email) {
            return null;
        }
        
        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Please enter a valid email address.');
            return this.promptForEmail();
        }
        
        const name = prompt('Please enter your name (optional):') || 'Anonymous User';
        
        return {
            email: email,
            name: name,
            id: btoa(email).replace(/[^a-zA-Z0-9]/g, '') // Simple ID from email
        };
    }

    async signIn() {
        try {
            console.log('📧 Email sign-in attempt started');
            
            // Get user email
            const userInfo = await this.promptForEmail();
            if (!userInfo) {
                return false;
            }
            
            this.user = {
                id: userInfo.id,
                name: userInfo.name,
                email: userInfo.email,
                imageUrl: `https://ui-avatars.com/api/?name=${encodeURIComponent(userInfo.name)}&background=random`
            };
            this.isSignedIn = true;
            
            // Load user data from backend
            await this.loadUserData();
            
            // Save to localStorage
            this.saveLocalUserData();
            
            console.log('✅ User signed in:', this.getUserInfo());
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
            this.user = null;
            this.isSignedIn = false;
            this.modelCount = 0;
            
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
            const userInfo = this.getUserInfo();
            const response = await fetch(`${window.API_URL || 'http://localhost:8000'}/api/user/info`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userInfo.id,
                    email: userInfo.email,
                    name: userInfo.name
                })
            });

            if (response.ok) {
                const userData = await response.json();
                this.modelCount = userData.model_count || 0;
                this.saveLocalUserData(); // Update localStorage
                console.log(`📊 User has generated ${this.modelCount}/${this.maxModels} models`);
            }
        } catch (error) {
            console.error('❌ Failed to load user data:', error);
        }
    }

    async incrementModelCount() {
        if (!this.isSignedIn) {
            throw new Error('User must be signed in to generate models');
        }

        if (this.modelCount >= this.maxModels) {
            throw new Error(`You have reached the maximum limit of ${this.maxModels} models. Please upgrade your account or contact support.`);
        }

        try {
            const userInfo = this.getUserInfo();
            const response = await fetch(`${window.API_URL || 'http://localhost:8000'}/api/user/increment-count`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userInfo.id
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.modelCount = result.model_count;
                this.saveLocalUserData(); // Update localStorage
                this.notifyAuthStateChanged();
                return true;
            } else {
                throw new Error('Failed to update model count');
            }
        } catch (error) {
            console.error('❌ Failed to increment model count:', error);
            throw error;
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
