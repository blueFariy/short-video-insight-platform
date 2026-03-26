<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import service, { videoService, insightService, API_URL } from '@/api'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const videoUrl = ref('')
const videoPlatform = ref('')

// 收藏夹相关
const collections = ref<any[]>([])
const selectedCollectionId = ref<string>('')

// 历史记录相关
const historyDialogVisible = ref(false)
const historyLoading = ref(false)
const analysisHistory = ref<any[]>([])

// 当前分析的video ID（用于去重和识别）
const currentVideoId = ref<string>('')

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

// 获取分析历史记录
const fetchAnalysisHistory = async () => {
  historyLoading.value = true
  try {
    const res = await service.get(API_URL.INSIGHT.VIDEO_INSIGHT_ALL, {
      params: { page: 1, page_size: 100 }
    }) as any
    const items = res?.items || []

    analysisHistory.value = items
      .filter((item: any) => item.video_id && item.video_id !== 0)
      .map((item: any) => {
        // 优先使用后端返回的 video_info
        const videoInfo = item.video_info || {}
        // 处理封面URL，解决B站图片403问题
        let coverUrl = videoInfo.cover_url || ''
        if (coverUrl && coverUrl.includes('hdslb.com')) {
          coverUrl = `${API_URL.COLLECTOR.IMAGE_PROXY}?url=${encodeURIComponent(coverUrl)}`
        }
        // 构建insight数据用于查看
        const insightData = {
          video: {
            title: videoInfo.title || item.ai_summary?.substring(0, 30) || '分析报告',
            cover: coverUrl,
            platform: videoInfo.platform || '',
            url: videoInfo.url || '',
            stats: {
              views: videoInfo.play_count || 0,
              likes: videoInfo.like_count || 0,
              comments: videoInfo.comment_count || 0
            }
          },
          insight: {
            overall: {
              summary: item.ai_summary || '',
              highlights: item.keywords || [],
              dimensions: item.viral_factors || {},
              improvements: item.improvements || []
            },
            hook: item.hook_3s ? {
              hook_text: item.hook_3s,
              hook_type: item.hook_type || ''
            } : null,
            structure: item.structure_analysis || (item.structure_type ? { type: item.structure_type } : null)
          }
        }
        // 直接使用后端返回的综合评分，或者前端计算
        let overallScore = item.overall_score || 0
        if (!overallScore) {
          const dimensions = item.viral_factors || {}
          if (dimensions) {
            const scoreValues: number[] = Object.entries(dimensions)
              .filter(([k, v]) => k.endsWith('_score') && typeof v === 'number')
              .map(([, v]) => v as number)
            if (scoreValues.length > 0) {
              overallScore = Math.round(scoreValues.reduce((sum, v) => sum + v, 0) / scoreValues.length)
            }
          }
        }
        return {
          id: item.id,
          video_id: item.video_id,
          title: videoInfo.title || item.ai_summary?.substring(0, 30) || '分析报告',
          platform: videoInfo.platform || '',
          cover: coverUrl,
          stats: {
            views: videoInfo.play_count || 0,
            likes: videoInfo.like_count || 0,
            comments: videoInfo.comment_count || 0
          },
          overall_score: overallScore,
          insight: insightData,
          video: videoInfo,
          created_at: item.created_at
        }
      })
  } catch (error) {
    console.error('Fetch history error:', error)
  } finally {
    historyLoading.value = false
  }
}

// 打开历史记录对话框
const openHistoryDialog = () => {
  fetchAnalysisHistory()
  historyDialogVisible.value = true
}

