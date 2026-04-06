<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { reportService, API_URL } from '@/api'
import TrendChart from '@/components/reports/TrendChart.vue'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(false)
const report = ref<any>(null)
const reportId = computed(() => Number(route.params.id))

// 平台映射
const platformMap: Record<string, string> = {
  douyin: '抖音',
  bilibili: 'B站',
  xiaohongshu: '小红书',
  kuaishou: '快手'
}

// 报告类型映射
const reportTypeMap: Record<string, string> = {
  daily: '日报',
  weekly: '周报',
  monthly: '月报'
}

// 获取报告详情
async function fetchReportDetail() {
  if (!reportId.value) return

  try {
    loading.value = true
    const data = await reportService.get(API_URL.REPORT.TREND_DETAIL(reportId.value))
    report.value = data
  } catch (error) {
    console.error('Failed to fetch report detail:', error)
    // 使用演示数据
    report.value = getDemoReport()
  } finally {
    loading.value = false
  }
}

// 演示数据
function getDemoReport() {
  return {
    id: reportId.value,
    report_type: 'weekly',
    title: `2024年第11周趋势报告`,
    summary: {
      total_videos: 1250,
      total_views: 50000000,
      views_growth: 15.2,
      total_viral_alerts: 48
    },
    period_start: '2024-03-11',
    period_end: '2024-03-17',
    hot_topics: [
      '美食探店 (12个爆款)',
      '美妆教程 (10个爆款)',
      '知识科普 (8个爆款)',
      '搞笑剧情 (6个爆款)',
      '科技评测 (5个爆款)'
    ],
    ai_insights: [
      '本周美食类内容增长显著，探店类视频平均播放量较上周提升 23%',
      '美妆教程类视频互动率高，适合做深度内容运营',
      '知识科普类视频在小红书平台表现突出',
      '建议关注剧情反转类内容，用户完播率高'
    ],
    platform_stats: [
      { platform: 'douyin', video_count: 500, total_views: 20000000 },
      { platform: 'bilibili', video_count: 350, total_views: 15000000 },
      { platform: 'xiaohongshu', video_count: 250, total_views: 10000000 },
      { platform: 'kuaishou', video_count: 150, total_views: 5000000 }
    ],
    category_stats: [
      { category: '美食', video_count: 320 },
      { category: '美妆', video_count: 280 },
      { category: '知识', video_count: 220 },
      { category: '科技', video_count: 180 },
      { category: '搞笑', video_count: 150 }
    ],
    daily_trends: generateDailyData(7),
    viral_trends: {
      by_level: { yellow: 30, orange: 15, red: 3 },
      by_platform: { douyin: 20, bilibili: 15, xiaohongshu: 10, kuaishou: 3 },
      recent_videos: [
        { video_id: '1', title: '探店北京网红餐厅，排队2小时值不值？', platform: 'douyin', alert_level: 'red' },
        { video_id: '2', title: '新手化妆教程，学会这三点就够了', platform: 'xiaohongshu', alert_level: 'orange' },
        { video_id: '3', title: 'AI如何改变我们的生活', platform: 'bilibili', alert_level: 'yellow' }
      ]
    },
    content_trends: {
      rising_categories: ['美食探店', '美妆教程', '知识科普'],
      declining_categories: ['游戏实况', '明星娱乐'],
      trending_topics: ['春季穿搭', '减脂餐', '职场技能']
    },
    created_at: '2024-03-18T08:00:00'
  }
}

function generateDailyData(days: number) {
  const data = []
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    data.push({
      date: date.toISOString().split('T')[0],
      video_count: 30 + Math.floor(Math.random() * 20),
      total_views: 1500000 + Math.floor(Math.random() * 500000),
      total_likes: 75000 + Math.floor(Math.random() * 25000)
    })
  }
  return data
}

// 返回列表
function goBack() {
  router.push('/reports')
}

onMounted(() => {
  fetchReportDetail()
})
</script>

