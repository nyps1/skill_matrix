const API_BASE = window.location.origin + '/api';

class Api {
    static getToken() {
        return localStorage.getItem('token');
    }

    static async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    window.location.href = '/login';
                }
                throw new Error(data.message || 'API Request Failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // --- Auth APIs ---
    static async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: { username, password }
        });
    }

    static async getMe() {
        return this.request('/auth/me');
    }

    static async changeMyPassword(currentPassword, newPassword) {
        return this.request('/auth/password', {
            method: 'PUT',
            body: { current_password: currentPassword, new_password: newPassword }
        });
    }

    // --- Leader APIs ---
    static async getAdminDashboard() {
        return this.request('/admin/dashboard');
    }

    static async getMyDashboard() {
        return this.request('/assessment/my-dashboard');
    }
    
    static async getUsers() {
        return this.request('/admin/users');
    }

    static async createUser(data) {
        return this.request('/admin/users', {
            method: 'POST',
            body: data
        });
    }

    static async resetUserPassword(userId, newPassword) {
        return this.request(`/admin/users/${userId}/password`, {
            method: 'PUT',
            body: { new_password: newPassword }
        });
    }

    static async updatePermissions(userId, skillIds) {
        return this.request(`/admin/users/${userId}/permissions`, {
            method: 'PUT',
            body: { skill_ids: skillIds }
        });
    }

    static async toggleActive(userId) {
        return this.request(`/admin/users/${userId}/toggle-active`, {
            method: 'PUT'
        });
    }

    // --- Assessment APIs (Skills & Questions) ---
    static async getSkills() {
        return this.request('/assessment/skills');
    }
    
    static async createSkill(data) {
        return this.request('/assessment/skills', {
            method: 'POST',
            body: data
        });
    }

    static async getQuestions() {
        return this.request('/assessment/questions');
    }

    static async createQuestion(data) {
        return this.request('/assessment/questions', {
            method: 'POST',
            body: data
        });
    }

    static async updateQuestion(id, data) {
        return this.request(`/assessment/questions/${id}`, {
            method: 'PUT',
            body: data
        });
    }

    // --- Assessment APIs (Exams) ---
    static async startExam() {
        return this.request('/assessment/exams/start', { method: 'POST' });
    }

    static async getExamQuestions(sessionId) {
        return this.request(`/assessment/exams/${sessionId}/questions`);
    }

    static async autosaveExam(sessionId, answers) {
        return this.request(`/assessment/exams/${sessionId}/autosave`, {
            method: 'POST',
            body: { answers }
        });
    }

    static async submitExam(sessionId) {
        return this.request(`/assessment/exams/${sessionId}/submit`, { method: 'POST' });
    }
}