// 从历史记录查看分析
const viewFromHistory = async (item: any) => {
  // 先关闭对话框
  historyDialogVisible.value = false

  if (!item.video_id) {
    ElMessage.warning('无效的视频ID')
    return
  }

  try {
    // 从后端获取完整的insight详情
    const res = await service.get(API_URL.INSIGHT.VIDEO_INSIGHT_DETAIL(item.video_id)) as any

    if (res) {
      const videoInfo = res.video_info || {}
      // 处理封面URL，解决B站图片403问题
      let coverUrl = videoInfo.cover_url || ''
      if (coverUrl && coverUrl.includes('hdslb.com')) {
        coverUrl = `${API_URL.COLLECTOR.IMAGE_PROXY}?url=${encodeURIComponent(coverUrl)}`
      }
      // 计算综合评分
      let overallScore = res.overall_score || 0
      if (!overallScore) {
        const dimensions = res.viral_factors || {}
        const scoreValues: number[] = Object.entries(dimensions)
          .filter(([k, v]) => k.endsWith('_score') && typeof v === 'number')
          .map(([, v]) => v as number)
        if (scoreValues.length > 0) {
          overallScore = Math.round(scoreValues.reduce((sum, v) => sum + v, 0) / scoreValues.length)
        }
      }
      // 构建完整的分析结果
      analysisResult.value = {
        video: {
          title: videoInfo.title || res.ai_summary?.substring(0, 30) || '分析报告',
          cover: coverUrl,
          platform: videoInfo.platform || '',
          url: videoInfo.url || '',
          stats: {
            views: videoInfo.play_count || 0,
            likes: videoInfo.like_count || 0,
            comments: videoInfo.comment_count || 0
          }
        },
        insight: {
          overall: {
            summary: res.ai_summary || '',
            highlights: res.keywords || [],
            dimensions: res.viral_factors || {},
            improvements: res.improvements || [],
            overall_score: overallScore
          },
          hook: res.hook_3s ? {
            hook_text: res.hook_3s,
            hook_type: res.hook_type || ''
          } : null,
          structure: res.structure_analysis || (res.structure_type ? { type: res.structure_type } : null)
        }
      }
      // 设置相关信息
      videoUrl.value = videoInfo.url || ''
      videoPlatform.value = videoInfo.platform || ''
      currentVideoId.value = item.video_id?.toString() || ''
    } else {
      ElMessage.warning('未找到分析数据')
    }
  } catch (error) {
    console.error('获取分析详情失败:', error)
    // 如果获取失败，尝试使用已有的数据
    if (item.insight) {
      analysisResult.value = item.insight
      videoUrl.value = item.video?.url || ''
      videoPlatform.value = item.video?.platform || ''
      currentVideoId.value = item.video_id?.toString() || ''
    } else {
      ElMessage.error('获取分析数据失败')
    }
  }
}

// Auto-fill from query params
onMounted(() => {
  const url = route.query.url as string
  const platform = route.query.platform as string
  const itemId = route.query.item_id as string
  const insightStr = route.query.insight as string

  // 如果有insight数据（从素材库查看），直接加载
  if (insightStr) {
    try {
      const insightData = JSON.parse(decodeURIComponent(insightStr))
      analysisResult.value = insightData
      videoUrl.value = url ? decodeURIComponent(url) : ''
      videoPlatform.value = platform || ''
      currentVideoId.value = itemId || ''
    } catch (e) {
      console.error('Parse insight error:', e)
    }
  } else if (url) {
    videoUrl.value = decodeURIComponent(url)
    videoPlatform.value = platform
    // Auto start analysis if params exist
    handleAnalyze()
  }
  // 获取收藏夹列表
  fetchCollections()
})
const analysisResult = ref<any>(null)

// Platform options
const platforms = [
  { value: 'douyin', label: '抖音' },
  { value: 'bilibili', label: 'B站' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'kuaishou', label: '快手' }
]

