<template>
  <div class="stats-page">
    <div v-if="isDesktop" class="page-title">数据统计</div>

    <!-- 概览统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-card-label">📚 作文总数</div>
        <div class="stat-card-value">{{ stats.total || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-label">⏳ 待处理</div>
        <div class="stat-card-value">{{ stats.pending || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-label">✅ 已修改</div>
        <div class="stat-card-value">{{ stats.corrected || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-label">📅 本月新增</div>
        <div class="stat-card-value">{{ stats.this_month || 0 }}</div>
      </div>
    </div>

    <!-- 近14天趋势 -->
    <div class="card chart-card">
      <div class="card-header"><h3>📈 近 14 天上传 / 修改趋势</h3></div>
      <v-chart class="chart" :option="trendOption" autoresize />
    </div>

    <div class="chart-row">
      <!-- 状态分布 -->
      <div class="card chart-card">
        <div class="card-header"><h3>🥧 作文状态分布</h3></div>
        <v-chart class="chart" :option="statusOption" autoresize />
      </div>

      <!-- 年级分布 -->
      <div class="card chart-card">
        <div class="card-header"><h3>📊 年级分布</h3></div>
        <v-chart class="chart" :option="gradeOption" autoresize />
      </div>
    </div>

    <div class="chart-row">
      <!-- 课程分布 -->
      <div class="card chart-card">
        <div class="card-header"><h3>🏫 课程分布</h3></div>
        <v-chart class="chart" :option="classOption" autoresize />
      </div>

      <!-- 收集者排行 -->
      <div class="card chart-card">
        <div class="card-header"><h3>🏆 收集者排行 TOP 10</h3></div>
        <v-chart class="chart" :option="collectorOption" autoresize />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../api'
import { useScreen } from '../composables/useScreen'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

const { isDesktop } = useScreen()
const stats = ref({})

const STATUS_COLORS = { pending: '#fa8c16', confirming: '#1677ff', rework: '#eb2f96', corrected: '#52c41a' }
const STATUS_LABELS = { pending: '未修改', confirming: '待确认', rework: '待重改', corrected: '已修改' }

const palette = ['#1677ff', '#52c41a', '#fa8c16', '#722ed1', '#eb2f96', '#13c2c2', '#f5222d', '#2f54eb', '#a0d911', '#faad14']

const COLLECTOR_COLORS = ['#13c2c2', '#722ed1', '#eb2f96', '#f5222d', '#faad14', '#a0d911', '#2f54eb', '#d4380d']

const trendOption = computed(() => {
  const days = (stats.value.trend || []).map(t => t.date)
  const collectors = stats.value.trend_collectors || []
  const legendData = ['上传', '修改', ...collectors.map(c => c.name)]
  const series = [
    { name: '上传', type: 'line', smooth: true, data: (stats.value.trend || []).map(t => t.uploaded), areaStyle: { opacity: 0.15 }, itemStyle: { color: '#1677ff' }, lineStyle: { width: 3 } },
    { name: '修改', type: 'line', smooth: true, data: (stats.value.trend || []).map(t => t.corrected), areaStyle: { opacity: 0.15 }, itemStyle: { color: '#52c41a' }, lineStyle: { width: 3 } },
    ...collectors.map((c, i) => ({
      name: c.name,
      type: 'line',
      smooth: true,
      data: (stats.value.trend || []).map(t => (t.by_collector || {})[String(c.id)] || 0),
      itemStyle: { color: COLLECTOR_COLORS[i % COLLECTOR_COLORS.length] },
      lineStyle: { width: 1.5, type: 'dashed' },
    })),
  ]
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: legendData, top: 0, type: 'scroll', textStyle: { fontSize: 11 } },
    grid: { left: 8, right: 8, top: 40, bottom: 8, containLabel: true },
    xAxis: { type: 'category', data: days, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1 },
    series,
  }
})

const statusOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie',
    radius: ['40%', '68%'],
    center: ['50%', '45%'],
    itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
    label: { formatter: '{b}: {c}' },
    data: ['pending', 'confirming', 'rework', 'corrected']
      .map(k => ({ name: STATUS_LABELS[k], value: stats.value[k] || 0, itemStyle: { color: STATUS_COLORS[k] } }))
      .filter(d => d.value > 0),
  }],
}))

const gradeOption = computed(() => {
  const data = stats.value.grade_dist || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 8, top: 16, bottom: 8, containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.name), axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'bar',
      data: data.map((d, i) => ({ value: d.value, itemStyle: { color: palette[i % palette.length] } })),
      barMaxWidth: 32,
    }],
  }
})

const classOption = computed(() => {
  const data = stats.value.class_dist || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 8, right: 8, top: 16, bottom: 8, containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.name), axisLabel: { fontSize: 11, interval: 0, rotate: data.length > 4 ? 30 : 0 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'bar',
      data: data.map((d, i) => ({ value: d.value, itemStyle: { color: palette[i % palette.length] } })),
      barMaxWidth: 32,
    }],
  }
})

const collectorOption = computed(() => {
  const data = stats.value.collector_rank || []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 24, top: 16, bottom: 8, containLabel: true },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', inverse: true, data: data.map(d => d.name), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: data.map((d, i) => ({ value: d.value, itemStyle: { color: palette[i % palette.length] } })),
      barMaxWidth: 18,
      label: { show: true, position: 'right', fontSize: 11 },
    }],
  }
})

onMounted(async () => {
  try {
    const res = await api.get('/essays/stats')
    stats.value = res.data || {}
  } catch {}
})
</script>

<style scoped>
.stats-page { padding: 0; }

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  text-align: center;
}

.stat-card-label {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}

.stat-card-value {
  font-size: 28px;
  font-weight: 700;
  color: #1677ff;
}

.chart-card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 16px; }

.card-header { margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #f0f0f0; }
.card-header h3 { font-size: 15px; font-weight: 600; margin: 0; }

.chart { height: 300px; width: 100%; }

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 767px) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .chart-row { grid-template-columns: 1fr; }
  .chart { height: 260px; }
  .chart-card { padding: 16px; }
}
</style>
