<template>
  <div class="page">
    <div v-if="isDesktop" class="page-title">批量上传</div>

    <!-- 模板选择区域 -->
    <van-cell-group inset style="margin-bottom:12px">
      <van-field :model-value="selectedTaskName" is-link readonly label="选择收集任务"
        placeholder="选择收集任务（自动填充年级等信息）" @click="showTaskPicker = true" />
      <van-cell v-if="selectedTaskTopic" title="文章主题" :label="selectedTaskTopic" />
    </van-cell-group>

    <!-- 模式选择（含各自上传说明） -->
    <div class="mode-boxes">
      <div class="mode-box" :class="{ active: mode === 'essay' }" @click="switchMode('essay')">
        <div class="mode-icon">📁</div>
        <div class="mode-title">批量上传文件夹作文</div>
        <div class="mode-desc">按学生文件夹结构上传原文</div>
        <div class="mode-tip">
          <div class="tip-label">文件夹结构：</div>
          <div class="tip-content">
            根文件/<br>
            &nbsp;&nbsp;├── 学生1/<br>
            &nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── 1.jpg<br>
            &nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── 2.jpg<br>
            &nbsp;&nbsp;├── 学生2/<br>
            &nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── 1.png<br>
            &nbsp;&nbsp;└── 学生3/<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── 作文.docx
          </div>
          <div class="tip-note">* 二级目录名称作为学生姓名</div>
          <div class="tip-note">* 支持格式：jpg/jpeg/png/gif/webp/docx/txt（不支持 .doc 旧版格式）</div>
          <div class="tip-note">* docx/txt 自动读取内容；含「修改前/修改后」则拆分，否则全部作修改前</div>
          <div class="tip-note">* 文件夹名可含「{年级}第{次数}次」自动填充（如：高二第三次作文）</div>
        </div>
      </div>
      <div class="mode-box" :class="{ active: mode === 'correction' }" @click="switchMode('correction')">
        <div class="mode-icon">📄</div>
        <div class="mode-title">批量上传修改后docx</div>
        <div class="mode-desc">上传批改后的 docx 文件</div>
        <div class="mode-tip">
          <div class="tip-label">文件名格式：</div>
          <div class="tip-content">
            改_原文件名——学生姓名.docx<br>
            改_作文——张三.docx<br>
            改_作文——李四.docx
          </div>
          <div class="tip-note">* 破折号「——」后的名字为学生姓名</div>
          <div class="tip-note">* 支持格式：docx（不支持 .doc 旧版格式）</div>
          <div class="tip-note">* 将自动识别学生姓名、标题和作文内容</div>
          <div class="tip-note">* 内容格式：第一行「修改前：」、第二行标题、第三行——（学生姓名），之后再「修改后：」</div>
        </div>
      </div>
    </div>

    <!-- 共用表单 -->
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field :model-value="selectedGrade" is-link readonly label="年级" placeholder="请选择（可不选）"
          @click="showGradePicker = true" />
        <van-field v-model="activeForm.essay_number" label="第几次" placeholder="数字（可不填）" type="digit" />
        <van-field name="teaching_mode" label="提交方式">
          <template #input>
            <van-radio-group v-model="activeForm.teaching_mode" direction="horizontal">
              <van-radio name="线下" style="margin-right:16px">线下</van-radio>
              <van-radio name="线上">线上</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field name="is_supplement" label="是否补交">
          <template #input><van-switch v-model="activeForm.is_supplement" size="24" /></template>
        </van-field>
        <van-field v-model="activeForm.collector_note" label="统一收集者备注" placeholder="应用到本批所有作文（可选）" />
        <van-field v-if="isAdmin" :model-value="selectedCollectorName" is-link readonly label="收集者" placeholder="默认当前用户"
          @click="showCollectorPicker = true" />
        <van-field name="pre_check_existing" label="跳过已存在的学生">
          <template #input><van-switch v-model="preCheckExisting" size="24" @change="onPreCheckChange" /></template>
        </van-field>
        <van-cell title="选择文件夹" :label="folderLabel" is-link @click="openFolderPicker" />
      </van-cell-group>
      <input ref="folderInput" type="file" webkitdirectory style="display:none" @change="onFolderChange" />
      <input ref="corFolderInput" type="file" webkitdirectory style="display:none" @change="onCorFolderChange" />

      <!-- 预检工具栏 -->
      <div v-if="(mode === 'essay' && folderSelected) || (mode === 'correction' && corFolderSelected && !corParsing)" class="preview-toolbar">
        <button class="btn" style="font-size:12px;padding:4px 10px" @click="checkExisting" :disabled="checkingExisting">
          {{ checkingExisting ? '检查中...' : '🔍 检查已存在' }}
        </button>
        <span v-if="!selectedTaskId" style="font-size:12px;color:#999">未选择任务，无法预检（仍会按 409 兜底跳过）</span>
        <span v-else-if="existingNames.length" style="font-size:12px;color:#d46b08">已有 {{ existingNames.length }} 位学生，将自动跳过</span>
        <span v-else-if="checkedExisting" style="font-size:12px;color:#52c41a">无已存在学生</span>
      </div>

      <!-- 预览：作文模式 -->
      <div v-if="mode === 'essay' && folderSelected" class="preview-list">
        <div v-for="(files, name) in studentMap" :key="name" class="preview-item" :class="{ 'preview-existing': existingNames.includes(name) }">
          <span class="preview-name">{{ name }}</span>
          <span v-if="existingNames.includes(name)" class="tag tag-pending">已存在</span>
          <span class="preview-files">{{ files.length }} 个文件</span>
          <button class="preview-remove" title="移除该学生" @click="removeStudent(name)">✕</button>
        </div>
        <div v-if="skipStats.total > 0" class="skip-note">
          已跳过 {{ skipStats.total }} 个文件（修改后目录 {{ skipStats.modifiedFolder }} / 不支持格式 {{ skipStats.unsupported }} / 非学生目录 {{ skipStats.noStudent }} / 图片超8MB {{ skipStats.oversize }}）
        </div>
      </div>

      <!-- 预览：修改后模式 -->
      <div v-if="mode === 'correction' && corFolderSelected" class="preview-list">
        <div v-if="corParsing" class="progress-box">
          <van-progress :percentage="corParsePercent" stroke-width="8" />
          <div class="progress-text">正在解析文件 {{ corParsedCount }}/{{ corFileTotal }}</div>
        </div>
        <template v-else>
          <div v-for="(item, idx) in corFiles" :key="idx" class="preview-item" :class="{ 'preview-existing': existingNames.includes(item.studentName) }">
            <div class="preview-main">
              <div class="preview-name">
                {{ item.studentName || '未识别' }}
                <span v-if="existingNames.includes(item.studentName)" class="tag tag-pending">已存在</span>
                <span v-if="!item.ok" class="tag tag-pending" style="margin-left:6px">解析失败</span>
              </div>
              <div v-if="item.ok" class="preview-files">
                {{ item.title || '无标题' }} · 修改前{{ item.before.length || 0 }}字 / 修改后{{ item.after.length || 0 }}字
              </div>
              <div v-else class="preview-files" style="color:#ff4d4f">{{ item.error || '解析失败，不会上传' }}</div>
            </div>
            <button class="preview-remove" title="移除该文件" @click="removeCorFile(idx)">✕</button>
          </div>
          <div v-if="corParseFailCount" class="skip-note">{{ corParseFailCount }} 个文件解析失败，将不会上传，请检查格式或移除</div>
        </template>
      </div>

      <!-- 提交 -->
      <div style="margin:16px">
        <van-button round block type="primary" native-type="submit" :loading="loading || corLoading" :disabled="submitDisabled">
          {{ submitLabel }}
        </van-button>
      </div>

      <!-- 进度：作文模式 -->
      <div v-if="loading" class="progress-box">
        <van-progress :percentage="essaysPercent" stroke-width="8" />
        <div class="progress-text">正在上传：{{ currentStudent }}</div>
        <div class="progress-stats">
          <span class="stat-success">成功 {{ essaysSuccess }}</span>
          <span class="stat-skip" v-if="essaysSkip">跳过 {{ essaysSkip }}</span>
          <span class="stat-fail">失败 {{ essaysFail }}</span>
        </div>
      </div>

      <!-- 进度：修改后模式 -->
      <div v-if="corLoading" class="progress-box">
        <van-progress :percentage="corPercent" stroke-width="8" />
        <div class="progress-text">正在上传：{{ corCurrentStudent }}</div>
        <div class="progress-stats">
          <span class="stat-success">成功 {{ corSuccess }}</span>
          <span class="stat-skip" v-if="corSkipExisting">跳过 {{ corSkipExisting }}</span>
          <span class="stat-fail">失败 {{ corFail }}</span>
        </div>
      </div>
    </van-form>

    <!-- 结果弹窗 -->
    <van-dialog v-model:show="resultDialog.show" :title="resultDialog.title" :show-cancel-button="false" :show-confirm-button="false" :close-on-click-overlay="true">
      <div style="padding:16px">
        <div class="result-body">{{ resultDialog.body }}</div>
        <div style="display:flex;gap:8px;margin-top:12px;justify-content:flex-end;flex-wrap:wrap">
          <button class="btn" @click="copyResult">📋 复制明细</button>
          <button class="btn" @click="resultDialog.show = false">关闭</button>
          <button v-if="resultDialog.canRetry" class="btn btn-primary" @click="retryFailed">仅重试失败 {{ resultDialog.retryCount }}</button>
        </div>
      </div>
    </van-dialog>

    <van-action-sheet v-model:show="showGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectGrade(g)" />
      </div>
    </van-action-sheet>

    <!-- 模板选择器 -->
    <van-action-sheet v-model:show="showTaskPicker" title="选择收集任务">
      <div class="picker-list">
        <div style="padding:8px 16px">
          <input v-model="taskSearch" placeholder="搜索任务名称/主题/年级..." style="width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;outline:none" />
        </div>
        <van-cell title="不使用模板" @click="selectTask(null)" style="color:#999" />
        <div class="task-split">
          <div class="task-col">
            <div class="task-col-title">线上</div>
            <van-cell v-for="t in filteredOnlineTasks" :key="t.id" @click="selectTask(t)">
              <template #title>
                <span style="font-weight:500">{{ t.name }}</span>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
              </template>
              <template #label>
                <span class="badge-mini tag-grade">{{ t.grade }}</span>
                <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                <span v-if="t.essay_topic" style="color:#999">{{ t.essay_topic }}</span>
              </template>
            </van-cell>
            <div v-if="!filteredOnlineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线上任务</div>
          </div>
          <div class="task-col">
            <div class="task-col-title">线下</div>
            <van-cell v-for="t in filteredOfflineTasks" :key="t.id" @click="selectTask(t)">
              <template #title>
                <span style="font-weight:500">{{ t.name }}</span>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
              </template>
              <template #label>
                <span class="badge-mini tag-grade">{{ t.grade }}</span>
                <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                <span v-if="t.essay_topic" style="color:#999">{{ t.essay_topic }}</span>
              </template>
            </van-cell>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import JSZip from 'jszip'