// Handle video analysis
const handleAnalyze = async () => {
  if (!videoUrl.value) {
    ElMessage.warning('请输入视频链接')
    return
  }

  loading.value = true
  try {
    // Call video service to process video
    const videoData = await videoService.post(API_URL.VIDEO.PROCESS, {
      url: videoUrl.value,
      platform: videoPlatform.value || undefined
    }) as any

    // Call insight service for comprehensive analysis
    const insightData = await insightService.post(API_URL.INSIGHT.COMPREHENSIVE, {
      video_title: videoData.title || '视频分析',
      video_script: videoData.script || '',
      keyframes: videoData.keyframes || [],
      duration: videoData.duration
    }) as any

    // 处理封面URL，解决B站图片403问题
    let coverUrl = videoData.cover_url || ''
    if (coverUrl && coverUrl.includes('hdslb.com')) {
      coverUrl = `${API_URL.COLLECTOR.IMAGE_PROXY}?url=${encodeURIComponent(coverUrl)}`
    }

    // 计算综合评分
    let overallScore = insightData?.overall?.overall_score || 0
    if (!overallScore && insightData?.overall?.dimensions) {
      const dimensions = insightData.overall.dimensions
      const scoreValues: number[] = Object.entries(dimensions)
        .filter(([k, v]) => k.endsWith('_score') && typeof v === 'number')
        .map(([, v]) => v as number)
      if (scoreValues.length > 0) {
        overallScore = Math.round(scoreValues.reduce((sum, v) => sum + v, 0) / scoreValues.length)
      }
    }

    analysisResult.value = {
      video: {
        title: videoData.title,
        cover: coverUrl,
        platform: videoData.platform,
        url: videoData.url || videoUrl.value,
        stats: {
          // 兼容不同字段名
          views: videoData.view_count || videoData.views || 0,
          likes: videoData.like_count || videoData.likes || 0,
          comments: videoData.comment_count || videoData.comments || 0
        }
      },
      insight: {
        ...insightData,
        overall: {
          ...insightData.overall,
          overall_score: overallScore
        }
      }
    }

    // 保存video ID用于后续去重识别
    currentVideoId.value = videoData.video_info.video_id || videoData.video_info.aweme_id || videoUrl.value

    ElMessage.success('分析完成')
  } catch (error: any) {
    console.error('Analysis error:', error)
    // Use demo data if API fails
    analysisResult.value = getDemoData()
    ElMessage.info('使用演示数据')
  } finally {
    loading.value = false
  }
}

// Demo data when API is not available
const getDemoData = () => ({
  video: {
    title: '如何用3句话留住用户',
    cover: 'https://picsum.photos/400/300?random=1',
    platform: '抖音',
    stats: { views: 125000, likes: 8500, comments: 320 }
  },
  insight: {
    type: 'comprehensive',
    overall: {
      overall_score: 85,
      dimensions: {
        hook_score: 90,
        value_score: 85,
        emotion_score: 80,
        cta_score: 85,
        structure_score: 85
      },
      highlights: ['开场吸引力强', '内容价值高', '结尾行动号召明确'],
      improvements: ['可增加更多情感元素', '中间部分可以更紧凑'],
      summary: '这是一个典型的爆款视频结构，黄金3秒开场成功抓住用户注意力，内容提供了实用价值。'
    },
    hook: {
      hook_text: '"别划走！看完这3句话，让你月瘦10斤"',
      hook_type: '利益式 + 悬念式',
      analysis: '通过利益承诺（月瘦10斤）和悬念（哪3句话）双重吸引',
      suggestions: '可以尝试更多情感共鸣的表达方式'
    },
    structure: {
      segments: [
        { time: '0-15s', type: '开场hook', content: '用痛点吸引注意' },
        { time: '15-45s', type: '问题解析', content: '解释为什么失败' },
        { time: '45-60s', type: '解决方案', content: '给出具体方法' }
      ]
    }
  }
})

