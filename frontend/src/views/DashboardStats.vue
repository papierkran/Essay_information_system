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

    <!-- GitHub 风格上传频率热力图 -->
    <div class="card chart-card">
      <div class="card-header heatmap-header">
        <h3>🔥 上传频率（按年）</h3>
        <div class="year-switch">
          <button class="year-btn" :disabled="!canPrevYear" @click="changeYear(-1)">‹</button>
          <button class="year-btn year-current" @click="showYearPicker = !showYearPicker">{{ activeYear }} 年 ▾</button>
          <button class="year-btn" :disabled="!canNextYear" @click="changeYear(1)">›</button>
        </div>
      </div>
      <div v-if="showYearPicker" class="year-picker">
        <button
          v-for="y in pickerYears"
          :key="y"
          class="year-opt"
          :class="{ active: y === activeYear }"
          @click="selectYear(y)"
        >{{ y }} 年</button>
      </div>
      <div class="heatmap-hint">💡 点击任意日期格子，可跳转到作文列表查看当天上传的作文</div>
      <v-chart class="chart chart-heatmap" :option="activityOption" autoresize @click="onHeatmapClick" />
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
import { LineChart, BarChart, PieChart, HeatmapChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  CalendarComponent,
  VisualMapComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useRouter } from 'vue-router'
import api from '../api'
import { useScreen } from '../composables/useScreen'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  HeatmapChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  CalendarComponent,
  VisualMapComponent,
])

const { isDesktop } = useScreen()
const router = useRouter()
const stats = ref({})
const activeYear = ref(null)
const showYearPicker = ref(false)

const pickerYears = computed(() => {
  const years = stats.value.available_years || []
  const cur = new Date().getFullYear()
  return [...new Set([...years, cur])].sort((a, b) => b - a)
})

const minYear = computed(() => {
  const list = pickerYears.value
  return list.length ? list[list.length - 1] : new Date().getFullYear()
})

const currentYear = computed(() => new Date().getFullYear())

const canPrevYear = computed(() => activeYear.value > minYear.value)

const canNextYear = computed(() => activeYear.value < currentYear.value)

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

const activityOption = computed(() => {
  const data = (stats.value.daily_upload || []).map(d => [d.date, d.count])
  const range = data.length ? [data[0][0], data[data.length - 1][0]] : []
  return {
    tooltip: {
      formatter: p => `${p.data[0]}：上传 ${p.data[1]} 篇`,
    },
    visualMap: {
      min: 0,
      max: 50,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#ebedf0', '#a7e9a7', '#5ecf4e', '#ffd700', '#ff9f1a', '#ff4d4f', '#7a0000'] },
      textStyle: { fontSize: 11 },
    },
    calendar: {
      range,
      top: 20,
      left: 20,
      right: 20,
      cellSize: ['auto', 14],
      itemStyle: { borderWidth: 3, borderColor: '#fff', borderRadius: 2 },
      dayLabel: { firstDay: 1, nameMap: ['日', '一', '二', '三', '四', '五', '六'], fontSize: 10 },
      monthLabel: { nameMap: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'], fontSize: 10 },
      yearLabel: { show: false },
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data,
    }],
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
    activeYear.value = new Date().getFullYear()
  } catch {}
})

async function loadStats() {
  try {
    const params = {}
    if (activeYear.value) params.year = activeYear.value
    const res = await api.get('/essays/stats', { params })
    stats.value = res.data || {}
  } catch {}
}

function changeYear(delta) {
  selectYear(activeYear.value + delta)
}

function selectYear(y) {
  activeYear.value = y
  showYearPicker.value = false
  loadStats()
}

function onHeatmapClick(params) {
  const date = params?.data?.[0]
  if (date) {
    router.push({ path: '/essay/list', query: { day: date } })
  }
}
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

.heatmap-header { display: flex; align-items: center; justify-content: space-between; }

.year-switch { display: flex; align-items: center; gap: 6px; }
.year-btn {
  min-width: 32px;
  height: 28px;
  padding: 0 8px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  color: #333;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.year-btn:hover:not(:disabled) { border-color: #4096ff; color: #1677ff; }
.year-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.year-current { font-weight: 600; min-width: 72px; }

.year-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}
.year-opt {
  padding: 5px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  transition: all 0.15s;
}
.year-opt:hover { border-color: #4096ff; color: #1677ff; }
.year-opt.active { background: #1677ff; color: #fff; border-color: #1677ff; }

.heatmap-hint {
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
}

.chart { height: 300px; width: 100%; }
.chart-heatmap { height: 260px; }

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