import { compressImageFile, isImageFile, IMAGE_UPLOAD_MAX_BYTES } from '../utils/imageCompress'

const route = useRoute()
const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isAdmin = computed(() => (currentUser.value.role || '').includes('admin'))
const isGuest = computed(() => (currentUser.value.role || '').includes('guest'))

const CONCURRENCY = 3
const mode = ref('essay')

// 共用表单
const form = ref({ grade: '', essay_number: '', teaching_mode: '线上', is_supplement: false, collector_note: '' })
const corForm = ref({ grade: '', essay_number: '', teaching_mode: '线上', is_supplement: false, collector_note: '' })
const activeForm = computed(() => mode.value === 'essay' ? form.value : corForm.value)
const selectedGrade = ref('')
const selectedTaskName = ref('')
const selectedTaskTopic = ref('')
const selectedTaskId = ref(null)
const selectedCourseId = ref(null)
const selectedCollector = ref(null)
const selectedCollectorName = ref('')
const collectorList = ref([])
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']
const folderInput = ref(null)
const corFolderInput = ref(null)
const tasks = ref([])
const showGradePicker = ref(false)
const showTaskPicker = ref(false)
const showCollectorPicker = ref(false)

// 预检
const preCheckExisting = ref(false)
const existingNames = ref([])
const checkingExisting = ref(false)
const checkedExisting = ref(false)

