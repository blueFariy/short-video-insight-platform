<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { collectorService, API_URL } from '@/api'

const router = useRouter()

// 今日洞察
const todayInsights = ref([
  { id: 1, type: 'warning', title: '美妆领域有1个话题正在起势', time: '10:30' },
  { id: 2, type: 'info', title: '您关注的达人发布了新视频', time: '09:15' }
])

// 热门爆款视频
const viralVideos = ref<any[]>([])

// 竞品动态
const competitors = ref([
  { id: 1, name: '美妆博主A', followers: '120W', latestVideo: '护肤教程', trend: 'up' },
  { id: 2, name: '剧情号B', followers: '85W', latestVideo: '反转剧情', trend: 'up' }
])

// 获取爆款视频列表
const fetchViralVideos = async () => {
  try {
    const res = await collectorService.get(API_URL.COLLECTOR.VIRAL_VIDEOS, {
      params: { limit: 3, min_play_count: 100000 }
    }) as any
    viralVideos.value = res.videos || []
  } catch (error) {
    console.error('获取爆款视频失败:', error)
    // 使用备用数据
    viralVideos.value = []
  }
}

// 点击视频跳转到平台
const handleVideoClick = (video: any) => {
  if (video.video_url) {
    window.open(video.video_url, '_blank')
  }
}

// 点击分析按钮，跳转到AI分析页面
const handleAnalyze = (video: any) => {
  const params = new URLSearchParams()
  params.set('platform', video.platform || '')
  params.set('url', video.video_url || '')
  router.push(`/analysis?${params.toString()}`)
}

// 查看更多跳转到数据采集的视频库
const goToCollector = () => {
  router.push('/collector')
}

const goToMonitor = () => {
  router.push('/monitor')
}

const goToLibrary = () => {
  ElMessage.info('素材库功能开发中')
}

// 平台标签
const getPlatformTag = (platform: string) => {
  const map: Record<string, { label: string; type: string }> = {
    douyin: { label: '抖音', type: 'danger' },
    bilibili: { label: 'B站', type: 'warning' },
    xiaohongshu: { label: '小红书', type: 'success' },
    kuaishou: { label: '快手', type: 'info' }
  }
  return map[platform] || { label: platform, type: 'info' }
}

// 格式化数字
const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  if (num >= 1000) return (num / 1000).toFixed(1) + '千'
  return num.toString()
}

onMounted(() => {
  fetchViralVideos()
})
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
              <el-button type="primary" link @click="goToCollector">查看更多</el-button>
            </div>
          </template>
          <div v-if="viralVideos.length === 0" class="empty-tip">
            暂无爆款视频数据，请先采集视频数据
          </div>
          <div v-else class="video-list">
            <div v-for="video in viralVideos" :key="video.id" class="video-item">
              <div class="video-info" @click="handleVideoClick(video)">
                <h4>{{ video.title }}</h4>
                <p>
                  <el-tag :type="getPlatformTag(video.platform).type" size="small">
                    {{ getPlatformTag(video.platform).label }}
                  </el-tag>
                  播放: {{ formatNumber(video.play_count) }} | 点赞: {{ formatNumber(video.like_count) }}
                </p>
              </div>
              <el-button type="primary" size="small" @click="handleAnalyze(video)">分析</el-button>
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
