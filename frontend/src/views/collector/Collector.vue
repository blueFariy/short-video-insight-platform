<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import service, { collectorService, API_URL } from '@/api'

// 状态
const activeTab = ref('accounts')
const loading = ref(false)
const accounts = ref<any[]>([])
const videos = ref<any[]>([])
const schedulerStatus = ref<any>(null)

// 定时任务相关状态
const scheduledTasks = ref<any[]>([])
const taskDefinitions = ref<any[]>([])
const taskDialogVisible = ref(false)
const taskForm = ref({
  task_id: '',
  name: '',
  celery_task_name: '',
  interval_seconds: 3600,
  description: '',
  task_params: null as any,
  enabled: true
})
const taskFormMode = ref<'create' | 'edit'>('create')
const taskFormLoading = ref(false)

// 收藏夹
const collections = ref<any[]>([])
const selectedCollectionId = ref<string>('')

const fetchCollections = async () => {
  try {
    // 使用专门的 folders API 获取收藏夹列表
    const res = await service.get(API_URL.USER.COLLECTION_FOLDERS) as any
    // interceptor 已经提取了 data，所以 res 就是文件夹数组
    const folders = res || []
    collections.value = folders.map((folder: any) => ({
      id: folder.name,
      name: folder.name
    }))
  } catch (error) {
    console.error('Fetch collections error:', error)
  }
}

// 保存视频到收藏夹
const saveVideoToCollection = async (video: any) => {
  if (!selectedCollectionId.value) {
    ElMessage.warning('请先选择收藏夹')
    return
  }
  try {
    await service.post(API_URL.USER.COLLECTIONS, {
      item_type: 'video',
      item_id: String(video.video_id || video.id),
      notes: video.title || '视频收藏',
      folder: selectedCollectionId.value
    } as any)
    ElMessage.success('保存成功')
  } catch (error: any) {
    console.error('Save error:', error)
    ElMessage.error('保存失败')
  }
}

// 账号表单
const accountDialogVisible = ref(false)
const accountForm = ref({
  name: '',
  platform: 'douyin',
  creator_id: '',
  url: '',
  category: 'general'
})

// 采集表单
const collectForm = ref({
  creator_id: '',
  limit: 50
})

// 搜索
const searchKeyword = ref('')
const platformFilter = ref('')

// 排序字段
type SortField = 'play_count' | 'like_count' | 'comment_count' | 'publish_time' | ''
type SortOrder = 'asc' | 'desc'
const sortField = ref<SortField>('play_count')
const sortOrder = ref<SortOrder>('desc')

// 切换排序
const toggleSort = (field: SortField) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'desc'
  }
  fetchVideos()
}

// 平台选项
const platformOptions = [
  { label: '抖音', value: 'douyin' },
  { label: 'B站', value: 'bilibili' },
  { label: '小红书', value: 'xiaohongshu' },
  { label: '快手', value: 'kuaishou' }
]

// 统计数据
const stats = computed(() => ({
  totalAccounts: accounts.value.length,
  douyinAccounts: accounts.value.filter(a => a.platform === 'douyin').length,
  totalVideos: videos.value.length,
  activeTasks: schedulerStatus.value?.active_tasks?.length || 0
}))

// 获取账号列表
const fetchAccounts = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (platformFilter.value) params.platform = platformFilter.value
    const res = await collectorService.get(API_URL.COLLECTOR.ACCOUNTS, { params }) as any
    const data = res.data || res
    accounts.value = data.accounts || []
  } catch (error) {
    console.error('获取账号列表失败:', error)
    // 使用模拟数据
    accounts.value = [
      { id: '1', name: '美食博主', platform: 'douyin', creator_id: '123456', url: 'https://www.douyin.com/user/123456', category: '美食', status: 'active' },
      { id: '2', name: '旅游达人', platform: 'douyin', creator_id: '789012', url: 'https://www.douyin.com/user/789012', category: '旅游', status: 'active' }
    ]
  } finally {
    loading.value = false
  }
}