// 作文模式状态
const studentMap = ref({})
const folderSelected = ref(false)
const skipStats = ref({ total: 0, modifiedFolder: 0, unsupported: 0, noStudent: 0, oversize: 0 })
const loading = ref(false)
const uploadedCount = ref(0)
const currentStudent = ref('')
const essaysSuccess = ref(0)
const essaysFail = ref(0)
const essaysSkip = ref(0)
const failedStudents = ref([])
const essaysPercent = computed(() => studentCount.value ? Math.round(uploadedCount.value / studentCount.value * 100) : 0)
const studentCount = computed(() => Object.keys(studentMap.value).length)
const totalFiles = computed(() => Object.values(studentMap.value).reduce((sum, files) => sum + files.length, 0))

// 修改后模式状态
const corFiles = ref([])
const corFolderSelected = ref(false)
const corParsing = ref(false)
const corParsedCount = ref(0)
const corFileTotal = ref(0)
const corParsePercent = computed(() => corFileTotal.value ? Math.round(corParsedCount.value / corFileTotal.value * 100) : 0)
const corValidCount = computed(() => corFiles.value.filter(i => i.ok).length)
const corParseFailCount = computed(() => corFiles.value.filter(i => !i.ok).length)
const corLoading = ref(false)
const corUploadedCount = ref(0)
const corCurrentStudent = ref('')
const corSuccess = ref(0)
const corFail = ref(0)
const corFailed = ref([])
const corSkipExisting = ref(0)
const corPercent = computed(() => corValidCount.value ? Math.round(corUploadedCount.value / corValidCount.value * 100) : 0)

