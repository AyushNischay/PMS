
// Base API URL
const API_URL = 'http://127.0.0.1:5000';

// Auth State Management
const Auth = {
    token: localStorage.getItem('token'),
    user: JSON.parse(localStorage.getItem('user') || '{}'),

    isLoggedIn: function() {
        return !!this.token;
    },

    login: async function(email, password) {
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await response.json();
            
            if (response.ok) {
                this.token = data.token;
                this.user = data.user;
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(data.user));
                return { success: true };
            } else {
                return { success: false, message: data.message };
            }
        } catch (error) {
            return { success: false, message: 'Network error' };
        }
    },

    logout: function() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    },

    getHeaders: function() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }
};

// UI Utilities
const UI = {
    showAlert: function(message, type = 'success') {
        const div = document.createElement('div');
        div.className = `alert alert-${type}`;
        div.textContent = message;
        // Basic alert styling would be needed in CSS or here
        // For now just logging
        console.log(`[${type}] ${message}`);
        alert(message); // Simple fallback
    }
};

// Protect Routes (Simple check)
function requireAuth() {
    if (!Auth.isLoggedIn()) {
        window.location.href = '/login';
    }
}
