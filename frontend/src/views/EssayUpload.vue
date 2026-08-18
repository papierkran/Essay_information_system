<template>
  <div class="page">
    <div v-if="isDesktop" class="page-title">上传作文</div>

    <!-- 补交规则提示 -->
    <div class="tips-box">
      <span class="tips-icon">💡</span>
      <span>未在收集中（未开始 / 已结束 / 已过期）的任务，选择后会自动勾选补交</span>
    </div>

    <!-- 模板选择区域 -->
    <van-cell-group inset style="margin-bottom:12px">
      <van-field :model-value="selectedTaskName" is-link readonly label="选择收集任务"
        placeholder="选择收集任务（将自动填充年级等信息）" @click="showTaskPicker = true" />
      <!-- 显示选中模板的文章主题与课程 -->
      <van-cell v-if="selectedTaskCourse" title="所属课程" :label="selectedTaskCourse" />
      <van-cell v-if="selectedTaskTopic" title="文章主题" :label="selectedTaskTopic" />
    </van-cell-group>

    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field :model-value="selectedGrade" is-link readonly label="年级"
          :placeholder="selectedGrade || '请选择年级'" @click="showGradePicker = true" />
        <van-field v-model="form.grade" v-show="false" />
        <van-field v-model="form.essay_number" label="第几次作文" placeholder="数字（不填表示无）" type="digit" />
        <van-field v-model="form.essay_title" label="作文标题" required placeholder="在粘贴文字中将自动填充第一行作为标题（必填）" />
        <div v-if="recentTitles.length" style="padding:0 16px 8px;display:flex;flex-wrap:wrap;gap:6px">
          <van-tag v-for="t in recentTitles" :key="t" plain size="medium" @click="form.essay_title = t" style="cursor:pointer">{{ t }}</van-tag>
        </div>
        <div class="student-name-cell">
          <van-field :model-value="form.student_name" label="学生姓名" required placeholder="输入姓名（必填）" @update:model-value="onNameChange" @focus="onStudentInput" @blur="onStudentBlur" />
          <div v-if="studentSuggestions.length" class="student-suggest">
            <div v-for="n in studentSuggestions" :key="n" class="student-suggest-item" @mousedown.prevent @click="pickStudent(n)">{{ n }}</div>
          </div>
        </div>
        <van-field name="is_supplement" label="是否补交">
          <template #input><van-switch v-model="form.is_supplement" size="24" /></template>
        </van-field>
        <van-field name="teaching_mode" label="学生提交方式">
          <template #input>
            <van-radio-group v-model="form.teaching_mode" direction="horizontal">
              <van-radio name="线下" style="margin-right:16px">线下</van-radio>
              <van-radio name="线上">线上</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field v-if="isAdmin" :model-value="selectedCollectorName" is-link readonly label="收集者" placeholder="默认当前用户"
          @click="showCollectorPicker = true" />
        <van-field v-model="form.collector_note" label="收集者备注" placeholder="收集者自定义备注（可选）" />
      </van-cell-group>
      <van-cell-group inset style="margin-top:12px">
        <van-field name="uploader" label="上传文件（docx/txt/图片，可多选）">
          <template #input>
            <div class="drop-zone" @dragover.prevent @dragenter.prevent @drop.prevent="onUploadDrop">
              <van-uploader v-model="fileList" :max-count="10" accept="image/*,.docx,.txt" multiple :before-read="beforeRead" :after-read="afterRead" :preview-full-image="false" @click-preview="onPreviewClick" />
              <div style="font-size:12px;color:#999;margin-top:8px">支持拖拽文件到此处 · docx/txt 自动读取内容 · 图片大小不超过 4MB</div>
            </div>
          </template>
        </van-field>
        <van-image-preview v-model:show="showPreview" :images="previewImages" :start-position="previewIndex" :closeable="true" />
        <van-field v-model="form.content_text" label="上传文本作文" type="textarea" placeholder="建议优先文字上传，粘贴作文内容..." rows="4" autosize />
        <div class="field-tips">tips：第一行为标题，会自动识别填充到「作文标题」</div>
        <div v-if="contentParagraphs.length" class="upload-preview">
          <div class="upload-preview-title">📄 预览</div>
          <div class="content-text">
            <p v-for="(para, i) in contentParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
          </div>
        </div>
      </van-cell-group>
      <div v-if="loading || showProgress" style="margin:0 16px 8px">
        <van-progress :percentage="uploadProgress" stroke-width="8" />
        <div style="font-size:12px;color:#999;margin-top:4px;text-align:center">{{ uploadProgress >= 100 ? '上传完成 ✓' : `正在上传 ${uploadProgress}%...` }}</div>
      </div>
      <div style="margin:16px">
        <van-button round block type="primary" native-type="submit" :loading="loading">提交作文</van-button>
        <van-checkbox v-model="keepTask" icon-size="16px" style="margin-top:10px;justify-content:center;font-size:13px;color:#666">连续上传时保持当前任务选择</van-checkbox>
      </div>
    </van-form>

    <!-- 年级选择器 -->
    <van-action-sheet v-model:show="showGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell title="暂不选择" @click="selectGrade('')" style="color:#999" />
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectGrade(g)" />
      </div>
    </van-action-sheet>

    <!-- 模板选择器 -->
    <van-action-sheet v-model:show="showTaskPicker" title="选择收集任务" class="task-picker-sheet"
      :style="{ maxHeight: '88vh', display: 'flex', flexDirection: 'column' }">
      <div class="picker-list">
        <div style="padding:8px 16px">
          <input v-model="taskSearch" placeholder="搜索任务名称/主题/年级..." style="width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;outline:none" />
        </div>
        <div style="padding:0 16px 8px;display:flex;align-items:center;gap:6px;font-size:13px;color:#666">
          <van-checkbox v-model="showActiveOnly" icon-size="16px" shape="square">只看收集中</van-checkbox>
          <span style="color:#999;font-size:12px">（关闭可查看全部 {{ sortedTasks.length }} 个任务）</span>
        </div>
        <van-cell title="不使用模板" @click="selectTask(null)" style="color:#999" />
        <div class="task-split">
          <div class="task-col">
            <div class="task-col-title">线上</div>
            <van-cell v-for="t in pagedOnlineTasks" :key="t.id" @click="selectTask(t)">
              <template #title>
                <span style="font-weight:500">{{ t.name }}</span>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
              </template>
              <template #label>
                <span class="badge-mini tag-grade">{{ t.grade }}</span>
                <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
                <span v-if="t.essay_topic" style="color:#999">{{ t.essay_topic }}</span>
              </template>
            </van-cell>
            <div v-if="filteredOnlineTasks.length > PAGE_SIZE" class="pagination-row">
              <button class="btn" :disabled="pageOnline <= 1" @click="pageOnline--">上一页</button>
              <span class="page-info">{{ pageOnline }} / {{ onlineTotalPages }}</span>
              <button class="btn" :disabled="pageOnline >= onlineTotalPages" @click="pageOnline++">下一页</button>
            </div>
            <div v-if="!filteredOnlineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线上任务</div>
          </div>
          <div class="task-col">
            <div class="task-col-title">线下</div>
            <van-cell v-for="t in pagedOfflineTasks" :key="t.id" @click="selectTask(t)">
              <template #title>
                <span style="font-weight:500">{{ t.name }}</span>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
              </template>
              <template #label>
                <span class="badge-mini tag-grade">{{ t.grade }}</span>
                <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
                <span v-if="t.essay_topic" style="color:#999">{{ t.essay_topic }}</span>
              </template>
            </van-cell>
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

    <!-- 收集者选择器 -->
    <van-action-sheet v-model:show="showCollectorPicker" title="选择收集者">
      <div class="picker-list">
        <van-cell title="默认（当前用户）" @click="selectCollector(null)" />
        <van-cell v-for="c in collectorList" :key="c.id" :title="c.nickname || c.username" @click="selectCollector(c)" />
      </div>
    </van-action-sheet>

    <!-- 上传成功弹窗 -->
    <van-dialog v-model:show="uploadSuccessDialog.show" title="✅ 上传成功" :show-cancel-button="false" :show-confirm-button="false" :close-on-click-overlay="false" class="upload-success-dialog">
      <div style="padding:16px">
        <p style="white-space:pre-line;font-size:15px;line-height:1.8;margin-bottom:12px">{{ uploadSuccessDialog.body }}</p>
        <div v-if="sessionUploaded.length > 1" style="margin-bottom:12px;font-size:13px;color:#666">
          本次会话已连续成功上传 <strong>{{ sessionUploaded.length }}</strong> 篇
          <div style="margin-top:6px;max-height:120px;overflow-y:auto;border:1px solid #f0f0f0;border-radius:6px;padding:4px 8px">
            <div v-for="(s, i) in sessionUploaded" :key="s.id" style="padding:3px 0;cursor:pointer;color:#1677ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" @click="openUploaded(s)">
              {{ i + 1 }}. {{ s.name }}《{{ s.title || '无标题' }}》
            </div>
          </div>
        </div>
        <div class="upload-success-actions">
          <button class="btn" @click="goUploadList">去列表查看</button>
          <button class="btn" :disabled="!uploadSuccessDialog.id" @click="viewUploaded">查看刚上传的作文</button>
          <button class="btn btn-primary" @click="continueUpload">继续上传</button>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showDialog, showConfirmDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { compressImageFile, isImageFile, IMAGE_UPLOAD_MAX_BYTES } from '../utils/imageCompress'
