<script setup lang="ts">
import { computed,ref } from 'vue'
import Settings from '@/views/settings/Settings.vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const settingsRef = ref()
const openSettings = () => settingsRef.value?.open()

const isLoginPage = computed(() => route.path === '/login')

const menuItems = [
  { path: '/', icon: 'House', label: '工作台' },
  { path: '/analysis', icon: 'DataAnalysis', label: 'AI分析报告' },
  { path: '/library', icon: 'Collection', label: '素材库' },
  { path: '/collector', icon: 'Upload', label: '数据采集' },
  { path: '/collector/manual', icon: 'Plus', label: '手动采集' },
  { path: '/monitor', icon: 'Monitor', label: '竞品监控' },
  { path: '/reports', icon: 'TrendCharts', label: '趋势报告' }
]

const handleCommand = (command: string) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      authStore.logout()
      router.push('/login')
    }).catch(() => {})
  }
  else if (command === 'profile') {
    openSettings()
  }
}
</script>

<template>
  <div class="app-container" v-if="!isLoginPage">
    <!-- Sidebar -->
    <el-aside width="220px" class="app-sidebar">
      <div class="logo">
        <h2>爆款洞察</h2>
      </div>
      <el-menu
        :default-active="route.path"
        class="sidebar-menu"
        router
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Main Content -->
    <el-container class="app-main">
      <!-- Header -->
      <el-header class="app-header">
        <div class="header-left">
          <h3>{{ route.meta.title || '短剧爆款洞察平台' }}</h3>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ authStore.userInfo?.nickname || authStore.userInfo?.username || '用户' }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Content -->
      <el-main class="app-content">
        <RouterView />
      </el-main>
    </el-container>
    <Settings ref="settingsRef" />
  </div>

  <!-- Login page doesn't have layout -->
  <RouterView v-else />
</template>

<style scoped lang="scss">
.app-container {
  display: flex;
  height: 100vh;
}

.app-sidebar {
  background-color: #304156;
  color: #fff;

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #263445;

    h2 {
      color: #fff;
      font-size: 18px;
      margin: 0;
    }
  }

  .sidebar-menu {
    border-right: none;
    background-color: #304156;

    :deep(.el-menu-item) {
      color: #bfcbd9;

      &:hover {
        background-color: #263445;
        color: #409eff;
      }

      &.is-active {
        background-color: #409eff;
        color: #fff;
      }
    }
  }
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;

  .header-left h3 {
    margin: 0;
    font-size: 16px;
    color: #333;
  }

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 8px 12px;
      border-radius: 4px;

      &:hover {
        background-color: #f5f7fa;
      }
    }
  }
}

.app-content {
  background-color: #f0f2f5;
  overflow-y: auto;
}
</style>
