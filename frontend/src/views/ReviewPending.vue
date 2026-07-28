<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">未改列表</div>

    <!-- 筛选栏 -->
    <div v-if="isDesktop" class="filter-bar">
      <div class="filter-row"><span class="filter-label">学生姓名</span><input v-model="filters.name" placeholder="搜索姓名" class="filter-input" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">作文标题</span><input v-model="filters.essayTitle" placeholder="搜索标题" class="filter-input" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">状态</span>
        <select v-model="filters.status" class="filter-input" @change="applyFilter">
          <option value="">全部(未修改+待确认)</option>
          <option value="pending">未修改</option>
          <option value="confirming">待确认</option>
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
      <div class="filter-row"><span class="filter-label">任务</span>
        <select v-model.number="filters.taskId" class="filter-input" @change="applyFilter">
          <option :value="0">全部</option>
          <option v-for="t in taskList" :key="t.id" :value="t.id">{{ t.name }}</option>
        </select>
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

    <!-- 批量操作工具栏 -->
    <div v-if="isDesktop && list.length" class="batch-bar">
      <span style="font-size:13px;color:#666">共 <strong>{{ total }}</strong> 条（本页 {{ sortedList.length }}）/ 已选 {{ selectedIds.length }} 条</span>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchOcr">🔍 批量OCR识别</button>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchAiCorrect">🤖 批量AI错别字修正</button>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchAiRewrite">🤖 批量一键修改</button>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px;background:#52c41a;border-color:#52c41a" :disabled="!selectedIds.length" @click="batchConfirm">✅ 批量确认修改</button>
      <button class="btn" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="selectedIds = []">取消选择</button>
    </div>

    <!-- 桌面端：表格 -->
    <table v-if="isDesktop && sortedList.length" class="desktop-table">
      <thead><tr>
        <th style="width:36px"><input type="checkbox" :checked="allSelected" @change="toggleAll" style="width:auto" /></th>
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
        <tr v-for="e in sortedList" :key="e.id" :class="{ 'row-selected': selectedIds.includes(e.id) }">
          <td><input type="checkbox" :checked="selectedIds.includes(e.id)" @change="toggleSelect(e.id)" style="width:auto" /></td>
          <td><span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span></td>
          <td>{{ e.student_name }}</td>
          <td>{{ e.essay_title || '无标题' }}</td>
          <td>{{ e.task_name || '-' }}</td>
          <td>{{ e.teaching_mode || '-' }}</td>
          <td>{{ e.essay_number || '-' }}</td>
          <td>{{ e.word_count || 0 }}</td>
          <td>{{ e.corrected_word_count || 0 }}</td>
          <td>{{ e.collector_name }}</td>
          <td>{{ e.file_type === 'image' ? '图片' : e.file_type === 'docx' ? '文档' : '文本' }}</td>
          <td>{{ formatDateTime(e.created_at) }}</td>
          <td style="white-space:nowrap">
            <router-link :to="`/review/detail/${e.id}`" class="btn" style="font-size:12px;padding:4px 8px;text-decoration:none;color:#333">详情编辑</router-link>
            <button v-if="e.status === 'confirming' && !isGuest" class="btn" style="font-size:12px;padding:4px 8px;color:#52c41a;margin-left:4px" @click="confirmSingle(e)">✅ 确认修改</button>
          </td>
        </tr>
      </tbody>
    </table>
    <!-- 分页 -->
    <div class="pagination" v-if="isDesktop && total > 0">
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
    <div v-if="isDesktop && !list.length && !loading" class="empty-state">
      <div class="icon">✅</div><p>没有待批作文</p>
    </div>

    <!-- 手机端：卡片列表 -->
    <van-list v-if="!isDesktop" v-model:loading="loading" :finished="mobileFinished" finished-text="没有待批作文" @load="loadMobile">
      <van-card v-for="e in list" :key="e.id"
        :title="e.student_name"
        :desc="`第${e.essay_number}次 · ${e.essay_title || ''}`"
        @click="goDetail(e)">
        <template #tags>
          <van-tag :type="e.status === 'confirming' ? 'warning' : 'default'">{{ statusLabel(e.status) }}</van-tag>
          <van-tag plain>{{ e.collector_name }}</van-tag>
          <van-tag plain type="primary">{{ e.grade || '未知' }}</van-tag>
        </template>
        <template #footer>
          <span style="font-size:12px;color:#1677ff">点击查看详情</span>
        </template>
      </van-card>
    </van-list>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showSuccessToast, showFailToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const isGuest = computed(() => ((getAuth()?.user?.role) || '').includes('guest'))