<template>
  <div class="report-detail" v-loading="loading">
    <!-- 返回按钮 -->
    <div class="back-action">
      <el-button @click="goBack" text>
        <el-icon><ArrowLeft /></el-icon>
        返回报告列表
      </el-button>
    </div>

    <!-- 报告头部 -->
    <el-card class="report-header" v-if="report">
      <div class="header-content">
        <div class="header-info">
          <el-tag :type="report.report_type === 'monthly' ? 'success' : 'primary'" size="large">
            {{ reportTypeMap[report.report_type] || report.report_type }}
          </el-tag>
          <h1>{{ report.title }}</h1>
          <p class="report-period">
            报告周期：{{ report.period_start }} ~ {{ report.period_end }}
          </p>
          <p class="report-time">
            生成时间：{{ report.created_at }}
          </p>
        </div>
      </div>
    </el-card>

    <!-- 核心数据 -->
    <el-row :gutter="16" class="core-metrics" v-if="report">
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-value">{{ report.summary?.total_videos?.toLocaleString() || 0 }}</div>
          <div class="metric-label">视频总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-value">{{ ((report.summary?.total_views || 0) / 10000).toFixed(0) }}万</div>
          <div class="metric-label">总播放量</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-value" :class="{ positive: report.summary?.views_growth >= 0, negative: report.summary?.views_growth < 0 }">
            {{ report.summary?.views_growth >= 0 ? '+' : '' }}{{ report.summary?.views_growth }}%
          </div>
          <div class="metric-label">播放增长</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-value">{{ report.summary?.total_viral_alerts || 0 }}</div>
          <div class="metric-label">爆款预警</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 趋势图表 -->
    <el-card class="trend-chart-card" v-if="report">
      <template #header>
        <span>每日趋势</span>
      </template>
      <TrendChart :data="report.daily_trends" height="350px" />
    </el-card>

    <!-- AI 洞察 -->
    <el-card class="insights-card" v-if="report?.ai_insights?.length">
      <template #header>
        <div class="card-header">
          <span>
            <el-icon><ChatDotRound /></el-icon>
            AI 洞察分析
          </span>
        </div>
      </template>
      <div class="insights-list">
        <div v-for="(insight, index) in report.ai_insights" :key="index" class="insight-item">
          <div class="insight-icon">
            <el-icon size="20"><Sunrise /></el-icon>
          </div>
          <div class="insight-content">{{ insight }}</div>
        </div>
      </div>
    </el-card>

    <!-- 热点话题 -->
    <el-card class="hot-topics-card" v-if="report?.hot_topics?.length">
      <template #header>
        <span>
          <el-icon><Star /></el-icon>
          热点话题
        </span>
      </template>
      <div class="hot-topics">
        <el-tag
          v-for="(topic, index) in report.hot_topics"
          :key="index"
          :type="index < 2 ? 'danger' : 'warning'"
          size="large"
          class="topic-tag"
        >
          {{ topic }}
        </el-tag>
      </div>
    </el-card>

    <!-- 平台分布 & 分类统计 -->
    <el-row :gutter="16" v-if="report">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>平台分布</span>
          </template>
          <div class="platform-stats">
            <div
              v-for="item in report.platform_stats"
              :key="item.platform"
              class="stat-item"
            >
              <div class="stat-header">
                <span class="stat-name">{{ platformMap[item.platform] || item.platform }}</span>
                <span class="stat-value">{{ item.video_count }} 个视频</span>
              </div>
              <el-progress
                :percentage="Math.round((item.total_views / (report.summary?.total_views || 1)) * 100)"
                :stroke-width="10"
                :show-text="true"
              />
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>分类统计</span>
          </template>
          <div class="category-stats">
            <div
              v-for="(item, index) in report.category_stats"
              :key="item.category"
              class="category-item"
            >
              <span class="category-rank" :class="{ top: index < 3 }">{{ index + 1 }}</span>
              <span class="category-name">{{ item.category }}</span>
              <span class="category-count">{{ item.video_count }} 个视频</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 爆款趋势 -->
    <el-card class="viral-trends-card" v-if="report">
      <template #header>
        <span>
          <el-icon><Warning /></el-icon>
          爆款趋势
        </span>
      </template>
      <el-row :gutter="16">
        <el-col :span="12">
          <h4>预警等级分布</h4>
          <div class="level-distribution">
            <div class="level-item">
              <el-tag type="warning" size="large">黄色预警</el-tag>
              <span class="level-count">{{ report.viral_trends?.by_level?.yellow || 0 }} 个</span>
            </div>
            <div class="level-item">
              <el-tag type="danger" size="large">橙色预警</el-tag>
              <span class="level-count">{{ report.viral_trends?.by_level?.orange || 0 }} 个</span>
            </div>
            <div class="level-item">
              <el-tag type="danger" effect="dark" size="large">红色预警</el-tag>
              <span class="level-count">{{ report.viral_trends?.by_level?.red || 0 }} 个</span>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <h4>爆款视频 TOP 3</h4>
          <div class="viral-videos">
            <div
              v-for="video in report.viral_trends?.recent_videos?.slice(0, 3)"
              :key="video.video_id"
              class="viral-video-item"
            >
              <el-tag
                :type="video.alert_level === 'red' ? 'danger' : video.alert_level === 'orange' ? 'warning' : 'info'"
                size="small"
              >
                {{ video.alert_level === 'red' ? '爆' : video.alert_level === 'orange' ? '热' : '新' }}
              </el-tag>
              <span class="video-title">{{ video.title }}</span>
              <span class="video-platform">{{ platformMap[video.platform] || video.platform }}</span>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 内容趋势 -->
    <el-card class="content-trends-card" v-if="report?.content_trends">
      <template #header>
        <span>
          <el-icon><TrendCharts /></el-icon>
          内容趋势
        </span>
      </template>
      <el-row :gutter="24">
        <el-col :span="8">
          <h4>
            <el-icon color="#67c23a"><Top /></el-icon>
            上升分类
          </h4>
          <div class="trend-list rising">
            <el-tag
              v-for="(cat, index) in report.content_trends?.rising_categories"
              :key="index"
              type="success"
              effect="plain"
            >
              {{ cat }}
            </el-tag>
          </div>
        </el-col>
        <el-col :span="8">
          <h4>
            <el-icon color="#909399"><Bottom /></el-icon>
            下降分类
          </h4>
          <div class="trend-list declining">
            <el-tag
              v-for="(cat, index) in report.content_trends?.declining_categories"
              :key="index"
              type="info"
              effect="plain"
            >
              {{ cat }}
            </el-tag>
          </div>
        </el-col>
        <el-col :span="8">
          <h4>
            <el-icon color="#409eff"><TrendCharts /></el-icon>
            热门话题
          </h4>
          <div class="trend-list trending">
            <el-tag
              v-for="(topic, index) in report.content_trends?.trending_topics"
              :key="index"
              type="primary"
            >
              {{ topic }}
            </el-tag>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.report-detail {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.back-action {
  margin-bottom: 20px;
}

.report-header {
  margin-bottom: 20px;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .header-info {
    h1 {
      font-size: 24px;
      margin: 12px 0;
    }

    .report-period,
    .report-time {
      color: var(--el-text-color-secondary);
      font-size: 14px;
      margin: 4px 0;
    }
  }
}

.core-metrics {
  margin-bottom: 20px;

  .metric-card {
    text-align: center;
    padding: 16px 0;

    .metric-value {
      font-size: 28px;
      font-weight: 600;
      color: var(--el-text-color-primary);

      &.positive {
        color: #67c23a;
      }

      &.negative {
        color: #f56c6c;
      }
    }

    .metric-label {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin-top: 8px;
    }
  }
}

.trend-chart-card,
.insights-card,
.hot-topics-card,
.viral-trends-card,
.content-trends-card {
  margin-bottom: 20px;
}

.insights-list {
  .insight-item {
    display: flex;
    gap: 16px;
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }
  }

  .insight-icon {
    color: #409eff;
    flex-shrink: 0;
  }

  .insight-content {
    font-size: 15px;
    line-height: 1.6;
    color: var(--el-text-color-primary);
  }
}

.hot-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;

  .topic-tag {
    font-size: 14px;
    padding: 8px 16px;
  }
}

.platform-stats {
  .stat-item {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .stat-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;

    .stat-name {
      font-weight: 500;
    }

    .stat-value {
      color: var(--el-text-color-secondary);
    }
  }
}

.category-stats {
  .category-item {
    display: flex;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }
  }

  .category-rank {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--el-fill-color);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    margin-right: 12px;

    &.top {
      background: #409eff;
      color: white;
    }
  }

  .category-name {
    flex: 1;
  }

  .category-count {
    color: var(--el-text-color-secondary);
  }
}

.viral-trends-card {
  h4 {
    margin-bottom: 16px;
    font-size: 15px;
  }

  .level-distribution {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .level-item {
    display: flex;
    align-items: center;
    gap: 12px;

    .level-count {
      font-weight: 500;
    }
  }

  .viral-videos {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .viral-video-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    background: var(--el-fill-color-light);
    border-radius: 8px;

    .video-title {
      flex: 1;
      font-size: 14px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .video-platform {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.content-trends-card {
  h4 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    font-size: 15px;
  }

  .trend-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
