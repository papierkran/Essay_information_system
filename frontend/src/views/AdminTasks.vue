<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">任务列表</div>

    <div v-if="isDesktop" style="margin-bottom:16px;display:flex;gap:8px;align-items:center">
      <button v-if="isAdmin" class="btn btn-success" @click="openTaskDialog()">+ 创建收集任务</button>
    </div>
    <div v-else style="margin:12px">
      <van-button v-if="isAdmin" type="success" size="small" @click="openTaskDialog()">创建收集任务</van-button>
    </div>

    <!-- 筛选栏 -->
    <div v-if="isDesktop" class="filter-bar">
      <input v-model="filters.name" placeholder="任务名称" class="filter-input" />
      <select v-model="filters.grade" class="filter-input">
        <option value="">全部年级</option>
        <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
      </select>
      <select v-model="filters.number" class="filter-input">
        <option value="">全部第几次</option>
        <option v-for="n in 10" :key="n" :value="n">第{{ n }}次</option>
      </select>
      <select v-model="filters.teachingMode" class="filter-input">
        <option value="">全部提交方式</option>
        <option value="线下">线下</option>
        <option value="线上">线上</option>
      </select>
      <select v-model="filters.status" class="filter-input">
        <option value="">全部状态</option>
        <option value="not_started">未开始</option>
        <option value="active">收集中</option>
        <option value="expired">已过期</option>
        <option value="ended">已结束</option>
      </select>
      <input v-model="filters.topic" placeholder="文章主题" class="filter-input" />
      <input v-model="filters.course" placeholder="课程名称" class="filter-input" />
      <button class="btn" style="font-size:13px;padding:6px 14px" @click="clearFilter">重置</button>
    </div>
    <div v-else style="display:flex;gap:8px;padding:0 12px;flex-wrap:wrap">
      <van-field v-model="filters.name" placeholder="任务名称" clearable style="flex:1;min-width:120px" />
      <van-field v-model="filters.course" placeholder="课程名称" clearable style="flex:1;min-width:120px" />
      <van-button size="small" @click="clearFilter">重置</van-button>
    </div>

    <!-- 桌面端任务列表 -->
    <div v-if="isDesktop">
      <table class="desktop-table" v-if="filteredTasks.length">
        <thead>
          <tr>
            <th v-for="(col, ci) in columns" :key="col.key"
              draggable="true"
              @dragstart="onDragStart($event, ci)"
              @dragover.prevent="onDragOver($event, ci)"
              @drop="onDrop($event, ci)"
              @click="toggleSort(col.key)"
              :class="{ sortable: col.sortable, sorted: sortKey === col.key }"
              :style="{ cursor: col.sortable ? 'pointer' : 'default' }">
              {{ col.label }}
              <span v-if="col.sortable && sortKey === col.key" class="sort-arrow">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in sortedTasks" :key="t.id">
            <td v-for="col in columns" :key="col.key">
              <template v-if="col.key === 'name'">
                <span class="task-name-link" @click="viewEssays(t)">{{ t.name }}</span>
              </template>
              <template v-else-if="col.key === 'grade'"><span class="badge-mini tag-grade">{{ t.grade || '-' }}</span></template>
              <template v-else-if="col.key === 'number'"><span class="badge-mini tag-number">{{ t.essay_number ? `第${t.essay_number}次` : '无' }}</span></template>
              <template v-else-if="col.key === 'topic'">{{ t.essay_topic || '-' }}</template>
              <template v-else-if="col.key === 'course'">{{ t.course_name || '-' }}</template>
              <template v-else-if="col.key === 'start_time'">{{ t.start_time ? formatDate(t.start_time) : '-' }}</template>
              <template v-else-if="col.key === 'deadline'">{{ t.deadline ? formatDeadline(t.deadline) : '无限制' }}</template>
              <template v-else-if="col.key === 'status'">
                <span :class="['tag', getTaskStatus(t).active ? 'tag-pending' : 'tag-corrected']">{{ getTaskStatus(t).label }}</span>
              </template>
              <template v-else-if="col.key === 'actions'">
                <button class="btn" style="font-size:12px;padding:2px 8px" @click="openTaskDialog(t)">编辑</button>
                <button class="btn" style="font-size:12px;padding:2px 8px" @click="cloneTask(t)" title="复制为新任务">复制</button>
                <button class="btn btn-primary" style="font-size:12px;padding:2px 8px" @click="goBatchUpload(t)">批量上传</button>
                <button class="btn" style="font-size:12px;padding:2px 8px" @click="toggleTaskActive(t)">{{ getTaskStatus(t).active ? '结束收集' : '开始收集' }}</button>
                <button class="btn" style="font-size:12px;padding:2px 8px;color:#ff4d4f" @click="confirmDelTask(t)">删除</button>
              </template>
              <template v-else-if="col.key === 'teaching_mode'"><span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span></template>
              <template v-else-if="col.key === 'submitted'"><span style="font-weight:600;color:#1677ff">{{ t.submitted_count || 0 }}</span></template>
              <template v-else-if="col.key === 'pending_count'"><span style="font-weight:600;color:#d46b08">{{ t.pending_count || 0 }}</span></template>
              <template v-else-if="col.key === 'corrected_count'"><span style="font-weight:600;color:#52c41a">{{ t.corrected_count || 0 }}</span></template>
              <template v-else>{{ t[col.key] }}</template>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="card" style="padding:32px;text-align:center;color:#999">
        {{ tasks.length ? '无匹配任务' : '暂无收集任务，点击上方按钮创建' }}
      </div>
    </div>

    <!-- 手机端任务列表 -->
    <template v-else>
      <div class="mobile-filter">
        <van-field v-model="mobileSearch" placeholder="搜索任务名称/课程/主题" clearable />
      </div>
      <div class="mobile-tabs">
        <span v-for="st in statusTabs" :key="st.value" class="mobile-tab" :class="{ active: filters.status === st.value }" @click="setStatusFilter(st.value)">{{ st.label }}</span>
      </div>
      <div v-if="filteredTasks.length" class="mobile-task-list">
        <div v-for="t in filteredTasks" :key="t.id" class="task-card">
          <div class="task-card-head" @click="onCardClick(t)">
            <span class="task-card-name">{{ t.name }}</span>
            <van-tag :type="statusTagType(t)" :plain="!getTaskStatus(t).active">{{ getTaskStatus(t).label }}</van-tag>
          </div>
          <div class="task-card-tags" @click="onCardClick(t)">
            <span class="badge-mini tag-grade">{{ t.grade || '未定年级' }}</span>
            <span class="badge-mini tag-number">{{ t.essay_number ? '第' + t.essay_number + '次' : '无第几次' }}</span>
            <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
            <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
          </div>
          <div v-if="t.essay_topic" class="task-card-topic" @click="onCardClick(t)">{{ t.essay_topic }}</div>
          <div class="task-card-meta" @click="onCardClick(t)">
            <span v-if="t.start_time">开始 {{ formatDate(t.start_time) }}</span>
            <span :class="{ 'deadline-soon': isExpired(t) }">截止 {{ formatDeadline(t.deadline) }}</span>
          </div>
          <div class="task-card-stats" @click="onCardClick(t)">
            <span class="stat stat-submitted">已交 <b>{{ t.submitted_count || 0 }}</b></span>
            <span class="stat stat-pending">未改 <b>{{ t.pending_count || 0 }}</b></span>
            <span class="stat stat-corrected">已改 <b>{{ t.corrected_count || 0 }}</b></span>
          </div>
          <div v-if="isAdmin" class="task-card-actions">
            <button class="act-btn" @click="viewEssays(t)">作文</button>
            <button class="act-btn" @click="goBatchUpload(t)">批量上传</button>
            <button class="act-btn" @click="openTaskDialog(t)">编辑</button>
            <button class="act-btn" @click="cloneTask(t)">复制</button>
            <button class="act-btn" :class="{ 'act-btn-success': !getTaskStatus(t).active }" @click="toggleTaskActive(t)">{{ getTaskStatus(t).active ? '结束收集' : '开始收集' }}</button>
            <button class="act-btn act-btn-danger" @click="confirmDelTask(t)">删除</button>
          </div>
        </div>
      </div>
      <div v-else style="padding:32px;text-align:center;color:#999">
        暂无收集任务
      </div>
    </template>

    <!-- 任务弹窗 -->
    <div v-if="showTaskDialog" class="modal-overlay" @click.self="showTaskDialog=false">
      <div class="modal-box" style="max-width:500px">
        <h3>{{ editingTask.id ? '编辑收集任务' : '创建收集任务' }}</h3>
        <van-form @submit="saveTask">
          <van-cell-group inset>
            <van-field v-model="taskForm.name" label="任务名称" placeholder="如：高二第三次作文" :rules="[{required:true}]" />
            <van-field :model-value="taskForm.grade || '暂不选择'" is-link readonly label="年级" placeholder="请选择年级（可暂不选择）" @click="showTaskGradePicker=true" />
            <van-field v-model="taskForm.essay_number" label="第几次作文" type="digit" placeholder="不填或0表示无第几次" />
            <van-field v-model="taskForm.essay_topic" label="文章主题" placeholder="如：议论文写作" />
            <van-field :model-value="taskForm.course_name || '请选择课程'" is-link readonly label="课程名称" placeholder="请选择课程" @click="showCoursePicker=true" />
            <van-field name="teaching_mode" label="提交方式">
              <template #input>
                <van-radio-group v-model="taskForm.teaching_mode" direction="horizontal">
                  <van-radio name="线下" style="margin-right:16px">线下</van-radio>
                  <van-radio name="线上">线上</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field v-model="taskForm.startTimeStr" label="开始时间" type="date" placeholder="可选" />
            <van-field v-model="taskForm.deadlineStr" label="截止时间" type="date" placeholder="可选" />
            <van-field name="is_active" label="立即开始收集">
              <template #input>
                <van-switch v-model="taskForm.is_active" size="24" />
              </template>
            </van-field>
          </van-cell-group>
          <div style="margin:16px;display:flex;gap:8px">
            <van-button block @click="showTaskDialog=false">取消</van-button>
            <van-button block type="primary" native-type="submit">保存</van-button>
          </div>
        </van-form>
      </div>
    </div>

    <!-- 年级选择器 -->
    <van-action-sheet v-model:show="showTaskGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell title="暂不选择年级" @click="selectTaskGrade('')" style="color:#999" />
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectTaskGrade(g)" />
      </div>
    </van-action-sheet>

    <!-- 课程选择器 -->
    <van-action-sheet v-model:show="showCoursePicker" title="选择课程">
      <div class="picker-list">
        <van-cell title="不选择课程" @click="selectCourse(null)" style="color:#999" />
        <van-cell v-for="c in courses" :key="c.id"
          :title="c.name"
          @click="selectCourse(c)" />
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDate as formatShortDate, formatDateTime } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isAdmin = computed(() => (currentUser.value.role || '').includes('admin'))

