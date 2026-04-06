<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reportService, API_URL } from '@/api'
import TrendChart from '@/components/reports/TrendChart.vue'

// 状态
const loading = ref(false)
const generating = ref(false)
const activeTab = ref('weekly')
const trendStatistics = ref<any>(null)
const viralTrends = ref<any>(null)
const trendReports = ref<any[]>([])
const selectedPlatform = ref<string | null>(null)
const daysRange = ref(7)

// 平台选项
const platformOptions = [
  { label: '全部平台', value: null },
  { label: '抖音', value: 'douyin' },
  { label: 'B站', value: 'bilibili' },
  { label: '小红书', value: 'xiaohongshu' },
  { label: '快手', value: 'kuaishou' }
]

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

// 过滤后的报告列表
const filteredReports = computed(() => {
  if (activeTab.value === 'all') {
    return trendReports.value
  }
  return trendReports.value.filter(r => r.report_type === activeTab.value)
})

// 获取趋势统计
async function fetchTrendStatistics() {
  try {
    loading.value = true
    const data = await reportService.get(API_URL.REPORT.TREND_STATISTICS, {
      params: {
        days: daysRange.value,
        platform: selectedPlatform.value
      }
    })
    trendStatistics.value = data
  } catch (error) {
    console.error('Failed to fetch trend statistics:', error)
    // 使用演示数据
    trendStatistics.value = getDemoStatistics()
  }
}

// 获取爆款趋势
async function fetchViralTrends() {
  try {
    const data = await reportService.get(API_URL.REPORT.TREND_VIRAL, {
      params: {
        days: daysRange.value,
        platform: selectedPlatform.value
      }
    })
    viralTrends.value = data
  } catch (error) {
    console.error('Failed to fetch viral trends:', error)
    viralTrends.value = getDemoViralTrends()
  }
}

// 获取报告列表
async function fetchTrendReports() {
  try {
    loading.value = true
    const response: any = await reportService.get(API_URL.REPORT.TREND_LIST, {
      params: {
        limit: 20
      }
    })
    // 处理响应数据，兼容不同响应格式
    if (Array.isArray(response)) {
      trendReports.value = response
    } else if (response && typeof response === 'object') {
      trendReports.value = response.reports || response.data || []
    } else {
      trendReports.value = []
    }
  } catch (error) {
    console.error('Failed to fetch trend reports:', error)
    trendReports.value = []
  } finally {
    loading.value = false
  }
}

// 生成报告
async function generateReport() {
  try {
    generating.value = true
    await ElMessageBox.confirm(
      `确定要生成 ${reportTypeMap[activeTab.value] || '趋势'} 报告吗？`,
      '生成报告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    await reportService.post(API_URL.REPORT.TREND_GENERATE, {
      type: activeTab.value === 'all' ? 'weekly' : activeTab.value,
      platform: selectedPlatform.value
    })

    ElMessage.success('报告生成成功')
    await fetchTrendReports()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to generate report:', error)
      ElMessage.error('报告生成失败')
    }
  } finally {
    generating.value = false
  }
}

// 查看报告详情
function viewReportDetail(reportId: number) {
  // 跳转到报告详情页
  window.location.href = `/reports/detail/${reportId}`
}

// 演示数据
function getDemoStatistics() {
  return {
    period_days: daysRange.value,
    total_videos: 1250,
    total_views: 50000000,
    total_likes: 2500000,
    views_growth: 15.2,
    platforms: [
      { platform: 'douyin', video_count: 500, total_views: 20000000 },
      { platform: 'bilibili', video_count: 350, total_views: 15000000 },
      { platform: 'xiaohongshu', video_count: 250, total_views: 10000000 },
      { platform: 'kuaishou', video_count: 150, total_views: 5000000 }
    ],
    categories: [
      { category: '美食', video_count: 320 },
      { category: '美妆', video_count: 280 },
      { category: '知识', video_count: 220 },
      { category: '科技', video_count: 180 },
      { category: '搞笑', video_count: 150 }
    ],
    daily_data: generateDailyData(daysRange.value)
  }
}