// Handle collect - 只更新已有收藏，不创建新记录
const handleCollect = async (type: string) => {
  if (!analysisResult.value) return

  if (!selectedCollectionId.value) {
    ElMessage.warning('请先选择收藏夹')
    return
  }

  try {
    // 使用视频URL作为唯一标识符，便于去重检查
    const videoId = currentVideoId.value || analysisResult.value.video.url || videoUrl.value

    // 构建要保存的数据
    const notesData = JSON.stringify({
      video: analysisResult.value.video,
      insight: analysisResult.value
    })

    // 先检查是否已存在相同视频的收藏
    const checkRes = await service.get(API_URL.USER.COLLECTIONS, {
      params: { page: 1, page_size: 10, item_id: videoId }
    }) as any

    const existingItems = checkRes?.items || []
    const existingItem = existingItems.find((item: any) => item.item_id === videoId)

    if (existingItem) {
      // 已存在该视频的收藏，更新为insight类型并保存分析数据
      await service.put(API_URL.USER.UPDATE_COLLECTION(existingItem.id), {
        item_type: 'insight',
        notes: notesData,
        tags: [type],
        folder: selectedCollectionId.value
      } as any)
      ElMessage.success('已更新为分析状态')
    } else {
      // 不存在该视频的收藏，不创建新记录，只提示用户
      ElMessage.info('该视频尚未收藏，请先从数据采集模块添加收藏后再分析')
    }
  } catch (error: any) {
    console.error('Save error:', error)
    ElMessage.error(error.message || '保存失败')
  }
}

// Handle save to library
const handleSave = async () => {
  if (!analysisResult.value) return

  try {
    // 构建视频信息
    const videoData = analysisResult.value.video
    const insightData = analysisResult.value.insight

    // 提取视频ID (platform_video_id)
    const platformVideoId = currentVideoId.value || videoData.url || ''

    // 从insight数据中提取结构化信息
    const requestData: any = {
      platform: videoData.platform || videoPlatform.value,
      video_id: platformVideoId,
      video_title: videoData.title,
      video_url: videoData.url,
      ai_summary: insightData?.overall?.summary || '',
      hook_3s: insightData?.analysis?.hook?.hook_text || '',
      hook_type: insightData?.analysis?.hook?.hook_type || '',
      structure_type: insightData?.analysis?.structure?.type || '',
      structure_analysis: insightData?.analysis?.structure ? { segments: insightData?.analysis.structure.segments } : null,
      keywords: insightData?.overall?.highlights || [],
      viral_factors: insightData?.overall?.dimensions || null,
      improvements: insightData?.overall?.improvements || []
    }

    // 调用保存insight接口
    await insightService.post(API_URL.INSIGHT.VIDEO_INSIGHTS, requestData)
    ElMessage.success('分析报告已保存到素材库')
  } catch (error: any) {
    console.error('Save insight error:', error)
    // 如果保存insight失败，回退到原来的保存方式
    handleCollect('script')
  }
}
</script>

