<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">未改列表</div>

    <!-- 筛选栏 -->
    <div v-if="isDesktop" class="filter-bar">
      <div class="filter-row"><span class="filter-label">学生姓名</span><input v-model="filters.name" placeholder="搜索姓名" class="filter-input" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">作文标题</span><input v-model="filters.essayTitle" placeholder="搜索标题" class="filter-input" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">状态</span>
        <select v-model="filters.status" class="filter-input" @change="applyFilter">
          <option value="">全部(未修改+待确认+待重改)</option>
          <option value="pending">未修改</option>
          <option value="confirming">待确认</option>
          <option value="rework">待重改</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">年级</span>
        <select v-model="filters.grade" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">第几次</span><input v-model.number="filters.essayNumber" type="number" min="1" placeholder="不限" class="filter-input" style="width:70px" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">提交方式</span>
        <select v-model="filters.teachingMode" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option value="线下">线下</option>
          <option value="线上">线上</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">收集者</span>
        <select v-model="filters.collectedBy" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option v-for="c in collectorList" :key="c.id" :value="c.id">{{ c.nickname }}</option>
        </select>
      </div>
      <div class="filter-row">
        <span class="filter-label">任务</span>
        <button class="filter-input task-select-btn" @click="showTaskPicker = true" :style="{ width: '140px', textAlign: 'left', cursor: 'pointer', color: filterTaskSearch ? '#333' : '#999' }">
          {{ filterTaskSearch || '搜索任务' }}
        </button>
      </div>
      <div class="filter-row"><span class="filter-label">上传起始</span><input v-model="filters.dateFrom" type="date" class="filter-input" style="width:140px" @change="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">上传截止</span><input v-model="filters.dateTo" type="date" class="filter-input" style="width:140px" @change="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">字数范围</span>
        <input v-model.number="filters.wordCountMin" type="number" min="0" placeholder="最小" class="filter-input" style="width:70px" @input="applyFilter" />
        <span style="color:#999">~</span>
        <input v-model.number="filters.wordCountMax" type="number" min="0" placeholder="最大" class="filter-input" style="width:70px" @input="applyFilter" />
      </div>
      <button class="btn" style="font-size:13px;padding:6px 14px" @click="clearFilter">重置</button>
    </div>

    <div v-if="loading" style="padding:24px;text-align:center;color:#999">⏳ 加载中...</div>

    <!-- 批量操作工具栏 -->
    <div v-if="list.length && !isGuest" class="batch-bar">
      <span style="font-size:13px;color:#666">共 <strong>{{ total }}</strong> 条（本页 {{ list.length }}）/ 已选 {{ selectedIds.length }} 条</span>
      <button v-if="isAdmin || isReviewer" class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchOcr">🔍 批量OCR识别</button>
      <button v-if="isAdmin || isReviewer" class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchAiCorrect">🤖 批量AI错别字修正</button>
      <button v-if="isAdmin || isReviewer" class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchAiRewrite">🤖 批量一键修改</button>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px;background:#52c41a;border-color:#52c41a" :disabled="!selectedIds.length || batchConfirming" @click="batchConfirm">✅ 批量确认修改</button>
      <button v-if="isAdmin || isReviewer" class="btn btn-primary" style="font-size:12px;padding:4px 12px;background:#fa8c16;border-color:#fa8c16" @click="batchPipeline">⏩ 一键批量流程修改</button>
      <button class="btn" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="selectedIds = []">取消选择</button>
    </div>

    <!-- 桌面端：表格 -->
    <table v-if="isDesktop && list.length" class="desktop-table">
      <thead><tr>
        <th v-if="!isGuest" style="width:36px"><input type="checkbox" :checked="allSelected" @change="toggleAll" style="width:auto" /></th>
        <th>状态</th>
        <th>学生姓名</th>
        <th>作文标题</th>
        <th>任务名称</th>
        <th class="sortable" @click="toggleSort('teaching_mode')">提交方式 {{ sortIcon('teaching_mode') }}</th>
        <th class="sortable" @click="toggleSort('essay_number')">第几次作文 {{ sortIcon('essay_number') }}</th>
        <th class="sortable" @click="toggleSort('word_count')">修改前字数 {{ sortIcon('word_count') }}</th>
        <th class="sortable" @click="toggleSort('corrected_word_count')">修改后字数 {{ sortIcon('corrected_word_count') }}</th>
        <th>收集者</th>
        <th>类型</th>
        <th class="sortable" @click="toggleSort('created_at')">上传时间 {{ sortIcon('created_at') }}</th>
        <th>操作</th>
      </tr></thead>
      <tbody>
        <tr v-for="e in list" :key="e.id" :class="{ 'row-selected': selectedIds.includes(e.id) }">
          <td v-if="!isGuest"><input type="checkbox" :checked="selectedIds.includes(e.id)" @change="toggleSelect(e.id)" style="width:auto" /></td>
          <td><span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span></td>
          <td>{{ e.student_name }}</td>
          <td>{{ e.essay_title || '无标题' }}</td>
          <td>{{ e.task_name || '-' }}</td>
          <td><span class="badge-mini" :class="e.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ e.teaching_mode || '-' }}</span></td>
          <td><span class="badge-mini tag-number">{{ e.essay_number ? '第' + e.essay_number + '次' : '-' }}</span></td>
          <td>{{ e.word_count || 0 }}</td>
          <td>{{ e.corrected_word_count || 0 }}</td>
          <td>{{ e.collector_name }}</td>
          <td>{{ e.file_type === 'image' ? '图片' : e.file_type === 'docx' ? '文档' : '文本' }}</td>
          <td>{{ formatDateTime(e.created_at) }}</td>
          <td style="white-space:nowrap">
            <router-link :to="`/review/detail/${e.id}?from=pending`" class="btn" style="font-size:12px;padding:4px 8px;text-decoration:none;color:#333">详情编辑</router-link>
            <button v-if="e.status === 'confirming' && !isGuest" class="btn" style="font-size:12px;padding:4px 8px;color:#52c41a;margin-left:4px" @click="confirmSingle(e)">✅ 确认修改</button>
            <button v-if="e.status === 'confirming' && !isGuest" class="btn" style="font-size:12px;padding:4px 8px;color:#fa8c16;margin-left:4px" @click="reworkSingle(e)">🔄 重改</button>
          </td>
        </tr>
      </tbody>
    </table>
    <!-- 分页 -->
    <div class="pagination" v-if="total > 0">
      <button class="btn" :disabled="page <= 1" @click="goPage(1)">首页</button>
      <button class="btn" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(totalPages)">末页</button>
      <span style="margin-left:12px;font-size:13px;color:#666">每页
        <select v-model.number="pageSize" @change="onPageSizeChange" style="padding:4px 8px;border:1px solid #d9d9d9;border-radius:4px">
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
        </select> 条
      </span>
    </div>
    <div v-if="!list.length && !loading" class="empty-state">
      <div class="icon">✅</div><p>没有待批作文</p>
    </div>

    <!-- 手机端：筛选 -->
    <div v-if="!isDesktop" class="mobile-filter">
      <van-button size="small" block :type="mobileFilterActive ? 'primary' : 'default'" icon="filter-o" @click="showMobileFilter = !showMobileFilter">
        筛选{{ mobileFilterActive ? '（已启用）' : '' }}
      </van-button>
      <div v-if="showMobileFilter" class="mobile-filter-panel">
        <div class="m-filter-row">
          <input v-model="filters.name" placeholder="学生姓名" class="m-filter-input" @input="applyFilter" />
          <input v-model="filters.essayTitle" placeholder="作文标题" class="m-filter-input" @input="applyFilter" />
        </div>
        <div class="m-filter-row">
          <select v-model="filters.status" class="m-filter-input" @change="applyFilter">
            <option value="">全部状态</option>
            <option value="pending">未修改</option>
            <option value="confirming">待确认</option>
            <option value="rework">待重改</option>
          </select>
          <select v-model="filters.grade" class="m-filter-input" @change="applyFilter">
            <option value="">全部年级</option>
            <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>
        <div class="m-filter-row">
          <select v-model="filters.teachingMode" class="m-filter-input" @change="applyFilter">
            <option value="">全部方式</option>
            <option value="线下">线下</option>
            <option value="线上">线上</option>
          </select>
          <select v-model="filters.collectedBy" class="m-filter-input" @change="applyFilter">
            <option value="">全部收集者</option>
            <option v-for="c in collectorList" :key="c.id" :value="c.id">{{ c.nickname }}</option>
          </select>
        </div>
        <div class="m-filter-row">
          <button class="m-filter-input task-select-btn" @click="showTaskPicker = true" :style="{ textAlign: 'left', cursor: 'pointer', color: filterTaskSearch ? '#333' : '#999' }">
            {{ filterTaskSearch || '搜索任务' }}
          </button>
          <input v-model.number="filters.essayNumber" type="number" min="1" placeholder="第几次" class="m-filter-input" @input="applyFilter" />
        </div>
        <div class="m-filter-row">
          <input v-model="filters.dateFrom" type="date" class="m-filter-input" @change="applyFilter" />
          <input v-model="filters.dateTo" type="date" class="m-filter-input" @change="applyFilter" />
        </div>
        <button class="btn" style="width:100%;margin-top:8px" @click="clearFilter">重置筛选</button>
      </div>
    </div>

    <!-- 手机端：卡片列表 -->
    <div v-if="!isDesktop && list.length" class="mobile-list">
      <div v-for="e in list" :key="e.id" class="mobile-card" :class="{ 'row-selected': selectedIds.includes(e.id) }">
        <div class="mobile-card-head" @click="goDetail(e)">
          <div class="mobile-card-name-wrap">
            <input v-if="!isGuest" type="checkbox" :checked="selectedIds.includes(e.id)" @click.stop @change="toggleSelect(e.id)" style="width:auto" />
            <span class="mobile-card-name">{{ e.student_name }}</span>
          </div>
          <span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span>
        </div>
        <div class="mobile-card-title" @click="goDetail(e)">{{ e.essay_title || '无标题' }}</div>
        <div class="mobile-card-meta" @click="goDetail(e)">
          <span class="badge-mini tag-grade">{{ e.grade || '未知' }}</span>
          <span class="badge-mini tag-number">{{ e.essay_number ? '第' + e.essay_number + '次' : '-' }}</span>
          <span class="badge-mini" :class="e.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ e.teaching_mode || '-' }}</span>
          <span>{{ e.task_name || '无任务' }}</span>
        </div>
        <div class="mobile-card-foot">
          <span>{{ formatDateTime(e.created_at) }}</span>
          <div class="mobile-card-actions">
            <span class="mobile-card-filetype">{{ e.file_type === 'image' ? '图片' : e.file_type === 'docx' ? '文档' : '文本' }}</span>
            <button v-if="e.status === 'confirming' && !isGuest" class="btn" style="font-size:12px;padding:3px 8px;color:#52c41a" @click.stop="confirmSingle(e)">✅ 确认</button>
            <button v-if="e.status === 'confirming' && !isGuest" class="btn" style="font-size:12px;padding:3px 8px;color:#fa8c16" @click.stop="reworkSingle(e)">🔄 重改</button>
            <router-link :to="`/review/detail/${e.id}?from=pending`" class="btn" style="font-size:12px;padding:3px 10px;text-decoration:none;color:#333" @click.stop>详情</router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 作文修改日志（页脚） -->
    <div v-if="isDesktop" class="log-panel">
      <div class="log-panel-header">
        <span class="log-panel-title">📝 作文修改日志</span>
        <span class="log-panel-sub">OCR识别 / AI错别字修正 / 一键修改 / 批量及流水线操作</span>
        <button class="btn" style="font-size:12px;padding:3px 10px;margin-left:auto" @click="refreshLogs">刷新</button>
      </div>

      <!-- 任务进度 -->
      <div v-if="monitorTasks.length" class="log-tasks">
        <div v-for="t in monitorTasks" :key="t.id" class="log-task">
          <span class="log-task-type">{{ typeLabel(t.type) }}</span>
          <span class="log-task-stage" v-if="t.stage">{{ t.stage }}</span>
          <div class="log-task-bar-wrap"><div class="log-task-bar" :class="'progress-' + t.status" :style="{ width: logTaskPercent(t) + '%' }"></div></div>
          <span class="log-task-count">{{ t.success }}/{{ t.total }}</span>
          <span class="log-task-status">{{ t.status === 'running' ? '⏳' : t.status === 'completed' ? '✅' : '❌' }}</span>
          <span class="log-task-current" v-if="t.current && t.status === 'running'">正在处理：{{ t.current }}</span>
        </div>
      </div>

      <!-- 日志表格 -->
      <table v-if="opLogs.length" class="desktop-table log-table">
        <thead><tr>
          <th>时间</th><th>学生</th><th>作文</th><th>操作</th><th>操作者</th><th>详情</th>
        </tr></thead>
        <tbody>
          <tr v-for="op in opLogs" :key="op.id">
            <td>{{ formatDateTime(op.created_at) }}</td>
            <td>{{ op.student_name || '-' }}</td>
            <td>
              <template v-if="op.batch_id"><span class="batch-tag">批量</span></template>
              {{ op.essay_title || '无标题' }}<span v-if="op.essay_number"> #{{ op.essay_number }}</span>
            </td>
            <td><span class="tag" :class="opActionClass(op.action)">{{ op.action }}</span></td>
            <td>{{ op.user_name }}</td>
            <td>{{ op.detail || '-' }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!opLogs.length && !loadingLogs" class="log-empty">暂无相关操作日志</div>
    </div>
  </div>

  <!-- 任务选择器 -->
  <van-action-sheet v-model:show="showTaskPicker" title="选择任务筛选" class="task-picker-sheet"
    :style="{ maxHeight: '88vh', display: 'flex', flexDirection: 'column' }">
    <div class="picker-list">
      <div style="padding:8px 16px">
        <input v-model="pickerTaskSearch" placeholder="搜索任务名称/主题/年级..." style="width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;outline:none" />
      </div>
      <div style="padding:0 16px 8px;display:flex;align-items:center;gap:6px;font-size:13px;color:#666">
        <van-checkbox v-model="showActiveOnly" icon-size="16px" shape="square">只看收集中</van-checkbox>
        <span style="color:#999;font-size:12px">（关闭可查看全部 {{ sortedTaskList.length }} 个任务）</span>
      </div>
      <div class="task-item-option" @click="selectTask(null)" :class="{ active: !filters.taskId }">
        <span style="font-weight:500">全部</span>
      </div>
      <div class="task-item-option" style="color:#999" @click="selectTask(0)" :class="{ active: filters.taskId === 0 }">
        <span>无任务</span>
      </div>
      <div class="task-split">
        <div class="task-col">
          <div class="task-col-title">线上</div>
          <template v-for="t in pagedOnlineTasks" :key="t.id">
            <div class="task-item-option" @click="selectTask(t)" :class="{ active: filters.taskId == t.id }">
              <div class="task-item-title">
                <span style="font-weight:500">{{ t.name }}</span>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
              </div>
              <div class="task-item-meta">
                <span class="badge-mini tag-grade">{{ t.grade }}</span>
                <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
                <span v-if="t.essay_topic" style="color:#999;font-size:12px">{{ t.essay_topic }}</span>
              </div>
            </div>
          </template>
          <div v-if="filteredOnlineTasks.length > PAGE_SIZE" class="pagination-row">
            <button class="btn" :disabled="pageOnline <= 1" @click="pageOnline--">上一页</button>
            <span class="page-info">{{ pageOnline }} / {{ onlineTotalPages }}</span>
            <button class="btn" :disabled="pageOnline >= onlineTotalPages" @click="pageOnline++">下一页</button>
          </div>
          <div v-if="!filteredOnlineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线上任务</div>
        </div>
        <div class="task-col">
          <div class="task-col-title">线下</div>
          <template v-for="t in pagedOfflineTasks" :key="t.id">
            <div class="task-item-option" @click="selectTask(t)" :class="{ active: filters.taskId == t.id }">
              <div class="task-item-title">
                <span style="font-weight:500">{{ t.name }}</span>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
              </div>
              <div class="task-item-meta">
                <span class="badge-mini tag-grade">{{ t.grade }}</span>
                <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
                <span v-if="t.essay_topic" style="color:#999;font-size:12px">{{ t.essay_topic }}</span>
              </div>
            </div>
          </template>
          <div v-if="filteredOfflineTasks.length > PAGE_SIZE" class="pagination-row">
            <button class="btn" :disabled="pageOffline <= 1" @click="pageOffline--">上一页</button>
            <span class="page-info">{{ pageOffline }} / {{ offlineTotalPages }}</span>
            <button class="btn" :disabled="pageOffline >= offlineTotalPages" @click="pageOffline++">下一页</button>
          </div>
          <div v-if="!filteredOfflineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线下任务</div>
        </div>
      </div>
    </div>
  </van-action-sheet>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'
import { useTaskMonitor, typeLabel } from '../composables/useTaskMonitor'

const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const isGuest = computed(() => ((getAuth()?.user?.role) || '').includes('guest'))
const isAdmin = computed(() => ((getAuth()?.user?.role) || '').includes('admin'))
const isReviewer = computed(() => ((getAuth()?.user?.role) || '').includes('reviewer'))
const { tasks: monitorTasks, addTask, addTasks } = useTaskMonitor()
const list = ref([])
const loading = ref(false)
const selectedIds = ref([])
const collectorList = ref([])
const taskList = ref([])
const filterTaskSearch = ref('')
const showTaskPicker = ref(false)
const pickerTaskSearch = ref('')
const showActiveOnly = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const showMobileFilter = ref(false)
const grades = ['初一','初二','初三','高一','高二','高三']

// ===== 作文修改日志 =====
const opLogs = ref([])
const loadingLogs = ref(false)
let logTimer = null
let logRefreshTimer = null
let logVisibilityHandler = null
const LOG_KEYWORDS = ['OCR', 'AI 错别字修正', 'AI 改写', 'AI 修改', '流水线']

function logTaskPercent(t) {
  if (!t.total) return 0
  return Math.round((t.success + (t.errors ? t.errors.length : 0)) / t.total * 100)
}

function opActionClass(action) {
  const m = { '编辑': 'tag-correcting', '批改': 'tag-corrected', 'OCR': 'tag-correcting' }
  return m[action] || 'tag-pending'
}

async function refreshLogs() {
  loadingLogs.value = true
  try {
    // 后端 keyword 只支持单个关键词，这里取最近 100 条后在端上过滤相关操作
    const res = await api.get('/essays/operations', { params: { page: 1, page_size: 100 } })
    opLogs.value = res.data.items.filter(op => {
      const d = op.detail || ''
      const a = op.action || ''
      return LOG_KEYWORDS.some(kw => d.includes(kw) || a.includes(kw))
    }).slice(0, 30)
  } catch { opLogs.value = [] }
  finally { loadingLogs.value = false }
}

function scheduleLogRefresh() {
  clearTimeout(logRefreshTimer)
  logRefreshTimer = setTimeout(refreshLogs, 2000)
}

function startLogPolling() {
  stopLogPolling()
  logTimer = setInterval(() => {
    if (!document.hidden) refreshLogs()
  }, 8000)
}

function stopLogPolling() {
  clearInterval(logTimer)
  logTimer = null
}

const filters = ref({
  name: '',
  essayTitle: '',
  status: '',
  grade: '',
  essayNumber: '',
  teachingMode: '',
  collectedBy: '',
  taskId: '',
  dateFrom: '',
  dateTo: '',
  wordCountMin: '',
  wordCountMax: '',
})

const mobileFilterActive = computed(() => {
  const f = filters.value
  return !!(f.name || f.essayTitle || f.status || f.grade || f.essayNumber || f.teachingMode || f.collectedBy || f.dateFrom || f.dateTo || f.wordCountMin || f.wordCountMax || filterTaskSearch.value)
})

function statusLabel(s) { return { pending: '未修改', confirming: '待确认', rework: '待重改', corrected: '已修改' }[s] || s }

const sortedTaskList = computed(() => {
  return [...taskList.value].sort((a, b) => {
    const aMig = (a.course_name || '').includes('迁移')
    const bMig = (b.course_name || '').includes('迁移')
    if (aMig !== bMig) return aMig ? 1 : -1
    const aActive = taskIsActive(a)
    const bActive = taskIsActive(b)
    if (aActive !== bActive) return aActive ? -1 : 1
    return 0
  })
})

const filteredOnlineTasks = computed(() => {
  let list = sortedTaskList.value.filter(t => t.teaching_mode === '线上')
  if (showActiveOnly.value && !pickerTaskSearch.value.trim()) list = list.filter(t => taskIsActive(t))
  if (pickerTaskSearch.value.trim()) {
    const kw = pickerTaskSearch.value.toLowerCase()
    list = list.filter(t => (t.name + (t.essay_topic || '') + (t.grade || '')).toLowerCase().includes(kw))
  }
  return list
})

const filteredOfflineTasks = computed(() => {
  let list = sortedTaskList.value.filter(t => t.teaching_mode !== '线上')
  if (showActiveOnly.value && !pickerTaskSearch.value.trim()) list = list.filter(t => taskIsActive(t))
  if (pickerTaskSearch.value.trim()) {
    const kw = pickerTaskSearch.value.toLowerCase()
    list = list.filter(t => (t.name + (t.essay_topic || '') + (t.grade || '')).toLowerCase().includes(kw))
  }
  return list
})

const PAGE_SIZE = 10
const pageOnline = ref(1)
const pageOffline = ref(1)
const onlineTotalPages = computed(() => Math.max(1, Math.ceil(filteredOnlineTasks.value.length / PAGE_SIZE)))
const offlineTotalPages = computed(() => Math.max(1, Math.ceil(filteredOfflineTasks.value.length / PAGE_SIZE)))
const pagedOnlineTasks = computed(() => {
  const start = (pageOnline.value - 1) * PAGE_SIZE
  return filteredOnlineTasks.value.slice(start, start + PAGE_SIZE)
})
const pagedOfflineTasks = computed(() => {
  const start = (pageOffline.value - 1) * PAGE_SIZE
  return filteredOfflineTasks.value.slice(start, start + PAGE_SIZE)
})

watch([pickerTaskSearch, showActiveOnly], () => {
  pageOnline.value = 1
  pageOffline.value = 1
})

function taskIsActive(t) {
  const now = new Date()
  return t.is_active
    && (!t.deadline || new Date(t.deadline) >= now)
    && (!t.start_time || new Date(t.start_time) <= now)
}

function selectTask(task) {
  if (task === null) {
    filters.value.taskId = ''
    filterTaskSearch.value = ''
  } else if (task === 0) {
    filters.value.taskId = 0
    filterTaskSearch.value = '无任务'
  } else {
    filters.value.taskId = task.id
    filterTaskSearch.value = task.name
  }
  showTaskPicker.value = false
  pickerTaskSearch.value = ''
  applyFilter()
}

const sortBy = ref('')
const sortOrder = ref('asc')

function toggleSort(field) {
  if (sortBy.value === field) {
    if (sortOrder.value === 'asc') sortOrder.value = 'desc'
    else if (sortOrder.value === 'desc') { sortBy.value = ''; sortOrder.value = 'asc' }
  } else {
    sortBy.value = field
    sortOrder.value = 'asc'
  }
  applyFilter()
}

function sortIcon(field) {
  if (sortBy.value !== field) return '⇅'
  return sortOrder.value === 'asc' ? '▲' : '▼'
}

const allSelected = computed(() => list.value.length > 0 && list.value.every(e => selectedIds.value.includes(e.id)))

function toggleAll() {
  if (isGuest.value) return
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    const visibleIds = list.value.map(e => e.id)
    const newSet = [...new Set([...selectedIds.value, ...visibleIds])]
    selectedIds.value = newSet
  }
}
function toggleSelect(id) {
  if (isGuest.value) return
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function buildParams() {
  const p = {}
  p.page = page.value
  p.page_size = pageSize.value
  if (sortBy.value) {
    p.sort_by = sortBy.value
    p.sort_order = sortOrder.value
  }
  if (filters.value.name) p.name = filters.value.name
  if (filters.value.essayTitle) p.essay_title = filters.value.essayTitle
  if (filters.value.status) p.status = filters.value.status
  if (filters.value.grade) p.grade = filters.value.grade
  if (filters.value.essayNumber) p.essay_number = filters.value.essayNumber
  if (filters.value.teachingMode) p.teaching_mode = filters.value.teachingMode
  if (filters.value.collectedBy) p.collected_by = filters.value.collectedBy
  if (filters.value.taskId !== '' && filters.value.taskId !== null && filters.value.taskId !== undefined) p.task_id = filters.value.taskId
  if (filterTaskSearch.value) p.task_name = filterTaskSearch.value
  if (filters.value.dateFrom) p.date_from = filters.value.dateFrom
  if (filters.value.dateTo) p.date_to = filters.value.dateTo
  if (filters.value.wordCountMin) p.word_count_min = filters.value.wordCountMin
  if (filters.value.wordCountMax) p.word_count_max = filters.value.wordCountMax
  return p
}

let loadTimer = null
function applyFilter() {
  page.value = 1
  clearTimeout(loadTimer)
  loadTimer = setTimeout(load, 300)
}

async function load() {
  loading.value = true
  try {
    const res = await api.get('/essays/pending', { params: buildParams() })
    list.value = res.data.items
    total.value = res.data.total
  }
  catch { showToast('加载失败') }
  finally { loading.value = false }
}

function goPage(p) { page.value = p; load() }
function onPageSizeChange() { page.value = 1; load() }

function clearFilter() {
  filters.value = { name: '', essayTitle: '', status: '', grade: '', essayNumber: '', teachingMode: '', collectedBy: '', taskId: '', dateFrom: '', dateTo: '', wordCountMin: '', wordCountMax: '' }
  filterTaskSearch.value = ''
  page.value = 1
  load()
}

function goDetail(e) { router.push(`/review/detail/${e.id}?from=pending`) }

async function batchOcr() {
  if (!selectedIds.value.length) return
  const confirmed = await showConfirmDialog({
    title: '批量OCR识别',
    message: `将对选中的 ${selectedIds.value.length} 篇作文执行 OCR 识别，是否继续？`,
  }).catch(() => false)
  if (!confirmed) return
  try {
    const res = await api.post('/essays/batch-task/ocr/start', { ids: selectedIds.value })
    addTask(res.data.task_id, 'ocr', res.data.total)
    selectedIds.value = []
    scheduleLogRefresh()
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '启动 OCR 任务失败')
  }
}