function getDemoViralTrends() {
  return {
    total_alerts: 48,
    alerts_by_level: { yellow: 30, orange: 15, red: 3 },
    alerts_by_platform: { douyin: 20, bilibili: 15, xiaohongshu: 10, kuaishou: 3 }
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

// 刷新数据
async function refreshData() {
  await Promise.all([
    fetchTrendStatistics(),
    fetchViralTrends(),
    fetchTrendReports()
  ])
}

// 监听筛选条件变化
function onFilterChange() {
  refreshData()
}

onMounted(() => {
  refreshData()
})
</script>

<template>
  <div class="trend-reports">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>趋势洞察</h2>
        <p>实时追踪短视频行业趋势，抢占流量先机</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedPlatform" placeholder="选择平台" clearable @change="onFilterChange">
          <el-option
            v-for="item in platformOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-select v-model="daysRange" placeholder="时间范围" @change="onFilterChange">
          <el-option :value="7" label="近7天" />
          <el-option :value="14" label="近14天" />
          <el-option :value="30" label="近30天" />
        </el-select>
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计概览卡片 -->
    <div class="statistics-overview" v-if="trendStatistics">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #409eff20;">
                <el-icon size="24" color="#409eff"><VideoPlay /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">视频总数</span>
                <span class="stat-value">{{ trendStatistics.total_videos?.toLocaleString() || 0 }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #67c23a20;">
                <el-icon size="24" color="#67c23a"><View /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">总播放量</span>
                <span class="stat-value">{{ (trendStatistics.total_views / 10000).toFixed(0) }}万</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #e6a23c20;">
                <el-icon size="24" color="#e6a23c"><TrendCharts /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">播放增长</span>
                <span class="stat-value" :class="trendStatistics.views_growth >= 0 ? 'positive' : 'negative'">
                  {{ trendStatistics.views_growth >= 0 ? '+' : '' }}{{ trendStatistics.views_growth }}%
                </span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background: #f56c6c20;">
                <el-icon size="24" color="#f56c6c"><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <span class="stat-label">爆款预警</span>
                <span class="stat-value">{{ viralTrends?.total_alerts || 0 }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 趋势图表 -->
    <div class="chart-section" v-if="trendStatistics">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>趋势走势</span>
          </div>
        </template>
        <TrendChart :data="trendStatistics.daily_data" />
      </el-card>
    </div>

    <!-- 平台分布 & 分类分布 -->
    <el-row :gutter="16" class="distribution-section" v-if="trendStatistics">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>平台分布</span>
            </div>
          </template>
          <div class="platform-list">
            <div
              v-for="item in trendStatistics.platforms"
              :key="item.platform"
              class="platform-item"
            >
              <div class="platform-info">
                <span class="platform-name">{{ platformMap[item.platform] || item.platform }}</span>
                <span class="platform-count">{{ item.video_count }} 个视频</span>
              </div>
              <el-progress
                :percentage="Math.round((item.total_views / (trendStatistics.total_views || 1)) * 100)"
                :stroke-width="8"
                :show-text="true"
              />
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>热门分类</span>
            </div>
          </template>
          <div class="category-list">
            <div
              v-for="(item, index) in trendStatistics.categories"
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

    <!-- 报告列表 -->
    <div class="reports-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>趋势报告</span>
            <el-button
              type="primary"
              size="small"
              @click="generateReport"
              :loading="generating"
            >
              生成报告
            </el-button>
          </div>
        </template>

        <!-- 报告标签页 -->
        <el-tabs v-model="activeTab" class="report-tabs">
          <el-tab-pane label="全部" name="all" />
          <el-tab-pane label="周报" name="weekly" />
          <el-tab-pane label="月报" name="monthly" />
          <el-tab-pane label="日报" name="daily" />
        </el-tabs>

        <!-- 报告列表 -->
        <div class="report-list">
          <el-empty v-if="filteredReports.length === 0" description="暂无报告" />

          <div
            v-for="report in filteredReports"
            :key="report.id"
            class="report-item"
            @click="viewReportDetail(report.id)"
          >
            <div class="report-icon">
              <el-icon size="28" :color="report.report_type === 'monthly' ? '#67c23a' : '#409eff'">
                <Document />
              </el-icon>
            </div>
            <div class="report-content">
              <h4>{{ report.title }}</h4>
              <div class="report-meta">
                <el-tag size="small" :type="report.report_type === 'monthly' ? 'success' : 'primary'">
                  {{ reportTypeMap[report.report_type] || report.report_type }}
                </el-tag>
                <span class="report-period">{{ report.period_start }} ~ {{ report.period_end }}</span>
                <span class="report-date">{{ report.created_at }}</span>
              </div>
            </div>
            <el-button type="primary" text>
              查看详情
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped lang="scss">
.trend-reports {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  .header-left {
    h2 {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 8px;
    }

    p {
      color: var(--el-text-color-secondary);
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.statistics-overview {
  margin-bottom: 20px;

  .stat-card {
    :deep(.el-card__body) {
      padding: 16px;
    }
  }

  .stat-content {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .stat-info {
    display: flex;
    flex-direction: column;
  }

  .stat-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-bottom: 4px;
  }

  .stat-value {
    font-size: 24px;
    font-weight: 600;

    &.positive {
      color: #67c23a;
    }

    &.negative {
      color: #f56c6c;
    }
  }
}

.chart-section {
  margin-bottom: 20px;
}

.distribution-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.platform-list {
  .platform-item {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .platform-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;

    .platform-name {
      font-weight: 500;
    }

    .platform-count {
      color: var(--el-text-color-secondary);
      font-size: 13px;
    }
  }
}

.category-list {
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
    font-weight: 500;
  }

  .category-count {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }
}

.report-list {
  .report-item {
    display: flex;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    cursor: pointer;
    transition: background-color 0.2s;

    &:hover {
      background-color: var(--el-fill-color-light);
    }

    &:last-child {
      border-bottom: none;
    }
  }

  .report-icon {
    margin-right: 16px;
  }

  .report-content {
    flex: 1;

    h4 {
      font-size: 15px;
      margin-bottom: 8px;
    }

    .report-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 13px;
      color: var(--el-text-color-secondary);

      .report-period,
      .report-date {
        &::before {
          content: '|';
          margin-right: 12px;
          color: var(--el-border-color);
        }
      }
    }
  }
}

.report-tabs {
  :deep(.el-tabs__content) {
    padding-top: 16px;
  }
}
</style>