// 结果弹窗
const resultDialog = ref({ show: false, title: '', body: '', canRetry: false, retryCount: 0, retryMode: '', retryNames: [] })

const folderLabel = computed(() => {
  if (mode.value === 'essay') {
    return folderSelected.value ? `${studentCount.value} 位学生，${totalFiles.value} 个文件` : '点击选择（学生文件夹）'
  }
  return corFolderSelected.value ? `${corValidCount.value} 个可上传文件` : '点击选择（docx 文件夹）'
})

const submitDisabled = computed(() => {
  if (mode.value === 'essay') return !folderSelected.value
  return !corFolderSelected.value || corParsing.value || corValidCount.value === 0
})

const submitLabel = computed(() => {
  if (loading.value) return `上传中 ${uploadedCount.value}/${studentCount.value}`
  if (corLoading.value) return `上传中 ${corUploadedCount.value}/${corValidCount.value}`
  return mode.value === 'essay' ? '开始上传文件夹作文' : '开始上传修改后docx'
})

const sortedTasks = computed(() => {
  return [...tasks.value].sort((a, b) => {
    const aActive = taskIsActive(a)
    const bActive = taskIsActive(b)
    if (aActive !== bActive) return aActive ? -1 : 1
    return 0
  })
})

const onlineTasks = computed(() => sortedTasks.value.filter(t => t.teaching_mode === '线上'))
const offlineTasks = computed(() => sortedTasks.value.filter(t => t.teaching_mode !== '线上'))

const taskSearch = ref('')
const filteredOnlineTasks = computed(() => {
  const kw = taskSearch.value.trim().toLowerCase()
  if (!kw) return onlineTasks.value
  return onlineTasks.value.filter(t => (t.name || '').toLowerCase().includes(kw) || (t.essay_topic || '').toLowerCase().includes(kw) || (t.grade || '').includes(kw))
})
const filteredOfflineTasks = computed(() => {
  const kw = taskSearch.value.trim().toLowerCase()
  if (!kw) return offlineTasks.value
  return offlineTasks.value.filter(t => (t.name || '').toLowerCase().includes(kw) || (t.essay_topic || '').toLowerCase().includes(kw) || (t.grade || '').includes(kw))
})

function taskIsActive(t) {
  const now = new Date()
  return t.is_active
    && (!t.deadline || new Date(t.deadline) >= now)
    && (!t.start_time || new Date(t.start_time) <= now)
}

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
      if (target) selectTask(target)
    }
  } catch {}
  if (isAdmin.value) {
    try {
      const res = await api.get('/essays/collectors')
      collectorList.value = res.data || []
    } catch {}
  }
})

function switchMode(m) {
  if (m === mode.value) return
  mode.value = m
  studentMap.value = {}
  folderSelected.value = false
  corFiles.value = []
  corFolderSelected.value = false
  corParsing.value = false
  existingNames.value = []
  checkedExisting.value = false
}

function openFolderPicker() {
  if (mode.value === 'essay') folderInput.value?.click()
  else corFolderInput.value?.click()
}

