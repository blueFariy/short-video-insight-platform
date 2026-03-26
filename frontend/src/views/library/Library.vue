<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import service, { insightService, API_URL } from '@/api'

const router = useRouter()

// 处理封面URL，解决B站图片403问题
const getCoverUrl = (coverUrl: string): string => {
  if (coverUrl && coverUrl.includes('hdslb.com')) {
    return `${API_URL.COLLECTOR.IMAGE_PROXY}?url=${encodeURIComponent(coverUrl)}`
  }
  return coverUrl
}

interface Folder {
  id: string
  name: string
  type: string
  item_count: number
}

interface FolderItem {
  id: string
  item_id: string
  title: string
  platform: string
  item_type: string
  creator_name: string
  url: string
  play_count: number
  like_count: number
  collect_count: number
  comment_count: number
  share_count: number
  publish_time: string
  notes: string
  tags: string[]
  created_at: string
  is_analyzed: boolean
}

const folders = ref<Folder[]>([])
const folderItems = ref<FolderItem[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const filterType = ref<string>('')

// 当前视图：'folders' | 'items'
const currentView = ref<string>('folders')
const currentFolder = ref<Folder | null>(null)

// 新建收藏夹对话框
const dialogVisible = ref(false)
const newFolderName = ref('')
const newFolderType = ref('video')

const handleCreateFolder = async () => {
  if (!newFolderName.value.trim()) {
    ElMessage.warning('请输入收藏夹名称')
    return
  }
  try {
    await service.post(API_URL.USER.COLLECTIONS, {
      item_type: newFolderType.value,
      item_id: '0',  // 使用字符串'0'表示创建文件夹
      notes: newFolderName.value,
      folder: newFolderName.value
    } as any)
    ElMessage.success('收藏夹创建成功')
    dialogVisible.value = false
    newFolderName.value = ''
    fetchFolders()
  } catch (error: any) {
    console.error('Create folder error:', error)
    ElMessage.error('创建失败')
  }
}

// 获取收藏夹列表（文件夹）
const fetchFolders = async () => {
  loading.value = true
  try {
    // 使用专门的 folders API 获取收藏夹列表及统计
    const res = await service.get(API_URL.USER.COLLECTION_FOLDERS) as any
    // interceptor 已经提取了 data，所以 res 就是文件夹数组
    const foldersData = res || []

    // 直接使用 API 返回的文件夹列表（已包含统计信息）
    folders.value = foldersData.map((f: any) => ({
      id: f.name || '',
      name: f.name || '未分类',
      type: 'video',
      item_count: f.count || 0
    }))
  } catch (error: any) {
    console.error('Fetch folders error:', error)
  } finally {
    loading.value = false
  }
}

// 获取收藏夹内的项目
const fetchFolderItems = async (folder: Folder) => {
  loading.value = true
  currentFolder.value = folder
  currentView.value = 'items'
  try {
    const params: any = { page: 1, page_size: 100, folder: folder.name }
    const res = await service.get(API_URL.USER.COLLECTIONS, { params }) as any
    // After interceptor transforms response, items are at res.items directly
    const items = res?.items || []

    folderItems.value = items
      .filter((item: any) => item.item_id !== "0" && item.item_id !== 0)
      .map((item: any) => {
        const videoInfo = item.video_info || {}
        return {
          id: String(item.id),
          item_id: String(item.item_id),
          title: videoInfo.title || item.notes || '未命名',
          platform: videoInfo.platform || '',
          item_type: item.item_type,
          creator_name: videoInfo.creator_name || '',
          url: videoInfo.url || '',
          play_count: videoInfo.play_count || 0,
          like_count: videoInfo.like_count || 0,
          collect_count: videoInfo.collect_count || 0,
          comment_count: videoInfo.comment_count || 0,
          share_count: videoInfo.share_count || 0,
          publish_time: videoInfo.publish_time ? videoInfo.publish_time.split('T')[0] : '',
          notes: item.notes || '',
          tags: item.tags || [],
          created_at: item.created_at ? new Date(item.created_at).toLocaleDateString() : '',
          is_analysis: videoInfo.is_analysis || item.item_type === 'insight'
        }
      })
  } catch (error: any) {
    console.error('Fetch folder items error:', error)
  } finally {
    loading.value = false
  }
}

// 返回文件夹列表
const goBackToFolders = () => {
  currentView.value = 'folders'
  currentFolder.value = null
  fetchFolders()
}

// 查看分析报告
const viewAnalysis = async (item: any) => {
  // 如果已分析，从后端获取分析数据
  if (item.is_analysis && item.item_id) {
    try {
      // item_id 是视频的原始ID (platform_video_id)
      // 需要先查找 videos 表获取视频主键ID，再获取 insight
      // 但更简单的是直接通过 item.item_id 在视频信息中查找
      // 让我们通过获取所有历史记录并筛选

      // 直接尝试获取视频的 insight 详情
      // 由于不知道视频的内部ID，我们使用通用查询
      const res = await insightService.get(API_URL.INSIGHT.VIDEO_INSIGHT_ALL, {
        params: { page: 1, page_size: 100 }
      }) as any

      if (res?.items && res.items.length > 0) {
        // 查找匹配的视频（通过对比标题或URL）
        const matchedItem = res.items.find((i: any) => {
          const vi = i.video_info || {}
          // 通过URL或标题匹配
          return vi.url === item.url || vi.title === item.title
        })

        if (matchedItem) {
          const insightItem = matchedItem
          // 使用后端返回的insight数据构建URL参数
          const params = new URLSearchParams()

          // 添加视频信息
          if (item.url) params.set('url', encodeURIComponent(item.url))
          if (item.platform) params.set('platform', item.platform)
          if (item.item_id) params.set('item_id', item.item_id)

          // 构建insight数据
          const videoInfo = insightItem.video_info || {}

          // 计算综合评分
          let overallScore = insightItem.overall_score || 0
          if (!overallScore) {
            const dimensions = insightItem.viral_factors || {}
            const scoreValues: number[] = Object.entries(dimensions)
              .filter(([k, v]) => k.endsWith('_score') && typeof v === 'number')
              .map(([, v]) => v as number)
            if (scoreValues.length > 0) {
              overallScore = Math.round(scoreValues.reduce((sum, v) => sum + v, 0) / scoreValues.length)
            }
          }

          const insightData: any = {
            video: {
              title: videoInfo.title || item.title,
              cover: getCoverUrl(videoInfo.cover_url || ''),
              platform: videoInfo.platform || item.platform || '',
              url: videoInfo.url || item.url || '',
              stats: {
                views: videoInfo.play_count || 0,
                likes: videoInfo.like_count || 0,
                comments: videoInfo.comment_count || 0
              }
            },
            insight: {
              overall: {
                summary: insightItem.ai_summary || '',
                highlights: insightItem.keywords || [],
                dimensions: insightItem.viral_factors || {},
                improvements: insightItem.improvements || [],
                overall_score: overallScore
              },
              hook: insightItem.hook_3s ? {
                hook_text: insightItem.hook_3s,
                hook_type: insightItem.hook_type || ''
              } : null,
              structure: insightItem.structure_analysis || (insightItem.structure_type ? { type: insightItem.structure_type } : null)
            }
          }

          params.set('insight', encodeURIComponent(JSON.stringify(insightData)))
          router.push(`/analysis?${params.toString()}`)
          return
        }
      }
    } catch (error) {
      console.error('获取分析数据失败:', error)
    }
  }

  // 如果没有分析或获取失败，回退到原来的逻辑
  const params = new URLSearchParams()
  if (item.url) params.set('url', encodeURIComponent(item.url))
  if (item.platform) params.set('platform', item.platform)
  if (item.item_id) params.set('item_id', item.item_id)
  if (item.item_type) params.set('item_type', item.item_type)

  // 如果有保存的insight数据，传递给分析页面
  // 数据存储在notes字段中，是JSON格式
  let insightData = null
  if (item.notes) {
    try {
      const parsed = JSON.parse(item.notes)
      // 兼容两种格式：直接是insight对象，或者嵌套在insight字段中
      if (parsed.insight) {
        insightData = parsed.insight
      } else if (parsed.video && parsed.insight) {
        // 另一种可能的格式
        insightData = parsed
      }
    } catch (e) {
      // notes不是JSON格式，可能是普通备注
      console.log('Notes is not JSON format:', item.notes)
    }
  }

  if (insightData) {
    params.set('insight', encodeURIComponent(JSON.stringify(insightData)))
  }

  router.push(`/analysis?${params.toString()}`)
}

const collectionTypes = [
  { value: '', label: '全部' },
  { value: 'video', label: '视频' },
  { value: 'script', label: '脚本' },
  { value: 'insight', label: '洞察' },
  { value: 'creator', label: '创作者' }
]

const handleDelete = async (id: string) => {
  try {
    await service.delete(API_URL.USER.DELETE_COLLECTION(id))
    ElMessage.success('删除成功')
    if (currentFolder.value) {
      fetchFolderItems(currentFolder.value)
    } else {
      fetchFolders()
    }
  } catch (error: any) {
    console.error('Delete error:', error)
    ElMessage.error(error.response?.data?.message || '删除失败')
  }
}

const getTypeTag = (type: string) => {
  const map: Record<string, { type: string; label: string }> = {
    video: { type: 'primary', label: '视频' },
    script: { type: 'success', label: '脚本' },
    insight: { type: 'warning', label: '洞察' },
    creator: { type: 'danger', label: '创作者' }
  }
  return map[type] || { type: 'info', label: type }
}

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 100000000) {
    return (num / 100000000).toFixed(1) + '亿'
  } else if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 获取平台标签
