import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_URL || 'https://financeagent-q0wm.onrender.com/api'

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    }
})

api.interceptors.request.use(
    (config) => {
        return config;
    },
    (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        console.error('API Error:', error.config?.method?.toUpperCase(), error.config?.url, error.response?.status, error.response?.data || error.message);
        return Promise.reject(error);
    }
);

export const authAPI= {
    register: (userData) => api.post('/register', userData),
    login: (loginData) => api.post('/login', loginData),
    getUser: (user_id) => api.get(`/user/${user_id}`),
};

export const transactionAPI = {
    addTransaction: (transactionData) => api.post('/transactions', transactionData),
    searchTransactions: (searchData) => {
        // Manual URL construction for proper encoding
        const encodedQuery = encodeURIComponent(searchData.query);
        return api.get(`/search?user_id=${searchData.user_id}&query=${encodedQuery}`);
    },
    getTransactions: (userId) => api.get(`/transactions/${userId}`),
};

export const analysisAPI = {
    getInsights: (userId, period = "this month") => api.get(`/insights/${userId}?period=${encodeURIComponent(period)}`),
};

export default api;