import { ensureContentHeader } from '../utils/essayHeader'

const route = useRoute()
const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isAdmin = computed(() => (currentUser.value.role || '').includes('admin'))
const isGuest = computed(() => (currentUser.value.role || '').includes('guest'))

const fileList = ref([])
const loading = ref(false)
const uploadProgress = ref(0)
const showProgress = ref(false)
const keepTask = ref(false)
const uploadSuccessDialog = ref({ show: false, id: null, body: '' })
const sessionUploaded = ref([])
const showGradePicker = ref(false)
const showTaskPicker = ref(false)
const showCollectorPicker = ref(false)
const showPreview = ref(false)
const previewIndex = ref(0)
const previewImages = ref([])
const selectedGrade = ref('')
const selectedTaskName = ref('')
const selectedTaskTopic = ref('')
const selectedTaskCourse = ref('')
const selectedTaskId = ref(null)
const selectedCourseId = ref(null)
const selectedCollector = ref(null)
const selectedCollectorName = ref('')
const collectorList = ref([])
const recentTitles = ref([])
const grades = ['初一','初二','初三','高一','高二','高三']
const tasks = ref([])

const contentParagraphs = computed(() => {
  return (form.value.content_text || '').split('\n').filter(s => s.trim())
})

const studentSuggestions = ref([])
const studentNames = ref([])
let studentNamesLoaded = false
async function loadStudentNames() {
  if (studentNamesLoaded) return
  try {
    const res = await api.get('/essays/student-names', { params: { limit: 0 }, __toastError: false })
    studentNames.value = res.data.names || []
    studentNamesLoaded = true
  } catch {}
}
function onNameChange(val) {
  form.value.student_name = val
  onStudentInput()
}
function onStudentInput() {
  const kw = form.value.student_name.trim()
  if (!kw) { studentSuggestions.value = []; return }
  if (!studentNamesLoaded) loadStudentNames()
  studentSuggestions.value = studentNames.value
    .filter(n => n && n !== form.value.student_name && n.includes(kw))
    .slice(0, 8)
}
watch(studentNames, () => onStudentInput())
function onStudentBlur() {
  setTimeout(() => { studentSuggestions.value = [] }, 150)
}
function pickStudent(name) {
  form.value.student_name = name
  studentSuggestions.value = []
}