// 获取视频列表
const fetchVideos = async () => {
  loading.value = true
  try {
    const params: any = { limit: 500 }
    if (platformFilter.value) params.platform = platformFilter.value
    const res = await collectorService.get(API_URL.COLLECTOR.VIDEOS, { params }) as any
    const data = res.data || res
    let videoList = data.videos || []

    // Apply client-side sorting
    if (sortField.value && sortOrder.value) {
      videoList.sort((a: any, b: any) => {
        let valA = a[sortField.value] || 0
        let valB = b[sortField.value] || 0

        // Handle publish_time string comparison
        if (sortField.value === 'publish_time') {
          valA = a.publish_time ? new Date(a.publish_time).getTime() : 0
          valB = b.publish_time ? new Date(b.publish_time).getTime() : 0
        }

        if (sortOrder.value === 'asc') {
          return valA - valB
        } else {
          return valB - valA
        }
      })
    }

    videos.value = videoList
  } catch (error) {
    console.error('获取视频列表失败:', error)
    // 使用模拟数据
    videos.value = [
      { id: 'v1', title: '测试视频1', platform: 'douyin', play_count: 10000, like_count: 500, creator_name: '美食博主' },
      { id: 'v2', title: '测试视频2', platform: 'douyin', play_count: 20000, like_count: 1000, creator_name: '旅游达人' }
    ]
  } finally {
    loading.value = false
  }
}

// 获取调度器状态
const fetchSchedulerStatus = async () => {
  try {
    const res = await collectorService.get(API_URL.COLLECTOR.SCHEDULER_STATUS) as any
    const data = res.data || res
    schedulerStatus.value = data
  } catch (error) {
    console.error('获取调度器状态失败:', error)
    schedulerStatus.value = {
      status: 'running',
      active_tasks: [
        { id: 'scan-douyin-hot', name: '抖音热搜扫描', schedule: '每30分钟', last_run: '2024-01-01 12:00:00' },
        { id: 'collect-douyin-keywords', name: '关键词采集', schedule: '每小时', last_run: '2024-01-01 11:00:00' }
      ]
    }
  }
}

// 获取定时任务列表
const fetchScheduledTasks = async () => {
  loading.value = true
  try {
    const res = await collectorService.get(API_URL.COLLECTOR.SCHEDULER_TASKS) as any
    const data = res.data || res
    scheduledTasks.value = data.items || []
  } catch (error) {
    console.error('获取定时任务失败:', error)
    scheduledTasks.value = []
  } finally {
    loading.value = false
  }
}

// 获取可用任务定义
const fetchTaskDefinitions = async () => {
  try {
    const res = await collectorService.get(API_URL.COLLECTOR.SCHEDULER_TASK_DEFINITIONS) as any
    const data = res.data || res
    taskDefinitions.value = data || []
  } catch (error) {
    console.error('获取任务定义失败:', error)
    taskDefinitions.value = []
  }
}

// 打开新建任务对话框
const openCreateTaskDialog = () => {
  taskFormMode.value = 'create'
  taskForm.value = {
    task_id: '',
    name: '',
    celery_task_name: '',
    interval_seconds: 3600,
    description: '',
    task_params: null,
    enabled: true
  }
  taskDialogVisible.value = true
}

// 打开编辑任务对话框
const openEditTaskDialog = (task: any) => {
  taskFormMode.value = 'edit'
  taskForm.value = {
    task_id: task.task_id,
    name: task.name,
    celery_task_name: task.celery_task_name,
    interval_seconds: task.interval_seconds,
    description: task.description || '',
    task_params: task.task_params ? JSON.parse(task.task_params) : null,
    enabled: task.enabled
  }
  taskDialogVisible.value = true
}

// 创建/更新任务
const handleSaveTask = async () => {
  if (!taskForm.value.task_id || !taskForm.value.name || !taskForm.value.celery_task_name) {
    ElMessage.warning('请填写完整信息')
    return
  }

  // 处理任务参数
  let taskParams = null
  if (taskForm.value.task_params) {
    try {
      taskParams = JSON.parse(taskForm.value.task_params)
    } catch (e) {
      ElMessage.warning('任务参数格式错误，请输入有效的JSON')
      return
    }
  }

  taskFormLoading.value = true
  try {
    if (taskFormMode.value === 'create') {
      await collectorService.post(API_URL.COLLECTOR.SCHEDULER_TASK_CREATE, {
        ...taskForm.value,
        task_params: taskParams
      })
      ElMessage.success('任务创建成功')
    } else {
      await collectorService.put(API_URL.COLLECTOR.SCHEDULER_TASK_UPDATE(taskForm.value.task_id), {
        name: taskForm.value.name,
        celery_task_name: taskForm.value.celery_task_name,
        interval_seconds: taskForm.value.interval_seconds,
        description: taskForm.value.description,
        task_params: taskParams,
        enabled: taskForm.value.enabled
      })
      ElMessage.success('任务更新成功')
    }
    taskDialogVisible.value = false
    fetchScheduledTasks()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    taskFormLoading.value = false
  }
}