function selectGrade(g) {
  form.value.grade = g
  corForm.value.grade = g
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

function selectTask(tpl) {
  if (tpl) {
    form.value.grade = tpl.grade
    corForm.value.grade = tpl.grade
    selectedGrade.value = tpl.grade
    form.value.essay_number = tpl.essay_number ? String(tpl.essay_number) : ''
    corForm.value.essay_number = tpl.essay_number ? String(tpl.essay_number) : ''
    if (tpl.teaching_mode) {
      form.value.teaching_mode = tpl.teaching_mode
      corForm.value.teaching_mode = tpl.teaching_mode
    }
    selectedTaskName.value = tpl.name
    selectedTaskTopic.value = tpl.essay_topic || ''
    selectedTaskId.value = tpl.id
    selectedCourseId.value = tpl.course_id || null
    if (preCheckExisting.value && (folderSelected.value || corFolderSelected.value)) checkExisting()
    showToast(`已选择：${tpl.name}`)
  } else {
    selectedTaskName.value = ''
    selectedTaskTopic.value = ''
    selectedTaskId.value = null
    selectedCourseId.value = null
    existingNames.value = []
    checkedExisting.value = false
    showToast('已取消模板选择')
  }
  showTaskPicker.value = false
}

function chineseToNumber(str) {
  const map = { '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10 }

  if (map[str] !== undefined) return map[str]

  if (str.startsWith('十')) {
    const rest = str.substring(1)
    return 10 + (map[rest] || 0)
  }

  if (str.endsWith('十')) {
    const first = str.charAt(0)
    return (map[first] || 0) * 10
  }

  if (str.includes('十')) {
    const parts = str.split('十')
    return (map[parts[0]] || 0) * 10 + (map[parts[1]] || 0)
  }

  return 0
}

function parseFolderName(folderName) {
  const result = { grade: '', essay_number: '' }

  const gradeMatch = folderName.match(/(初一|初二|初三|高一|高二|高三)/)
  if (gradeMatch) {
    result.grade = gradeMatch[1]
  }

  const numberMatch = folderName.match(/第([一二三四五六七八九十百零\d]+)次/)
  if (numberMatch) {
    const numStr = numberMatch[1]
    if (/^\d+$/.test(numStr)) {
      result.essay_number = numStr
    } else {
      const num = chineseToNumber(numStr)
      if (num > 0) result.essay_number = String(num)
    }
  }

  return result
}

function getFolderPath(files) {
  for (const file of files) {
    const relativePath = file.webkitRelativePath
    if (relativePath) {
      return relativePath.split('/')[0]
    }
  }
  return ''
}

// ===== 作文模式 =====
async function onFolderChange(e) {
  const files = Array.from(e.target.files)
  if (files.length === 0) return

  const map = {}
  const supportedExts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.docx', '.doc', '.txt']
  const skipFolders = ['修改后']
  skipStats.value = { total: 0, modifiedFolder: 0, unsupported: 0, noStudent: 0, oversize: 0 }

  const folderName = getFolderPath(files)

  for (const file of files) {
    const relativePath = file.webkitRelativePath
    if (!relativePath) { skipStats.value.noStudent++; continue }

    const parts = relativePath.split('/')
    if (parts.length < 2) { skipStats.value.noStudent++; continue }

    const studentName = parts[1]
    if (skipFolders.includes(studentName)) { skipStats.value.modifiedFolder++; continue }

    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!supportedExts.includes(ext)) { skipStats.value.unsupported++; continue }

    if (isImageFile(file) && file.size > IMAGE_UPLOAD_MAX_BYTES) { skipStats.value.oversize++; continue }

    const out = await compressImageFile(file)
    if (!map[studentName]) map[studentName] = []
    map[studentName].push(out)
  }
  skipStats.value.total = skipStats.value.modifiedFolder + skipStats.value.unsupported + skipStats.value.noStudent + skipStats.value.oversize

  if (Object.keys(map).length === 0) {
    showToast('未找到有效的学生文件')
    return
  }

  studentMap.value = map
  folderSelected.value = true

  if (folderName) {
    const parsed = parseFolderName(folderName)
    if (parsed.grade && !form.value.grade) {
      form.value.grade = parsed.grade
      selectedGrade.value = parsed.grade
    }
    if (parsed.essay_number && !form.value.essay_number) {
      form.value.essay_number = parsed.essay_number
    }
  }

  if (preCheckExisting.value && selectedTaskId.value) {
    checkExisting()
  } else {
    existingNames.value = []
    checkedExisting.value = false
  }
}

function removeStudent(name) {
  const map = { ...studentMap.value }
  delete map[name]
  studentMap.value = map
  if (!Object.keys(map).length) folderSelected.value = false
}

// ===== 修改后模式 =====
async function parseDocxContent(file) {
  const zip = await JSZip.loadAsync(file)
  const docXml = await zip.file('word/document.xml').async('string')

  const parser = new DOMParser()
  const xmlDoc = parser.parseFromString(docXml, 'text/xml')
  const paragraphs = xmlDoc.getElementsByTagName('w:p')

  let fullText = ''
  for (const p of paragraphs) {
    const texts = p.getElementsByTagName('w:t')
    let line = ''
    for (const t of texts) {
      line += t.textContent
    }
    fullText += line + '\n'
  }

  const beforeMatch = fullText.match(/修改前[：:]\s*([\s\S]*?)(?=修改后[：:]|$)/)
  const afterMatch = fullText.match(/修改后[：:]\s*([\s\S]*?)$/)

  let title = ''
  let studentNameFromDoc = ''

  if (beforeMatch) {
    const lines = beforeMatch[1].split('\n').map(l => l.trim()).filter(l => l)
    if (lines.length > 0) {
      title = lines[0]
    }
    if (lines.length > 1) {
      const thirdLine = lines[1]
      const dashIdx = thirdLine.indexOf('——')
      if (dashIdx !== -1) {
        studentNameFromDoc = thirdLine.substring(dashIdx + 2).trim()
      }
    }
  }

  return {
    title: title,
    studentName: studentNameFromDoc,
    before: beforeMatch ? beforeMatch[1].trim() : '',
    after: afterMatch ? afterMatch[1].trim() : ''
  }
}

async function onCorFolderChange(e) {
  const files = Array.from(e.target.files)
  if (files.length === 0) return

  const parsed = []
  const docxFiles = files.filter(f => {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    return ext === '.docx' || ext === '.doc'
  })
  if (docxFiles.length === 0) {
    showToast('未找到 docx/doc 文件')
    return
  }

  corParsing.value = true
  corParsedCount.value = 0
  corFileTotal.value = docxFiles.length

  for (const file of docxFiles) {
    const nameWithoutExt = file.name.replace(/\.(docx|doc)$/i, '')
    let dashIndex = nameWithoutExt.indexOf('——')
    if (dashIndex === -1) dashIndex = nameWithoutExt.indexOf('-')
    const studentName = dashIndex === -1 ? '' : nameWithoutExt.substring(dashIndex + (nameWithoutExt.charAt(dashIndex) === '—' ? 2 : 1)).trim()

    if (!studentName) {
      parsed.push({ file, studentName: '', ok: false, error: '文件名未按「改_xxx——学生名」命名' })
      corParsedCount.value++
      continue
    }

    try {
      const { title, before, after } = await parseDocxContent(file)
      if (!before && !after) {
        parsed.push({ file, studentName, ok: false, error: '未识别到「修改前：/修改后：」内容' })
      } else {
        parsed.push({ file, studentName, ok: true, title, before, after })
      }
    } catch (err) {
      parsed.push({ file, studentName, ok: false, error: '文件解析失败（不支持 .doc 旧格式或文件损坏）' })
    }
    corParsedCount.value++
  }

  corParsing.value = false

  if (parsed.length === 0) {
    showToast('未找到可解析的文件')
    return
  }

  corFiles.value = parsed
  corFolderSelected.value = true

  const folderName = getFolderPath(files)
  if (folderName) {
    const parsedFolder = parseFolderName(folderName)
    if (parsedFolder.grade && !corForm.value.grade) {
      corForm.value.grade = parsedFolder.grade
      selectedGrade.value = parsedFolder.grade
    }
    if (parsedFolder.essay_number && !corForm.value.essay_number) {
      corForm.value.essay_number = parsedFolder.essay_number
    }
  }

  if (preCheckExisting.value && selectedTaskId.value) {
    checkExisting()
  } else {
    existingNames.value = []
    checkedExisting.value = false
  }
}

function removeCorFile(idx) {
  corFiles.value.splice(idx, 1)
  if (!corFiles.value.length) corFolderSelected.value = false
}

// ===== 预检 =====
async function checkExisting() {
  if (!selectedTaskId.value) { showToast('请先选择收集任务'); return }
  checkingExisting.value = true
  try {
    const params = { task_id: selectedTaskId.value }
    if (activeForm.value.essay_number) params.essay_number = parseInt(activeForm.value.essay_number)
    if (activeForm.value.is_supplement) params.is_supplement = activeForm.value.is_supplement
    const res = await api.get('/essays/existing-students', { params })
    existingNames.value = res.data.students || []
    checkedExisting.value = true
  } catch {
    existingNames.value = []
    showToast('检查失败，请稍后重试')
  } finally {
    checkingExisting.value = false
  }
}

function onPreCheckChange(val) {
  existingNames.value = []
  checkedExisting.value = false
  if (val && (folderSelected.value || corFolderSelected.value) && selectedTaskId.value) {
    checkExisting()
  }
}

// ===== 并发工具 =====
async function runConcurrent(items, worker) {
  let i = 0
  const n = Math.min(CONCURRENCY, items.length)
  const runners = []
  for (let w = 0; w < n; w++) {
    runners.push((async () => {
      while (i < items.length) {
        const item = items[i++]
        await worker(item)
      }
    })())
  }
  await Promise.all(runners)
}

// ===== 上传：作文模式 =====
function buildEssayFormData(name) {
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
  fd.append('grade', form.value.grade)
  const essayNumber = parseInt(form.value.essay_number)
  fd.append('essay_number', isNaN(essayNumber) || essayNumber <= 0 ? '0' : String(essayNumber))
  fd.append('student_name', name)
  fd.append('is_supplement', form.value.is_supplement ? 'true' : 'false')
  fd.append('teaching_mode', form.value.teaching_mode)
  fd.append('collector_note', form.value.collector_note || '')
  fd.append('content_text', '')
  studentMap.value[name].forEach(f => fd.append('files', f))
  return fd
}

async function uploadEssays() {
  const names = Object.keys(studentMap.value)
  if (!names.length) { showToast('请先选择文件夹'); return }

  const skipNames = names.filter(n => existingNames.value.includes(n))
  const toUpload = names.filter(n => !existingNames.value.includes(n))
  if (toUpload.length === 0) {
    showToast('所选学生均已存在，无需上传')
    return
  }

  const confirmed = await showConfirmDialog({
    title: '确认开始上传',
    message: `共 ${names.length} 位学生\n将上传：${toUpload.length} 位\n跳过已存在：${skipNames.length} 位`,
    confirmButtonText: '开始上传',
    cancelButtonText: '取消',
  }).then(() => true).catch(() => false)
  if (!confirmed) return

  loading.value = true
  uploadedCount.value = skipNames.length
  essaysSuccess.value = 0
  essaysFail.value = 0
  essaysSkip.value = skipNames.length
  currentStudent.value = ''
  failedStudents.value = []

  await runConcurrent(toUpload, async (name) => {
    currentStudent.value = name
    try {
      await api.post('/essays/upload', buildEssayFormData(name), { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 })
      essaysSuccess.value++
    } catch (err) {
      const status = err.response?.status
      if (status === 409 && preCheckExisting.value) {
        essaysSkip.value++
      } else {
        essaysFail.value++
        failedStudents.value.push({ name, detail: err.response?.data?.detail || err.message })
      }
    } finally {
      uploadedCount.value++
    }
  })

  loading.value = false

  const failed = failedStudents.value
  let body = `成功：${essaysSuccess.value} 位\n跳过已存在：${essaysSkip.value}`
  if (failed.length) {
    body += `\n失败：${failed.length} 位\n\n` + failed.map(f => `· ${f.name}${f.detail ? '：' + f.detail : ''}`).join('\n')
  }
  resultDialog.value = {
    show: true,
    title: failed.length ? '上传完成（有失败）' : '上传成功',
    body,
    canRetry: failed.length > 0,
    retryCount: failed.length,
    retryMode: 'essay',
    retryNames: failed.map(f => f.name),
  }
}

// ===== 上传：修改后模式 =====
async function uploadCorrections(items, skipCount = 0) {
  corLoading.value = true
  corUploadedCount.value = skipCount
  corSuccess.value = 0
  corFail.value = 0
  corSkipExisting.value = skipCount
  corCurrentStudent.value = ''
  corFailed.value = []

  await runConcurrent(items, async (item) => {
    corCurrentStudent.value = item.studentName
    try {
      const fd = new FormData()
      if (selectedTaskId.value) {
        fd.append('task_id', String(selectedTaskId.value))
      }
      if (selectedCourseId.value) {
        fd.append('course_id', String(selectedCourseId.value))
      }
      fd.append('grade', corForm.value.grade)
      const essayNumber = parseInt(corForm.value.essay_number)
      fd.append('essay_number', isNaN(essayNumber) || essayNumber <= 0 ? '0' : String(essayNumber))
      fd.append('teaching_mode', corForm.value.teaching_mode)
      fd.append('student_name', item.studentName)
      fd.append('essay_title', item.title || '')
      fd.append('content_text', item.before || '')
      fd.append('corrected_text', item.after || '')
      fd.append('is_supplement', corForm.value.is_supplement ? 'true' : 'false')
      fd.append('collector_note', corForm.value.collector_note || '')
      fd.append('file', item.file)
      if (selectedCollector.value) {
        fd.append('collected_by', String(selectedCollector.value))
      }
      await api.post('/essays/upload-correction-docx', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 })
      corSuccess.value++
    } catch (err) {
      corFail.value++
      corFailed.value.push({ studentName: item.studentName, detail: err.response?.data?.detail || err.message })
    } finally {
      corUploadedCount.value++
    }
  })

  corLoading.value = false

  const failed = corFailed.value
  let body = `成功：${corSuccess.value} 个\n跳过已存在：${corSkipExisting.value} 个` + (corParseFailCount.value ? `\n解析失败跳过：${corParseFailCount.value} 个` : '')
  if (failed.length) {
    body += `\n失败：${failed.length} 个\n\n` + failed.map(f => `· ${f.studentName}${f.detail ? '：' + f.detail : ''}`).join('\n')
  }
  resultDialog.value = {
    show: true,
    title: failed.length ? '上传完成（有失败）' : '上传成功',
    body,
    canRetry: failed.length > 0,
    retryCount: failed.length,
    retryMode: 'correction',
    retryNames: failed.map(f => f.studentName),
  }
}

