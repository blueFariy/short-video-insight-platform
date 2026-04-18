<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { collectorService, API_URL } from '@/api'
import { Refresh, List, Grid } from '@element-plus/icons-vue'

const router = useRouter()

// WebSocket连接
let ws: WebSocket | null = null

// 今日洞察 - 从 viral_alerts 获取
const todayInsights = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(12)
const totalCount = ref(0)

// 筛选条件
const filterIsRead = ref<boolean | ''>('')
const filterAlertLevel = ref('')
const filterCategories = ref<string[]>([])  // 存储查询用的叶子节点值数组
const filterCategoriesPath = ref<string[][]>([])  // 存储级联选择器的嵌套路径
const filterPlatform = ref('')
const filterKeyword = ref('')
const filterDateRange = ref<[string, string] | null>(null)  // 时间范围筛选 (格式: YYYY-MM-DD HH:mm:ss)
const sortOrder = ref<'desc' | 'asc'>('desc')

// 分类选项（级联选择器）- 从后端获取
const categoryOptions = ref<any[]>([])
// 用户兴趣配置
const userInterestCategories = ref<string[]>([])
// 刷新状态
const isRefreshing = ref(false)
// 视图模式：list 或 card
const viewMode = ref<'list' | 'card'>('list')
// 每页条数选项
const pageSizes = [12, 24, 36, 48, 60, 72, 84, 96]

// 获取用户兴趣配置
const fetchUserInterest = async () => {
  try {
    const data = await collectorService.get(API_URL.COLLECTOR.USER_INTEREST_GET) as any
    // collectorService interceptor 返回的是 res.data，所以 data 已经是 {category_weights: {...}, ...} 格式
    if (data && data.category_weights && typeof data.category_weights === 'object') {
      userInterestCategories.value = Object.keys(data.category_weights)
      console.log('用户兴趣分类:', userInterestCategories.value)
    }
  } catch (error) {
    console.error('获取用户兴趣配置失败:', error)
    userInterestCategories.value = []
  }
}

// 获取分类树并根据用户兴趣过滤
const fetchCategories = async () => {
  try {
    // collectorService response interceptor already returns res.data, so res is the data directly
    const data = await collectorService.get(API_URL.COLLECTOR.CATEGORIES) as any
    if (data && Array.isArray(data)) {
      // 根据用户兴趣过滤分类
      if (userInterestCategories.value.length > 0) {
        // 收集所有主分类名称，用于排除本身就是独立主分类的子分类
        const mainCategoryNames = new Set(data.map((c: any) => c.value))

        const filtered = data
          .map((category: any) => {
            // 1. 如果主分类在用户兴趣中，显示整个分类及其所有子分类
            if (userInterestCategories.value.includes(category.value)) {
              return category
            }
            // 2. 如果主分类不在用户兴趣中，检查是否有子分类在用户兴趣中
            // 但要排除那些本身就是独立主分类的子分类
            const matchingChildren = category.children?.filter(
              (child: any) =>
                userInterestCategories.value.includes(child.value) &&
                !mainCategoryNames.has(child.value)  // 排除本身就是独立主分类的子分类
            )
            // 如果有匹配的子分类，只返回包含这些子分类的分类（去重子分类）
            if (matchingChildren && matchingChildren.length > 0) {
              return {
                ...category,
                children: matchingChildren
              }
            }
            return null
          })
          .filter((c: any) => c !== null)

        categoryOptions.value = filtered
      } else {
        categoryOptions.value = data
      }
    }
  } catch (error) {
    console.error('获取分类树失败:', error)
    // 备用本地数据
    categoryOptions.value = [
      { label: '动画', value: '动画', children: [
        { label: 'MAD·AMV', value: 'MAD·AMV' },
        { label: 'MMD·3D', value: 'MMD·3D' },
        { label: '同人·手书', value: '同人·手书' }
      ]},
      { label: '音乐', value: '音乐', children: [
        { label: '原创音乐', value: '原创音乐' },
        { label: '音乐现场', value: '音乐现场' }
      ]}
    ]
  }
}