const tasks = ref([])
const courses = ref([])
const filters = ref({ name: '', grade: '', status: '', course: '', number: '', teachingMode: '', topic: '' })
const statusFilterLabel = { active: '收集中', expired: '已过期', ended: '已结束', not_started: '未开始' }
const statusTabs = [
  { value: '', label: '全部' },
  { value: 'active', label: '收集中' },
  { value: 'not_started', label: '未开始' },
  { value: 'expired', label: '已过期' },
  { value: 'ended', label: '已结束' },
]
const mobileSearch = ref('')

const columnDefs = [
  { key: 'name', label: '任务名称', sortable: true },
  { key: 'grade', label: '年级', sortable: true },
  { key: 'number', label: '第几次', sortable: true },
  { key: 'topic', label: '文章主题', sortable: false },
  { key: 'course', label: '课程名称', sortable: true },
  { key: 'teaching_mode', label: '提交方式', sortable: true },
  { key: 'submitted', label: '已交学生数', sortable: true },
  { key: 'pending_count', label: '未改', sortable: true },
  { key: 'corrected_count', label: '已改', sortable: true },
  { key: 'start_time', label: '开始时间', sortable: true },
  { key: 'deadline', label: '截止时间', sortable: true },
  { key: 'status', label: '状态', sortable: false },
]

