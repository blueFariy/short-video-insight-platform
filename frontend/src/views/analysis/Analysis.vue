<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import service, { API_URL } from '@/api'

const router = useRouter()
const loading = ref(false)
const videoUrl = ref('')
const videoPlatform = ref('')
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
    const videoData = await service.post(API_URL.VIDEO.PROCESS, {
      url: videoUrl.value,
      platform: videoPlatform.value || undefined
    }) as any

    // Call insight service for comprehensive analysis
    const insightData = await service.post(API_URL.INSIGHT.COMPREHENSIVE, {
      video_title: videoData.title || '视频分析',
      video_script: videoData.script || '',
      keyframes: videoData.keyframes || [],
      duration: videoData.duration
    }) as any

    analysisResult.value = {
      video: {
        title: videoData.title,
        cover: videoData.cover_url,
        platform: videoData.platform,
        stats: {
          views: videoData.views || 0,
          likes: videoData.likes || 0,
          comments: videoData.comments || 0
        }
      },
      insight: insightData
    }

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

// Handle collect
const handleCollect = async (type: string) => {
  if (!analysisResult.value) return

  try {
    await service.post(API_URL.USER.ADD_COLLECTION, {
      title: analysisResult.value.video.title,
      type,
      content: type === 'hook'
        ? analysisResult.value.insight.hook?.hook_text
        : JSON.stringify(analysisResult.value.insight.structure?.segments),
      tags: [type]
    })
    ElMessage.success('收藏成功')
  } catch (error) {
    ElMessage.info('收藏功能演示')
  }
}

// Handle save to library
const handleSave = () => {
  handleCollect('script')
}
</script>

<template>
  <div class="analysis-page">
    <div class="page-header">
      <h2>AI爆款拆解</h2>
      <p>输入视频链接，AI自动生成深度分析报告</p>
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
  </div>
</template>

<style scoped lang="scss">
.analysis-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;

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
