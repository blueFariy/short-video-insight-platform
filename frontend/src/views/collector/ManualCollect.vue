<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import service, { collectorService, API_URL } from '@/api'

// B站分区选项
const bilibiliRegions = ref([
  { id: 1, name: '动画' },
  { id: 3, name: '音乐' },
  { id: 4, name: '游戏' },
  { id: 5, name: '娱乐' },
  { id: 36, name: '科技' },
  { id: 119, name: '鬼畜' },
  { id: 129, name: '舞蹈' },
  { id: 155, name: '时尚' },
  { id: 160, name: '生活' },
  { id: 188, name: '数码' },
  { id: 211, name: '美食' },
  { id: 234, name: '汽车' }
])

// 状态
const activePlatform = ref('bilibili')
const activeTab = ref('trending')
const loading = ref(false)

// 表单数据
const searchForm = ref({
  keyword: '',
  limit: 20
})

const regionForm = ref({
  rid: 36,  // 默认科技
  pn: 1
})

const creatorForm = ref({
  creator_id: '',
  limit: 50
})

// 结果数据
const videos = ref<any[]>([])
const creatorInfo = ref<any>(null)
const stats = ref({
  fetched: 0,
  saved: 0
})

// 收藏夹相关
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

// 获取封面URL，处理B站403问题
const getCoverUrl = (video: any) => {
  let url = video.cover_url || video.pic || video.cover || ''
  // B站图片使用后端代理解决403问题
  if (url && url.includes('hdslb.com')) {
    url = `${API_URL.COLLECTOR.IMAGE_PROXY}?url=${encodeURIComponent(url)}`
  }
  return url
}

// 处理封面加载失败
const handleCoverError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = 'https://via.placeholder.com/280x160?text=No+Cover'
}

// 获取指标值（处理嵌套的metrics对象）
const getMetricValue = (video: any, key: string) => {
  // 首先检查嵌套在 metrics 中的数据 (主要格式)
  if (video.metrics) {
    if (video.metrics[key] !== undefined) return video.metrics[key]
    // 播放量兼容
    if (key === 'play_count' && video.metrics.play_count !== undefined) return video.metrics.play_count
    // 点赞兼容
    if (key === 'like_count' && video.metrics.like_count !== undefined) return video.metrics.like_count
  }

  // 直接访问顶级字段
  if (video[key] !== undefined) return video[key]

  // B站 stat 对象兼容
  if (video.stat) {
    if (key === 'play_count' && video.stat.view !== undefined) return video.stat.view
    if (key === 'like_count' && video.stat.like !== undefined) return video.stat.like
    if (key === 'comment_count' && video.stat.reply !== undefined) return video.stat.reply
    if (key === 'share_count' && video.stat.share !== undefined) return video.stat.share
  }

  // 兼容不同字段名
  if (key === 'play_count' && video.views !== undefined) return video.views

  return 0
}

// 格式化数字
const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 100000000) return (num / 100000000).toFixed(1) + '亿'
  if (num >= 10000) return (num / 10000).toFixed(1) + 'W'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

// 获取热门/排行榜
const fetchTrending = async () => {
  loading.value = true
  try {
    const res = await collectorService.post(API_URL.COLLECTOR.MANUAL_COLLECT, {
      platform: activePlatform.value,
      collect_type: 'trending',
      params: { limit: searchForm.value.limit }
    }) as any
    const data = res.data || res
    videos.value = data.videos || []
    stats.value.fetched = data.fetched
    stats.value.saved = data.saved
    ElMessage.success(`获取成功，共 ${data.fetched} 条，已入库 ${data.saved} 条`)
  } catch (error: any) {
    ElMessage.error(error.message || '获取失败')
  } finally {
    loading.value = false
  }
}

// 获取分区视频
const fetchRegionVideos = async () => {
  loading.value = true
  try {
    const res = await collectorService.post(API_URL.COLLECTOR.MANUAL_COLLECT, {
      platform: activePlatform.value,
      collect_type: 'region',
      params: { rid: regionForm.value.rid, pn: regionForm.value.pn }
    }) as any
    const data = res.data || res
    videos.value = data.videos || []
    stats.value.fetched = data.fetched
    stats.value.saved = data.saved
    ElMessage.success(`获取成功，共 ${data.fetched} 条，已入库 ${data.saved} 条`)
  } catch (error: any) {
    ElMessage.error(error.message || '获取失败')
  } finally {
    loading.value = false
  }
}

