<template>
  <div class="page">
    <div class="page-title">作文列表</div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-row"><span class="filter-label">学生姓名</span><input v-model="filters.name" placeholder="搜索姓名" class="filter-input" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">作文标题</span><input v-model="filters.essayTitle" placeholder="搜索标题" class="filter-input" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">年级</span>
        <select v-model="filters.grade" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">第几次</span><input v-model.number="filters.number" type="number" min="1" placeholder="不限制" class="filter-input" style="width:70px" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">状态</span>
        <select v-model="filters.status" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option value="pending">待批</option>
          <option value="corrected">已批</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">提交方式</span>
        <select v-model="filters.mode" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option value="线下">线下</option>
          <option value="线上">线上</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">收集者</span><input v-model="filters.reviewer" placeholder="搜收集者" class="filter-input" @input="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">备注</span><input v-model="filters.remark" placeholder="搜备注" class="filter-input" @input="applyFilter" /></div>
      <button class="btn btn-primary" style="font-size:13px;padding:6px 14px" @click="applyFilter">查询</button>
      <button class="btn" style="font-size:13px;padding:6px 14px" @click="clearFilter">重置</button>
      <button class="btn" style="font-size:13px;padding:6px 14px" @click="exportCSV">导出CSV</button>
    </div>

    <!-- 批量操作栏 -->
    <div class="batch-bar" v-if="selectedIds.length">
      <span style="font-size:13px;color:#666">已选 {{ selectedIds.length }} 条</span>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" @click="batchExportDocx">📥 批量导出docx</button>
      <button class="btn btn-danger" style="font-size:12px;padding:4px 12px" @click="batchDelete">批量删除</button>
      <button class="btn" style="font-size:12px;padding:4px 12px" @click="selectedIds=[]">取消选择</button>
    </div>

    <!-- 统计行 -->
    <div class="stats-bar">
      <span>共 <strong>{{ total }}</strong> 条</span>
      <span class="stat-pending">待批 <strong>{{ pendingTotal }}</strong></span>
      <span class="stat-corrected">已批 <strong>{{ correctedTotal }}</strong></span>
    </div>

    <!-- 表格 -->
    <div class="table-wrap">
      <table class="desktop-table" v-if="list.length">
        <thead>
          <tr>
            <th style="width:36px"><input type="checkbox" :checked="allSelected" @change="toggleAll" style="width:auto" /></th>
            <th class="sortable" @click="toggleSort('student_name')">学生 {{ sortIcon('student_name') }}</th>
            <th>年级</th>
            <th>作文标题</th>
            <th class="sortable" @click="toggleSort('essay_number')">第几次 {{ sortIcon('essay_number') }}</th>
            <th>提交方式</th>
            <th class="sortable" @click="toggleSort('status')">状态 {{ sortIcon('status') }}</th>
            <th class="sortable" @click="toggleSort('collector_name')">收集者 {{ sortIcon('collector_name') }}</th>
            <th>备注</th>
            <th class="sortable" @click="toggleSort('created_at')">收集时间 {{ sortIcon('created_at') }}</th>
            <th class="sortable" @click="toggleSort('corrected_at')">修改时间 {{ sortIcon('corrected_at') }}</th>
            <th>文件</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in list" :key="e.id" :class="{ 'row-selected': selectedIds.includes(e.id), 'row-readonly': !isOwner(e) }">
            <td><input type="checkbox" :checked="selectedIds.includes(e.id)" @change="toggleSelect(e.id)" style="width:auto" /></td>
            <td>{{ e.student_name }}</td>
            <td>{{ e.grade || '-' }}</td>
            <td>{{ e.essay_title || '-' }}</td>
            <td>{{ e.essay_number }}</td>
            <td>{{ e.teaching_mode || '-' }}</td>
            <td><span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span></td>
            <td>{{ e.collector_name || '-' }}</td>
            <td>{{ e.remark || '-' }}</td>
            <td>{{ formatDateTime(e.created_at) }}</td>
            <td>{{ formatDateTime(e.corrected_at) || '-' }}</td>
            <td><span class="tag" :class="e.file_saved ? 'tag-corrected' : 'tag-pending'">{{ e.file_saved ? '已存' : '丢失' }}</span></td>
            <td style="white-space:nowrap">
              <template v-if="isOwner(e)">
                <router-link :to="`/review/detail/${e.id}`" class="btn" style="font-size:12px;padding:4px 8px;text-decoration:none">详情编辑</router-link>
                <button class="btn" style="font-size:12px;padding:4px 8px;color:#ff4d4f" @click="confirmDelete(e)">删除</button>
              </template>
              <router-link v-else :to="`/review/detail/${e.id}?readonly=1`" class="readonly-hint" style="text-decoration:none">
                <span class="text-readonly">仅查看</span>
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!list.length && !loading" class="empty-state"><div class="icon">📭</div><p>暂无作文</p></div>

    <!-- 分页 -->
    <div class="pagination" v-if="totalPages > 1">
      <button class="btn" :disabled="page <= 1" @click="goPage(1)">首页</button>
      <button class="btn" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(totalPages)">末页</button>
      <span class="page-jump" style="margin-left:12px">跳至
        <input v-model.number="jumpPage" type="number" min="1" :max="totalPages" class="page-jump-input" @keyup.enter="jumpToPage" />
        <button class="btn" style="font-size:12px;padding:4px 8px" @click="jumpToPage">GO</button>
      </span>
      <span class="page-size" style="margin-left:12px">每页
        <select v-model.number="pageSize" @change="applyFilter">
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
        条
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast, showLoadingToast, closeToast, showSuccessToast, showFailToast } from 'vant'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'