async function batchAiCorrect() {
  if (!selectedIds.value.length) return
  const confirmed = await showConfirmDialog({
    title: '批量AI错别字修正',
    message: `将对选中的 ${selectedIds.value.length} 篇作文执行 AI 错别字修正，是否继续？`,
  }).catch(() => false)
  if (!confirmed) return
  try {
    const res = await api.post('/essays/batch-task/ai-correct/start', { ids: selectedIds.value })
    addTask(res.data.task_id, 'ai_correct', res.data.total)
    selectedIds.value = []
    scheduleLogRefresh()
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '启动 AI 修正任务失败')
  }
}

async function batchAiRewrite() {
  if (!selectedIds.value.length) return
  const confirmed = await showConfirmDialog({
    title: '批量AI一键修改',
    message: `将对选中的 ${selectedIds.value.length} 篇作文执行 AI 改写，是否继续？`,
  }).catch(() => false)
  if (!confirmed) return
  try {
    const res = await api.post('/essays/batch-task/ai-rewrite/start', { ids: selectedIds.value })
    addTask(res.data.task_id, 'ai_rewrite', res.data.total)
    selectedIds.value = []
    scheduleLogRefresh()
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '启动 AI 改写任务失败')
  }
}

async function batchPipeline() {
  let ids = selectedIds.value
  if (!ids.length) {
    ids = list.value.filter(e => e.status === 'pending').map(e => e.id)
    if (!ids.length) { showToast('当前页没有状态为「未修改」的作文'); return }
  } else {
    const pendingIds = ids.filter(id => {
      const e = list.value.find(x => x.id === id)
      return e && e.status === 'pending'
    })
    if (!pendingIds.length) { showToast('选中的条目中没有状态为「未修改」的作文'); return }
    ids = pendingIds
  }

  const confirmed = await showConfirmDialog({
    title: '一键批量流程修改',
    message: `将对 ${ids.length} 篇「未修改」作文执行 流水线（OCR→AI修正→AI改写），是否继续？`,
  }).catch(() => false)
  if (!confirmed) return

  try {
    const res = await api.post('/essays/batch-task/pipeline/start', { ids })
    addTasks(res.data.tasks)
    selectedIds.value = []
    scheduleLogRefresh()
    showSuccessToast(`流水线已启动，共 ${res.data.total} 条，可在右下角查看进度`)
  } catch (err) {
    showFailToast(err.response?.data?.detail || '流水线启动失败')
  }
}