// 弹窗相关
const alertDialogVisible = ref(false)
const currentAlert = ref<any>({})

// 获取今日洞察数据（从 viral_alerts 表）
const fetchTodayInsights = async () => {
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
      sort_order: sortOrder.value
    }
    if (filterAlertLevel.value) {
      params.alert_level = filterAlertLevel.value
    }
    if (filterCategories.value.length > 0) {
      // 直接使用展开后的叶子节点值数组
      params.categories = filterCategories.value.join(',')
    }
    if (filterPlatform.value) {
      params.platform = filterPlatform.value
    }
    if (filterIsRead.value !== '') {
      params.is_read = filterIsRead.value
    }
    if (filterKeyword.value) {
      params.keyword = filterKeyword.value
    }
    // 时间范围筛选（精确到小时）
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      params.start_time = filterDateRange.value[0]
      params.end_time = filterDateRange.value[1]
    }

    const res = await collectorService.get(API_URL.COLLECTOR.ALERTS, {
      params
    }) as any
    let alerts = res.items || []
    totalCount.value = res.total || 0

    // 转换为今日洞察格式
    todayInsights.value = alerts.map((alert: any) => ({
      id: alert.id,
      type: alert.alert_level,
      alert_level: alert.alert_level,
      platform: alert.platform,
      category: alert.category,
      title: alert.title,
      coverUrl: alert.cover_url,
      url: alert.video_url,
      factors: alert.factors || [],
      time: alert.created_at ? alert.created_at.replace('T', ' ').substring(0, 16) : '',
      created_at: alert.created_at,
      is_read: alert.is_read || false
    }))
  } catch (error) {
    console.error('获取今日洞察失败:', error)
  }
}

// 分类筛选变化
const handleCategoryChange = (paths: string[][]) => {
  // 获取当前所有主分类
  const mainCategories = categoryOptions.value.map((opt: any) => opt.value)

  // 计算每个主分类下已选中的子分类数量
  const mainCategoryStatus = new Map<string, { total: number; selected: number }>()

  // 初始化主分类状态
  for (const mainCategory of mainCategories) {
    const mainOption = categoryOptions.value.find((opt: any) => opt.value === mainCategory)
    const totalChildren = mainOption?.children?.length || 0
    mainCategoryStatus.set(mainCategory, { total: totalChildren, selected: 0 })
  }

  // 统计已选中的子分类
  for (const path of paths) {
    if (path.length === 2) {
      const mainCategory = path[0]
      const status = mainCategoryStatus.get(mainCategory)
      if (status) {
        status.selected++
      }
    }
  }

  // 处理联动逻辑
  let newPaths = [...paths]

  // 检查每个主分类的选中状态，决定是否自动添加/移除主分类
  for (const [mainCategory, status] of mainCategoryStatus.entries()) {
    const isMainSelected = paths.some(path => path.length === 1 && path[0] === mainCategory)

    if (status.total > 0) {
      if (status.selected === status.total && !isMainSelected) {
        // 所有子分类都被选中了，但主分类未选中 -> 自动添加主分类
        newPaths.push([mainCategory])
      } else if (status.selected < status.total && isMainSelected) {
        // 不是所有子分类都被选中，但主分类被选中了 -> 自动移除主分类
        const mainIndex = newPaths.findIndex(path => path.length === 1 && path[0] === mainCategory)
        if (mainIndex !== -1) {
          newPaths.splice(mainIndex, 1)
        }
      }
    }
  }

  // 去重处理
  const uniquePaths = newPaths.filter((path, index, self) =>
    index === self.findIndex(p =>
      p.length === path.length &&
      p.every((val, i) => val === path[i])
    )
  )

  // 更新显示值
  filterCategoriesPath.value = uniquePaths

  // 展开所有选中的分类用于查询
  const expandedCategories: string[] = []

  for (const path of uniquePaths) {
    if (path.length === 1) {
      // 主分类 - 展开为所有子分类
      const mainCategory = path[0]
      const mainOption = categoryOptions.value.find((opt: any) => opt.value === mainCategory)
      if (mainOption && mainOption.children && mainOption.children.length > 0) {
        for (const child of mainOption.children) {
          if (!expandedCategories.includes(child.value)) {
            expandedCategories.push(child.value)
          }
        }
      } else {
        if (!expandedCategories.includes(mainCategory)) {
          expandedCategories.push(mainCategory)
        }
      }
    } else {
      // 子分类 - 直接添加
      const leafValue = path[path.length - 1]
      if (!expandedCategories.includes(leafValue)) {
        expandedCategories.push(leafValue)
      }
    }
  }

  filterCategories.value = expandedCategories
  currentPage.value = 1
  fetchTodayInsights()
}