const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isOwner = (essay) => currentUser.value.role?.includes('admin') || essay.collected_by === currentUser.value.id

const router = useRouter()
const list = ref([])
const loading = ref(false)
const total = ref(0)
const pendingTotal = ref(0)
const correctedTotal = ref(0)
const page = ref(1)
const pageSize = ref(50)
const jumpPage = ref(1)
const sortBy = ref('created_at')
const sortOrder = ref('desc')
const selectedIds = ref([])
const grades = ['初一','初二','初三','高一','高二','高三']

const filters = ref({ name: '', essayTitle: '', grade: '', number: '', status: '', mode: '', reviewer: '', remark: '' })

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const allSelected = computed(() => list.value.length > 0 && selectedIds.value.length === list.value.length)

function statusLabel(s) { return { pending:'待修改', correcting:'修改中', corrected:'已修改' }[s] || s }
function sortIcon(field) { if (sortBy.value !== field) return '⇅'; return sortOrder.value === 'asc' ? '↑' : '↓' }

function toggleSort(field) {
  if (sortBy.value === field) { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc' }
  else { sortBy.value = field; sortOrder.value = 'desc' }
  applyFilter()
}

function buildParams() {
  const p = { page: page.value, page_size: pageSize.value, sort_by: sortBy.value, sort_order: sortOrder.value }
  if (filters.value.name) p.name = filters.value.name
  if (filters.value.essayTitle) p.essay_title = filters.value.essayTitle
  if (filters.value.grade) p.grade = filters.value.grade
  if (filters.value.number) p.essay_number = filters.value.number
  if (filters.value.status) p.status = filters.value.status
  if (filters.value.mode) p.teaching_mode = filters.value.mode
  if (filters.value.reviewer) p.reviewer = filters.value.reviewer
  if (filters.value.remark) p.remark = filters.value.remark
  return p
}

async function applyFilter() {
  page.value = 1; selectedIds.value = []
  await loadData()
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.get('/essays', { params: buildParams() })
    list.value = res.data.items
    total.value = res.data.total
    pendingTotal.value = res.data.pending
    correctedTotal.value = res.data.corrected
  } catch { showToast('查询失败') }
  finally { loading.value = false }
}

function goPage(p) { page.value = p; loadData() }
function jumpToPage() {
  const p = parseInt(jumpPage.value)
  if (isNaN(p) || p < 1 || p > totalPages.value) {
    showToast('请输入有效的页码')
    return
  }
  goPage(p)
}
function clearFilter() { filters.value = { name: '', essayTitle: '', grade: '', number: '', status: '', mode: '', reviewer: '', remark: '' }; applyFilter() }

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}
function toggleAll() {
  if (allSelected.value) selectedIds.value = []
  else selectedIds.value = list.value.map(e => e.id)
}

async function inlineEdit(e, field, val) {
  try {
    const res = await api.put(`/essays/${e.id}`, null, { params: { [field]: val } })
    Object.assign(e, res.data)
    showToast('已更新')
  } catch(err) { showToast(err.response?.data?.detail || '更新失败') }
}