const batchConfirming = ref(false)

async function batchConfirm() {
  if (!selectedIds.value.length) return
  if (batchConfirming.value) return
  const confirmingIds = list.value.filter(e => selectedIds.value.includes(e.id) && e.status === 'confirming').map(e => e.id)
  if (!confirmingIds.length) { showToast('选中的条目中没有待确认的作文'); return }
  const confirmed = await showConfirmDialog({
    title: '确认批量确认修改',
    message: `将把选中的 ${confirmingIds.length} 篇「待确认」作文标记为「已修改」，是否继续？`,
  }).catch(() => false)
  if (!confirmed) return
  batchConfirming.value = true
  try {
    const res = await api.post('/essays/batch-confirm', { ids: confirmingIds })
    const d = res.data
    showSuccessToast(`确认完成：成功 ${d.success} 条` + (d.errors?.length ? `，失败 ${d.errors.length} 条` : ''))
    selectedIds.value = []
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '批量确认失败')
  } finally {
    batchConfirming.value = false
  }
}

async function confirmSingle(e) {
  try {
    await api.post(`/essays/${e.id}/confirm`)
    showSuccessToast('已确认修改')
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '确认失败')
  }
}

async function reworkSingle(e) {
  try {
    await api.post(`/essays/${e.id}/rework`)
    showSuccessToast('已标记为待重改')
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '标记重改失败')
  }
}

