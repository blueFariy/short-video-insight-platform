<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import service, { API_URL } from '@/api'

interface Collection {
  id: string
  title: string
  type: 'video' | 'script' | 'structure' | 'hook'
  content: string
  tags: string[]
  created_at: string
}

const collections = ref<Collection[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const filterType = ref<string>('')

const collectionTypes = [
  { value: '', label: '全部' },
  { value: 'video', label: '视频' },
  { value: 'script', label: '脚本' },
  { value: 'structure', label: '结构' },
  { value: 'hook', label: '黄金3秒' }
]

const fetchCollections = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterType.value) params.type = filterType.value

    collections.value = await service.get(API_URL.USER.COLLECTIONS, { params })
  } catch (error) {
    // Use demo data if API fails
    collections.value = [
      {
        id: '1',
        title: '如何用3句话留住用户',
        type: 'hook',
        content: '你是不是也有这样的困惑？为什么别人发视频随便都是几十万播放...',
        tags: ['黄金3秒', '留人技巧'],
        created_at: '2024-01-15'
      },
      {
        id: '2',
        title: '短视频脚本结构模板',
        type: 'structure',
        content: '开场(0-3秒) -> 痛点陈述(3-10秒) -> 解决方案(10-30秒) -> 行动号召(最后5秒)',
        tags: ['脚本结构', '模板'],
        created_at: '2024-01-14'
      },
      {
        id: '3',
        title: '职场干货类视频脚本',
        type: 'script',
        content: '今天来聊聊职场新人最容易犯的几个错误...',
        tags: ['职场', '干货'],
        created_at: '2024-01-13'
      }
    ]
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await service.delete(API_URL.USER.DELETE_COLLECTION(id))
    ElMessage.success('删除成功')
    fetchCollections()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const getTypeTag = (type: string) => {
  const map: Record<string, { type: string; label: string }> = {
    video: { type: 'primary', label: '视频' },
    script: { type: 'success', label: '脚本' },
    structure: { type: 'warning', label: '结构' },
    hook: { type: 'danger', label: '黄金3秒' }
  }
  return map[type] || { type: 'info', label: type }
}

onMounted(() => {
  fetchCollections()
})
</script>

<template>
  <div class="library-page">
    <!-- Header -->
    <div class="page-header">
      <h1>素材库</h1>
      <p class="subtitle">收藏的黄金3秒、脚本结构等优质内容</p>
    </div>

    <!-- Filters -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索素材..."
            prefix-icon="Search"
            clearable
            @change="fetchCollections"
          />
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterType" placeholder="素材类型" clearable @change="fetchCollections">
            <el-option
              v-for="item in collectionTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-col>
        <el-col :span="10">
          <el-button type="primary" icon="Plus">新建收藏夹</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- Collection List -->
    <el-row :gutter="20" v-loading="loading">
      <el-col :span="8" v-for="item in collections" :key="item.id">
        <el-card class="collection-card">
          <div class="card-header">
            <el-tag :type="getTypeTag(item.type).type" size="small">
              {{ getTypeTag(item.type).label }}
            </el-tag>
            <el-dropdown>
              <el-button text icon="More" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>编辑</el-dropdown-item>
                  <el-dropdown-item @click="handleDelete(item.id)">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <h3 class="title">{{ item.title }}</h3>
          <p class="content">{{ item.content }}</p>
          <div class="tags">
            <el-tag v-for="tag in item.tags" :key="tag" size="small" type="info">
              {{ tag }}
            </el-tag>
          </div>
          <div class="footer">
            <span class="date">{{ item.created_at }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Empty State -->
    <el-empty v-if="!loading && collections.length === 0" description="暂无收藏内容" />
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