<template>
  <div class="analysis-page">
    <div class="page-header">
      <div class="header-left">
        <h2>AI爆款拆解</h2>
        <p>输入视频链接，AI自动生成深度分析报告</p>
      </div>
      <el-button type="primary" link @click="openHistoryDialog">
        <el-icon><Clock /></el-icon> 历史记录
      </el-button>
    </div>

    <!-- Input Section -->
    <el-card class="input-card">
      <el-row :gutter="20">
        <el-col :span="18">
          <el-input
            v-model="videoUrl"
            placeholder="请输入抖音/B站/小红书/快手视频链接"
            size="large"
            @keyup.enter="handleAnalyze"
          >
            <template #prepend>
              <el-select v-model="videoPlatform" placeholder="选择平台" style="width: 120px">
                <el-option v-for="p in platforms" :key="p.value" :label="p.label" :value="p.value" />
              </el-select>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" size="large" :loading="loading" style="width: 100%" @click="handleAnalyze">
            {{ loading ? '分析中...' : '开始分析' }}
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Results Section -->
    <div v-if="analysisResult" class="results-section">
      <!-- Video Info -->
      <el-card class="video-card">
        <div class="video-header">
          <img :src="analysisResult.video.cover" alt="cover" class="cover" />
          <div class="video-info">
            <h3>{{ analysisResult.video.title }}</h3>
            <p>平台: {{ analysisResult.video.platform }}</p>
            <p>
              播放: {{ analysisResult.video.stats.views.toLocaleString() }} |
              点赞: {{ analysisResult.video.stats.likes.toLocaleString() }} |
              评论: {{ analysisResult.video.stats.comments.toLocaleString() }}
            </p>
          </div>
        </div>
      </el-card>

      <!-- Overall Score -->
      <el-card v-if="analysisResult.insight?.overall" class="score-card">
        <template #header>
          <div class="card-header">
            <span>综合评分</span>
          </div>
        </template>
        <div class="score-display">
          <div class="total-score">
            <span class="score">{{ analysisResult.insight.overall.overall_score }}</span>
            <span class="label">/100</span>
          </div>
          <div class="dimension-scores">
            <div class="dimension" v-for="(value, key) in analysisResult.insight.overall.dimensions" :key="key">
              <span class="dim-label">{{ String(key).replace('_score', '') }}</span>
              <el-progress :percentage="value" :stroke-width="8" />
            </div>
          </div>
        </div>
      </el-card>

      <!-- Core Insights -->
      <el-card class="insight-card core-insight">
        <template #header>
          <div class="card-header">
            <span>核心爆点总结</span>
          </div>
        </template>
        <div class="insight-content">
          <p class="highlight">{{ analysisResult.insight.overall?.summary || '分析完成' }}</p>
        </div>
      </el-card>

      <!-- Hook 3s -->
      <el-card v-if="analysisResult.insight?.hook" class="insight-card">
        <template #header>
          <div class="card-header">
            <span>黄金3秒</span>
            <el-button type="primary" link @click="handleCollect('hook')">
              <el-icon><Star /></el-icon> 一键收藏
            </el-button>
          </div>
        </template>
        <div class="hook-content">
          <p class="hook-text">"{{ analysisResult.insight.hook.hook_text }}"</p>
          <el-tag type="success">{{ analysisResult.insight.hook.hook_type }}</el-tag>
        </div>
      </el-card>

      <!-- Structure -->
      <el-card v-if="analysisResult.insight?.structure" class="insight-card">
        <template #header>
          <div class="card-header">
            <span>脚本结构</span>
            <el-button type="primary" link @click="handleCollect('structure')">
              <el-icon><Star /></el-icon> 一键收藏
            </el-button>
          </div>
        </template>
        <div class="structure-content">
          <div class="structure-timeline">
            <div v-for="(part, index) in analysisResult.insight.structure.segments" :key="index" class="timeline-item">
              <div class="time">{{ part.time }}</div>
              <div class="title">{{ part.type }}</div>
              <div class="desc">{{ part.content }}</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Highlights & Improvements -->
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="insight-card">
            <template #header>
              <span>亮点</span>
            </template>
            <ul class="list">
              <li v-for="(item, i) in analysisResult.insight.overall?.highlights" :key="i">{{ item }}</li>
            </ul>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="insight-card">
            <template #header>
              <span>改进建议</span>
            </template>
            <ul class="list">
              <li v-for="(item, i) in analysisResult.insight.overall?.improvements" :key="i">{{ item }}</li>
            </ul>
          </el-card>
        </el-col>
      </el-row>

      <!-- Actions -->
      <div class="actions">
        <el-select v-model="selectedCollectionId" placeholder="选择收藏夹" style="width: 150px">
          <el-option v-for="c in collections" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" @click="handleSave">
          <el-icon><Collection /></el-icon> 保存到素材库
        </el-button>
        <el-button @click="router.push('/reports')">
          <el-icon><TrendCharts /></el-icon> 查看趋势报告
        </el-button>
      </div>
    </div>

    <!-- Empty State -->
    <el-empty v-else description="输入视频链接开始分析" />

    <!-- 历史记录对话框 -->
    <el-dialog v-model="historyDialogVisible" title="分析历史记录" width="900px">
      <div v-loading="historyLoading">
        <el-table :data="analysisHistory" v-if="analysisHistory.length > 0" max-height="400">
          <el-table-column label="封面" width="80">
            <template #default="{ row }">
              <el-image v-if="row.cover" :src="row.cover" fit="cover" style="width: 60px; height: 45px; border-radius: 4px;" />
              <div v-else class="no-cover">无</div>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="视频标题" min-width="150" show-overflow-tooltip />
          <el-table-column prop="platform" label="平台" width="70">
            <template #default="{ row }">
              <el-tag v-if="row.platform" :type="row.platform === 'bilibili' ? 'primary' : row.platform === 'douyin' ? 'danger' : row.platform === 'xiaohongshu' ? 'success' : 'warning'" size="small">
                {{ row.platform === 'bilibili' ? 'B站' : row.platform === 'douyin' ? '抖音' : row.platform === 'xiaohongshu' ? '小红书' : row.platform === 'kuaishou' ? '快手' : row.platform }}
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="播放/点赞/评论" width="130">
            <template #default="{ row }">
              {{ (row.stats?.views || 0).toLocaleString() }} /
              {{ (row.stats?.likes || 0).toLocaleString() }} /
              {{ (row.stats?.comments || 0).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="overall_score" label="评分" width="70">
            <template #default="{ row }">
              <el-tag v-if="row.overall_score" :type="row.overall_score >= 80 ? 'success' : row.overall_score >= 60 ? 'warning' : 'danger'" size="small">
                {{ row.overall_score }}
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="分析时间" width="150">
            <template #default="{ row }">
              {{ new Date(row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="viewFromHistory(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无分析历史记录" />
      </div>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.analysis-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;

  .no-cover {
    width: 60px;
    height: 45px;
    background: #f5f7fa;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #999;
    font-size: 12px;
  }
}

.page-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;

  .header-left {
    flex: 1;
  }

  h2 {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  p {
    color: var(--text-secondary);
  }
}

.input-card {
  margin-bottom: 20px;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-card {
  .video-header {
    display: flex;
    gap: 20px;

    .cover {
      width: 240px;
      height: 180px;
      object-fit: cover;
      border-radius: 8px;
    }

    .video-info {
      h3 {
        font-size: 18px;
        margin-bottom: 12px;
      }

      p {
        color: var(--text-secondary);
        margin-bottom: 8px;
      }
    }
  }
}

.score-card {
  .score-display {
    display: flex;
    gap: 40px;

    .total-score {
      text-align: center;

      .score {
        font-size: 48px;
        font-weight: bold;
        color: #409eff;
      }

      .label {
        font-size: 18px;
        color: #999;
      }
    }

    .dimension-scores {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 12px;

      .dimension {
        display: flex;
        align-items: center;
        gap: 12px;

        .dim-label {
          width: 80px;
          font-size: 13px;
          color: #666;
        }

        .el-progress {
          flex: 1;
        }
      }
    }
  }
}

.insight-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &.core-insight {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;

    :deep(.el-card__header) {
      border-bottom: 1px solid rgba(255,255,255,0.2);
    }

    :deep(.el-card__body) {
      padding: 20px;
    }

    .highlight {
      font-size: 16px;
      line-height: 1.8;
    }
  }
}

.hook-content {
  .hook-text {
    font-size: 18px;
    font-weight: 500;
    color: var(--primary-color);
    margin-bottom: 12px;
    padding: 16px;
    background: #f0f9ff;
    border-radius: 8px;
  }
}

.structure-content {
  .structure-timeline {
    margin-top: 16px;

    .timeline-item {
      display: flex;
      align-items: center;
      padding: 12px;
      background: #f5f7fa;
      border-radius: 6px;
      margin-bottom: 8px;

      .time {
        font-weight: 600;
        color: var(--primary-color);
        width: 80px;
      }

      .title {
        font-weight: 500;
        width: 100px;
      }

      .desc {
        color: var(--text-secondary);
        flex: 1;
      }
    }
  }
}

.list {
  padding-left: 20px;

  li {
    margin-bottom: 8px;
    color: #666;
  }
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}
</style>