function visibleColumnDefs() {
  const defs = [...columnDefs]
  if (isAdmin.value) {
    defs.push({ key: 'actions', label: '操作', sortable: false })
  }
  return defs
}

const columns = ref([])
const sortKey = ref('')
const sortDir = ref('asc')
let draggedIndex = null

function initColumns() {
  const defs = visibleColumnDefs()
  const validKeys = new Set(defs.map(c => c.key))
  const saved = localStorage.getItem('taskColumns')
  if (saved) {
    try {
      const savedCols = JSON.parse(saved)
      // 合并：保留已保存的顺序，同时补充新增的列；过滤不可见列
      const merged = []
      for (const def of defs) {
        const found = savedCols.find(c => c && c.key === def.key)
        merged.push(found ? { ...def, ...found } : { ...def })
      }
      // 去除已不存在的列（不在columnDefs中的旧列）或当前角色不可见的列
      columns.value = merged.filter(c => validKeys.has(c.key))
      return
    } catch {}
  }
  columns.value = defs.map(c => ({ ...c }))
}

function saveColumns() {
  localStorage.setItem('taskColumns', JSON.stringify(columns.value))
}

function onDragStart(e, ci) { draggedIndex = ci; e.dataTransfer.effectAllowed = 'move' }
function onDragOver(e, ci) {
  e.dataTransfer.dropEffect = 'move'
  const ths = e.currentTarget.parentElement.children
  for (let i = 0; i < ths.length; i++) ths[i].classList.remove('drag-over')
  ths[ci].classList.add('drag-over')
}
function onDrop(e, ci) {
  const ths = e.currentTarget.parentElement.children
  for (let i = 0; i < ths.length; i++) ths[i].classList.remove('drag-over')
  if (draggedIndex === null || draggedIndex === ci) return
  const item = columns.value.splice(draggedIndex, 1)[0]
  columns.value.splice(ci, 0, item)
  saveColumns()
  draggedIndex = null
}

