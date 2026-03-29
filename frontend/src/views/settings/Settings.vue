<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { collectorService, API_URL } from '@/api'

// 平台选项
const platformOptions = [
  { label: '抖音', value: 'douyin' },
  { label: 'B站', value: 'bilibili' },
  { label: '小红书', value: 'xiaohongshu' }
]

// 分类选项（B站视频主分区）
const categoryOptions = [
  { label: '动画', value: '动画' },
  { label: '音乐', value: '音乐' },
  { label: '游戏', value: '游戏' },
  { label: '娱乐', value: '娱乐' },
  { label: '电视剧', value: '电视剧' },
  { label: '番剧', value: '番剧' },
  { label: '电影', value: '电影' },
  { label: '知识', value: '知识' },
  { label: '舞蹈', value: '舞蹈' },
  { label: '时尚', value: '时尚' },
  { label: '生活', value: '生活' },
  { label: '国创', value: '国创' },
  { label: '纪录片', value: '纪录片' },
  { label: '影视', value: '影视' },
  { label: '科技', value: '科技' },
  { label: '资讯', value: '资讯' },
  { label: '美食', value: '美食' },
  { label: '动物圈', value: '动物圈' },
  { label: '鬼畜', value: '鬼畜' },
  { label: '汽车', value: '汽车' },
  { label: '运动', value: '运动' },
  { label: 'VLOG', value: 'VLOG' }
]

// 预警级别选项
const alertLevelOptions = [
  { label: '黄色预警', value: 'yellow' },
  { label: '橙色预警', value: 'orange' },
  { label: '红色预警', value: 'red' }
]

// 通知方式选项
const notificationOptions = [
  { label: '平台通知', value: 'platform' },
  { label: 'App通知', value: 'app' }
]

// 表单数据
const formData = ref({
  platforms: ['douyin', 'bilibili', 'xiaohongshu'] as string[],
  categories: [] as string[],
  interestKeywords: [] as string[],
  alertLevels: ['yellow', 'orange', 'red'] as string[],
  notificationChannels: ['app'] as string[]
})

// 关键词输入
const keywordInput = ref('')

// 弹窗显示状态
const dialogVisible = ref(false)

// 加载状态
const loading = ref(false)

// 弹窗标题
const dialogTitle = '个人设置'

// 打开弹窗
const open = () => {
  dialogVisible.value = true
  fetchUserInterest()
}

// 关闭弹窗
const close = () => {
  dialogVisible.value = false
}

// 添加关键词
const addKeyword = () => {
  const keyword = keywordInput.value.trim()
  if (keyword && !formData.value.interestKeywords.includes(keyword)) {
    formData.value.interestKeywords.push(keyword)
  }
  keywordInput.value = ''
}

// 删除关键词
const removeKeyword = (keyword: string) => {
  const index = formData.value.interestKeywords.indexOf(keyword)
  if (index > -1) {
    formData.value.interestKeywords.splice(index, 1)
  }
}

// 获取用户兴趣配置
const fetchUserInterest = async () => {
  loading.value = true
  try {
    const res = await collectorService.get(API_URL.COLLECTOR.USER_INTEREST_GET) as any
    const data = res || {}
    if (data) {
      formData.value.platforms = data.platforms || ['douyin', 'bilibili', 'xiaohongshu']

      // 从category_weights中提取分类
      if (data.category_weights) {
        formData.value.categories = Object.keys(data.category_weights)
      }

      formData.value.interestKeywords = data.interest_keywords || []
      formData.value.alertLevels = data.alert_levels || ['yellow', 'orange', 'red']
      formData.value.notificationChannels = data.notification_channels || ['app']
    }
  } catch (error) {
    console.error('获取用户兴趣配置失败:', error)
  } finally {
    loading.value = false
  }
}

// 保存用户兴趣配置
const saveUserInterest = async () => {
  loading.value = true
  try {
    // 构建category_weights
    const categoryWeights: Record<string, number> = {}
    formData.value.categories.forEach(cat => {
      categoryWeights[cat] = 0.8
    })

    await collectorService.post(API_URL.COLLECTOR.USER_INTEREST_UPDATE, {
      category_weights: categoryWeights,
      interest_keywords: formData.value.interestKeywords,
      platforms: formData.value.platforms,
      alert_levels: formData.value.alertLevels,
      notification_channels: formData.value.notificationChannels
    })

    ElMessage.success('保存成功')
    close()
  } catch (error) {
    console.error('保存用户兴趣配置失败:', error)
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

// 暴露open方法
defineExpose({
  open
})
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="600px"
    :close-on-click-modal="false"
    @close="close"
  >
    <div v-loading="loading">
      <!-- 感兴趣的平台 -->
      <el-form-item label="感兴趣的平台">
        <el-checkbox-group v-model="formData.platforms">
          <el-checkbox
            v-for="option in platformOptions"
            :key="option.value"
            :label="option.value"
          >
            {{ option.label }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <!-- 感兴趣的分类 -->
      <el-form-item label="感兴趣的分类">
        <el-checkbox-group v-model="formData.categories">
          <el-checkbox
            v-for="option in categoryOptions"
            :key="option.value"
            :label="option.value"
          >
            {{ option.label }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <!-- 感兴趣的话题 -->
      <el-form-item label="感兴趣的话题">
        <div class="keyword-input-container">
          <el-input
            v-model="keywordInput"
            placeholder="输入话题关键词，按回车添加"
            @keyup.enter="addKeyword"
            style="width: 300px; margin-right: 10px;"
          >
            <template #append>
              <el-button @click="addKeyword">添加</el-button>
            </template>
          </el-input>
        </div>
        <div class="keyword-tags">
          <el-tag
            v-for="keyword in formData.interestKeywords"
            :key="keyword"
            closable
            @close="removeKeyword(keyword)"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ keyword }}
          </el-tag>
        </div>
      </el-form-item>

      <!-- 预警级别 -->
      <el-form-item label="预警级别">
        <el-checkbox-group v-model="formData.alertLevels">
          <el-checkbox
            v-for="option in alertLevelOptions"
            :key="option.value"
            :label="option.value"
          >
            {{ option.label }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <!-- 通知方式 -->
      <el-form-item label="通知方式">
        <el-checkbox-group v-model="formData.notificationChannels">
          <el-checkbox
            v-for="option in notificationOptions"
            :key="option.value"
            :label="option.value"
          >
            {{ option.label }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="close">取消</el-button>
        <el-button type="primary" @click="saveUserInterest" :loading="loading">
          保存
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.keyword-input-container {
  margin-bottom: 10px;
}

.keyword-tags {
  min-height: 32px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>