const list = ref([])
const loading = ref(false)
const selectedIds = ref([])
const collectorList = ref([])
const taskList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const mobileFinished = ref(false)
const grades = ['初一','初二','初三','高一','高二','高三']

const filters = ref({
  name: '',
  essayTitle: '',
  status: '',
  grade: '',
  essayNumber: '',
  teachingMode: '',
  collectedBy: '',
  taskId: 0,
  dateFrom: '',
  dateTo: '',
  wordCountMin: '',
  wordCountMax: '',
})

function statusLabel(s) { return { pending: '未修改', confirming: '待确认', corrected: '已修改' }[s] || s }

const sortBy = ref('')
const sortOrder = ref('asc')

const sortedList = computed(() => {
  const arr = [...list.value]
  if (!sortBy.value) return arr
  arr.sort((a, b) => {
    let va = a[sortBy.value] ?? ''
    let vb = b[sortBy.value] ?? ''
    if (typeof va === 'string') va = va.toLowerCase()
    if (typeof vb === 'string') vb = vb.toLowerCase()
    if (va < vb) return sortOrder.value === 'asc' ? -1 : 1
    if (va > vb) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })
  return arr
})

function toggleSort(field) {
  if (sortBy.value === field) {
    if (sortOrder.value === 'asc') sortOrder.value = 'desc'
    else if (sortOrder.value === 'desc') { sortBy.value = ''; sortOrder.value = 'asc' }
  } else {
    sortBy.value = field
    sortOrder.value = 'asc'
  }
}

function sortIcon(field) {
  if (sortBy.value !== field) return '⇅'
  return sortOrder.value === 'asc' ? '▲' : '▼'
}

const allSelected = computed(() => sortedList.value.length > 0 && sortedList.value.every(e => selectedIds.value.includes(e.id)))

function toggleAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    const visibleIds = sortedList.value.map(e => e.id)
    const newSet = [...new Set([...selectedIds.value, ...visibleIds])]
    selectedIds.value = newSet
  }
}
function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function buildParams() {
  const p = {}
  p.page = page.value
  p.page_size = pageSize.value
  if (filters.value.name) p.name = filters.value.name
  if (filters.value.essayTitle) p.essay_title = filters.value.essayTitle
  if (filters.value.status) p.status = filters.value.status
  if (filters.value.grade) p.grade = filters.value.grade
  if (filters.value.essayNumber) p.essay_number = filters.value.essayNumber
  if (filters.value.teachingMode) p.teaching_mode = filters.value.teachingMode
  if (filters.value.collectedBy) p.collected_by = filters.value.collectedBy
  if (filters.value.taskId) p.task_id = filters.value.taskId
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

async function loadMobile() {
  loading.value = true
  try {
    const res = await api.get('/essays/pending', { params: { ...buildParams(), page: 1, page_size: 200 } })
    list.value = res.data.items
    mobileFinished.value = true
  }
  catch { showToast('加载失败') }
  finally { loading.value = false }
}

function clearFilter() {
  filters.value = { name: '', essayTitle: '', status: '', grade: '', essayNumber: '', teachingMode: '', collectedBy: '', taskId: 0, dateFrom: '', dateTo: '', wordCountMin: '', wordCountMax: '' }
  page.value = 1
  load()
}

function goDetail(e) { router.push(`/review/detail/${e.id}`) }

async function batchOcr() {
  if (!selectedIds.value.length) return
  const toast = showLoadingToast({ message: 'OCR 识别中...', duration: 0, forbidClick: true })
  try {
    const res = await api.post('/essays/batch-ocr', { ids: selectedIds.value })
    const d = res.data
    closeToast()
    let msg = `OCR 完成：成功 ${d.success} 条`
    if (d.errors.length) msg += `，失败 ${d.errors.length} 条`
    if (d.success === 0 && d.errors.length === 0) msg = `选中 ${d.total} 条，全部非图片类型，无需 OCR`
    if (d.success === 0 && d.errors.length > 0) {
      showFailToast(`OCR 全部失败：${d.errors[0]?.reason || '未知'}`)
    } else {
      showSuccessToast(msg)
    }
    if (d.errors.length) console.warn('OCR 失败明细:', d.errors)
    selectedIds.value = []
    await load()
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '批量 OCR 失败（请确认系统设置中 OCR 已启用）')
  }
}

