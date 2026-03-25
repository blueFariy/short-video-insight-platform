import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/Dashboard.vue'),
    meta: { title: '工作台' }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/analysis/Analysis.vue'),
    meta: { title: 'AI分析报告' }
  },
  {
    path: '/library',
    name: 'Library',
    component: () => import('@/views/library/Library.vue'),
    meta: { title: '素材库' }
  },
  {
    path: '/collector',
    name: 'Collector',
    component: () => import('@/views/collector/Collector.vue'),
    meta: { title: '数据采集' }
  },
  {
    path: '/collector/manual',
    name: 'ManualCollect',
    component: () => import('@/views/collector/ManualCollect.vue'),
    meta: { title: '手动采集' }
  },
  {
    path: '/monitor',
    name: 'Monitor',
    component: () => import('@/views/monitor/Monitor.vue'),
    meta: { title: '竞品监控' }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/reports/Reports.vue'),
    meta: { title: '趋势报告' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || '短剧爆款洞察平台'}`
  next()
})

export default router
