<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">操作历史</div>

    <!-- 桌面端筛选栏 -->
    <div v-if="isDesktop" class="filter-bar">
      <div class="filter-row"><input v-model="filters.keyword" placeholder="搜索学生/操作内容" class="filter-input" @keyup.enter="applyFilter" /></div>
      <div class="filter-row">
        <select v-model="filters.action" class="filter-input" @change="applyFilter">
          <option value="">全部操作</option>
          <option v-for="a in actionOptions" :key="a" :value="a">{{ a }}</option>
        </select>
      </div>
      <div class="filter-row">
        <select v-model="filters.detail" class="filter-input" @change="applyFilter">
          <option value="">全部子类型</option>
          <option v-for="d in detailOptions" :key="d" :value="d">{{ d }}</option>
        </select>
      </div>
      <div class="filter-row" v-if="isAdmin">
        <select v-model="filters.userId" class="filter-input" @change="applyFilter">
          <option value="">全部操作者</option>
          <option v-for="u in userList" :key="u.id" :value="u.id">{{ u.nickname || u.username }}</option>
        </select>
      </div>
      <label v-else class="filter-row filter-check">
        <input type="checkbox" v-model="filters.onlyMine" @change="applyFilter" style="width:auto" />
        <span class="filter-label">只看我的操作</span>
      </label>
      <div class="filter-row"><input v-model="filters.studentName" placeholder="学生姓名" class="filter-input" @keyup.enter="applyFilter" /></div>
      <div class="filter-row"><input v-model="filters.dateFrom" type="date" class="filter-input" style="width:140px" @change="applyFilter" /><span style="color:#d9d9d9;font-size:12px">~</span><input v-model="filters.dateTo" type="date" class="filter-input" style="width:140px" @change="applyFilter" /></div>
      <button class="btn btn-primary" style="font-size:13px;padding:6px 14px" @click="applyFilter">查询</button>
      <button class="btn" style="font-size:13px;padding:6px 14px" @click="clearFilter">重置</button>
    </div>

    <!-- 手机端筛选 -->
    <div v-if="!isDesktop" class="mobile-filter">
      <van-button size="small" block :type="mobileFilterActive ? 'primary' : 'default'" icon="filter-o" @click="showMobileFilter = !showMobileFilter">
        筛选{{ mobileFilterActive ? '（已启用）' : '' }}
      </van-button>
      <div v-if="showMobileFilter" class="mobile-filter-panel">
        <div class="m-filter-row">
          <input v-model="filters.keyword" placeholder="搜索学生/操作内容" class="m-filter-input" @input="applyFilter" />
          <select v-model="filters.action" class="m-filter-input" @change="applyFilter">
            <option value="">全部操作</option>
            <option v-for="a in actionOptions" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>
        <div class="m-filter-row">
          <select v-model="filters.detail" class="m-filter-input" @change="applyFilter">
            <option value="">全部子类型</option>
            <option v-for="d in detailOptions" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
        <div class="m-filter-row" v-if="isAdmin">
          <select v-model="filters.userId" class="m-filter-input" @change="applyFilter">
            <option value="">全部操作者</option>
            <option v-for="u in userList" :key="u.id" :value="u.id">{{ u.nickname || u.username }}</option>
          </select>
          <input v-model="filters.studentName" placeholder="学生姓名" class="m-filter-input" @input="applyFilter" />
        </div>
        <div class="m-filter-row" v-if="!isAdmin">
          <label class="m-filter-check"><input type="checkbox" v-model="filters.onlyMine" @change="applyFilter" style="width:auto" /> 只看我的操作</label>
          <input v-model="filters.studentName" placeholder="学生姓名" class="m-filter-input" @input="applyFilter" />
        </div>
        <div class="m-filter-row">
          <input v-model="filters.dateFrom" type="date" class="m-filter-input" @change="applyFilter" />
          <input v-model="filters.dateTo" type="date" class="m-filter-input" @change="applyFilter" />
        </div>
        <button class="btn" style="width:100%;margin-top:8px" @click="clearFilter">重置筛选</button>
      </div>
    </div>

    <!-- 统计行 -->
    <div class="stats-bar" v-if="isDesktop">
      <span>共 <strong>{{ total }}</strong> 条记录</span>
    </div>

    <div v-if="loading" style="padding:24px;text-align:center;color:#999">⏳ 加载中...</div>

    <!-- 桌面端：表格 -->
    <table v-if="isDesktop && list.length" class="desktop-table">
      <thead><tr>
        <th>时间</th><th>学生</th><th>作文</th><th>操作</th><th>状态</th><th>操作者</th><th>详情</th><th>操作前</th><th>操作后</th><th>操作</th>
      </tr></thead>
      <tbody>
        <tr v-for="op in list" :key="op.id">
          <td style="cursor:pointer" @click="goDetail(op)">{{ formatDateTime(op.created_at) }}</td>
          <td style="cursor:pointer" @click="goDetail(op)">{{ op.student_name || '-' }}</td>
          <td style="cursor:pointer" @click="goDetail(op)">
            <template v-if="op.batch_id">
              <span class="batch-tag">批量</span>
            </template>
            {{ op.corrected_title || op.essay_title || '无标题' }}<span v-if="op.essay_number"> #{{ op.essay_number }}</span>
          </td>
          <td><span class="tag" :class="actionClass(op.action)">{{ op.action }}</span></td>
          <td><span v-if="opStatus(op)" class="tag" :class="'tag-' + opStatus(op)">{{ statusText(opStatus(op)) }}</span><span v-else>-</span></td>
          <td>{{ op.user_name }}</td>
          <td style="cursor:pointer" @click="goDetail(op)">{{ op.detail || '-' }}</td>
          <td style="font-size:12px;color:#999;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="formatChange(op, 'old')">{{ formatChangeDisplay(op, 'old') }}</td>
          <td style="font-size:12px;color:#999;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="formatChangeDisplay(op, 'new')">{{ formatChangeDisplay(op, 'new') }}</td>
          <td style="white-space:nowrap">
            <button class="btn btn-detail" @click="showChange(op)" style="margin-right:4px">查看详情</button>
            <button v-if="isAdmin" class="btn btn-undo" @click="confirmUndo(op)" :disabled="undoingId === op.id">
              {{ undoingId === op.id ? '撤回中...' : '↩ 撤回' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="isDesktop && !list.length && !loading" class="empty-state">
      <div class="icon">📭</div><p>暂无操作记录</p>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="isDesktop && totalPages > 1">
      <button class="btn" :disabled="page <= 1" @click="goPage(1)">首页</button>
      <button class="btn" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(totalPages)">末页</button>
    </div>

    <!-- 手机端：卡片列表 -->
    <van-list v-if="!isDesktop" v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="loadMore">
      <van-cell v-for="op in list" :key="op.id"
        :title="`${op.action} · ${op.student_name || '?'}`"
        :label="op.corrected_title || op.essay_title || '无标题'"
        :value="formatDateTime(op.created_at)"
        @click="goDetail(op)">
        <template #extra>
          <span class="tag" :class="actionClass(op.action)" style="font-size:11px">{{ op.action }}</span>
          <button class="btn btn-detail-mobile" @click.stop="showChange(op)">详情</button>
          <button v-if="isAdmin" class="btn btn-undo btn-undo-mobile" @click.stop="confirmUndo(op)">↩</button>
        </template>
      </van-cell>
    </van-list>

    <!-- 撤回确认弹窗 -->
    <van-dialog v-model:show="undoDialog.show" title="确认撤回"
      :show-cancel-button="true" @confirm="doUndo" :close-on-click-overlay="false">
      <div style="padding:16px;font-size:14px;line-height:1.8">
        <p>确定撤回「<strong>{{ undoDialog.action }}</strong>」操作吗？</p>
        <p style="color:#e6a23c;margin-top:8px;font-weight:bold">{{ undoDialog.consequence }}</p>
        <p style="color:#999;margin-top:8px">{{ undoDialog.detail }}</p>
      </div>
    </van-dialog>

    <!-- 变更内容弹窗 -->
    <van-popup v-model:show="changeDialog.show" position="center" class="change-popup" :style="{ width: 'min(760px, 94vw)', borderRadius: '10px' }" @click-overlay="changeDialog.show = false">
      <div class="change-header">
        <div class="change-header-title">变更内容</div>
        <button class="change-close" @click="changeDialog.show = false">✕</button>
      </div>
      <div class="change-meta">
        <span v-if="changeDialog.action" class="tag" :class="actionClass(changeDialog.action)">{{ changeDialog.action }}</span>
        <span v-if="changeDialog.studentName" style="margin-left:6px">{{ changeDialog.studentName }}</span>
        <span v-if="changeDialog.essayTitle" style="color:#999;margin-left:6px">{{ changeDialog.essayTitle }}</span>
        <span v-if="changeDialog.detail" style="color:#666;margin-left:6px">{{ changeDialog.detail }}</span>
      </div>
      <div class="change-body">
        <div v-if="!changeDialog.fields.length" style="color:#999;text-align:center;padding:32px 0">无详细变更数据</div>
        <div v-for="(field, idx) in changeDialog.fields" :key="idx" class="change-field">
          <div class="change-field-name">{{ fieldLabel(field.name) }}</div>
          <div class="change-field-row">
            <div class="change-col change-col-old">
              <div class="change-col-label">修改前</div>
              <div class="change-col-value">{{ field.old }}</div>
            </div>
            <div class="change-arrow">→</div>
            <div class="change-col change-col-new">
              <div class="change-col-label">修改后</div>
              <div class="change-col-value">{{ field.new }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="change-footer">
        <button class="btn btn-primary" style="font-size:13px;padding:6px 24px" @click="changeDialog.show = false">关闭</button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isAdmin = computed(() => ((currentUser.value.role) || '').includes('admin'))
const list = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(40)
const finished = ref(false)
const undoingId = ref(null)
const showMobileFilter = ref(false)
const userList = ref([])

const undoDialog = ref({ show: false, id: null, action: '', detail: '', consequence: '' })
const changeDialog = ref({ show: false, fields: [], action: '', detail: '', studentName: '', essayTitle: '' })

const actionOptions = ['上传', '修改', '编辑', '删除', '恢复', '批改', 'OCR']
const detailOptions = ['AI 错别字修正', 'AI 改写', '确认修改', '标记为重改']

const filters = ref({ keyword: '', action: '', detail: '', userId: '', onlyMine: false, studentName: '', dateFrom: '', dateTo: '' })

const mobileFilterActive = computed(() => {
  const f = filters.value
  return !!(f.keyword || f.action || f.detail || f.userId || f.onlyMine || f.studentName || f.dateFrom || f.dateTo)
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

function actionClass(action) {
  const m = { '上传': 'tag-pending', '修改': 'tag-corrected', '编辑': 'tag-correcting', '删除': 'tag-pending', '恢复': 'tag-corrected', '批改': 'tag-corrected', 'OCR': 'tag-correcting' }
  return m[action] || ''
}

function buildParams() {
  const p = { page: page.value, page_size: pageSize.value }
  if (filters.value.keyword) p.keyword = filters.value.keyword
  if (filters.value.action) p.action = filters.value.action
  if (filters.value.detail) p.detail = filters.value.detail
  if (filters.value.userId) p.user_id = Number(filters.value.userId)
  else if (filters.value.onlyMine) p.user_id = currentUser.value.id
  if (filters.value.studentName) p.student_name = filters.value.studentName
  if (filters.value.dateFrom) p.date_from = filters.value.dateFrom
  if (filters.value.dateTo) p.date_to = filters.value.dateTo
  return p
}

let loadTimer = null
function applyFilter() {
  page.value = 1
  finished.value = false
  clearTimeout(loadTimer)
  loadTimer = setTimeout(loadData, 300)
}

function clearFilter() {
  filters.value = { keyword: '', action: '', detail: '', userId: '', onlyMine: false, studentName: '', dateFrom: '', dateTo: '' }
  applyFilter()
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.get('/essays/operations', { params: buildParams() })
    list.value = res.data.items
    total.value = res.data.total
    finished.value = list.value.length >= total.value
  } catch { showToast('加载失败') }
  finally { loading.value = false }
}

function goPage(p) { page.value = p; loadData() }

async function loadMore() {
  page.value++
  loading.value = true
  try {
    const res = await api.get('/essays/operations', { params: buildParams() })
    list.value.push(...res.data.items)
    total.value = res.data.total
    finished.value = list.value.length >= total.value
  } catch { showToast('加载失败') }
  finally { loading.value = false }
}

function goDetail(op) {
  if (op.essay_id) {
    router.push(`/review/detail/${op.essay_id}`)
  }
}

function parseChange(op, side) {
  const key = side === 'old' ? 'old_value' : 'new_value'
  try {
    const data = op[key] ? JSON.parse(op[key]) : {}
    const isBatch = Object.keys(data).some(k => /^\d+$/.test(k))
    if (isBatch) return `批量操作（${Object.keys(data).length} 篇）`
    const idFieldMap = { 'task_id': '_task_name', 'course_id': '_course_name', 'collected_by': '_collector_name', 'reviewer_id': '_reviewer_name' }
    const dateFields = ['corrected_at', 'deleted_at']
    const parts = []
    for (const [k, v] of Object.entries(data)) {
      if (k.startsWith('_')) continue
      const displayKey = idFieldMap[k]
      let val = displayKey ? (data[displayKey] ?? '') : (v?.[side] ?? v ?? '')
      if (val === '' || val == null) continue
      const label = fieldLabel(k)
      val = dateFields.includes(k) ? formatDateTime(val) : formatValue(String(val))
      const s = String(val).substring(0, 30)
      parts.push(`${label}: ${s}${String(val).length > 30 ? '…' : ''}`)
    }
    return parts.join(' | ')
  } catch { return '' }
}

function formatChange(op, side) {
  return parseChange(op, side) || '-'
}

function formatChangeDisplay(op, side) {
  const raw = parseChange(op, side)
  if (!raw) return '-'
  return raw.replace(/([^:]+):\s*([^|]+)/g, (_, label, val) => {
    return `${label.trim()}: ${formatValue(val.trim())}`
  })
}

function extractStatus(val) {
  if (val == null) return ''
  if (typeof val === 'string') return val
  if (typeof val === 'object') {
    if ('new' in val) return extractStatus(val.new)
    if ('old' in val) return extractStatus(val.old)
    if ('status' in val) return extractStatus(val.status)
  }
  return ''
}

function opStatus(op) {
  try {
    const data = op.new_value ? JSON.parse(op.new_value) : {}
    const isBatch = Object.keys(data).some(k => /^\d+$/.test(k))
    if (isBatch) {
      const first = Object.values(data)[0]
      return extractStatus(first)
    }
    return extractStatus(data.status)
  } catch { return '' }
}

function statusText(s) {
  const m = { 'pending': '未修改', 'confirming': '待确认', 'corrected': '已修改', 'rework': '待重改' }
  return m[s] || s
}

function hasChange(op) {
  return !!(op.old_value || op.new_value)
}

function fieldLabel(name) {
  const m = { 'grade': '年级', 'essay_number': '第几次', 'student_name': '学生姓名', 'teaching_mode': '提交方式', 'essay_title': '标题', 'corrected_title': '修改后标题', 'remark': '备注', 'is_supplement': '补交标记', 'collected_by': '收集者', 'task_id': '任务', 'course_id': '课程', 'content_text': '原文内容', 'corrected_text': '修改后文章', 'status': '状态', 'reviewer_id': '批改者', 'file_type': '文件类型', 'corrected_at': '批改时间', 'deleted_at': '删除时间' }
  return m[name] || name
}

function formatValue(val) {
  if (val == null || val === '') return '(空)'
  const m = { 'pending': '未修改', 'confirming': '待确认', 'corrected': '已修改', 'rework': '待重改', 'true': '是', 'false': '否', 'image': '图片', 'docx': '文档', 'text': '文本' }
  return m[val] ?? val
}

function showChange(op) {
  const fields = []
  try {
    const oldRaw = op.old_value ? JSON.parse(op.old_value) : {}
    const newRaw = op.new_value ? JSON.parse(op.new_value) : {}
    const isBatch = Object.keys(oldRaw).some(k => /^\d+$/.test(k))
    if (isBatch) {
      const count = Object.keys(oldRaw).length
      fields.push({ name: '批量操作', old: `${count} 篇作文`, new: `${count} 篇作文` })
    } else {
      // 正文相关字段成对展示（原文内容 + 修改后文章）
      const contentKeys = ['content_text', 'corrected_text']
      const hasContentChange = contentKeys.some(k => String(oldRaw[k] ?? '') !== String(newRaw[k] ?? ''))
      if (hasContentChange) {
        for (const k of contentKeys) {
          const oldV = String(oldRaw[k] ?? '')
          const newV = String(newRaw[k] ?? '')
          fields.push({ name: k, old: oldV || '(空)', new: newV || '(空)' })
        }
      }
      // 其他字段（跳过正文、_开头的内部字段、status 单独处理、id 类字段）
      const idFieldMap = { 'task_id': '_task_name', 'course_id': '_course_name', 'collected_by': '_collector_name', 'reviewer_id': '_reviewer_name' }
      const dateFields = ['corrected_at', 'deleted_at']
      for (const key of Object.keys({ ...oldRaw, ...newRaw })) {
        if (key.startsWith('_')) continue
        if (contentKeys.includes(key) && hasContentChange) continue
        if (key === 'status') continue
        const displayKey = idFieldMap[key]
        const rawOld = displayKey ? (oldRaw[displayKey] ?? '') : (oldRaw[key]?.old ?? oldRaw[key] ?? '')
        const rawNew = displayKey ? (newRaw[displayKey] ?? '') : (newRaw[key]?.new ?? newRaw[key] ?? '')
        const oldVal = dateFields.includes(key) ? formatDateTime(rawOld) : formatValue(String(rawOld))
        const newVal = dateFields.includes(key) ? formatDateTime(rawNew) : formatValue(String(rawNew))
        if (String(oldVal) !== String(newVal)) {
          fields.push({ name: key, old: oldVal, new: newVal })
        }
      }
      // status 放最后
      if (oldRaw.status !== undefined && String(oldRaw.status) !== String(newRaw.status)) {
        fields.push({ name: 'status', old: formatValue(String(oldRaw.status)), new: formatValue(String(newRaw.status)) })
      }
    }
  } catch {}
  changeDialog.value = { show: true, fields, action: op.action || '', detail: op.detail || '', studentName: op.student_name || '', essayTitle: op.corrected_title || op.essay_title || '' }
}

function undoConsequence(action) {
  const m = {
    '上传': '撤回上传将删除该作文（软删除，可在回收站恢复）',
    '修改': '撤回修改将恢复批改前的原文内容',
    '编辑': '撤回编辑将恢复修改前的字段值',
    '删除': '撤回删除将恢复该作文',
    '恢复': '撤回恢复将重新删除该作文',
    '批改': '撤回批改将恢复批改前的原文内容',
    'OCR': '撤回OCR将清除识别出的文字内容',
  }
  return m[action] || '撤回此操作将恢复操作前的状态'
}

function confirmUndo(op) {
  undoDialog.value = {
    show: true,
    id: op.id,
    action: op.action,
    detail: op.detail || (op.batch_id ? `批量操作，${op.essay_ids ? JSON.parse(op.essay_ids).length : '?'} 篇` : ''),
    consequence: undoConsequence(op.action),
  }
}

async function doUndo() {
  const id = undoDialog.value.id
  undoDialog.value.show = false
  undoingId.value = id
  try {
    const res = await api.post(`/essays/operations/${id}/undo`)
    showToast(res.data.message || '撤回成功')
    await loadData()
  } catch (err) {
    showToast(err.response?.data?.detail || '撤回失败')
  } finally {
    undoingId.value = null
  }
}

onMounted(async () => {
  loadData()
  if (isAdmin.value) {
    try { const res = await api.get('/admin/users'); userList.value = res.data || [] } catch {}
  }
})
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
.filter-check { gap: 6px; cursor: pointer; }
.filter-input { padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 13px; outline: none; background: #fff; min-width: 120px; }
.filter-input:focus { border-color: #4096ff; }

.stats-bar {
  display: flex;
  gap: 20px;
  padding: 8px 0;
  font-size: 13px;
  color: #666;
}
.stats-bar strong { font-size: 15px; }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 20px 0;
}
.page-info { font-size: 14px; color: #333; }

.batch-tag {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  background: #e6f4ff;
  color: #1677ff;
  margin-right: 4px;
}

.btn-undo {
  font-size: 12px;
  padding: 3px 10px;
  color: #ff4d4f;
  border-color: #ffccc7;
}
.btn-undo:hover { border-color: #ff4d4f; background: #fff2f0; }

.btn-undo-mobile {
  margin-left: 8px;
  padding: 2px 8px;
}

.btn-detail {
  font-size: 12px;
  padding: 3px 10px;
  color: #1677ff;
  border-color: #91caff;
}
.btn-detail:hover { border-color: #1677ff; background: #e6f4ff; }

.btn-detail-mobile {
  margin-left: 4px;
  padding: 2px 6px;
  font-size: 11px;
  color: #1677ff;
  border-color: #91caff;
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
.m-filter-row { display: flex; gap: 8px; align-items: center; }
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
.m-filter-check { font-size: 13px; color: #666; white-space: nowrap; }

@media (max-width: 767px) { .page { min-height: 100vh; } }
</style>

<style>
/* 变更内容弹窗 — 非 scoped，适配 Vant popup teleport 到 body */
.change-popup { overflow: hidden; }
.change-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px 10px; border-bottom: 1px solid #f0f0f0;
}
.change-header-title { font-size: 16px; font-weight: 600; color: #222; }
.change-close { background: none; border: none; font-size: 18px; color: #999; cursor: pointer; padding: 0 4px; }
.change-close:hover { color: #333; }
.change-meta {
  padding: 10px 18px; font-size: 13px; color: #555;
  background: #fafafa; border-bottom: 1px solid #f0f0f0;
  display: flex; align-items: center; flex-wrap: wrap; gap: 4px;
}
.change-body {
  padding: 12px 18px; max-height: 55vh; overflow-y: auto;
  font-size: 13px; line-height: 1.6;
}
.change-field { margin-bottom: 14px; border-bottom: 1px solid #f0f0f0; padding-bottom: 12px; }
.change-field:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.change-field-name { font-weight: 600; color: #333; margin-bottom: 6px; font-size: 14px; }
.change-field-row { display: flex; align-items: flex-start; gap: 8px; }
.change-col { flex: 1; min-width: 0; border-radius: 6px; padding: 8px 10px; }
.change-col-old { background: #fff2f0; border: 1px solid #ffccc7; }
.change-col-new { background: #f6ffed; border: 1px solid #b7eb8f; }
.change-col-label { font-size: 11px; color: #999; margin-bottom: 4px; }
.change-col-value { color: #333; word-break: break-all; white-space: pre-wrap; font-size: 13px; }
.change-arrow { flex-shrink: 0; color: #ccc; font-size: 18px; line-height: 36px; user-select: none; }
.change-footer { padding: 10px 18px 14px; text-align: center; border-top: 1px solid #f0f0f0; }
</style>