async function batchAiCorrect() {
  if (!selectedIds.value.length) return
  const toast = showLoadingToast({ message: 'AI 错别字修正中...', duration: 0, forbidClick: true })
  try {
    const res = await api.post('/essays/batch-ai-correct', { ids: selectedIds.value })
    const d = res.data
    closeToast()
    if (d.success === 0 && d.errors.length > 0) {
      showFailToast(`AI 修正全部失败：${d.errors[0]?.reason || '未知'}`)
    } else {
      let msg = `AI 修正完成：成功 ${d.success} 条`
      if (d.errors.length) msg += `，失败 ${d.errors.length} 条`
      showSuccessToast(msg)
    }
    if (d.errors.length) console.warn('AI 修正失败明细:', d.errors)
    selectedIds.value = []
    await load()
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '批量 AI 修正失败')
  }
}

async function batchAiRewrite() {
  if (!selectedIds.value.length) return
  const toast = showLoadingToast({ message: 'AI 一键修改中...', duration: 0, forbidClick: true })
  try {
    const res = await api.post('/essays/batch-ai-rewrite', { ids: selectedIds.value })
    const d = res.data
    closeToast()
    if (d.success === 0 && d.errors.length > 0) {
      showFailToast(`AI 改写全部失败：${d.errors[0]?.reason || '未知原因'}`)
    } else if (d.success === 0 && d.errors.length === 0) {
      showFailToast(`选中 ${d.total} 条，全部无文字内容，请先进行 🔍 OCR识别`)
    } else {
      let msg = `AI 改写完成：成功 ${d.success} 条`
      if (d.errors.length) msg += `，失败 ${d.errors.length} 条`
      showSuccessToast(msg)
    }
    if (d.errors.length) console.warn('AI 改写失败明细:', d.errors)
    selectedIds.value = []
    await load()
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '批量 AI 改写失败（请确认系统设置中 AI 改作文已启用）')
  }
}

async function batchConfirm() {
  if (!selectedIds.value.length) return
  const confirmingIds = list.value.filter(e => selectedIds.value.includes(e.id) && e.status === 'confirming').map(e => e.id)
  if (!confirmingIds.length) { showToast('选中的条目中没有待确认的作文'); return }
  try {
    const res = await api.post('/essays/batch-confirm', { ids: confirmingIds })
    const d = res.data
    showSuccessToast(`确认完成：成功 ${d.success} 条`)
    selectedIds.value = []
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '批量确认失败')
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

async function fetchCollectorsAndTasks() {
  try { const res = await api.get('/essays/collectors'); collectorList.value = res.data }
  catch (err) { console.warn('获取收集者列表失败:', err) }
  try { const res = await api.get('/essays/tasks'); taskList.value = res.data }
  catch (err) { console.warn('获取任务列表失败:', err) }
}

onMounted(() => { load(); fetchCollectorsAndTasks() })
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
.tag-correcting { background: #e6f4ff; color: #1677ff; }
.tag-corrected { background: #f6ffed; color: #52c41a; }

@media (max-width: 767px) {
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-row { width: 100%; }
  .filter-input { flex: 1; }
}
</style>