const getPlatformTag = (platform: string) => {
  const map: Record<string, { type: string; label: string }> = {
    douyin: { type: 'danger', label: '抖音' },
    bilibili: { type: 'primary', label: 'B站' },
    xiaohongshu: { type: 'warning', label: '小红书' },
    kuaishou: { type: 'success', label: '快手' }
  }
  return map[platform] || { type: 'info', label: platform }
}

// 跳转到视频链接
const goToVideo = (item: any) => {
  if (item.url) {
    window.open(item.url, '_blank')
  }
}

// 跳转到创作者主页
const goToCreator = (item: any) => {
  if (!item.platform || !item.creator_name) return
  let url = ''
  if (item.platform === 'bilibili') {
    // B站创作者主页需要通过搜索跳转
    url = `https://space.bilibili.com/?${encodeURIComponent(item.creator_name)}`
  } else if (item.platform === 'douyin') {
    url = `https://www.douyin.com/user/${encodeURIComponent(item.creator_name)}`
  } else if (item.platform === 'xiaohongshu') {
    url = `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(item.creator_name)}`
  } else if (item.platform === 'kuaishou') {
    url = `https://www.kuaishou.com/search/${encodeURIComponent(item.creator_name)}`
  }
  if (url) {
    window.open(url, '_blank')
  }
}

