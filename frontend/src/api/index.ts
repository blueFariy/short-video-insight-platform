/**
 * API Service - Axios HTTP Client
 */
import axios, {AxiosInstance, AxiosResponse} from 'axios'
import {ElMessage} from 'element-plus'

// Base URL configuration
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || '/user_service/api/v1'
const VIDEO_BASE_URL = (import.meta as any).env?.VITE_VIDEO_BASE_URL || '/video_service/api/v1'
const INSIGHT_BASE_URL = (import.meta as any).env?.VITE_INSIGHT_BASE_URL || '/insight_service/api/v1'
const COLLECTOR_BASE_URL = (import.meta as any).env?.VITE_COLLECTOR_BASE_URL || '/data_collector/api/v1'
// 未使用的URL配置，保留供将来使用
// const MONITOR_BASE_URL = (import.meta as any).env?.VITE_MONITOR_BASE_URL || 'http://localhost:8005'
// const REPORT_BASE_URL = (import.meta as any).env?.VITE_REPORT_BASE_URL || 'http://localhost:8006'

// Create axios instance
const service: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Video service (port 8002)
const videoService: AxiosInstance = axios.create({
    baseURL: VIDEO_BASE_URL,
    timeout: 60000,
    headers: {'Content-Type': 'application/json'}
})
videoService.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})
videoService.interceptors.response.use(
    (response: AxiosResponse) => response.data?.code === 200 ? response.data.data : response.data,
    (error) => {
        console.error('Video service error:', error);
        return Promise.reject(error)
    }
)

// Insight service (port 8003)
const insightService: AxiosInstance = axios.create({
    baseURL: INSIGHT_BASE_URL,
    timeout: 60000,
    headers: {'Content-Type': 'application/json'}
})
insightService.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})
insightService.interceptors.response.use(
    (response: AxiosResponse) => response.data?.code === 200 ? response.data.data : response.data,
    (error) => {
        console.error('Insight service error:', error);
        return Promise.reject(error)
    }
)

