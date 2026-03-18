<script setup lang="ts">
import { ref } from 'vue'

const competitors = ref([
  { id: 1, name: '美妆博主A', platform: '抖音', followers: '120W', videos: 5, trend: 'up' },
  { id: 2, name: '剧情号B', platform: '抖音', followers: '85W', videos: 3, trend: 'up' },
  { id: 3, name: '知识博主C', platform: 'B站', followers: '50W', videos: 2, trend: 'stable' }
])

const dialogVisible = ref(false)
const newCompetitor = ref({ name: '', platform: 'douyin', url: '' })

const handleAdd = () => {
  dialogVisible.value = true
}

const confirmAdd = () => {
  competitors.value.push({
    id: Date.now(),
    name: newCompetitor.value.name,
    platform: newCompetitor.value.platform === 'douyin' ? '抖音' : 'B站',
    followers: '0',
    videos: 0,
    trend: 'up'
  })
  dialogVisible.value = false
  newCompetitor.value = { name: '', platform: 'douyin', url: '' }
}

const handleDelete = (id: number) => {
  competitors.value = competitors.value.filter(c => c.id !== id)
}
</script>

<template>
  <div class="monitor-page">
    <div class="page-header">
      <h2>竞品与达人透视</h2>
      <p>追踪您关注的竞品账号，实时了解最新动态</p>
    </div>

    <!-- Stats -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon size="32" color="#409eff"><User /></el-icon>
            <div class="stat-info">
              <span class="value">{{ competitors.length }}</span>
              <span class="label">监控中</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon size="32" color="#67c23a"><VideoCamera /></el-icon>
            <div class="stat-info">
              <span class="value">10</span>
              <span class="label">新增视频</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon size="32" color="#e6a23a"><TrendCharts /></el-icon>
            <div class="stat-info">
              <span class="value">3</span>
              <span class="label">增长达人</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon size="32" color="#f56c6c"><Warning /></el-icon>
            <div class="stat-info">
              <span class="value">1</span>
              <span class="label">预警</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Competitor List -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>监控列表</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon> 添加监控
          </el-button>
        </div>
      </template>

      <el-table :data="competitors" style="width: 100%">
        <el-table-column prop="name" label="账号名称" width="180">
          <template #default="{ row }">
            <div class="creator-cell">
              <el-avatar :size="36">{{ row.name[0] }}</el-avatar>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="platform" label="平台" width="100" />
        <el-table-column prop="followers" label="粉丝" width="120" />
        <el-table-column label="近期视频" width="120">
          <template #default="{ row }">
            <el-tag type="info">{{ row.videos }}个</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="趋势" width="100">
          <template #default="{ row }">
            <el-icon v-if="row.trend === 'up'" color="#67c23a"><Top /></el-icon>
            <el-icon v-else-if="row.trend === 'down'" color="#f56c6c"><Bottom /></el-icon>
            <el-icon v-else><Minus /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button type="primary" link>查看详情</el-button>
            <el-button type="danger" link @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add Dialog -->
    <el-dialog v-model="dialogVisible" title="添加监控" width="400px">
      <el-form label-width="80px">
        <el-form-item label="账号名称">
          <el-input v-model="newCompetitor.name" placeholder="请输入账号名称" />
        </el-form-item>
        <el-form-item label="平台">
          <el-select v-model="newCompetitor.platform">
            <el-option label="抖音" value="douyin" />
            <el-option label="B站" value="bilibili" />
            <el-option label="小红书" value="xiaohongshu" />
          </el-select>
        </el-form-item>
        <el-form-item label="主页链接">
          <el-input v-model="newCompetitor.url" placeholder="请输入主页链接" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.monitor-page {
  padding: 20px;
  max-width: 1400px;
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
        }

        .label {
          font-size: 12px;
          color: var(--text-secondary);
        }
      }
    }
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.creator-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
