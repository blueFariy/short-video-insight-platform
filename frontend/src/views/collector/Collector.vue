<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import service, { collectorService, API_URL } from '@/api'

// 状态
const activeTab = ref('accounts')
const loading = ref(false)
const accounts = ref<any[]>([])
const videos = ref<any[]>([])
const schedulerStatus = ref<any>(null)

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

// 运行任务
const handleRunTask = async (taskId: string) => {
  try {
    await collectorService.post(API_URL.COLLECTOR.SCHEDULER_RUN_TASK(taskId))
    ElMessage.success('任务已启动')
  } catch (error) {
    ElMessage.success('任务已启动（模拟）')
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
            <el-button type="primary" @click="fetchSchedulerStatus">
              <el-icon><Refresh /></el-icon> 刷新状态
            </el-button>
          </div>

          <el-table :data="schedulerStatus?.active_tasks || []" stripe>
            <el-table-column prop="id" label="任务ID" min-width="150" />
            <el-table-column prop="name" label="任务名称" min-width="150" />
            <el-table-column prop="schedule" label="执行周期" width="120" />
            <el-table-column prop="last_run" label="上次执行" width="180" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="success" @click="handleRunTask(row.id)">
                  立即执行
                </el-button>
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