// 搜索视频
const handleSearch = async () => {
  if (!searchForm.value.keyword.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  loading.value = true
  try {
    const res = await collectorService.post(API_URL.COLLECTOR.MANUAL_COLLECT, {
      platform: activePlatform.value,
      collect_type: 'search',
      params: {
        keyword: searchForm.value.keyword,
        limit: searchForm.value.limit
      }
    }) as any
    const data = res.data || res
    videos.value = data.videos || []
    stats.value.fetched = data.fetched
    stats.value.saved = data.saved
    ElMessage.success(`搜索成功，共 ${data.fetched} 条，已入库 ${data.saved} 条`)
  } catch (error: any) {
    ElMessage.error(error.message || '搜索失败')
  } finally {
    loading.value = false
  }
}

// 获取UP主信息
const fetchCreatorInfo = async () => {
  if (!creatorForm.value.creator_id.trim()) {
    ElMessage.warning('请输入UP主ID')
    return
  }
  loading.value = true
  try {
    const res = await collectorService.get(API_URL.COLLECTOR.BILIBILI_CREATOR(creatorForm.value.creator_id)) as any
    creatorInfo.value = res.data || res
  } catch (error: any) {
    ElMessage.error(error.message || '获取UP主信息失败')
  } finally {
    loading.value = false
  }
}

// 采集UP主视频
const collectCreatorVideos = async () => {
  if (!creatorForm.value.creator_id.trim()) {
    ElMessage.warning('请输入UP主ID')
    return
  }
  loading.value = true
  try {
    const res = await collectorService.post(
      `/api/v1/collector/bilibili/creator/collect?creator_id=${creatorForm.value.creator_id}&limit=${creatorForm.value.limit}`
    ) as any
    const data = res.data || res
    videos.value = data.videos || []
    stats.value.fetched = data.fetched
    stats.value.saved = data.saved
    creatorInfo.value = data.creator
    ElMessage.success(`采集成功，共 ${data.fetched} 条，已入库 ${data.saved} 条`)
  } catch (error: any) {
    ElMessage.error(error.message || '采集失败')
  } finally {
    loading.value = false
  }
}

// 保存单个视频到数据库
const saveVideo = async (video: any) => {
  try {
    const platform = activePlatform.value
    const videoId = video.video_id || video.bvid || video.aweme_id

    // 保存到采集表
    await collectorService.get(API_URL.COLLECTOR.VIDEO_SAVE(videoId, platform))

    // 如果选择了收藏夹，同时保存到收藏夹
    if (selectedCollectionId.value) {
      await service.post(API_URL.USER.COLLECTIONS, {
        item_type: 'video',
        item_id: String(videoId),
        notes: video.title || video.name || '视频收藏',
        folder: selectedCollectionId.value
      } as any)
    }

    ElMessage.success('保存成功')
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  }
}

// 保存所有视频
const saveAllVideos = async () => {
  if (videos.value.length === 0) {
    ElMessage.warning('没有可保存的视频')
    return
  }
  try {
    for (const video of videos.value) {
      await saveVideo(video)
    }
    ElMessage.success('全部保存成功')
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  }
}

// 跳转到分析页面
const goToAnalysis = (video: any) => {
  const url = video.url || ''
  window.location.href = `/analysis?url=${encodeURIComponent(url)}&platform=${activePlatform.value}`
}

onMounted(() => {
  // 加载后自动获取热门
  fetchTrending()
  // 获取收藏夹列表
  fetchCollections()
})
</script>

<template>
  <div class="manual-collect-page">
    <div class="page-header">
      <h2>手动数据采集</h2>
      <p>选择平台和采集方式，获取视频数据并入库</p>
    </div>

    <!-- 平台选择 -->
    <el-card class="platform-card">
      <div class="platform-tabs">
        <el-radio-group v-model="activePlatform" @change="activeTab = 'trending'">
          <el-radio-button value="bilibili">B站</el-radio-button>
          <el-radio-button value="douyin">抖音</el-radio-button>
        </el-radio-group>
      </div>
    </el-card>

    <!-- 采集类型 -->
    <el-card class="type-card">
      <el-tabs v-model="activeTab">
        <!-- 热门/排行榜 -->
        <el-tab-pane label="热门/排行榜" name="trending">
          <div class="action-bar">
            <el-input
              v-model="searchForm.limit"
              type="number"
              placeholder="采集数量"
              style="width: 120px"
            />
            <el-button type="primary" @click="fetchTrending" :loading="loading">
              获取热门视频
            </el-button>
          </div>
        </el-tab-pane>

        <!-- 分区视频 -->
        <el-tab-pane label="分区视频" name="region" v-if="activePlatform === 'bilibili'">
          <div class="action-bar">
            <el-select v-model="regionForm.rid" placeholder="选择分区" style="width: 150px">
              <el-option
                v-for="region in bilibiliRegions"
                :key="region.id"
                :label="region.name"
                :value="region.id"
              />
            </el-select>
            <el-input
              v-model="regionForm.pn"
              type="number"
              placeholder="页码"
              style="width: 80px"
            />
            <el-button type="primary" @click="fetchRegionVideos" :loading="loading">
              获取分区视频
            </el-button>
          </div>
        </el-tab-pane>

        <!-- UP主视频 -->
        <el-tab-pane label="UP主视频" name="creator" v-if="activePlatform === 'bilibili'">
          <div class="action-bar">
            <el-input
              v-model="creatorForm.creator_id"
              placeholder="UP主ID (如: 202656997)"
              style="width: 200px"
              @keyup.enter="fetchCreatorInfo"
            />
            <el-button @click="fetchCreatorInfo" :loading="loading">
              查询UP主
            </el-button>
            <el-divider direction="vertical" />
            <el-input
              v-model="creatorForm.limit"
              type="number"
              placeholder="采集数量"
              style="width: 100px"
            />
            <el-button type="primary" @click="collectCreatorVideos" :loading="loading">
              采集视频入库
            </el-button>
          </div>

          <!-- UP主信息 -->
          <div v-if="creatorInfo" class="creator-info">
            <el-descriptions :column="4" border>
              <el-descriptions-item label="UP主">{{ creatorInfo.name }}</el-descriptions-item>
              <el-descriptions-item label="MID">{{ creatorInfo.creator_id }}</el-descriptions-item>
              <el-descriptions-item label="粉丝数">{{ formatNumber(creatorInfo.follower_count) }}</el-descriptions-item>
              <el-descriptions-item label="视频数">{{ formatNumber(creatorInfo.video_count) }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>

        <!-- 关键词搜索 -->
        <el-tab-pane label="关键词搜索" name="search">
          <div class="action-bar">
            <el-input
              v-model="searchForm.keyword"
              placeholder="输入搜索关键词"
              style="width: 250px"
              @keyup.enter="handleSearch"
            />
            <el-input
              v-model="searchForm.limit"
              type="number"
              placeholder="数量"
              style="width: 100px"
            />
            <el-button type="primary" @click="handleSearch" :loading="loading">
              搜索
            </el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 结果展示 -->
    <el-card class="result-card" v-if="videos.length > 0">
      <template #header>
        <div class="result-header">
          <span>采集结果 ({{ stats.fetched }} 条，已入库 {{ stats.saved }} 条)</span>
          <div style="display: flex; gap: 10px; align-items: center;">
            <el-select v-model="selectedCollectionId" placeholder="选择收藏夹" clearable style="width: 150px">
              <el-option v-for="c in collections" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-button type="success" size="small" @click="saveAllVideos">
              批量保存
            </el-button>
          </div>
        </div>
      </template>

      <div class="videos-grid">
        <div v-for="video in videos" :key="video.video_id || video.bvid || video.aweme_id" class="video-item">
          <!-- 封面 -->
          <div class="video-cover">
            <img :src="getCoverUrl(video)" alt="cover" @error="handleCoverError($event)" />
            <span class="duration">{{ video.duration ? Math.floor(video.duration / 60) + ':' + (video.duration % 60).toString().padStart(2, '0') : '' }}</span>
          </div>
          <!-- 信息 -->
          <div class="video-info">
            <div class="video-title" :title="video.title">{{ video.title }}</div>
            <div class="video-meta">
              <span class="author">{{ video.creator_name || video.owner?.name || video.author?.name || '' }}</span>
            </div>
            <div class="video-stats">
              <span><i class="el-icon-view"></i> {{ formatNumber(getMetricValue(video, 'play_count')) }}</span>
              <span><i class="el-icon-star-on"></i> {{ formatNumber(getMetricValue(video, 'like_count')) }}</span>
              <span><i class="el-icon-chat-dot-round"></i> {{ formatNumber(getMetricValue(video, 'comment_count')) }}</span>
            </div>
            <div class="video-actions">
              <el-button size="small" type="primary" @click="goToAnalysis(video)">分析</el-button>
              <el-button size="small" @click="saveVideo(video)">保存</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="videos.length === 0 && !loading" description="暂无数据，请选择采集方式" />
  </div>
</template>

<style scoped lang="scss">
.manual-collect-page {
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

.platform-card {
  margin-bottom: 20px;

  .platform-tabs {
    display: flex;
    justify-content: center;
  }
}

.type-card {
  margin-bottom: 20px;

  .action-bar {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 20px;
  }

  .creator-info {
    margin-top: 20px;
  }
}

.result-card {
  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.video-item {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.3s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .video-cover {
    position: relative;
    height: 160px;
    background: #f5f5f5;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .duration {
      position: absolute;
      bottom: 8px;
      right: 8px;
      background: rgba(0, 0, 0, 0.7);
      color: #fff;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 12px;
    }
  }

  .video-info {
    padding: 12px;

    .video-title {
      font-size: 14px;
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-bottom: 8px;
    }

    .video-meta {
      font-size: 12px;
      color: #999;
      margin-bottom: 8px;

      .author {
        color: #666;
      }
    }

    .video-stats {
      display: flex;
      gap: 12px;
      font-size: 12px;
      color: #999;
      margin-bottom: 12px;

      span {
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }

    .video-actions {
      display: flex;
      gap: 8px;
    }
  }
}
</style>