// 筛选变化
const handleFilterChange = () => {
  currentPage.value = 1
  fetchTodayInsights()
}

// 翻页
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchTodayInsights()
}

// 连接 WebSocket
const connectWebSocket = () => {
  const wsUrl = `ws://data_collector/api/v1/ws/viral-alerts`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket connected')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'viral_alert') {
        // 添加新预警到列表顶部
        const alert = data.data
        const now = new Date().toISOString()
        todayInsights.value.unshift({
          id: alert.id,
          type: alert.alert_level,
          alert_level: alert.alert_level,
          platform: alert.platform,
          title: alert.title,
          url: alert.url,
          factors: alert.factors || [],
          time: now.replace('T', ' ').substring(0, 16),
          created_at: now
        })

        // 展示消息通知
        showNotification(alert)
      }
    } catch (e) {
      console.error('Parse WebSocket message failed:', e)
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  ws.onclose = () => {
    console.log('WebSocket disconnected, reconnecting...')
    // 重新连接
    setTimeout(connectWebSocket, 3000)
  }
}

// 显示桌面通知
const showNotification = (alert: any) => {
  const typeMap: Record<string, 'warning' | 'info'> = {
    red: 'warning',
    orange: 'warning',
    yellow: 'info'
  }
  ElMessage({
    message: `【${getAlertLevelText(alert.alert_level)}】${alert.platform} - ${alert.title.substring(0, 20)}`,
    type: typeMap[alert.alert_level] || 'info',
    duration: 5000
  })
}

// 获取预警级别文本
const getAlertLevelText = (level: string) => {
  const map: Record<string, string> = {
    red: '红色预警',
    orange: '橙色预警',
    yellow: '黄色预警'
  }
  return map[level] || level
}

