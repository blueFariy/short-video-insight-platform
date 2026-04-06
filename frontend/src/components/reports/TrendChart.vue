<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  data: Array<{
    date: string
    video_count: number
    total_views: number
    total_likes: number
  }>
  height?: string
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const chartHeight = computed(() => props.height || '300px')

// 初始化图表
function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表数据
function updateChart() {
  if (!chartInstance || !props.data) return

  const dates = props.data.map(d => d.date)
  const viewsData = props.data.map(d => d.total_views / 10000) // 转换为万
  const likesData = props.data.map(d => d.total_likes / 1000) // 转换为千
  const videoCountData = props.data.map(d => d.video_count)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function (params: any) {
        const date = params[0].axisValue
        let html = `<div style="font-weight: 600; margin-bottom: 8px;">${date}</div>`
        params.forEach((param: any) => {
          const marker = `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${param.color};"></span>`
          let value = param.value
          let unit = ''
          if (param.seriesName === '播放量') {
            value = (param.value * 10000).toLocaleString()
            unit = ''
          } else if (param.seriesName === '点赞数') {
            value = (param.value * 1000).toLocaleString()
            unit = ''
          } else {
            unit = ' 个'
          }
          html += `<div style="margin: 4px 0;">${marker}${param.seriesName}: ${value}${unit}</div>`
        })
        return html
      }
    },
    legend: {
      data: ['播放量', '点赞数', '视频数'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: {
        rotate: 45,
        fontSize: 11
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '播放/点赞(万)',
        position: 'left',
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '视频数',
        position: 'right',
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '播放量',
        type: 'line',
        smooth: true,
        data: viewsData,
        itemStyle: {
          color: '#409eff'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '点赞数',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: likesData,
        itemStyle: {
          color: '#67c23a'
        }
      },
      {
        name: '视频数',
        type: 'bar',
        yAxisIndex: 1,
        data: videoCountData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#f56c6c' },
            { offset: 1, color: '#f56c6c80' }
          ])
        },
        barWidth: '50%'
      }
    ]
  }

  chartInstance.setOption(option)
}

// 响应窗口大小变化
function handleResize() {
  chartInstance?.resize()
}

watch(() => props.data, () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时销毁图表
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<template>
  <div ref="chartRef" class="trend-chart" :style="{ height: chartHeight }"></div>
</template>

<style scoped lang="scss">
.trend-chart {
  width: 100%;
  min-height: 300px;
}
</style>
