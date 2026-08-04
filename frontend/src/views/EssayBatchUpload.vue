<template>
  <div class="page">
    <div v-if="isDesktop" class="page-title">批量上传</div>

    <!-- 模板选择区域 -->
    <van-cell-group inset style="margin-bottom:12px">
      <van-field :model-value="selectedTaskName" is-link readonly label="选择收集任务"
        placeholder="选择收集任务（自动填充年级等信息）" @click="showTaskPicker = true" />
    </van-cell-group>

    <div class="batch-grid">
      <!-- 左侧：批量上传作文 -->
      <div class="batch-card">
        <h3 class="card-title">批量上传作文</h3>
        <div class="format-tip">
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
          <div class="tip-note">* 支持格式：jpg/jpeg/png/gif/webp/docx/doc</div>
        </div>

        <van-form @submit="onSubmitEssays">
          <van-field :model-value="selectedGrade" is-link readonly label="年级" placeholder="请选择"
            @click="showGradePicker = true" :rules="[{ required: true }]" />
          <van-field v-model="form.essay_number" label="第几次" placeholder="数字" type="digit" :rules="[{ required: true }]" />
          <van-field name="teaching_mode" label="提交方式">
            <template #input>
              <van-radio-group v-model="form.teaching_mode" direction="horizontal">
                <van-radio name="线下" style="margin-right:16px">线下</van-radio>
                <van-radio name="线上">线上</van-radio>
              </van-radio-group>
            </template>
          </van-field>
          <van-field v-if="isAdmin" :model-value="selectedCollectorName" is-link readonly label="收集者" placeholder="默认当前用户"
            @click="showCollectorPicker = true" />

          <van-cell title="选择文件夹" :label="folderSelected ? `${studentCount} 位学生，${totalFiles} 个文件` : '点击选择'" is-link @click="$refs.folderInput.click()" />
          <input ref="folderInput" type="file" webkitdirectory style="display:none" @change="onFolderChange" />

          <div v-if="folderSelected" class="preview-list">
            <div v-for="(files, name) in studentMap" :key="name" class="preview-item">
              <span class="preview-name">{{ name }}</span>
              <span class="preview-files">{{ files.length }} 个文件</span>
            </div>
          </div>

          <van-button round block type="primary" native-type="submit" :loading="loading" :disabled="!folderSelected" style="margin-top:12px">
            {{ loading ? `上传中 ${uploadedCount}/${studentCount}` : '开始上传' }}
          </van-button>

          <div v-if="loading" class="progress-box">
            <van-progress :percentage="essaysPercent" stroke-width="8" />
            <div class="progress-text">正在上传：{{ currentStudent }}</div>
            <div class="progress-stats">
              <span class="stat-success">成功 {{ essaysSuccess }}</span>
              <span class="stat-fail">失败 {{ essaysFail }}</span>
            </div>
          </div>
        </van-form>
      </div>

      <!-- 右侧：批量上传修改后 -->
      <div class="batch-card">
        <h3 class="card-title">批量上传修改后docx</h3>
        <div class="format-tip">
          <div class="tip-label">文件名格式：</div>
          <div class="tip-content">
            改_原文件名——学生姓名.docx<br>
            改_作文——张三.docx<br>
            改_作文——李四.docx
          </div>
          <div class="tip-note">* 破折号「——」后的名字为学生姓名</div>
          <div class="tip-note">* 支持格式：docx/doc</div>
          <div class="tip-note">* 将自动识别学生姓名、标题和作文内容</div>
          <div class="tip-note">* 格式为以下格式才会正常识别   </div>
          <div class="tip-note">* {第一行}修改前：</div>
          <div class="tip-note">* {第二行}（作文标题）</div>
          <div class="tip-note">* {第三行}——（学生姓名）</div>
        </div>

        <van-form @submit="onSubmitCorrections">
          <van-field :model-value="corSelectedGrade" is-link readonly label="年级" placeholder="请选择"
            @click="showCorGradePicker = true" :rules="[{ required: true }]" />
          <van-field v-model="corForm.essay_number" label="第几次" placeholder="数字" type="digit" :rules="[{ required: true }]" />
          <van-field name="teaching_mode" label="提交方式">
            <template #input>
              <van-radio-group v-model="corForm.teaching_mode" direction="horizontal">
                <van-radio name="线下" style="margin-right:16px">线下</van-radio>
                <van-radio name="线上">线上</van-radio>
              </van-radio-group>
            </template>
          </van-field>
          <van-field v-if="isAdmin" :model-value="selectedCollectorName" is-link readonly label="收集者" placeholder="默认当前用户"
            @click="showCollectorPicker = true" />

          <van-cell title="选择文件夹" :label="corFolderSelected ? `${corFiles.length} 个文件` : '点击选择'" is-link @click="$refs.corFolderInput.click()" />
          <input ref="corFolderInput" type="file" webkitdirectory style="display:none" @change="onCorFolderChange" />

          <div v-if="corFolderSelected" class="preview-list">
            <div v-for="(item, idx) in corFiles" :key="idx" class="preview-item">
              <span class="preview-name">{{ item.studentName }}</span>
              <span class="preview-files">{{ item.file.name }}</span>
            </div>
          </div>

          <van-button round block type="primary" native-type="submit" :loading="corLoading" :disabled="!corFolderSelected" style="margin-top:12px">
            {{ corLoading ? `上传中 ${corUploadedCount}/${corFiles.length}` : '开始上传' }}
          </van-button>

          <div v-if="corLoading" class="progress-box">
            <van-progress :percentage="corPercent" stroke-width="8" />
            <div class="progress-text">正在上传：{{ corCurrentStudent }}</div>
            <div class="progress-stats">
              <span class="stat-success">成功 {{ corSuccess }}</span>
              <span class="stat-fail">失败 {{ corFail }}</span>
            </div>
          </div>
        </van-form>
      </div>
    </div>

    <van-action-sheet v-model:show="showGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectGrade(g)" />
      </div>
    </van-action-sheet>

    <van-action-sheet v-model:show="showCorGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectCorGrade(g)" />
      </div>
    </van-action-sheet>

    <!-- 模板选择器 -->
    <van-action-sheet v-model:show="showTaskPicker" title="选择收集任务">
      <div class="picker-list">
        <van-cell title="不使用模板" @click="selectTask(null)" style="color:#999" />
        <van-cell v-for="t in sortedTasks" :key="t.id"
          :title="t.name"
          :label="`${t.grade} 第${t.essay_number}次 ${t.essay_topic || ''}`"
          @click="selectTask(t)">
          <template #right-icon>
            <van-tag v-if="taskIsActive(t)" type="primary" style="margin-right:8px">收集中</van-tag>
          </template>
        </van-cell>
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
import { showToast, showDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import JSZip from 'jszip'

const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isAdmin = computed(() => (currentUser.value.role || '').includes('admin'))

const loading = ref(false)
const corLoading = ref(false)
const showGradePicker = ref(false)
const showCorGradePicker = ref(false)
const showTaskPicker = ref(false)
const showCollectorPicker = ref(false)
const selectedGrade = ref('')
const corSelectedGrade = ref('')
const selectedTaskName = ref('')
const selectedTaskId = ref(null)
const selectedCollector = ref(null)
const selectedCollectorName = ref('')
const collectorList = ref([])
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']
const folderInput = ref(null)
const corFolderInput = ref(null)
const tasks = ref([])

const sortedTasks = computed(() => {
  return [...tasks.value].sort((a, b) => {
    const aActive = taskIsActive(a)
    const bActive = taskIsActive(b)
    if (aActive !== bActive) return aActive ? -1 : 1
    return 0
  })
})

function taskIsActive(t) {
  return t.is_active && (!t.deadline || new Date(t.deadline) >= new Date())
}

const form = ref({ grade: '', essay_number: '', teaching_mode: '线上' })
const corForm = ref({ grade: '', essay_number: '', teaching_mode: '线下' })

// 批量上传作文
const studentMap = ref({})
const folderSelected = ref(false)
const uploadedCount = ref(0)
const currentStudent = ref('')
const essaysSuccess = ref(0)
const essaysFail = ref(0)
const essaysPercent = computed(() => studentCount.value ? Math.round(uploadedCount.value / studentCount.value * 100) : 0)

const studentCount = computed(() => Object.keys(studentMap.value).length)
const totalFiles = computed(() => Object.values(studentMap.value).reduce((sum, files) => sum + files.length, 0))

// 批量上传修改后
const corFiles = ref([])
const corFolderSelected = ref(false)
const corUploadedCount = ref(0)
const corCurrentStudent = ref('')
const corSuccess = ref(0)
const corFail = ref(0)
const corPercent = computed(() => corFiles.value.length ? Math.round(corUploadedCount.value / corFiles.value.length * 100) : 0)

onMounted(async () => {
  try {
    const res = await api.get('/essays/tasks')
    tasks.value = res.data
  } catch {}
  if (isAdmin.value) {
    try {
      const res = await api.get('/essays/collectors')
      collectorList.value = res.data || []
    } catch {}
  }
})

function selectGrade(g) {
  form.value.grade = g
  selectedGrade.value = g
  showGradePicker.value = false
}

function selectCorGrade(g) {
  corForm.value.grade = g
  corSelectedGrade.value = g
  showCorGradePicker.value = false
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
    selectedGrade.value = tpl.grade
    form.value.essay_number = String(tpl.essay_number)
    // 自动填充提交方式
    if (tpl.teaching_mode) {
      form.value.teaching_mode = tpl.teaching_mode
    }
    corForm.value.grade = tpl.grade
    corSelectedGrade.value = tpl.grade
    corForm.value.essay_number = String(tpl.essay_number)
    // 自动填充提交方式
    if (tpl.teaching_mode) {
      corForm.value.teaching_mode = tpl.teaching_mode
    }
    selectedTaskName.value = tpl.name
    selectedTaskId.value = tpl.id
    showToast(`已选择：${tpl.name}`)
  } else {
    selectedTaskName.value = ''
    selectedTaskId.value = null
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

function onFolderChange(e) {
  const files = Array.from(e.target.files)
  if (files.length === 0) return

  const map = {}
  const supportedExts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.docx', '.doc']
  const skipFolders = ['修改后']

  const folderName = getFolderPath(files)

  for (const file of files) {
    const relativePath = file.webkitRelativePath
    if (!relativePath) continue

    const parts = relativePath.split('/')
    if (parts.length < 2) continue

    const studentName = parts[1]
    if (skipFolders.includes(studentName)) continue

    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!supportedExts.includes(ext)) continue

    if (!map[studentName]) map[studentName] = []
    map[studentName].push(file)
  }

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
}

function onCorFolderChange(e) {
  const files = Array.from(e.target.files)
  if (files.length === 0) return

  const parsed = []

  for (const file of files) {
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (ext !== '.docx' && ext !== '.doc') continue

    const nameWithoutExt = file.name.replace(/\.(docx|doc)$/i, '')
    let dashIndex = nameWithoutExt.indexOf('——')
    if (dashIndex === -1) dashIndex = nameWithoutExt.indexOf('-')

    if (dashIndex === -1) continue

    const studentName = nameWithoutExt.substring(dashIndex + (nameWithoutExt.charAt(dashIndex) === '—' ? 2 : 1)).trim()
    if (!studentName) continue

    parsed.push({ file, studentName })
  }

  if (parsed.length === 0) {
    showToast('未找到"改*——学生名.docx"或"改*-学生名.docx"格式的文件')
    return
  }

  corFiles.value = parsed
  corFolderSelected.value = true

  const folderName = getFolderPath(files)
  if (folderName) {
    const parsedFolder = parseFolderName(folderName)
    if (parsedFolder.grade && !corForm.value.grade) {
      corForm.value.grade = parsedFolder.grade
      corSelectedGrade.value = parsedFolder.grade
    }
    if (parsedFolder.essay_number && !corForm.value.essay_number) {
      corForm.value.essay_number = parsedFolder.essay_number
    }
  }
}

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

async function onSubmitEssays() {
  if (!form.value.grade) { showToast('请选择年级'); return }
  if (studentCount.value === 0) { showToast('请选择文件夹'); return }

  loading.value = true
  uploadedCount.value = 0
  essaysSuccess.value = 0
  essaysFail.value = 0
  currentStudent.value = ''
  const errorDetails = []

  for (const [studentName, files] of Object.entries(studentMap.value)) {
    currentStudent.value = studentName
    try {
      const fd = new FormData()
      fd.append('class_id', '1')
      if (selectedTaskId.value) {
        fd.append('task_id', String(selectedTaskId.value))
      }
      if (selectedCollector.value) {
        fd.append('collected_by', String(selectedCollector.value))
      }
      fd.append('grade', form.value.grade)
      fd.append('essay_number', form.value.essay_number || 1)
      fd.append('student_name', studentName)
      fd.append('is_supplement', 'false')
      fd.append('teaching_mode', form.value.teaching_mode)
      fd.append('collector_note', form.value.collector_note || '')
      fd.append('content_text', '')
      files.forEach(f => fd.append('files', f))

      console.log('上传学生:', studentName, '文件数:', files.length)
      const res = await api.post('/essays/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      console.log('上传成功:', res.data)
      essaysSuccess.value++
    } catch (err) {
      console.error('上传失败:', studentName, err.response?.data || err.message)
      errorDetails.push(`${studentName}: ${err.response?.data?.detail || err.message}`)
      essaysFail.value++
    }
    uploadedCount.value++
  }

  loading.value = false
  showDialog({
    title: essaysFail.value === 0 ? '上传成功' : '上传完成',
    message: `成功：${essaysSuccess.value} 位学生` + (errorDetails.length > 0 ? `\n失败：\n${errorDetails.join('\n')}` : ''),
    confirmButtonText: '确定',
  })

  if (essaysFail.value === 0) {
    studentMap.value = {}
    folderSelected.value = false
  }
}

async function onSubmitCorrections() {
  if (!corForm.value.grade) { showToast('请选择年级'); return }
  if (corFiles.value.length === 0) { showToast('请选择文件夹'); return }

  corLoading.value = true
  corUploadedCount.value = 0
  corSuccess.value = 0
  corFail.value = 0
  corCurrentStudent.value = ''
  const errorDetails = []

  for (const { file, studentName } of corFiles.value) {
    corCurrentStudent.value = studentName
    let finalStudentName = studentName
    try {
      console.log('解析文件:', file.name, '文件名学生:', studentName)
      const { title, studentName: docStudentName, before, after } = await parseDocxContent(file)
      finalStudentName = docStudentName || studentName
      console.log('解析结果 - 学生:', finalStudentName, '标题:', title, '修改前:', before.length, '字, 修改后:', after.length, '字')

      if (!before && !after) {
        errorDetails.push(`${finalStudentName}: 文件内容解析失败`)
        corFail.value++
        corUploadedCount.value++
        continue
      }

      const fd = new FormData()
      fd.append('grade', corForm.value.grade)
      fd.append('essay_number', corForm.value.essay_number || 1)
      fd.append('teaching_mode', corForm.value.teaching_mode)
      fd.append('student_name', finalStudentName)
      fd.append('essay_title', title)
      fd.append('content_text', before || '')
      fd.append('corrected_text', after || '')
      fd.append('file', file)
      if (selectedCollector.value) {
        fd.append('collected_by', String(selectedCollector.value))
      }

      console.log('上传:', finalStudentName)
      await api.post('/essays/upload-correction-docx', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      console.log('成功:', finalStudentName)
      corSuccess.value++
    } catch (err) {
      console.error('失败:', finalStudentName, err.response?.data || err.message)
      errorDetails.push(`${finalStudentName}: ${err.response?.data?.detail || err.message}`)
      corFail.value++
    }
    corUploadedCount.value++
  }

  corLoading.value = false
  showDialog({
    title: corFail.value === 0 ? '上传成功' : '上传完成',
    message: `成功：${corSuccess.value} 个` + (errorDetails.length > 0 ? `\n失败：\n${errorDetails.join('\n')}` : ''),
    confirmButtonText: '确定',
  })

  if (corFail.value === 0) {
    corFiles.value = []
    corFolderSelected.value = false
  }
}
</script>

<style scoped>
.page { padding: 16px; }
.picker-list { max-height: 300px; overflow-y: auto; }

.batch-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.batch-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.format-tip {
  background: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
  font-size: 13px;
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

.preview-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  margin-top: 8px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #f5f5f5;
  font-size: 13px;
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-name {
  font-weight: 500;
  color: #333;
}

.preview-files {
  color: #888;
  font-size: 12px;
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

.stat-fail {
  color: #ff4d4f;
}

@media (max-width: 767px) {
  .batch-grid {
    grid-template-columns: 1fr;
  }
}
</style>