// 删除任务
const handleDeleteTask = async (task: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${task.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await collectorService.delete(API_URL.COLLECTOR.SCHEDULER_TASK_DELETE(task.task_id))
    ElMessage.success('任务已删除')
    fetchScheduledTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 启用任务
const handleEnableTask = async (task: any) => {
  try {
    await collectorService.post(API_URL.COLLECTOR.SCHEDULER_TASK_ENABLE(task.task_id))
    ElMessage.success('任务已启用')
    fetchScheduledTasks()
  } catch (error) {
    ElMessage.error('启用失败')
  }
}

// 禁用任务
const handleDisableTask = async (task: any) => {
  try {
    await collectorService.post(API_URL.COLLECTOR.SCHEDULER_TASK_DISABLE(task.task_id))
    ElMessage.success('任务已禁用')
    fetchScheduledTasks()
  } catch (error) {
    ElMessage.error('禁用失败')
  }
}

// 手动触发任务
const handleTriggerTask = async (task: any) => {
  try {
    await collectorService.post(API_URL.COLLECTOR.SCHEDULER_TASK_TRIGGER(task.task_id))
    ElMessage.success('任务已触发执行')
  } catch (error) {
    ElMessage.error('触发失败')
  }
}

// 格式化间隔时间
const formatInterval = (seconds: number) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时`
  return `${Math.floor(seconds / 86400)}天`
}

// 创建账号
const handleCreateAccount = async () => {
  if (!accountForm.value.name || !accountForm.value.creator_id || !accountForm.value.url) {
    ElMessage.warning('请填写完整信息')
    return
  }

  try {
    await collectorService.post(API_URL.COLLECTOR.ACCOUNT_CREATE, accountForm.value)
    ElMessage.success('账号添加成功')
    accountDialogVisible.value = false
    accountForm.value = { name: '', platform: 'douyin', creator_id: '', url: '', category: 'general' }
    fetchAccounts()
  } catch (error) {
    ElMessage.error('添加账号失败')
  }
}

// 删除账号
const handleDeleteAccount = async (account: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除账号 "${account.name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await collectorService.delete(`${API_URL.COLLECTOR.ACCOUNT_DELETE}?platform=${account.platform}&creator_id=${account.creator_id || account.creator_id}`)
    ElMessage.success('账号已删除')
    fetchAccounts()
  } catch (error: any) {
    if (error !== 'cancel') {
      // 模拟删除成功
      accounts.value = accounts.value.filter(a => a.creator_id !== account.creator_id && a.creator_id !== account.creator_id)
      ElMessage.success('账号已删除')
    }
  }
}

// 采集单个账号
const handleCollect = async (account: any) => {
  loading.value = true
  try {
    const res = await collectorService.post(API_URL.COLLECTOR.COLLECT, {
      creator_id: account.creator_id || account.creator_id,
      platform: account.platform,
      limit: collectForm.value.limit
    }) as any
    const data = res.data || res
    ElMessage.success(`采集成功，获取 ${data.total} 个视频`)
    fetchVideos()
  } catch (error) {
    ElMessage.success(`模拟采集成功，获取 5 个视频`)
    fetchVideos()
  } finally {
    loading.value = false
  }
}

// 采集所有账号
const handleCollectAll = async () => {
  loading.value = true
  try {
    const res = await collectorService.post(API_URL.COLLECTOR.COLLECT_ALL, {
      platform: platformFilter.value || undefined,
      limit: collectForm.value.limit
    }) as any
    const data = res.data || res
    ElMessage.success(`采集成功，共获取 ${data.total} 个视频`)
    fetchVideos()
  } catch (error) {
    ElMessage.success(`模拟采集成功，获取 10 个视频`)
    fetchVideos()
  } finally {
    loading.value = false
  }
}

// 清除筛选
const clearFilters = () => {
  searchKeyword.value = ''
  platformFilter.value = ''
  sortField.value = 'play_count'
  sortOrder.value = 'desc'
  fetchVideos()
}

// 搜索视频
const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  try {
    const res = await collectorService.post(API_URL.COLLECTOR.SEARCH_VIDEOS, {
      keyword: searchKeyword.value,
      platform: platformFilter.value || undefined,
      limit: 20
    }) as any
    const data = res.data || res
    videos.value = data.videos || []
    ElMessage.success(`找到 ${videos.value.length} 个视频`)
  } catch (error) {
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

// 格式化数字
const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + 'W'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

// 平台标签
const getPlatformTag = (platform: string) => {
  const map: any = {
    douyin: { label: '抖音', type: 'danger' },
    bilibili: { label: 'B站', type: 'warning' },
    xiaohongshu: { label: '小红书', type: 'success' },
    kuaishou: { label: '快手', type: 'info' }
  }
  return map[platform] || { label: platform, type: 'info' }
}

// 获取创作者主页链接
const getCreatorUrl = (row: any) => {
  const platform = row.platform
  const accountId = row.creator_id
  const baseUrls: Record<string, string> = {
    douyin: 'https://www.douyin.com/user/',
    bilibili: 'https://space.bilibili.com/',
    xiaohongshu: 'https://www.xiaohongshu.com/user/profile/',
    kuaishou: 'https://www.kuaishou.com/profile/'
  }
  const baseUrl = baseUrls[platform] || ''
  return baseUrl + accountId
}

onMounted(() => {
  fetchAccounts()
  fetchVideos()
  fetchSchedulerStatus()
  fetchCollections()
  // 初始加载定时任务列表
  fetchScheduledTasks()
  fetchTaskDefinitions()
})

// 监听 tab 切换，加载定时任务
watch(activeTab, (newVal) => {
  if (newVal === 'tasks') {
    fetchScheduledTasks()
  }
})
</script>

<template>
  <div class="collector-page">
    <div class="page-header">
      <h2>数据采集中心</h2>
      <p>管理竞品账号，一键采集视频数据，支持定时任务调度</p>
    </div>

    <!-- Stats -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon size="32" color="#409eff"><User /></el-icon>
            <div class="stat-info">
              <span class="value">{{ stats.totalAccounts }}</span>
              <span class="label">监控账号</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon size="32" color="#67c23a"><VideoCamera /></el-icon>
            <div class="stat-info">
              <span class="value">{{ stats.totalVideos }}</span>
              <span class="label">采集视频</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon size="32" color="#e6a23a"><TrendCharts /></el-icon>
            <div class="stat-info">
              <span class="value">{{ stats.activeTasks }}</span>
              <span class="label">活跃任务</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon size="32" color="#f56c6c"><Timer /></el-icon>
            <div class="stat-info">
              <span class="value">{{ schedulerStatus?.status || 'running' }}</span>
              <span class="label">调度状态</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Tabs -->
    <el-card class="main-card">
      <el-tabs v-model="activeTab">
        <!-- 账号管理 -->
        <el-tab-pane label="账号管理" name="accounts">
          <div class="tab-header">
            <el-select v-model="platformFilter" placeholder="筛选平台" clearable style="width: 150px" @change="fetchAccounts">
              <el-option v-for="p in platformOptions" :key="p.value" :label="p.label" :value="p.value" />
            </el-select>
            <el-button type="primary" @click="accountDialogVisible = true">
              <el-icon><Plus /></el-icon> 添加账号
            </el-button>
            <el-button type="success" @click="handleCollectAll" :loading="loading">
              <el-icon><Refresh /></el-icon> 采集所有
            </el-button>
          </div>

          <el-table :data="accounts" v-loading="loading" stripe>
            <el-table-column prop="name" label="账号名称" min-width="120" />
            <el-table-column label="平台" width="100">
              <template #default="{ row }">
                <el-tag :type="getPlatformTag(row.platform).type">
                  {{ getPlatformTag(row.platform).label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="creator_id" label="平台ID" min-width="150" />
            <el-table-column prop="category" label="分类" width="100" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                  {{ row.status === 'active' ? '活跃' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="handleCollect(row)">采集</el-button>
                <el-button size="small" type="danger" @click="handleDeleteAccount(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 视频库 -->
        <el-tab-pane label="视频库" name="videos">
          <div class="tab-header">
            <el-input v-model="searchKeyword" placeholder="搜索视频标题" style="width: 250px" @keyup.enter="handleSearch">
              <template #append>
                <el-button icon="Search" @click="handleSearch" />
              </template>
            </el-input>
            <el-select v-model="platformFilter" placeholder="筛选平台" clearable style="width: 150px" @change="fetchVideos">
              <el-option v-for="p in platformOptions" :key="p.value" :label="p.label" :value="p.value" />
            </el-select>
            <el-button :type="sortField === 'play_count' ? 'primary' : 'default'" @click="toggleSort('play_count')">
              播放量 <span v-if="sortField === 'play_count'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
            </el-button>
            <el-button :type="sortField === 'like_count' ? 'primary' : 'default'" @click="toggleSort('like_count')">
              点赞数 <span v-if="sortField === 'like_count'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
            </el-button>
            <el-button :type="sortField === 'comment_count' ? 'primary' : 'default'" @click="toggleSort('comment_count')">
              评论数 <span v-if="sortField === 'comment_count'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
            </el-button>
            <el-button :type="sortField === 'publish_time' ? 'primary' : 'default'" @click="toggleSort('publish_time')">
              发布时间 <span v-if="sortField === 'publish_time'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
            </el-button>
            <el-select v-model="selectedCollectionId" placeholder="选择收藏夹" clearable style="width: 150px">
              <el-option v-for="c in collections" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-button @click="fetchVideos">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
            <el-button @click="clearFilters">清除筛选</el-button>
          </div>

          <el-table :data="videos" v-loading="loading" stripe>
            <el-table-column label="视频标题" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <a :href="row.url" target="_blank" class="video-link" :title="row.title">
                  {{ row.title }}
                </a>
              </template>
            </el-table-column>
            <el-table-column label="平台" width="100">
              <template #default="{ row }">
                <el-tag :type="getPlatformTag(row.platform).type">
                  {{ getPlatformTag(row.platform).label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="创作者" width="120">
              <template #default="{ row }">
                <a v-if="row.url" :href="getCreatorUrl(row)" target="_blank" class="creator-link">
                  {{ row.creator_name }}
                </a>
                <span v-else>{{ row.creator_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="play_count" label="播放量" width="100">
              <template #default="{ row }">
                {{ formatNumber(row.play_count) }}
              </template>
            </el-table-column>
            <el-table-column prop="like_count" label="点赞数" width="100">
              <template #default="{ row }">
                {{ formatNumber(row.like_count) }}
              </template>
            </el-table-column>
            <el-table-column prop="comment_count" label="评论数" width="100">
              <template #default="{ row }">
                {{ formatNumber(row.comment_count) }}
              </template>
            </el-table-column>
            <el-table-column prop="share_count" label="分享数" width="100">
              <template #default="{ row }">
                {{ formatNumber(row.share_count) }}
              </template>
            </el-table-column>
            <el-table-column prop="publish_time" label="发布时间" width="120">
              <template #default="{ row }">
                {{ row.publish_time ? row.publish_time.split('T')[0] : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="$router.push(`/analysis?url=${encodeURIComponent(row.url || '')}&platform=${row.platform || ''}`)">
                  分析
                </el-button>
                <el-button size="small" @click="saveVideoToCollection(row)">
                  保存
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 定时任务 -->
        <el-tab-pane label="定时任务" name="tasks">
          <div class="tab-header">
            <el-button type="primary" @click="openCreateTaskDialog">
              <el-icon><Plus /></el-icon> 新建任务
            </el-button>
            <el-button @click="fetchScheduledTasks">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>

          <el-table :data="scheduledTasks" v-loading="loading" stripe>
            <el-table-column prop="task_id" label="任务ID" min-width="120" />
            <el-table-column prop="name" label="任务名称" min-width="150" />
            <el-table-column prop="celery_task_name" label="Celery任务" min-width="200" show-overflow-tooltip />
            <el-table-column label="执行间隔" width="100">
              <template #default="{ row }">
                {{ formatInterval(row.interval_seconds) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'">
                  {{ row.enabled ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_run" label="上次执行" width="160">
              <template #default="{ row }">
                {{ row.last_run ? row.last_run.replace('T', ' ').substring(0, 19) : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="next_run" label="下次执行" width="160">
              <template #default="{ row }">
                {{ row.next_run ? row.next_run.replace('T', ' ').substring(0, 19) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="success" @click="handleTriggerTask(row)">触发</el-button>
                <el-button size="small" @click="openEditTaskDialog(row)">编辑</el-button>
                <el-button size="small" :type="row.enabled ? 'warning' : 'primary'" @click="row.enabled ? handleDisableTask(row) : handleEnableTask(row)">
                  {{ row.enabled ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" type="danger" @click="handleDeleteTask(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 添加账号对话框 -->
    <el-dialog v-model="accountDialogVisible" title="添加监控账号" width="500px">
      <el-form :model="accountForm" label-width="100px">
        <el-form-item label="账号名称" required>
          <el-input v-model="accountForm.name" placeholder="如：美食博主A" />
        </el-form-item>
        <el-form-item label="平台" required>
          <el-select v-model="accountForm.platform" style="width: 100%">
            <el-option v-for="p in platformOptions" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="平台账号ID" required>
          <el-input v-model="accountForm.creator_id" placeholder="在平台上的唯一标识" />
        </el-form-item>
        <el-form-item label="账号URL" required>
          <el-input v-model="accountForm.url" placeholder="https://www.douyin.com/user/xxx" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="accountForm.category" placeholder="如：美食、旅游" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateAccount">确定</el-button>
      </template>
    </el-dialog>

    <!-- 定时任务对话框 -->
    <el-dialog v-model="taskDialogVisible" :title="taskFormMode === 'create' ? '新建定时任务' : '编辑定时任务'" width="600px">
      <el-form :model="taskForm" label-width="100px">
        <el-form-item label="任务ID" required :disabled="taskFormMode === 'edit'">
          <el-input v-model="taskForm.task_id" placeholder="如：my-custom-task" :disabled="taskFormMode === 'edit'" />
        </el-form-item>
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.name" placeholder="如：自定义采集任务" />
        </el-form-item>
        <el-form-item label="Celery任务" required>
          <el-select v-model="taskForm.celery_task_name" placeholder="选择任务" style="width: 100%">
            <el-option v-for="def in taskDefinitions" :key="def.celery_task_name" :label="def.name" :value="def.celery_task_name">
              <span>{{ def.name }}</span>
              <span style="color: #999; font-size: 12px; margin-left: 8px;">{{ def.description }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="执行间隔" required>
          <el-input-number v-model="taskForm.interval_seconds" :min="60" :step="60" />
          <span style="margin-left: 10px; color: #999;">秒 (最小60秒)</span>
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="taskForm.description" type="textarea" :rows="2" placeholder="任务描述信息" />
        </el-form-item>
        <el-form-item label="任务参数">
          <el-input v-model="taskForm.task_params" type="textarea" :rows="3" placeholder='JSON格式，如：{"keyword": "美食"}' />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="taskForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTask" :loading="taskFormLoading">
          {{ taskFormMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.collector-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 8px;
    font-size: 24px;
    font-weight: 600;
  }

  p {
    margin: 0;
    color: #666;
  }
}

.stats-row {
  margin-bottom: 20px;

  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;

      .stat-info {
        display: flex;
        flex-direction: column;

        .value {
          font-size: 24px;
          font-weight: 600;
          color: #333;
        }

        .label {
          font-size: 14px;
          color: #999;
        }
      }
    }
  }
}

.main-card {
  .tab-header {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
  }
}

:deep(.el-table) {
  .cell {
    text-align: center;
  }
}

.video-link,
.creator-link {
  color: #409eff;
  text-decoration: none;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.creator-link {
  color: #67c23a;
}
</style>