function toggleSort(key) {
  const col = columns.value.find(c => c.key === key)
  if (col && !col.sortable) return
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

const filteredTasks = computed(() => {
  const kw = filters.value.name.toLowerCase()
  return tasks.value.filter(t => {
    if (kw && !t.name.toLowerCase().includes(kw)) return false
    if (mobileSearch.value) {
      const mw = mobileSearch.value.toLowerCase()
      const ok = (t.name || '').toLowerCase().includes(mw)
        || (t.course_name || '').toLowerCase().includes(mw)
        || (t.essay_topic || '').toLowerCase().includes(mw)
      if (!ok) return false
    }
    if (filters.value.grade && t.grade !== filters.value.grade) return false
    if (filters.value.number && String(t.essay_number) !== String(filters.value.number)) return false
    if (filters.value.teachingMode && t.teaching_mode !== filters.value.teachingMode) return false
    if (filters.value.topic && !(t.essay_topic || '').toLowerCase().includes(filters.value.topic.toLowerCase())) return false
    if (filters.value.course && !(t.course_name || '').toLowerCase().includes(filters.value.course.toLowerCase())) return false
    const taskStatus = getTaskStatus(t).label
    if (filters.value.status && taskStatus !== statusFilterLabel[filters.value.status]) return false
    return true
  })
})

const sortedTasks = computed(() => {
  const list = filteredTasks.value
  if (!sortKey.value) return list
  return [...list].sort((a, b) => {
    let va = getSortValue(a, sortKey.value)
    let vb = getSortValue(b, sortKey.value)
    if (va == null) va = ''
    if (vb == null) vb = ''
    const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb
    return sortDir.value === 'asc' ? cmp : -cmp
  })
})

function getSortValue(t, key) {
  if (key === 'number') return t.essay_number || 0
  if (key === 'start_time') return t.start_time || ''
  if (key === 'deadline') return t.deadline || ''
  if (key === 'status') return getTaskStatus(t).label
  if (key === 'course') return t.course_name || ''
  if (key === 'teaching_mode') return t.teaching_mode || ''
  if (key === 'topic') return t.essay_topic || ''
  if (key === 'submitted') return t.submitted_count || 0
  if (key === 'pending_count') return t.pending_count || 0
  if (key === 'corrected_count') return t.corrected_count || 0
  return t[key] || ''
}
function clearFilter() {
  filters.value = { name: '', grade: '', status: '', course: '', number: '', teachingMode: '', topic: '' }
  mobileSearch.value = ''
}
function setStatusFilter(v) {
  filters.value.status = v
}
const showTaskDialog = ref(false)
const editingTask = ref({})
const showTaskGradePicker = ref(false)
const showCoursePicker = ref(false)
const grades = ['初一','初二','初三','高一','高二','高三']
const taskForm = ref({
  name: '', grade: '', essay_number: 1, essay_topic: '', course_id: '', course_name: '',
  teaching_mode: '线下', startTimeStr: '', deadlineStr: '', is_active: false
})

onMounted(() => { initColumns(); loadData() })

async function loadData() {
  try {
    const [taskRes, courseRes] = await Promise.all([
      api.get('/admin/tasks'),
      api.get('/essays/courses')
    ])
    tasks.value = taskRes.data
    courses.value = courseRes.data || []
  } catch {}
}

function formatDate(dateStr) {
  return formatShortDate(dateStr) || '-'
}

function formatDeadline(deadline) {
  if (!deadline) return '无限制'
  return formatDateTime(deadline)
}

function isExpired(tpl) {
  if (!tpl.deadline) return false
  return new Date(tpl.deadline) < new Date()
}

function notStarted(tpl) {
  if (!tpl.start_time) return false
  return new Date(tpl.start_time) > new Date()
}

function getTaskStatus(tpl) {
  if (notStarted(tpl)) return { active: false, label: '未开始' }
  if (isExpired(tpl)) return { active: false, label: '已过期' }
  if (tpl.is_active) return { active: true, label: '收集中' }
  return { active: false, label: '已结束' }
}

function statusTagType(tpl) {
  const s = getTaskStatus(tpl).label
  if (s === '收集中') return 'primary'
  if (s === '未开始') return 'warning'
  if (s === '已过期') return 'danger'
  return 'default'
}

function onCardClick(tpl) {
  if (isAdmin.value) openTaskDialog(tpl)
  else viewEssays(tpl)
}

function openTaskDialog(tpl) {
  if (tpl) {
    editingTask.value = tpl
    const startTimeStr = tpl.start_time ? new Date(tpl.start_time).toISOString().slice(0, 10) : ''
    const deadlineStr = tpl.deadline ? new Date(tpl.deadline).toISOString().slice(0, 10) : ''
    taskForm.value = {
      name: tpl.name, grade: tpl.grade, essay_number: tpl.essay_number,
      essay_topic: tpl.essay_topic || '', course_id: tpl.course_id || '', course_name: tpl.course_name || '',
      teaching_mode: tpl.teaching_mode || '线下', startTimeStr, deadlineStr, is_active: tpl.is_active
    }
  } else {
    editingTask.value = {}
    taskForm.value = {
      name: '', grade: '', essay_number: '', essay_topic: '', course_id: '', course_name: '',
      teaching_mode: '线下', startTimeStr: '', deadlineStr: '', is_active: false
    }
  }
  showTaskDialog.value = true
}

function selectTaskGrade(g) {
  taskForm.value.grade = g
  showTaskGradePicker.value = false
}

function selectCourse(c) {
  taskForm.value.course_id = c ? c.id : ''
  taskForm.value.course_name = c ? c.name : ''
  showCoursePicker.value = false
}

async function saveTask() {
  try {
    const payload = {
      name: taskForm.value.name,
      grade: taskForm.value.grade,
      essay_number: parseInt(taskForm.value.essay_number) || 0,
      essay_topic: taskForm.value.essay_topic,
      course_id: taskForm.value.course_id ? parseInt(taskForm.value.course_id) : null,
      teaching_mode: taskForm.value.teaching_mode,
      start_time: taskForm.value.startTimeStr ? new Date(taskForm.value.startTimeStr).toISOString() : null,
      deadline: taskForm.value.deadlineStr ? new Date(taskForm.value.deadlineStr).toISOString() : null,
      is_active: taskForm.value.is_active,
    }
    if (editingTask.value.id) {
      await api.put(`/admin/tasks/${editingTask.value.id}`, payload)
      showToast('更新成功')
    } else {
      await api.post('/admin/tasks', payload)
      showToast('创建成功')
    }
    showTaskDialog.value = false
    loadData()
  } catch(err) { showToast(err.response?.data?.detail || '操作失败') }
}

async function toggleTaskActive(tpl) {
  try {
    const res = await api.put(`/admin/tasks/${tpl.id}/activate`)
    showToast(res.data?.is_active ? '已开始收集' : '已结束收集')
    loadData()
  } catch(err) { showToast(err.response?.data?.detail || '操作失败') }
}

async function cloneTask(tpl) {
  try {
    await api.post(`/admin/tasks/${tpl.id}/clone`)
    showToast('已复制为新任务（默认停用，请编辑后开始收集）')
    loadData()
  } catch(err) { showToast(err.response?.data?.detail || '复制失败') }
}

function confirmDelTask(tpl) {
  showDialog({ title: '确认删除', message: `删除收集任务「${tpl.name}」？`, showCancelButton: true })
    .then(async () => {
      await api.delete(`/admin/tasks/${tpl.id}`)
      tasks.value = tasks.value.filter(x => x.id !== tpl.id)
      showToast('已删除')
    }).catch(() => {})
}

function viewEssays(tpl) {
  // 重置作文列表的筛选，再按当前任务筛选
  localStorage.removeItem('essay_list_filters')
  router.push({ path: '/essay/list', query: { task_id: tpl.id } })
}

function goBatchUpload(tpl) {
  router.push({ path: '/essay/batch-upload', query: { task_id: tpl.id } })
}
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }
.picker-list { max-height: 300px; overflow-y: auto; }
.task-name-link {
  color: #1677ff;
  cursor: pointer;
  font-weight: 500;
}
.task-name-link:hover {
  text-decoration: underline;
}

