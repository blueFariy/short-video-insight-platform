/**
 * API Service - Axios HTTP Client
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// Base URL configuration
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8001'
const COLLECTOR_BASE_URL = (import.meta as any).env?.VITE_COLLECTOR_BASE_URL || 'http://localhost:8004'

// Create axios instance
const service: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Collector service (Data Collector on port 8004)
const collectorService: AxiosInstance = axios.create({
  baseURL: COLLECTOR_BASE_URL,
  timeout: 60000,  // Longer timeout for data collection
  headers: {
    'Content-Type': 'application/json'
  }
})

// Collector request interceptor
collectorService.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Collector response interceptor
collectorService.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    if (res.code !== undefined) {
      if (res.code === 200) {
        return res.data !== undefined ? res.data : res
      } else {
        ElMessage.error(res.message || 'Request failed')
        return Promise.reject(new Error(res.message || 'Request failed'))
      }
    }
    return response.data
  },
  (error) => {
    console.error('Collector response error:', error)
    if (error.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      window.location.href = '/login'
    } else if (error.response?.status === 404) {
      ElMessage.error('请求的资源不存在')
    }
    return Promise.reject(error)
  }
)

// Request interceptor
service.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data

    // Check if response has standard format
    if (res.code !== undefined) {
      if (res.code === 200) {
        return res.data !== undefined ? res.data : res
      } else {
        ElMessage.error(res.message || 'Request failed')
        return Promise.reject(new Error(res.message || 'Request failed'))
      }
    }

    return response.data
  },
  (error) => {
    console.error('Response error:', error)

    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        localStorage.removeItem('token')
        window.location.href = '/login'
      } else if (status === 403) {
        ElMessage.error('没有权限访问')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后重试')
      }
    } else if (error.request) {
      ElMessage.error('网络连接失败，请检查网络')
    }

    return Promise.reject(error)
  }
)

export { collectorService }
export default service

// API service URLs
export const API_URL = {
  // User Service (port 8001)
  USER: {
    LOGIN: '/api/v1/users/login',
    REGISTER: '/api/v1/users/register',
    PROFILE: '/api/v1/users/profile',
    CHANGE_PASSWORD: '/api/v1/users/password',
    COLLECTIONS: '/api/v1/collections',
    ADD_COLLECTION: '/api/v1/collections',
    DELETE_COLLECTION: (id: string) => `/api/v1/collections/${id}`
  },

  // Video Service (port 8002)
  VIDEO: {
    PROCESS: '/api/v1/videos/process',
    SEARCH: '/api/v1/videos/search',
    LIST: '/api/v1/videos',
    DETAIL: (id: string) => `/api/v1/videos/${id}`
  },

  // Insight Service (port 8003)
  INSIGHT: {
    GOLDEN_HOOK: '/api/v1/insights/golden-hook',
    SCRIPT_STRUCTURE: '/api/v1/insights/script-structure',
    SENTIMENT: '/api/v1/insights/sentiment',
    COMPREHENSIVE: '/api/v1/insights/comprehensive',
    TEMPLATES: '/api/v1/insights/templates'
  },

  // Data Collector (port 8004)
  COLLECTOR: {
    ACCOUNTS: '/api/v1/collector/accounts',
    ACCOUNT_DETAIL: (id: string) => `/api/v1/collector/accounts/${id}`,
    ACCOUNT_CREATE: '/api/v1/collector/accounts',
    ACCOUNT_UPDATE: (id: string) => `/api/v1/collector/accounts/${id}`,
    ACCOUNT_DELETE: (id: string) => `/api/v1/collector/accounts/${id}`,
    COLLECT: '/api/v1/collector/collect',
    COLLECT_ALL: '/api/v1/collector/collect/all',
    VIDEOS: '/api/v1/collector/videos',
    VIDEO_DETAIL: (id: string) => `/api/v1/collector/videos/${id}`,
    SEARCH_VIDEOS: '/api/v1/collector/videos/search',
    SCHEDULER_STATUS: '/api/v1/collector/scheduler/status',
    SCHEDULER_RUN_TASK: (taskId: string) => `/api/v1/collector/scheduler/tasks/${taskId}/run`
  },

  // Competitor Monitor (port 8005)
  MONITOR: {
    METRICS: '/api/v1/monitor/metrics',
    METRICS_DETAIL: (id: string) => '/api/v1/monitor/metrics/' + id,
    METRICS_TREND: (id: string) => '/api/v1/monitor/metrics/' + id + '/trend',
    METRICS_COMPARE: '/api/v1/monitor/metrics/compare',
    ALERTS: '/api/v1/monitor/alerts',
    CHECK_ALERTS: (id: string) => '/api/v1/monitor/alerts/check/' + id,
    ALERT_ACK: (id: string) => '/api/v1/monitor/alerts/' + id + '/acknowledge',
    ALERT_RESOLVE: (id: string) => '/api/v1/monitor/alerts/' + id + '/resolve'
  },

  // Report Service (port 8006)
  REPORT: {
    STATS_OVERVIEW: '/api/v1/reports/statistics/overview',
    STATS_PLATFORMS: '/api/v1/reports/statistics/platforms',
    STATS_CATEGORIES: '/api/v1/reports/statistics/categories',
    STATS_TIME: '/api/v1/reports/statistics/time',
    STATS_TOP: '/api/v1/reports/statistics/top',
    STATS_ENGAGEMENT: '/api/v1/reports/statistics/engagement',
    REPORTS: '/api/v1/reports/reports',
    REPORT_DETAIL: (id: string) => `/api/v1/reports/reports/${id}`,
    GENERATE_VIDEO: '/api/v1/reports/reports/generate/video',
    GENERATE_COMPETITOR: '/api/v1/reports/reports/generate/competitor',
    GENERATE_TREND: '/api/v1/reports/reports/generate/trend',
    EXPORT: (id: string) => `/api/v1/reports/reports/${id}/export`,
    EXPORT_FORMATS: '/api/v1/reports/export/formats'
  }
}