// 点击洞察项
const handleInsightClick = async (item: any) => {
  currentAlert.value = item
  alertDialogVisible.value = true

  // 标记为已读（如果未读）
  if (!item.is_read) {
    try {
      await collectorService.post(`${API_URL.COLLECTOR.ALERTS}/${item.id}/read`)
      // 更新本地状态
      item.is_read = true
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }
}

// 打开视频链接
const openVideoUrl = (url: string) => {
  if (url) {
    window.open(url, '_blank')
  }
}

// 图片加载失败处理
const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

// 获取代理后的图片URL
const getProxyImageUrl = (url: string) => {
  if (!url) return ''
  return `/collector/proxy/image?url=${encodeURIComponent(url)}`
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

// 预警级别标签
const getAlertLevelTag = (level: string) => {
  const map: Record<string, string> = {
    red: 'danger',
    orange: 'warning',
    yellow: 'info'
  }
  return map[level] || 'info'
}

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

// 格式化数字
const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num.toString()
}

// 刷新今日洞察
const handleRefresh = async () => {
  isRefreshing.value = true
  try {
    await fetchTodayInsights()
    ElMessage.success('刷新成功')
  } catch (error) {
    console.error('刷新失败:', error)
    ElMessage.error('刷新失败')
  } finally {
    isRefreshing.value = false
  }
}

onMounted(async () => {
  // 先获取用户兴趣配置
  await fetchUserInterest()
  // 再获取分类树（根据用户兴趣过滤）
  await fetchCategories()
  // 获取今日洞察和爆款视频
  fetchTodayInsights()
  fetchViralVideos()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
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
          <!-- 筛选器 -->
          <div class="filter-bar">
            <el-select v-model="filterIsRead" placeholder="已读状态" clearable @change="handleFilterChange" style="width: 100px">
              <el-option label="未读" :value="false" />
              <el-option label="已读" :value="true" />
            </el-select>
            <el-select v-model="filterAlertLevel" placeholder="预警颜色" clearable @change="handleFilterChange" style="width: 120px">
              <el-option label="黄色预警" value="yellow" />
              <el-option label="橙色预警" value="orange" />
              <el-option label="红色预警" value="red" />
            </el-select>
            <el-select v-model="filterPlatform" placeholder="平台" clearable @change="handleFilterChange" style="width: 100px">
              <el-option label="抖音" value="douyin" />
              <el-option label="B站" value="bilibili" />
              <el-option label="小红书" value="xiaohongshu" />
            </el-select>
            <el-cascader
              v-model="filterCategoriesPath"
              :options="categoryOptions"
              :props="{ multiple: true, checkStrictly: false, emitPath: true }"
              placeholder="分类筛选"
              clearable
              @change="handleCategoryChange"
              style="width: 220px"
            />
            <el-input v-model="filterKeyword" placeholder="关键词搜索" clearable @change="handleFilterChange" style="width: 150px" />
            <el-date-picker
              v-model="filterDateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DD HH:mm:ss"
              clearable
              @change="handleFilterChange"
              style="width: 340px"
            />
            <el-radio-group v-model="sortOrder" @change="handleFilterChange">
              <el-radio-button value="desc">最新优先</el-radio-button>
              <el-radio-button value="asc">最旧优先</el-radio-button>
            </el-radio-group>
            <el-button type="primary" :icon="Refresh" :loading="isRefreshing" @click="handleRefresh" circle title="刷新今日洞察" />
            <el-button-group>
              <el-button :type="viewMode === 'list' ? 'primary' : 'default'" :icon="List" @click="viewMode = 'list'" title="列表视图" />
              <el-button :type="viewMode === 'card' ? 'primary' : 'default'" :icon="Grid" @click="viewMode = 'card'" title="卡片视图" />
            </el-button-group>
          </div>
          <!-- 列表视图 -->
          <div v-if="viewMode === 'list'" class="alert-list">
            <div v-for="item in todayInsights" :key="item.id" class="alert-item" @click="handleInsightClick(item)">
              <el-tag v-if="item.is_read" type="success" size="small">已读</el-tag>
              <el-tag :type="getAlertLevelTag(item.type)" size="small">
                {{ getAlertLevelText(item.type) }}
              </el-tag>
              <el-tag :type="getPlatformTag(item.platform).type" size="small">
                {{ getPlatformTag(item.platform).label }}
              </el-tag>
              <el-tag v-if="item.category" type="info" size="small">
                {{ item.category }}
              </el-tag>
              <span class="alert-title">{{ item.title }}</span>
              <span class="time">{{ item.time }}</span>
              <a class="open-link" @click.stop="openVideoUrl(item.url)">打开链接</a>
            </div>
            <!-- 翻页 -->
            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="pageSizes"
                :total="totalCount"
                layout="prev, pager, next, sizes"
                @current-change="handlePageChange"
                @size-change="handleFilterChange"
              />
            </div>
          </div>
          <!-- 卡片视图 -->
          <div v-else class="alert-card-grid">
            <div v-for="item in todayInsights" :key="item.id" class="alert-card-item" @click="handleInsightClick(item)">
              <div class="card-cover" v-if="item.coverUrl">
                <img :src="getProxyImageUrl(item.coverUrl)" alt="封面" @error="handleImageError" />
              </div>
              <div class="card-content">
                <div class="card-tags">
                  <el-tag v-if="item.is_read" type="success" size="small">已读</el-tag>
                  <el-tag :type="getAlertLevelTag(item.type)" size="small">
                    {{ getAlertLevelText(item.type) }}
                  </el-tag>
                  <el-tag :type="getPlatformTag(item.platform).type" size="small">
                    {{ getPlatformTag(item.platform).label }}
                  </el-tag>
                  <el-tag v-if="item.category" type="info" size="small">
                    {{ item.category }}
                  </el-tag>
                </div>
                <div class="card-title">{{ item.title }}</div>
                <div class="card-time">{{ item.time }}</div>
              </div>
            </div>
            <!-- 翻页 -->
            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="pageSizes"
                :total="totalCount"
                layout="prev, pager, next, sizes"
                @current-change="handlePageChange"
                @size-change="handleFilterChange"
              />
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

    <!-- 预警详情弹窗 -->
    <el-dialog v-model="alertDialogVisible" title="预警详情" width="500px" class="insight-dialog">
      <div class="alert-detail">
        <div class="detail-row">
          <el-tag :type="getAlertLevelTag(currentAlert.alert_level)" size="large">
            {{ getAlertLevelText(currentAlert.alert_level) }}
          </el-tag>
          <el-tag :type="getPlatformTag(currentAlert.platform).type" size="large">
            {{ getPlatformTag(currentAlert.platform).label }}
          </el-tag>
        </div>
        <div class="detail-title">
          <h3>{{ currentAlert.title }}</h3>
        </div>
        <div class="detail-cover" v-if="currentAlert.coverUrl">
          <img :src="getProxyImageUrl(currentAlert.coverUrl)" alt="视频封面" @error="handleImageError" />
        </div>
        <div class="detail-factors" v-if="currentAlert.factors && currentAlert.factors.length > 0">
          <h4>影响因素：</h4>
          <ul>
            <li v-for="(factor, index) in currentAlert.factors" :key="index">
              {{ factor }}
            </li>
          </ul>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <span class="dialog-date">{{ currentAlert.created_at ? currentAlert.created_at.replace('T', ' ').substring(0, 19) : '' }}</span>
          <div class="dialog-buttons">
            <el-button @click="alertDialogVisible = false">关闭</el-button>
            <el-button type="primary" @click="openVideoUrl(currentAlert.url)">打开视频链接</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
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
      padding: 12px 8px;
      border-bottom: 1px solid var(--border-color);
      cursor: pointer;
      transition: background-color 0.2s;

      &:hover {
        background-color: var(--hover-color);
      }

      &:last-child {
        border-bottom: none;
      }

      .el-tag {
        margin-right: 8px;
      }

      .alert-title {
        flex: 1;
        margin-left: 8px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .open-link {
        margin-left: 8px;
        color: var(--el-color-primary);
        cursor: pointer;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
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

/* 弹窗内容居中样式 */
:deep(.insight-dialog) {
  .el-dialog__body {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 150px;
    padding: 10px 20px;
  }

  .alert-detail {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 120px;

    .detail-row {
      display: flex;
      gap: 10px;
      margin-bottom: 16px;
    }

    .detail-title {
      margin-bottom: 12px;

      h3 {
        margin: 0;
        word-break: break-all;
      }
    }

    .detail-cover {
      margin-bottom: 16px;
      display: flex;
      justify-content: center;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 8px;
      }
    }

    .detail-factors {
      h4 {
        margin: 0 0 8px;
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          margin-bottom: 4px;
          color: var(--text-regular);
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  .dialog-date {
    color: #909399;
    font-size: 14px;
  }

  .dialog-buttons {
    display: flex;
    gap: 10px;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background-color: var(--bg-color);
  border-radius: 4px;
  flex-wrap: wrap;
}

.alert-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 16px 0;

  .alert-card-item {
    background: var(--bg-color);
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s;
    border: 1px solid var(--border-color);

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .card-cover {
      width: 100%;
      height: 160px;
      overflow: hidden;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .card-content {
      padding: 12px;

      .card-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin-bottom: 8px;

        .el-tag {
          margin-right: 0;
        }
      }

      .card-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 8px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        word-break: break-all;
      }

      .card-time {
        font-size: 12px;
        color: var(--text-secondary);
      }
    }
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px 0;
  grid-column: 1 / -1;
}
</style>
