
// Base API URL
const API_URL = window.API_URL || '';  // Use relative paths or inject via server-side template
// Auth State Management
const Auth = {
    // Token is now HttpOnly cookie, not accessible to JS
    user: JSON.parse(localStorage.getItem('user') || '{}'),
    exp: localStorage.getItem('token_exp'),

    isLoggedIn: function() {
        if (!this.exp) return false;
        // Check if expired
        const now = Math.floor(Date.now() / 1000);
        const expTime = parseInt(this.exp, 10);
        if (isNaN(expTime) || now > expTime) {
            this.logout();
            return false;
        }
        return true;
    },    
    // Async check for critical actions or app load
    validateOptions: async function() {
        if (!this.isLoggedIn()) return false;
        try {
            const response = await fetch(`${API_URL}/auth/validate`, {
                credentials: 'include'
            });
            if (response.ok) return true;
        } catch (e) { console.error(e); }
        this.logout();
        return false;
    },
    login: async function(email, password) {
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            let data = {};
            try {
                data = await response.json();
            } catch (err) {
                console.error("Failed to parse JSON", err);
                const text = await response.text();
                return { success: false, message: text || 'Invalid server response' };
            }
            
            if (response.ok) {
                if (data.user && data.exp) {
                    this.user = data.user;
                    this.exp = data.exp;
                    localStorage.setItem('user', JSON.stringify(data.user));
                    localStorage.setItem('token_exp', data.exp);
                    return { success: true };
                } else {
                    return { success: false, message: 'Invalid response structure' };
                }
            } else {
                return { success: false, message: data.message || 'Login failed' };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, message: 'Network error' };
        }
    },

    logout: function() {
        this.user = {};
        this.exp = null;
        localStorage.removeItem('user');
        localStorage.removeItem('token_exp');
        
        // Call backend to clear cookie
        fetch(`${API_URL}/auth/logout`, { method: 'POST' })
            .then(() => window.location.href = '/login')
            .catch(() => window.location.href = '/login');
    },
    getHeaders: function() {
        // Cookies handling auth, so just content type
        return { 'Content-Type': 'application/json' };
    }};

// UI Utilities
const UI = {
    showAlert: function(message, type = 'success') {
        console.log(`[${type}] ${message}`);
        alert(message);  // TODO: Implement proper toast/notification UI
    }};

// Protect Routes (Simple check)
function requireAuth() {
    if (!Auth.isLoggedIn()) {
        window.location.href = '/login';
    }
}