function retryFailed() {
  const d = resultDialog.value
  resultDialog.value.show = false
  if (d.retryMode === 'essay') {
    const map = {}
    d.retryNames.forEach(n => { if (studentMap.value[n]) map[n] = studentMap.value[n] })
    studentMap.value = map
    existingNames.value = existingNames.value.filter(n => map[n])
    uploadEssays()
  } else {
    const names = new Set(d.retryNames)
    uploadCorrections(corFiles.value.filter(i => names.has(i.studentName)))
  }
}

function copyResult() {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(resultDialog.value.body).then(() => showToast('已复制明细')).catch(() => showToast('复制失败'))
  } else {
    showToast('当前浏览器不支持一键复制')
  }
}

async function onSubmit() {
  if (!activeForm.value.grade) {
    const ok = await showConfirmDialog({
      title: '提示',
      message: '未选择年级，将按「未定年级」归档。确定继续上传吗？',
      confirmButtonText: '继续上传',
      cancelButtonText: '取消',
    }).then(() => true).catch(() => false)
    if (!ok) return
  }
  if (!activeForm.value.essay_number) {
    const ok = await showConfirmDialog({
      title: '提示',
      message: '未填写第几次，将按「无第几次」归档。确定继续上传吗？',
      confirmButtonText: '继续上传',
      cancelButtonText: '取消',
    }).then(() => true).catch(() => false)
    if (!ok) return
  }
  if (mode.value === 'essay') {
    await uploadEssays()
  } else {
    let items = corFiles.value.filter(i => i.ok)
    let skipCount = 0
    if (preCheckExisting.value && existingNames.value.length) {
      skipCount = items.filter(i => existingNames.value.includes(i.studentName)).length
      items = items.filter(i => !existingNames.value.includes(i.studentName))
    }
    if (!items.length) {
      showToast(skipCount ? '所选学生均已存在，无需上传' : '没有可上传的文件（请先修复解析失败项或移除）')
      return
    }
    const confirmed = await showConfirmDialog({
      title: '确认开始上传',
      message: `可上传：${items.length} 个文件\n跳过已存在：${skipCount} 个\n解析失败（不上传）：${corParseFailCount.value} 个`,
      confirmButtonText: '开始上传',
      cancelButtonText: '取消',
    }).then(() => true).catch(() => false)
    if (!confirmed) return
    await uploadCorrections(items, skipCount)
  }
}
</script>