const sortedTasks = computed(() => {
  return [...tasks.value].sort((a, b) => {
    // 迁移任务排到末尾
    const aMig = (a.course_name || '').includes('迁移')
    const bMig = (b.course_name || '').includes('迁移')
    if (aMig !== bMig) return aMig ? 1 : -1
    const aActive = taskIsActive(a)
    const bActive = taskIsActive(b)
    if (aActive !== bActive) return aActive ? -1 : 1
    return 0
  })
})

const onlineTasks = computed(() => sortedTasks.value.filter(t => t.teaching_mode === '线上'))
const offlineTasks = computed(() => sortedTasks.value.filter(t => t.teaching_mode !== '线上'))

const taskSearch = ref('')
const showActiveOnly = ref(false)
const filteredOnlineTasks = computed(() => {
  const kw = taskSearch.value.trim().toLowerCase()
  let list = onlineTasks.value
  if (showActiveOnly.value && !kw) list = list.filter(taskIsActive)
  if (!kw) return list
  return list.filter(t => (t.name || '').toLowerCase().includes(kw) || (t.essay_topic || '').toLowerCase().includes(kw) || (t.grade || '').includes(kw))
})
const filteredOfflineTasks = computed(() => {
  const kw = taskSearch.value.trim().toLowerCase()
  let list = offlineTasks.value
  if (showActiveOnly.value && !kw) list = list.filter(taskIsActive)
  if (!kw) return list
  return list.filter(t => (t.name || '').toLowerCase().includes(kw) || (t.essay_topic || '').toLowerCase().includes(kw) || (t.grade || '').includes(kw))
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

function taskIsActive(t) {
  const now = new Date()
  return t.is_active
    && (!t.deadline || new Date(t.deadline) >= now)
    && (!t.start_time || new Date(t.start_time) <= now)
}

const form = ref({
  grade: '', essay_number: '', essay_title: '',
  student_name: '', is_supplement: false, teaching_mode: '线上', collector_note: '', content_text: '',
})

watch(contentParagraphs, (paras) => {
  const first = (paras[0] || '').trim()
  if (first && !form.value.essay_title) {
    form.value.essay_title = first
  }
})

watch([taskSearch, showActiveOnly], () => {
  pageOnline.value = 1
  pageOffline.value = 1
})

onMounted(async () => {
  if (isGuest.value) {
    router.replace('/dashboard')
    showToast('游客无上传权限')
    return
  }
  try {
    const res = await api.get('/essays/tasks')
    tasks.value = res.data
    const taskIdFromQuery = Number(route.query.task_id)
    if (taskIdFromQuery) {
      const target = tasks.value.find(t => t.id === taskIdFromQuery)
      if (target) {
        selectTask(target)
      }
    }
  } catch {}
  if (isAdmin.value) {
    try {
      const res = await api.get('/essays/collectors')
      collectorList.value = res.data || []
    } catch {}
  }
  try {
    const res = await api.get('/essays/recent-titles', { params: { limit: 5 } })
    recentTitles.value = res.data || []
  } catch {}
  loadStudentNames()
})

function selectGrade(g) {
  form.value.grade = g
  selectedGrade.value = g
  showGradePicker.value = false
}

function selectCollector(c) {
  if (c) {
    selectedCollector.value = c.id
    selectedCollectorName.value = c.nickname || c.username
  } else {
    selectedCollector.value = null
    selectedCollectorName.value = ''
  }
  showCollectorPicker.value = false
}

async function beforeRead(file) {
  const list = Array.isArray(file) ? file : [file]
  const accepted = []
  for (const f of list) {
    if (isImageFile(f) && f.size > IMAGE_UPLOAD_MAX_BYTES) {
      showToast(`${f.name} 超过 8MB，请压缩后重试`)
      continue
    }
    accepted.push(f)
  }
  if (accepted.length === 0) return false
  const compressed = await Promise.all(accepted.map(f => compressImageFile(f)))
  return Array.isArray(file) ? compressed : compressed[0]
}

const ACCEPT_EXTS = ['.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.webp']

function buildPreviewImages() {
  previewImages.value = fileList.value
    .filter(item => item.file?.type?.startsWith('image/'))
    .map(item => item.objectUrl || URL.createObjectURL(item.file))
}

function afterRead() {
  // 兜底：确保每个图片项都有 objectUrl，供缩略图显示
  for (const item of fileList.value) {
    if (item.file && isImageFile(item.file) && !item.objectUrl && !item.content) {
      item.objectUrl = URL.createObjectURL(item.file)
    }
  }
  buildPreviewImages()
}

async function onUploadDrop(e) {
  const files = Array.from(e.dataTransfer?.files || [])
  if (!files.length) return
  let added = 0
  let rejected = 0
  let docRejected = 0
  for (const file of files) {
    if (fileList.value.length >= 10) break
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (ext === '.doc') { docRejected++; continue }
    if (!ACCEPT_EXTS.includes(ext)) continue
    if (isImageFile(file) && file.size > IMAGE_UPLOAD_MAX_BYTES) {
      rejected++
      continue
    }
    const out = await compressImageFile(file)
    const item = { file: out, status: 'done', message: '' }
    if (isImageFile(out)) {
      item.objectUrl = URL.createObjectURL(out)
    }
    fileList.value.push(item)
    added++
  }
  if (docRejected) {
    showToast(`${docRejected} 个 .doc 旧版文件不支持，请另存为 .docx 后再传`)
    return
  }
  if (rejected) {
    showToast(`${rejected} 张图片超过 8MB，未添加`)
  }
  if (added) {
    buildPreviewImages()
  } else {
    showToast('没有可添加的文件（支持 docx/txt/图片）')
  }
}

function onPreviewClick(item, detail) {
  if (!item?.file?.type?.startsWith('image/')) return
  buildPreviewImages()
  const imageItems = fileList.value.filter(x => x.file?.type?.startsWith('image/'))
  const idx = imageItems.findIndex(x => x === item || (x.file && item?.file && x.file === item.file))
  previewIndex.value = idx >= 0 ? idx : 0
  showPreview.value = true
}

function selectTask(tpl) {
  if (tpl) {
    form.value.grade = tpl.grade
    selectedGrade.value = tpl.grade
    form.value.essay_number = tpl.essay_number ? String(tpl.essay_number) : ''
    if (tpl.teaching_mode) {
      form.value.teaching_mode = tpl.teaching_mode
    }
    // 已过截止时间的任务自动勾选补交
    if (tpl.deadline && new Date(tpl.deadline) < new Date()) {
      form.value.is_supplement = true
    } else {
      form.value.is_supplement = false
    }
    selectedTaskName.value = tpl.name
    selectedTaskTopic.value = tpl.essay_topic || ''
    selectedTaskCourse.value = tpl.course_name || ''
    selectedTaskId.value = tpl.id
    selectedCourseId.value = tpl.course_id || null
    showToast(`已选择：${tpl.name}`)
  } else {
    selectedTaskName.value = ''
    selectedTaskTopic.value = ''
    selectedTaskCourse.value = ''
    selectedTaskId.value = null
    selectedCourseId.value = null
    showToast('已取消任务选择')
  }
  showTaskPicker.value = false
}

async function onSubmit() {
  if (!form.value.student_name) { showToast('请填写学生姓名'); return }
  if (!form.value.essay_title || !form.value.essay_title.trim()) { showToast('请填写作文标题'); return }
  if (!selectedTaskId.value) {
    const ok = await showConfirmDialog({
      title: '提示',
      message: '您当前没有选择收集任务，是否有新的作文需要收集，如有请及时联系管理员进行编辑收集任务，若无请忽略',
      confirmButtonText: '继续上传',
      cancelButtonText: '取消',
    }).then(() => true).catch(() => false)
    if (!ok) return
  }
  loading.value = true
  uploadProgress.value = 0
  showProgress.value = true
  try {
    const fd = new FormData()
    if (selectedTaskId.value) {
      fd.append('task_id', String(selectedTaskId.value))
    }
    if (selectedCourseId.value) {
      fd.append('course_id', String(selectedCourseId.value))
    }
    if (selectedCollector.value) {
      fd.append('collected_by', String(selectedCollector.value))
    }
    fd.append('grade', form.value.grade || '')
    const essayNumber = parseInt(form.value.essay_number)
    fd.append('essay_number', isNaN(essayNumber) || essayNumber <= 0 ? '0' : String(essayNumber))
    fd.append('essay_title', form.value.essay_title)
    fd.append('student_name', form.value.student_name)
    fd.append('is_supplement', form.value.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', form.value.teaching_mode)
    fd.append('collector_note', form.value.collector_note || '')
    let uploadContent = form.value.content_text
    if (uploadContent && uploadContent.trim()) {
      const ensured = ensureContentHeader(uploadContent, form.value.essay_title, form.value.student_name)
      if (ensured.changed.length) {
        uploadContent = ensured.text
      }
    }
    fd.append('content_text', uploadContent)
    if (fileList.value.length > 0) {
      fileList.value.forEach(item => fd.append('files', item.file))
    }
    const res = await api.post('/essays/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
      onUploadProgress: (e) => {
        if (e.total) uploadProgress.value = Math.min(99, Math.round(e.loaded / e.total * 100))
      },
    })
    uploadProgress.value = 100
    const keep = keepTask.value
    const keepFields = {
      grade: form.value.grade,
      essay_number: form.value.essay_number,
      teaching_mode: form.value.teaching_mode,
      is_supplement: form.value.is_supplement,
    }
    uploadSuccessDialog.value = {
      show: true,
      id: res.data?.id || null,
      body: `学生：${form.value.student_name}\n年级：${form.value.grade || '暂不选择'}\n第${isNaN(essayNumber) || essayNumber <= 0 ? '无' : essayNumber}次\n提交方式：${form.value.teaching_mode}`,
    }
    if (res.data?.id) {
      sessionUploaded.value.push({ id: res.data.id, name: form.value.student_name, title: form.value.essay_title })
    }
    const gradeBackup = form.value.grade
    form.value = {
      grade: keep ? keepFields.grade : '',
      essay_number: keep ? keepFields.essay_number : '',
      essay_title: '',
      student_name: '',
      is_supplement: keep ? keepFields.is_supplement : false,
      teaching_mode: keepFields.teaching_mode,
      collector_note: '',
      content_text: '',
    }
    fileList.value = []
    previewImages.value = []
    if (keep) {
      selectedGrade.value = gradeBackup
    } else {
      selectedGrade.value = ''
      selectedTaskName.value = ''
      selectedTaskTopic.value = ''
      selectedTaskCourse.value = ''
      selectedTaskId.value = null
      selectedCourseId.value = null
    }
  } catch (err) {
    showProgress.value = false
    const detail = err.response?.data?.detail
    const status = err.response?.status
    let msg = '上传失败'
    if (detail) msg = detail
    else if (status) msg = `服务器错误 (${status})`
    else if (err.message) msg = err.message

    // 409 冲突：保留表单数据，引导用户操作
    if (status === 409) {
      showDialog({
        title: '⚠️ 作文已存在',
        message: msg,
        confirmButtonText: '知道了',
        cancelButtonText: '去列表查看',
        showCancelButton: true,
        className: 'upload-msg-dialog',
      }).then((action) => {
        if (action === 'cancel') {
          window.location.hash = '#/essay/list'
        }
      })
      return
    }

    showDialog({
      title: '❌ 上传失败',
      message: msg,
      confirmButtonText: '重试',
      cancelButtonText: '知道了',
      showCancelButton: true,
      className: 'upload-msg-dialog',
    }).then((action) => {
      if (action === 'confirm') onSubmit()
    })
  }
  finally { loading.value = false }
}

function continueUpload() {
  uploadSuccessDialog.value.show = false
  showProgress.value = false
}

function goUploadList() {
  uploadSuccessDialog.value.show = false
  showProgress.value = false
  router.push('/essay/list')
}

function viewUploaded() {
  if (!uploadSuccessDialog.value.id) return
  uploadSuccessDialog.value.show = false
  showProgress.value = false
  router.push(`/review/detail/${uploadSuccessDialog.value.id}`)
}

function openUploaded(s) {
  if (!s.id) return
  uploadSuccessDialog.value.show = false
  showProgress.value = false
  router.push(`/review/detail/${s.id}`)
}
</script>

<style scoped>
.page { padding: 16px; }
.picker-list { max-height: 70vh; overflow-y: auto; }
@media (max-width: 767px) { .page { padding: 0; } }

.tips-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0 16px 12px;
  padding: 10px 14px;
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #ad6800;
}
.tips-icon {
  flex-shrink: 0;
  font-size: 15px;
}

.field-tips {
  padding: 4px 16px 10px;
  font-size: 12px;
  color: #1677ff;
  background: #e6f4ff;
}

/* 任务选择面板：避免双重滚动容器导致无法回拉 */
:deep(.task-picker-sheet) {
  max-height: 88vh;
  display: flex;
  flex-direction: column;
}
:deep(.task-picker-sheet .van-action-sheet__header) {
  flex-shrink: 0;
}
:deep(.task-picker-sheet .van-action-sheet__content) {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}
:deep(.task-picker-sheet .picker-list) {
  max-height: none;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.upload-preview {
  margin: 8px 16px 16px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.drop-zone {
  width: 100%;
  padding: 10px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  transition: all 0.15s;
}
.drop-zone:hover, .drop-zone:active { border-color: #1677ff; background: #f0f7ff; }
.upload-preview-title {
  padding: 8px 12px;
  font-size: 12px;
  color: #999;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
  border-radius: 8px 8px 0 0;
}
.content-text { padding: 12px 16px; }
.content-text p { font-size: 14px; line-height: 1.8; margin: 0 0 8px 0; text-indent: 2em; }
.content-text .para-center-bold { text-indent: 0; text-align: center; font-weight: bold; }

.student-suggest {
  margin: 0 12px 8px;
  border: 1px solid #e8f0ff;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  max-height: 200px;
  overflow-y: auto;
  z-index: 5;
}
.student-suggest-item {
  padding: 10px 16px;
  font-size: 14px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
}
.student-suggest-item:last-child { border-bottom: none; }
.student-suggest-item:hover { background: #f5f8ff; color: #1677ff; }

:deep(.upload-msg-dialog) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

.task-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-top: 1px solid #f0f0f0;
}

.task-col {
  max-height: 65vh;
  overflow-y: auto;
  padding: 8px 0;
}

.task-col + .task-col {
  border-left: 1px solid #f0f0f0;
}

.task-col-title {
  padding: 8px 16px 4px;
  font-size: 13px;
  font-weight: 600;
  color: #666;
}

:deep(.upload-msg-dialog .van-dialog__message) {
  font-size: 16px;
  font-weight: 500;
  color: #e53935;
  line-height: 1.6;
  padding: 16px 20px;
}

:deep(.upload-success-dialog) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

.upload-success-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}
.upload-success-actions .btn {
  flex: 1;
  min-width: 96px;
  justify-content: center;
}
@media (max-width: 480px) {
  .upload-success-actions .btn {
    min-width: 100%;
  }
}

:deep(.upload-success-dialog .van-dialog__message) {
  white-space: pre-line;
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}
.pagination-row { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 8px 0; }
.page-info { font-size: 12px; color: #666; }
</style>