async function batchDelete() {
  if (!selectedIds.value.length) return
  showDialog({
    title: '批量删除',
    message: `确定删除 ${selectedIds.value.length} 条作文吗？`,
    showCancelButton: true,
  }).then(async () => {
    for (const id of selectedIds.value) {
      try { await api.delete(`/essays/${id}?force=true`) } catch {}
    }
    showToast(`已删除 ${selectedIds.value.length} 条`)
    selectedIds.value = []
    applyFilter()
  }).catch(() => {})
}

async function batchExportDocx() {
  if (!selectedIds.value.length) return
  try {
    showLoadingToast({ message: '正在导出...', forbidClick: true, duration: 0 })
    const res = await api.post('/essays/batch-export-docx', selectedIds.value, { responseType: 'blob' })
    
    // 从响应头解析文件名
    const disposition = res.headers['content-disposition']
    let filename = '作文导出.zip'
    if (disposition) {
      const match = disposition.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i)
      if (match) filename = decodeURIComponent(match[1])
    }
    
    // 创建 Blob URL 并下载
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
    
    closeToast()
    showSuccessToast('导出成功')
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '导出失败')
  }
}

function confirmDelete(e) {
  showDialog({
    title: '确认删除',
    message: `确定删除 ${e.student_name} 的作文吗？`,
    showCancelButton: true,
  }).then(async () => {
    try {
      await api.delete(`/essays/${e.id}?force=true`)
      applyFilter()
      showToast('删除成功')
    } catch (err) { showToast(err.response?.data?.detail || '删除失败') }
  }).catch(() => {})
}

function goDetail(e) { router.push(`/review/detail/${e.id}`) }

function exportCSV() {
  const headers = ['学生','年级','作文','第几次','提交方式','状态','收集者','备注','收集时间','修改时间']
  const rows = list.value.map(e => [
    e.student_name, e.grade, e.essay_title, `第${e.essay_number}次`,
    e.teaching_mode, statusLabel(e.status), e.collector_name, e.remark,
    e.created_at ? formatDateTime(e.created_at) : '', e.corrected_at ? formatDateTime(e.corrected_at) : '',
  ])
  const csv = [headers.join(','), ...rows.map(r => r.map(v => `"${v}"`).join(','))].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = '作文列表.csv'; a.click()
  URL.revokeObjectURL(url)
}

onMounted(applyFilter)
</script>

<style scoped>
.page { padding: 0; }

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

.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #fffbe6;
  border-radius: 8px;
  margin-bottom: 8px;
}

.stats-bar {
  display: flex;
  gap: 20px;
  padding: 8px 0;
  font-size: 13px;
  color: #666;
}
.stats-bar strong { font-size: 15px; }
.stat-pending { color: #d46b08; }
.stat-corrected { color: #52c41a; }

.table-wrap { overflow-x: auto; }
.inline-select {
  padding: 2px 4px;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  background: transparent;
}
.inline-select:hover { border-color: #d9d9d9; background: #fff; }
.inline-select:focus { border-color: #4096ff; outline: none; }

.row-selected { background: #e6f4ff !important; }

.sortable { cursor: pointer; user-select: none; }
.sortable:hover { background: #f0f0f0; }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 20px 0;
}
.page-info { font-size: 14px; color: #333; }
.page-jump { display: flex; align-items: center; gap: 4px; font-size: 13px; color: #666; }
.page-jump-input { width: 50px; padding: 4px 6px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; text-align: center; }
.page-jump-input:focus { border-color: #4096ff; outline: none; }
.page-size { display: flex; align-items: center; gap: 4px; font-size: 13px; color: #666; }
.page-size select { padding: 4px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; }

.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.tag-pending { background: #fff7e6; color: #d46b08; }
.tag-correcting { background: #e6f4ff; color: #1677ff; }
.tag-corrected { background: #f6ffed; color: #52c41a; }

.btn-disabled { opacity: 0.5; cursor: not-allowed; pointer-events: none; }
.row-readonly { background: #fafafa; }
.readonly-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #e6f4ff;
  border-radius: 4px;
  color: #1677ff;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.readonly-hint:hover { background: #bae0ff; }
.icon-readonly { font-size: 14px; }
.text-readonly { font-size: 11px; }

@media (max-width: 767px) {
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-row { width: 100%; }
  .filter-input { flex: 1; }
  .table-wrap { overflow-x: auto; }
  .pagination { flex-direction: column; gap: 12px; }
}
</style>