.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.filter-input {
  padding: 6px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: #fff;
  min-width: 120px;
}
.filter-input:focus {
  border-color: #4096ff;
  box-shadow: 0 0 0 2px rgba(24,144,255,0.1);
}

.sort-arrow {
  font-size: 10px;
  margin-left: 2px;
}
.desktop-table th.sortable {
  user-select: none;
}
.desktop-table th.sorted {
  color: #1677ff;
}
.desktop-table th.drag-over {
  border-left: 2px solid #1677ff;
  border-right: 2px solid #1677ff;
}

/* ===== 手机端任务列表 ===== */
.mobile-filter { padding: 8px 12px 0; }
.mobile-tabs {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  position: sticky;
  top: 48px;
  background: #fff;
  z-index: 10;
}
.mobile-tab {
  flex-shrink: 0;
  padding: 5px 14px;
  font-size: 13px;
  color: #666;
  background: #f5f5f5;
  border-radius: 16px;
  white-space: nowrap;
}
.mobile-tab.active {
  background: #1677ff;
  color: #fff;
  font-weight: 500;
}
.mobile-task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 8px 12px 16px;
}
.task-card {
  background: #fff;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.task-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.task-card-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}
.tag-course { background: #f0f5ff; color: #2f54eb; }
.task-card-topic {
  font-size: 13px;
  color: #555;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}
.deadline-soon { color: #ff4d4f; }
.task-card-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
  margin-bottom: 10px;
}
.task-card-stats b { font-size: 14px; }
.stat-submitted b { color: #1677ff; }
.stat-pending b { color: #d46b08; }
.stat-corrected b { color: #52c41a; }
.task-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid #f5f5f5;
}
.act-btn {
  flex: 1;
  min-width: 72px;
  padding: 6px 8px;
  font-size: 13px;
  color: #1677ff;
  background: #e6f4ff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.act-btn-success { color: #52c41a; background: #f6ffed; }
.act-btn-danger { color: #ff4d4f; background: #fff1f0; }
</style>
