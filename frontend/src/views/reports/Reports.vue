<script setup lang="ts">
import { ref } from 'vue'

const reports = ref([
  { id: 1, title: '2024年第11周美妆行业趋势报告', type: 'weekly', date: '2024-03-15', views: 1250 },
  { id: 2, title: '2024年2月短视频内容趋势月报', type: 'monthly', date: '2024-03-01', views: 980 },
  { id: 3, title: '2024年第10周美妆行业趋势报告', type: 'weekly', date: '2024-03-08', views: 890 }
])

const activeTab = ref('weekly')
</script>

<template>
  <div class="reports-page">
    <div class="page-header">
      <h2>趋势风向标</h2>
      <p>每周/每月自动生成的行业趋势洞察报告</p>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="report-tabs">
      <el-tab-pane label="周报" name="weekly">
        <el-card v-for="report in reports.filter(r => r.type === 'weekly')" :key="report.id" class="report-card">
          <div class="report-content">
            <div class="report-icon">
              <el-icon size="32" color="#409eff"><Document /></el-icon>
            </div>
            <div class="report-info">
              <h3>{{ report.title }}</h3>
              <p>发布于 {{ report.date }} | 阅读 {{ report.views }}</p>
            </div>
            <el-button type="primary">查看详情</el-button>
          </div>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="月报" name="monthly">
        <el-card v-for="report in reports.filter(r => r.type === 'monthly')" :key="report.id" class="report-card">
          <div class="report-content">
            <div class="report-icon">
              <el-icon size="32" color="#67c23a"><DataAnalysis /></el-icon>
            </div>
            <div class="report-info">
              <h3>{{ report.title }}</h3>
              <p>发布于 {{ report.date }} | 阅读 {{ report.views }}</p>
            </div>
            <el-button type="primary">查看详情</el-button>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped lang="scss">
.reports-page {
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

.report-tabs {
  :deep(.el-tabs__content) {
    padding-top: 20px;
  }
}

.report-card {
  margin-bottom: 16px;

  .report-content {
    display: flex;
    align-items: center;
    gap: 20px;

    .report-icon {
      flex-shrink: 0;
    }

    .report-info {
      flex: 1;

      h3 {
        font-size: 16px;
        margin-bottom: 8px;
      }

      p {
        font-size: 13px;
        color: var(--text-secondary);
      }
    }
  }
}
</style>