// Collector service (Data Collector on port 8004)
const collectorService: AxiosInstance = axios.create({
    baseURL: COLLECTOR_BASE_URL,
    timeout: 60000,
    headers: {'Content-Type': 'application/json'}
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

export {videoService, insightService, collectorService}
export default service

// API service URLs
export const API_URL = {
    // User Service (port 8001)
    USER: {
        LOGIN: '/users/login',
        REGISTER: '/users/register',
        PROFILE: '/users/profile',
        CHANGE_PASSWORD: '/users/password',
        COLLECTIONS: '/collections',
        COLLECTION_FOLDERS: '/collections/folders',
        ADD_COLLECTION: '/collections',
        UPDATE_COLLECTION: (id: string) => `/collections/${id}`,
        DELETE_COLLECTION: (id: string) => `/collections/${id}`,
    },

    // Video Service (port 8002)
    VIDEO: {
        PROCESS: `/videos/process`,
        SEARCH: `/videos/search`,
        LIST: `/videos`,
        DETAIL: (id: string) => `/videos/${id}`
    },

    // Insight Service (port 8003)
    INSIGHT: {
        GOLDEN_HOOK: `/insights/golden-hook`,
        SCRIPT_STRUCTURE: `/insights/script-structure`,
        SENTIMENT: `/insights/sentiment`,
        COMPREHENSIVE: `/insights/comprehensive`,
        TEMPLATES: `/insights/templates`,
        VIDEO_INSIGHTS: `/insights/video-insights`,
        VIDEO_INSIGHT_DETAIL: (videoId: number) => `/insights/video-insights/${videoId}`,
        VIDEO_INSIGHT_ALL: `/insights/video-insights/all`,
    },

    // Data Collector (port 8004)
    COLLECTOR: {
        ACCOUNTS: `/collector/accounts`,
        ACCOUNT_DETAIL: `/collector/accounts/detail`,
        ACCOUNT_CREATE: `/collector/accounts`,
        ACCOUNT_UPDATE: `/collector/accounts/detail`,
        ACCOUNT_DELETE: `/collector/accounts/detail`,
        COLLECT: `/collector/collect`,
        COLLECT_ALL: `/collector/collect/all`,
        VIDEOS: `/collector/videos`,
        VIDEO_DETAIL: (id: string) => `/collector/videos/${id}`,
        VIDEO_SAVE: (id: string, platform: string) => `/collector/videos/${id}/save?platform=${platform}`,
        SEARCH_VIDEOS: `/collector/videos/search`,
        // 手动采集
        MANUAL_COLLECT: `/collector/manual/collect`,
        BILIBILI_REGIONS: `/collector/bilibili/regions`,
        BILIBILI_CREATOR: (id: string) => `/collector/bilibili/creator/${id}`,
        BILIBILI_CREATOR_COLLECT: (id: string) => `/collector/bilibili/creator/collect?creator_id=${id}`,
        SCHEDULER_STATUS: `/collector/scheduler/status`,
        SCHEDULER_RUN_TASK: (taskId: string) => `/collector/scheduler/tasks/${taskId}/run`,
        // 定时任务管理 (新接口)
        SCHEDULER_TASKS: `/scheduler/tasks`,
        SCHEDULER_TASK_DETAIL: (taskId: string) => `/scheduler/tasks/${taskId}`,
        SCHEDULER_TASK_CREATE: `/scheduler/tasks`,
        SCHEDULER_TASK_UPDATE: (taskId: string) => `/scheduler/tasks/${taskId}`,
        SCHEDULER_TASK_DELETE: (taskId: string) => `/scheduler/tasks/${taskId}`,
        SCHEDULER_TASK_ENABLE: (taskId: string) => `/scheduler/tasks/${taskId}/enable`,
        SCHEDULER_TASK_DISABLE: (taskId: string) => `/scheduler/tasks/${taskId}/disable`,
        SCHEDULER_TASK_TRIGGER: (taskId: string) => `/scheduler/tasks/${taskId}/trigger`,
        SCHEDULER_TASK_DEFINITIONS: `/scheduler/tasks/definitions`,
        // 爆款视频
        VIRAL_VIDEOS: `/collector/videos/viral`,
        // 图片代理 - 解决B站图片403问题
        IMAGE_PROXY: `/collector/proxy/image`,
        // 用户兴趣配置
        USER_INTEREST_GET: `/viral/user/interest`,
        USER_INTEREST_UPDATE: `/viral/user/interest`,
        ALERTS: `/viral/alerts`
    },

    // Competitor Monitor (port 8005)
    MONITOR: {
        METRICS: '/monitor/metrics',
        METRICS_DETAIL: (id: string) => '/monitor/metrics/' + id,
        METRICS_TREND: (id: string) => '/monitor/metrics/' + id + '/trend',
        METRICS_COMPARE: '/monitor/metrics/compare',
        ALERTS: '/monitor/alerts',
        CHECK_ALERTS: (id: string) => '/monitor/alerts/check/' + id,
        ALERT_ACK: (id: string) => '/monitor/alerts/' + id + '/acknowledge',
        ALERT_RESOLVE: (id: string) => '/monitor/alerts/' + id + '/resolve'
    },

    // Report Service (port 8006)
    REPORT: {
        STATS_OVERVIEW: '/reports/statistics/overview',
        STATS_PLATFORMS: '/reports/statistics/platforms',
        STATS_CATEGORIES: '/reports/statistics/categories',
        STATS_TIME: '/reports/statistics/time',
        STATS_TOP: '/reports/statistics/top',
        STATS_ENGAGEMENT: '/reports/statistics/engagement',
        REPORTS: '/reports/reports',
        REPORT_DETAIL: (id: string) => `/reports/reports/${id}`,
        GENERATE_VIDEO: '/reports/reports/generate/video',
        GENERATE_COMPETITOR: '/reports/reports/generate/competitor',
        GENERATE_TREND: '/reports/reports/generate/trend',
        EXPORT: (id: string) => `/reports/reports/${id}/export`,
        EXPORT_FORMATS: '/reports/export/formats'
    }
}