onMounted(() => {
  fetchFolders()
})
</script>

<template>
  <div class="library-page">
    <!-- Header -->
    <div class="page-header">
      <h1>素材库</h1>
      <p class="subtitle">收藏的视频、脚本、洞察等优质内容</p>
    </div>

    <!-- Back button when viewing items -->
    <div v-if="currentView === 'items'" class="back-header">
      <el-button @click="goBackToFolders">
        ← 返回收藏夹列表
      </el-button>
      <span class="folder-title">{{ currentFolder?.name }}</span>
      <span class="item-count">({{ folderItems.length }} 个项目)</span>
    </div>

    <!-- Filters (only show in folders view) -->
    <el-card class="filter-card" v-if="currentView === 'folders'">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索素材..."
            prefix-icon="Search"
            clearable
            @change="fetchFolders"
          />
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterType" placeholder="素材类型" clearable @change="fetchFolders">
            <el-option
              v-for="item in collectionTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-col>
        <el-col :span="10">
          <el-button type="primary" icon="Plus" @click="dialogVisible = true">新建收藏夹</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Folders View -->
    <div v-if="currentView === 'folders'">
      <el-row :gutter="20" v-loading="loading">
        <el-col :span="8" v-for="folder in folders" :key="folder.id">
          <el-card class="folder-card" @click="fetchFolderItems(folder)">
            <div class="folder-icon">📁</div>
            <h3 class="folder-name">{{ folder.name }}</h3>
            <p class="folder-count">{{ folder.item_count }} 个项目</p>
            <el-tag :type="getTypeTag(folder.type).type" size="small">
              {{ getTypeTag(folder.type).label }}
            </el-tag>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="!loading && folders.length === 0" description="暂无收藏夹，请先创建收藏夹" />
    </div>

    <!-- Folder Items View -->
    <div v-if="currentView === 'items'">
      <el-table :data="folderItems" v-loading="loading" stripe>
        <el-table-column prop="title" label="名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <a href="javascript:void(0)" @click="goToVideo(row)" style="color: #409eff; cursor: pointer;">
              {{ row.title }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="platform" label="平台" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.platform" :type="getPlatformTag(row.platform).type" size="small">
              {{ getPlatformTag(row.platform).label }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="item_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.item_type).type" size="small">
              {{ getTypeTag(row.item_type).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="创作者" width="120">
          <template #default="{ row }">
            <a v-if="row.creator_name" href="javascript:void(0)" @click="goToCreator(row)" style="color: #409eff; cursor: pointer;">
              {{ row.creator_name }}
            </a>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="play_count" label="播放量" width="90">
          <template #default="{ row }">
            {{ formatNumber(row.play_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="like_count" label="点赞数" width="90">
          <template #default="{ row }">
            {{ formatNumber(row.like_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="comment_count" label="评论数" width="90">
          <template #default="{ row }">
            {{ formatNumber(row.comment_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="publish_time" label="发布时间" width="100" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.is_analysis" type="success" size="small">已分析</el-tag>
            <el-tag v-else type="info" size="small">未分析</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <div style="display: flex; gap: 4px;">
              <el-button v-if="row.is_analysis" size="small" type="primary" @click="viewAnalysis(row)">
                查看
              </el-button>
              <el-button v-else size="small" type="primary" @click="viewAnalysis(row)">
                分析
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row.id)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && folderItems.length === 0" description="该收藏夹暂无内容" />
    </div>

    <!-- 新建收藏夹对话框 -->
    <el-dialog v-model="dialogVisible" title="新建收藏夹" width="400px">
      <el-form label-width="80px">
        <el-form-item label="收藏夹名称">
          <el-input v-model="newFolderName" placeholder="请输入收藏夹名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newFolderType" style="width: 100%">
            <el-option value="video" label="视频" />
            <el-option value="script" label="脚本" />
            <el-option value="insight" label="洞察" />
            <el-option value="creator" label="创作者" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateFolder">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.library-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;

  h1 {
    font-size: 24px;
    margin-bottom: 8px;
  }

  .subtitle {
    color: var(--text-secondary);
  }
}

.filter-card {
  margin-bottom: 20px;
}

.back-header {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 15px;

  .folder-title {
    font-size: 18px;
    font-weight: 600;
  }

  .item-count {
    color: #666;
  }
}

.folder-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
  padding: 20px;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }

  .folder-icon {
    font-size: 48px;
    margin-bottom: 10px;
  }

  .folder-name {
    font-size: 16px;
    margin: 10px 0 5px;
  }

  .folder-count {
    color: #666;
    margin-bottom: 10px;
  }
}

.collection-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .title {
    font-size: 16px;
    margin-bottom: 8px;
    color: #333;
  }

  .content {
    font-size: 13px;
    color: #666;
    margin-bottom: 12px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .tags {
    margin-bottom: 12px;

    .el-tag {
      margin-right: 8px;
    }
  }

  .footer {
    .date {
      font-size: 12px;
      color: #999;
    }
  }
}
</style>
