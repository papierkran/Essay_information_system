<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">课程管理</div>

    <div v-if="isDesktop" style="margin-bottom:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <button class="btn btn-success" @click="openCourseDialog()">+ 创建课程</button>
      <label class="btn btn-primary" style="cursor:pointer">📥 导入CSV<input type="file" accept=".csv" @change="previewCSV" style="display:none" /></label>
      <button class="btn" @click="downloadTemplate">📄 下载模板</button>
      <span v-if="importing" style="font-size:13px;color:#999">解析中...</span>
      <span style="font-size:12px;color:#999">CSV 第一列为 ClassIn 班级 ID，第二列为课程名称</span>
      <input v-model="keyword" placeholder="搜索课程名称" class="filter-input" style="margin-left:auto" />
    </div>

    <!-- 导入预览弹窗 -->
    <div v-if="showImportPreview" class="modal-overlay" @click.self="showImportPreview=false">
      <div class="modal-box" style="max-width:600px">
        <h3>📥 选择要导入的课程</h3>
        <p style="font-size:13px;color:#999;margin-bottom:12px">共 {{ previewCourses.length }} 个，已存在 {{ previewCourses.filter(c => c.exists).length }} 个</p>
        <div style="max-height:400px;overflow-y:auto">
          <label v-for="(c, i) in previewCourses" :key="i"
            style="display:flex;align-items:center;gap:8px;padding:8px 4px;border-bottom:1px solid #f5f5f5;cursor:pointer">
            <input type="checkbox" :value="c.name" v-model="selectedNames" style="width:auto" />
            <span>{{ c.name }}<span v-if="c.classin_id" style="color:#999;font-size:12px;margin-left:6px">[{{ c.classin_id }}]</span></span>
            <span v-if="c.exists" class="tag tag-corrected" style="margin-left:auto">已存在</span>
          </label>
        </div>
        <div class="form-actions" style="margin-top:12px">
          <button class="btn" @click="showImportPreview=false">取消</button>
          <button class="btn" @click="selectAll">全选</button>
          <button class="btn" @click="selectNewOnly">只选新增</button>
          <span style="font-size:13px;color:#999">已选 {{ selectedNames.length }} 个</span>
          <button class="btn btn-primary" @click="confirmImport" :disabled="selectedNames.length===0">确认导入</button>
        </div>
      </div>
    </div>

    <!-- 手机端操作按钮 -->
    <template v-if="!isDesktop">
      <div style="display:flex;gap:8px;padding:12px 12px 0;flex-wrap:wrap">
        <van-button type="success" size="small" @click="openCourseDialog()">创建课程</van-button>
        <van-button type="primary" size="small" @click="$refs.csvInput.click()">导入CSV</van-button>
        <van-button size="small" @click="downloadTemplate">模板</van-button>
        <van-field v-model="keyword" placeholder="搜索课程名称" clearable style="flex:1;min-width:120px" />
      </div>
      <div style="padding:6px 12px 0;font-size:12px;color:#999">CSV 第一列为 ClassIn 班级 ID，第二列为课程名称</div>
      <input type="file" ref="csvInput" accept=".csv" style="display:none" @change="previewCSV" />
    </template>

    <!-- 桌面端课程列表 -->
    <div v-if="isDesktop">
      <table class="desktop-table" v-if="filteredCourses.length">
        <thead>
          <tr>
            <th style="cursor:pointer" @click="toggleSort('name')">课程名称 {{ sortIcon('name') }}</th>
            <th>ClassIn ID</th>
            <th style="cursor:pointer" @click="toggleSort('task_count')">关联任务 {{ sortIcon('task_count') }}</th>
            <th style="cursor:pointer" @click="toggleSort('essay_count')">关联作文 {{ sortIcon('essay_count') }}</th>
            <th style="cursor:pointer" @click="toggleSort('created_at')">创建时间 {{ sortIcon('created_at') }}</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in sortedCourses" :key="c.id">
            <td>{{ c.name }}</td>
            <td>{{ c.classin_id || '-' }}</td>
            <td><span style="font-weight:600;color:#1677ff;cursor:pointer" :title="'查看「' + c.name + '」的作文'" @click="goEssays(c)">{{ c.task_count || 0 }}</span></td>
            <td><span style="font-weight:600;color:#52c41a;cursor:pointer" :title="'查看「' + c.name + '」的作文'" @click="goEssays(c)">{{ c.essay_count || 0 }}</span></td>
            <td>{{ c.created_at?.substring(0,10) }}</td>
            <td style="white-space:nowrap">
              <button class="btn" style="font-size:12px;padding:2px 8px" @click="openCourseDialog(c)">编辑</button>
              <button class="btn" style="font-size:12px;padding:2px 8px;color:#ff4d4f" @click="confirmDelCourse(c)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="card" style="padding:32px;text-align:center;color:#999">暂无课程</div>
    </div>

    <!-- 手机端课程列表 -->
    <van-cell-group v-if="!isDesktop" inset style="margin-top:12px">
      <van-swipe-cell v-for="c in sortedCourses" :key="c.id">
        <van-cell :title="c.name" is-link @click="openCourseDialog(c)">
          <template #label>
            <span v-if="c.classin_id" style="color:#999">[{{ c.classin_id }}]</span> 任务 {{ c.task_count || 0 }} · <span style="color:#1677ff" @click.stop="goEssays(c)">作文 {{ c.essay_count || 0 }}</span> · {{ c.created_at?.substring(0,10) }}
          </template>
        </van-cell>
        <template #right>
          <van-button square type="danger" text="删除" style="height:100%" @click="confirmDelCourse(c)" />
        </template>
      </van-swipe-cell>
      <van-cell v-if="!filteredCourses.length" title="暂无课程" />
    </van-cell-group>

    <!-- 课程弹窗 -->
    <van-dialog v-model:show="showCourseDialog" :title="editingCourse.id ? '编辑课程' : '创建课程'" show-cancel-button :before-close="onCourseClose">
      <van-form ref="courseFormRef">
        <van-field v-model="courseForm.name" label="课程名称" maxlength="30" :rules="[{required:true}]" />
        <van-field v-model="courseForm.classin_id" label="ClassIn班级ID" maxlength="50" placeholder="可选，如 C001" />
        <div v-if="editingCourse.id" style="padding:0 16px 12px;font-size:13px;color:#999">
          当前关联：{{ editingCourse.task_count || 0 }} 个任务 / {{ editingCourse.essay_count || 0 }} 篇作文
        </div>
      </van-form>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog, showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api from '../api'

