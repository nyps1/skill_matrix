const API_BASE = 'http://127.0.0.1:5000/api';

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
                    // Token expired or invalid
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    window.location.reload();
                }
                throw new Error(data.message || 'API Request Failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    static async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: { username, password }
        });
    }

    static async getMe() {
        return this.request('/auth/me');
    }

    static async getAdminDashboard() {
        return this.request('/admin/dashboard');
    }
    
    static async getSkills() {
        return this.request('/admin/skills');
    }
    
    static async createQuestion(data) {
        return this.request('/admin/questions', {
            method: 'POST',
            body: data
        });
    }

    static async startExam() {
        return this.request('/assessment/exams/start', { method: 'POST' });
    }

    static async getExamQuestions(sessionId) {
        return this.request(`/assessment/exams/${sessionId}/questions`);
    }

    static async autosaveExam(sessionId, answers) {
        return this.request(`/assessment/exams/${sessionId}/autosave`, {
            method: 'PUT',
            body: { answers }
        });
    }

    static async submitExam(sessionId) {
        return this.request(`/assessment/exams/${sessionId}/submit`, { method: 'POST' });
    }
}