<style scoped>
.page { padding: 16px; }
.picker-list { max-height: 70vh; overflow-y: auto; }
@media (max-width: 767px) { .page { padding: 0; } }

.mode-boxes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}
.mode-box {
  background: #fff;
  border: 2px solid #f0f0f0;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
}
.mode-box:hover { border-color: #bcd6ff; }
.mode-box.active { border-color: #1677ff; background: #eef5ff; }
.mode-icon { font-size: 26px; }
.mode-title { font-weight: 600; font-size: 14px; margin-top: 6px; color: #333; }
.mode-desc { font-size: 12px; color: #999; margin-top: 4px; }

.mode-tip {
  text-align: left;
  background: #f8f9fb;
  border-radius: 8px;
  padding: 10px;
  margin-top: 10px;
  font-size: 12px;
  max-height: 260px;
  overflow-y: auto;
}
.mode-box.active .mode-tip { background: #fff; }

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
  padding: 8px 16px;
  font-size: 13px;
  color: #888;
  font-weight: 500;
}

.tip-label {
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.tip-content {
  background: #fff;
  padding: 10px 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.8;
  color: #555;
  border: 1px solid #e8e8e8;
}

.tip-note {
  margin-top: 8px;
  color: #888;
  font-size: 12px;
}

.preview-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 0 4px;
  font-size: 12px;
  flex-wrap: wrap;
}

.preview-list {
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  margin-top: 8px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #f5f5f5;
  font-size: 13px;
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-item.preview-existing { background: #fafafa; }
.preview-existing .preview-name { color: #999; text-decoration: line-through; }

.preview-main { flex: 1; min-width: 0; }

.preview-name {
  font-weight: 500;
  color: #333;
}

.preview-files {
  color: #888;
  font-size: 12px;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-remove {
  flex: none;
  width: 20px;
  height: 20px;
  line-height: 18px;
  text-align: center;
  border: none;
  border-radius: 50%;
  background: #f5f5f5;
  color: #999;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.preview-remove:hover { background: #ff4d4f; color: #fff; }

.skip-note {
  padding: 8px 12px;
  font-size: 12px;
  color: #d46b08;
  background: #fffbe6;
  border-top: 1px dashed #ffe58f;
}

.progress-box {
  margin-top: 12px;
  padding: 12px;
  background: #f6f8fa;
  border-radius: 6px;
}

.progress-text {
  margin-top: 8px;
  font-size: 13px;
  color: #555;
}

.progress-stats {
  margin-top: 6px;
  font-size: 12px;
  display: flex;
  gap: 16px;
}

.stat-success {
  color: #52c41a;
}

.stat-skip {
  color: #fa8c16;
}

.stat-fail {
  color: #ff4d4f;
}

.result-body {
  max-height: 40vh;
  overflow-y: auto;
  white-space: pre-line;
  font-size: 13px;
  line-height: 1.7;
}
</style>
