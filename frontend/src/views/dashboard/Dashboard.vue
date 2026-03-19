<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

// Placeholder data
const todayInsights = ref([
  { id: 1, type: 'warning', title: '美妆领域有1个话题正在起势', time: '10:30' },
  { id: 2, type: 'info', title: '您关注的达人发布了新视频', time: '09:15' }
])

const recentVideos = ref([
  { id: '1', title: '如何用3句话留住用户', views: 125000, likes: 8500 },
  { id: '2', title: '爆款视频的黄金3秒法则', views: 98000, likes: 6200 }
])

const competitors = ref([
  { id: 1, name: '美妆博主A', followers: '120W', latestVideo: '护肤教程', trend: 'up' },
  { id: 2, name: '剧情号B', followers: '85W', latestVideo: '反转剧情', trend: 'up' }
])

const handleAnalyze = (videoId: string) => {
  router.push(`/analysis?id=${videoId}`)
}

const goToMonitor = () => {
  router.push('/monitor')
}

const goToLibrary = () => {
  ElMessage.info('素材库功能开发中')
}
</script>

<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <h1>工作台</h1>
      <p class="subtitle">欢迎回来，这里是您的AI创意副驾</p>
    </div>

    <!-- Alert Section -->
    <el-row :gutter="20" class="alert-section">
      <el-col :span="24">
        <el-card class="alert-card">
          <template #header>
            <div class="card-header">
              <span class="title">今日洞察</span>
              <el-tag type="warning" size="small">实时更新</el-tag>
            </div>
          </template>
          <div class="alert-list">
            <div v-for="item in todayInsights" :key="item.id" class="alert-item">
              <el-icon><WarningFilled v-if="item.type === 'warning'" /><InfoFilled v-else /></el-icon>
              <span>{{ item.title }}</span>
              <span class="time">{{ item.time }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Actions -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :span="8">
        <el-card class="action-card" @click="goToLibrary">
          <div class="action-content">
            <el-icon size="40" color="#409eff"><Collection /></el-icon>
            <h3>爆款素材库</h3>
            <p>收藏的黄金3秒、脚本结构</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="action-card" @click="goToMonitor">
          <div class="action-content">
            <el-icon size="40" color="#67c23a"><DataAnalysis /></el-icon>
            <h3>竞品监控</h3>
            <p>追踪达人动态和趋势</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="action-card" @click="router.push('/reports')">
          <div class="action-content">
            <el-icon size="40" color="#e6a23c"><TrendCharts /></el-icon>
            <h3>趋势报告</h3>
            <p>周/月度行业趋势分析</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Videos & Competitors -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>热门爆款参考</span>
              <el-button type="primary" link>查看更多</el-button>
            </div>
          </template>
          <div class="video-list">
            <div v-for="video in recentVideos" :key="video.id" class="video-item" @click="handleAnalyze(video.id)">
              <div class="video-info">
                <h4>{{ video.title }}</h4>
                <p>播放: {{ (video.views / 10000).toFixed(1) }}万 | 点赞: {{ (video.likes / 10000).toFixed(1) }}万</p>
              </div>
              <el-button type="primary" size="small">分析</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>竞品最新动态</span>
              <el-button type="primary" link @click="goToMonitor">管理</el-button>
            </div>
          </template>
          <div class="competitor-list">
            <div v-for="comp in competitors" :key="comp.id" class="competitor-item">
              <div class="comp-info">
                <h4>{{ comp.name }}</h4>
                <p>粉丝: {{ comp.followers }} | 最新: {{ comp.latestVideo }}</p>
              </div>
              <el-icon v-if="comp.trend === 'up'" color="#67c23a"><Top /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 24px;

  h1 {
    font-size: 28px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .subtitle {
    color: var(--text-secondary);
  }
}

.alert-section {
  margin-bottom: 20px;
}

.alert-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .alert-list {
    .alert-item {
      display: flex;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--border-color);

      &:last-child {
        border-bottom: none;
      }

      .el-icon {
        margin-right: 12px;
      }

      .time {
        margin-left: auto;
        color: var(--text-secondary);
        font-size: 12px;
      }
    }
  }
}

.quick-actions {
  margin-bottom: 20px;

  .action-card {
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
  }

  .action-content {
    text-align: center;
    padding: 20px;

    h3 {
      margin: 12px 0 8px;
      font-size: 16px;
    }

    p {
      color: var(--text-secondary);
      font-size: 13px;
    }
  }
}

.video-list, .competitor-list {
  .video-item, .competitor-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;

    &:last-child {
      border-bottom: none;
    }

    &:hover {
      background-color: #f5f7fa;
      margin: 0 -20px;
      padding: 12px 20px;
    }
  }

  .video-info h4, .comp-info h4 {
    font-size: 14px;
    margin-bottom: 4px;
  }

  .video-info p, .comp-info p {
    font-size: 12px;
    color: var(--text-secondary);
  }
}
</style>