const router = useRouter()
const { isDesktop } = useScreen()
const courses = ref([])
const keyword = ref('')
const filteredCourses = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return courses.value
  return courses.value.filter(c => (c.name || '').toLowerCase().includes(kw))
})

const sortKey = ref('')
const sortDir = ref('desc')
const sortedCourses = computed(() => {
  const list = filteredCourses.value
  if (!sortKey.value) return list
  return [...list].sort((a, b) => {
    let va = a[sortKey.value]
    let vb = b[sortKey.value]
    if (va == null) va = ''
    if (vb == null) vb = ''
    const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb
    return sortDir.value === 'asc' ? cmp : -cmp
  })
})
function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}
function sortIcon(key) {
  if (sortKey.value !== key) return '⇅'
  return sortDir.value === 'asc' ? '▲' : '▼'
}

const showCourseDialog = ref(false)
const courseFormRef = ref(null)
const editingCourse = ref({})
const courseForm = ref({ name: '' })
const importing = ref(false)
const showImportPreview = ref(false)
const previewCourses = ref([])
const selectedNames = ref([])
let pendingFile = null

onMounted(loadData)

async function loadData() {
  try {
    const res = await api.get('/admin/courses')
    courses.value = res.data
  } catch { showToast('加载失败，请重试') }
}

function goEssays(cls) {
  // 重置作文列表筛选后按课程跳转
  localStorage.removeItem('essay_list_filters')
  router.push({ path: '/essay/list', query: { course_id: cls.id } })
}

function downloadTemplate() {
  const content = '\ufeff班级ID,课程名称\nC001,示例课程一\nC002,示例课程二\n'
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = '课程导入模板.csv'; a.click()
  URL.revokeObjectURL(url)
}

function selectAll() { selectedNames.value = previewCourses.value.map(c => c.name) }
function selectNewOnly() { selectedNames.value = previewCourses.value.filter(c => !c.exists).map(c => c.name) }

function openCourseDialog(cls) {
  if (cls) { editingCourse.value = cls; courseForm.value = { name: cls.name, classin_id: cls.classin_id || '' } }
  else { editingCourse.value = {}; courseForm.value = { name: '', classin_id: '' } }
  showCourseDialog.value = true
}

async function saveCourse() {
  try {
    const payload = { name: courseForm.value.name, classin_id: courseForm.value.classin_id }
    if (editingCourse.value.id) {
      await api.put(`/admin/courses/${editingCourse.value.id}`, payload)
      showToast('更新成功')
    } else {
      await api.post('/admin/courses', payload)
      showToast('创建成功')
    }
    showCourseDialog.value = false; loadData()
  } catch(err) { showToast(err.response?.data?.detail || '操作失败') }
}

function onCourseClose(action) {
  if (action !== 'confirm') return true
  return courseFormRef.value.validate().then(() => saveCourse().then(() => true)).catch(() => false)
}

function confirmDelCourse(cls) {
  showDialog({
    title: '确认删除',
    message: `删除课程「${cls.name}」？\n（关联 ${cls.task_count || 0} 个任务 / ${cls.essay_count || 0} 篇作文，删除后这些数据的课程关联将失效，显示为「无课程」）`,
    showCancelButton: true,
  })
    .then(async () => {
      await api.delete(`/admin/courses/${cls.id}`)
      courses.value = courses.value.filter(x => x.id !== cls.id)
      showToast('已删除')
    }).catch(() => {})
}

async function previewCSV(e) {
  const file = e.target.files[0]
  if (!file) return
  pendingFile = file
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await api.post('/admin/import-courses-csv/preview', fd)
    previewCourses.value = res.data.courses
    selectedNames.value = res.data.courses.filter(c => !c.exists).map(c => c.name)
    showImportPreview.value = true
  } catch(err) {
    showToast('解析失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    importing.value = false
    e.target.value = ''
  }
}

async function confirmImport() {
  if (!pendingFile || selectedNames.value.length === 0) return
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', pendingFile)
    fd.append('selected', JSON.stringify(selectedNames.value))
    const res = await api.post('/admin/import-courses-csv/confirm', fd)
    showToast(`导入 ${res.data.imported} 个，跳过 ${res.data.skipped} 个`)
    showImportPreview.value = false
    loadData()
  } catch(err) {
    showToast('导入失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.page { padding: 0; }
.filter-input {
  padding: 6px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  min-width: 160px;
}
.filter-input:focus { border-color: #4096ff; }
@media (max-width: 767px) { .page { min-height: 100vh; } }
</style>
