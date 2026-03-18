<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const loading = ref(false)
const videoUrl = ref('')

// Analysis result placeholder
const analysisResult = ref<any>(null)

// Mock analysis data
const mockAnalysis = {
  video: {
    title: '如何用3句话留住用户',
    cover: 'https://picsum.photos/400/300',
    platform: '抖音',
    stats: { views: 125000, likes: 8500, comments: 320 }
  },
  hook3s: {
    content: '“别划走！看完这3句话，让你月瘦10斤”',
    type: '利益式 + 悬念式'
  },
  structure: {
    type: '是什么-为什么-怎么办',
    parts: [
      { time: '0-15s', title: '开场hook', content: '用痛点吸引注意' },
      { time: '15-45s', title: '问题解析', content: '解释为什么失败' },
      { time: '45-60s', title: '解决方案', content: '给出具体方法' }
    ]
  },
  keywords: ['减肥', '方法', '坚持', '效果', '饮食'],
  sentiment: 0.75
}

const handleAnalyze = async () => {
  if (!videoUrl.value) return
  loading.value = true
  // Simulate API call
  setTimeout(() => {
    analysisResult.value = mockAnalysis
    loading.value = false
  }, 1500)
}

const handleCollect = (type: string) => {
  console.log('Collect:', type)
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
      <el-input
        v-model="videoUrl"
        placeholder="请输入抖音/B站视频链接"
        size="large"
        @keyup.enter="handleAnalyze"
      >
        <template #append>
          <el-button type="primary" @click="handleAnalyze" :loading="loading">
            开始分析
          </el-button>
        </template>
      </el-input>
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
            <p>播放: {{ analysisResult.video.stats.views }} | 点赞: {{ analysisResult.video.stats.likes }} | 评论: {{ analysisResult.video.stats.comments }}</p>
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
          <p class="highlight">本视频成功关键在于开场3秒的<strong>利益+悬念</strong>组合，以及结尾提供的<strong>实用方法</strong>。</p>
        </div>
      </el-card>

      <!-- Hook 3s -->
      <el-card class="insight-card">
        <template #header>
          <div class="card-header">
            <span>黄金3秒</span>
            <el-button type="primary" link @click="handleCollect('hook')">
              <el-icon><Star /></el-icon> 一键收藏
            </el-button>
          </div>
        </template>
        <div class="hook-content">
          <p class="hook-text">"{{ analysisResult.hook3s.content }}"</p>
          <el-tag type="success">{{ analysisResult.hook3s.type }}</el-tag>
        </div>
      </el-card>

      <!-- Structure -->
      <el-card class="insight-card">
        <template #header>
          <div class="card-header">
            <span>脚本结构</span>
            <el-button type="primary" link @click="handleCollect('structure')">
              <el-icon><Star /></el-icon> 一键收藏
            </el-button>
          </div>
        </template>
        <div class="structure-content">
          <el-tag type="warning">{{ analysisResult.structure.type }}</el-tag>
          <div class="structure-timeline">
            <div v-for="(part, index) in analysisResult.structure.parts" :key="index" class="timeline-item">
              <div class="time">{{ part.time }}</div>
              <div class="title">{{ part.title }}</div>
              <div class="desc">{{ part.content }}</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Keywords -->
      <el-card class="insight-card">
        <template #header>
          <div class="card-header">
            <span>关键词</span>
          </div>
        </template>
        <div class="keywords">
          <el-tag v-for="kw in analysisResult.keywords" :key="kw" type="info">{{ kw }}</el-tag>
        </div>
      </el-card>
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

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