async function fetchCollectorsAndTasks() {
  try { const res = await api.get('/essays/collectors'); collectorList.value = res.data }
  catch (err) { console.warn('获取收集者列表失败:', err) }
  try { const res = await api.get('/essays/tasks'); taskList.value = res.data }
  catch (err) { console.warn('获取任务列表失败:', err) }
}

onMounted(() => {
  load()
  fetchCollectorsAndTasks()
  refreshLogs()
  if (isDesktop.value) {
    startLogPolling()
    logVisibilityHandler = () => {
      if (document.hidden) stopLogPolling()
      else startLogPolling()
    }
    document.addEventListener('visibilitychange', logVisibilityHandler)
  }
})
onUnmounted(() => {
  stopLogPolling()
  clearTimeout(logRefreshTimer)
  if (logVisibilityHandler) {
    document.removeEventListener('visibilitychange', logVisibilityHandler)
    logVisibilityHandler = null
  }
})
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.filter-row { display: flex; align-items: center; gap: 4px; }
.filter-label { font-size: 13px; color: #666; white-space: nowrap; }
.filter-input { padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 13px; outline: none; }
.filter-input:focus { border-color: #4096ff; }
.filter-input[type="number"] { width: 60px; }

.batch-bar { display: flex; align-items: center; gap: 8px; padding: 8px 0; flex-wrap: wrap; }
.row-selected { background-color: #e6f4ff !important; }
.sortable { cursor: pointer; user-select: none; white-space: nowrap; }
.sortable:hover { background: #f0f0f0; }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 16px 0;
}
.page-info { font-size: 14px; color: #333; }

.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.tag-pending { background: #fff7e6; color: #d46b08; }
.tag-confirming { background: #e6f4ff; color: #1677ff; }
.tag-rework { background: #fff1f0; color: #ff4d4f; }
.tag-correcting { background: #e6f4ff; color: #1677ff; }
.tag-corrected { background: #f6ffed; color: #52c41a; }

/* ===== 作文修改日志 ===== */
.log-panel {
  margin-top: 20px;
  padding: 14px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.log-panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.log-panel-title { font-size: 15px; font-weight: 600; color: #333; }
.log-panel-sub { font-size: 12px; color: #999; }

.log-tasks {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  background: #fafafa;
  border-radius: 6px;
  margin-bottom: 10px;
}
.log-task {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.log-task-type { font-weight: 600; color: #333; white-space: nowrap; }
.log-task-stage {
  font-size: 11px;
  color: #fa8c16;
  background: #fff7e6;
  border-radius: 3px;
  padding: 1px 6px;
  white-space: nowrap;
}
.log-task-bar-wrap {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
  min-width: 120px;
}
.log-task-bar { height: 100%; border-radius: 3px; transition: width 0.3s; }
.log-task-bar.progress-running { background: #1677ff; }
.log-task-bar.progress-completed { background: #52c41a; }
.log-task-bar.progress-failed { background: #ff4d4f; }
.log-task-count { color: #666; white-space: nowrap; }
.log-task-status { color: #666; }
.log-task-current { color: #999; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.log-table { margin-top: 4px; }
.log-table th { white-space: nowrap; }
.log-empty { padding: 20px; text-align: center; color: #999; font-size: 13px; }

.batch-tag {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  background: #e6f4ff;
  color: #1677ff;
  margin-right: 4px;
}

@media (max-width: 767px) {
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-row { width: 100%; }
  .filter-input { flex: 1; }
}

/* ===== 手机端筛选 ===== */
.mobile-filter { margin-bottom: 10px; }
.mobile-filter-panel {
  margin-top: 8px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.m-filter-row { display: flex; gap: 8px; }
.m-filter-input {
  flex: 1;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: #fff;
}
.m-filter-input:focus { border-color: #4096ff; }

/* ===== 手机端卡片列表 ===== */
.mobile-list { display: flex; flex-direction: column; gap: 10px; }
.mobile-card {
  background: #fff;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.mobile-card.row-selected { background: #e6f4ff; }
.mobile-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.mobile-card-name-wrap { display: flex; align-items: center; gap: 8px; min-width: 0; }
.mobile-card-name { font-size: 15px; font-weight: 600; color: #333; }
.mobile-card-title {
  font-size: 13px;
  color: #555;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mobile-card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.m-sep { color: #d9d9d9; }
.mobile-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #aaa;
  padding-top: 8px;
  border-top: 1px dashed #f0f0f0;
}
.mobile-card-actions { display: flex; align-items: center; gap: 6px; }
.mobile-card-filetype {
  font-size: 11px;
  color: #666;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 1px 6px;
}

/* 任务选择器 */
.task-picker-sheet :deep(.van-action-sheet__content) { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
.task-picker-sheet .picker-list { flex: 1; overflow-y: auto; padding-bottom: 16px; }
.task-item-option {
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  transition: background 0.15s;
}
.task-item-option:hover { background: #f5f5f5; }
.task-item-option.active { background: #e6f4ff; }
.task-item-title { display: flex; align-items: center; margin-bottom: 4px; }
.task-item-title span { font-size: 14px; }
.task-item-meta { display: flex; align-items: center; gap: 6px; font-size: 12px; flex-wrap: wrap; }
.task-split { display: flex; gap: 8px; padding: 0 4px; }
.task-col { flex: 1; min-width: 0; }
.task-col-title { font-size: 13px; color: #999; padding: 12px 12px 6px; font-weight: 600; }
.task-select-btn { background: #fff; border: 1px solid #d9d9d9; border-radius: 6px; padding: 6px 12px; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-select-btn:hover { border-color: #1677ff; }
.pagination-row { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 8px 0; }
.page-info { font-size: 12px; color: #666; }
</style>
