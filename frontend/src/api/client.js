// ============================================================================
// MCP Cloud Orchestrator - API Client
// ============================================================================
// 설명: 백엔드 API와 통신하는 Axios 클라이언트
// Production: Nginx 프록시를 통해 /api/* → Backend로 라우팅
// ============================================================================

import axios from 'axios';

// API 기본 URL 설정
// Production: /api (Nginx 프록시 사용)
// Development: 직접 백엔드 URL 사용 가능
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Axios 인스턴스 생성
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
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

    getCapacity: () =>
        api.get('/dashboard/capacity'),
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

// ============================================================================
// Ray Cluster API
// ============================================================================

export const rayAPI = {
    getNodes: () =>
        api.get('/ray/nodes'),

    getResources: () =>
        api.get('/ray/resources'),

    getStatus: () =>
        api.get('/ray/status'),

    getBestNode: () =>
        api.get('/ray/best-node'),
};

// Ray Dashboard URL
export const RAY_DASHBOARD_URL = 'http://100.117.45.28:8265';

export default api;
