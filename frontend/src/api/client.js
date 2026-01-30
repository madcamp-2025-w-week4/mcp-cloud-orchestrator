// ============================================================================
// MCP Cloud Orchestrator - API Client
// ============================================================================
// 설명: 백엔드 API와 통신하는 Axios 클라이언트
// ============================================================================

import axios from 'axios';

// API 기본 URL 설정
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Axios 인스턴스 생성
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 요청 인터셉터 - 사용자 ID 헤더 추가
api.interceptors.request.use((config) => {
    const userId = localStorage.getItem('userId') || 'user-demo-001';
    config.headers['X-User-ID'] = userId;
    return config;
});

// 응답 인터셉터 - 에러 처리
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

// ============================================================================
// Auth API
// ============================================================================

export const authAPI = {
    login: (username, password) =>
        api.post('/auth/login', { username, password }),

    getCurrentUser: () =>
        api.get('/auth/me'),

    getQuota: () =>
        api.get('/auth/quota'),

    logout: () =>
        api.post('/auth/logout'),
};

// ============================================================================
// Instance API
// ============================================================================

export const instanceAPI = {
    list: (status = null) => {
        const params = status ? { status } : {};
        return api.get('/instances', { params });
    },

    get: (instanceId) =>
        api.get(`/instances/${instanceId}`),

    create: (data) =>
        api.post('/instances', data),

    stop: (instanceId) =>
        api.post(`/instances/${instanceId}/stop`),

    start: (instanceId) =>
        api.post(`/instances/${instanceId}/start`),

    terminate: (instanceId) =>
        api.delete(`/instances/${instanceId}`),

    getSummary: () =>
        api.get('/instances/summary'),
};

// ============================================================================
// Dashboard API
// ============================================================================

export const dashboardAPI = {
    getSummary: () =>
        api.get('/dashboard/summary'),

    getHealth: () =>
        api.get('/dashboard/health'),

    getNodesStatus: () =>
        api.get('/dashboard/nodes/status'),

    getImages: () =>
        api.get('/dashboard/images'),
};

// ============================================================================
// Cluster API
// ============================================================================

export const clusterAPI = {
    getStatus: (includeNodes = false) =>
        api.get('/cluster/status', { params: { include_nodes: includeNodes } }),

    getNodes: (role = null) => {
        const params = role ? { role } : {};
        return api.get('/cluster/nodes', { params });
    },

    healthCheck: () =>
        api.post('/cluster/health-check'),
};

export default api;
