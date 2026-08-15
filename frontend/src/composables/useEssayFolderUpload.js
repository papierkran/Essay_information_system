import { ref, computed } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import api from '../api'
import { compressImageFile, isImageFile, IMAGE_UPLOAD_MAX_BYTES } from '../utils/imageCompress'
import { extractTitleFromText, readDocxText, splitBeforeAfterText } from '../utils/docxParse'

const CONCURRENCY = 3
const SUPPORTED_EXTS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.docx', '.txt']
const SKIP_FOLDERS = ['修改后']

export function useEssayFolderUpload(contextRef, { onResult, onFolderSelected } = {}) {
  // 每名学生可有多篇：{ studentName, title, before, after, files }
  const essayGroups = ref([])
  const folderSelected = ref(false)
  const skipStats = ref({ total: 0, modifiedFolder: 0, unsupported: 0, noStudent: 0, oversize: 0, docOld: 0 })
  const loading = ref(false)
  const uploadedCount = ref(0)
  const currentStudent = ref('')
  const essaysSuccess = ref(0)
  const essaysFail = ref(0)
  const essaysSkip = ref(0)
  const failedStudents = ref([])
  const uploadFinished = ref(false)
  const compressing = ref(false)
  const compressTotal = ref(0)
  const compressDone = ref(0)

  const compressPercent = computed(() => compressTotal.value ? Math.round(compressDone.value / compressTotal.value * 100) : 0)
  const studentCount = computed(() => new Set(essayGroups.value.map(g => g.studentName)).size)
  const essayTotal = computed(() => essayGroups.value.length)
  const totalFiles = computed(() => essayGroups.value.reduce((sum, g) => sum + g.files.length, 0))
  const essaysPercent = computed(() => essayTotal.value ? Math.round(uploadedCount.value / essayTotal.value * 100) : 0)
  const essayBeforeTotal = computed(() => essayGroups.value.reduce((s, g) => s + (g.before || '').length, 0))
  const essayAfterTotal = computed(() => essayGroups.value.reduce((s, g) => s + (g.after || '').length, 0))

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

  async function readFileText(file) {
    const name = (file.name || '').toLowerCase()
    if (name.endsWith('.docx')) return readDocxText(file)
    return file.text()
  }

  function displayName(item) {
    return item.studentName + (item.title ? `（${item.title}）` : '')
  }

  async function onFolderChange(e) {
    const files = Array.from(e.target.files)
    if (files.length === 0) return
    uploadFinished.value = false

    const map = {}
    skipStats.value = { total: 0, modifiedFolder: 0, unsupported: 0, noStudent: 0, oversize: 0, docOld: 0 }

    const pendingCompress = []
    for (const file of files) {
      const relativePath = file.webkitRelativePath
      if (!relativePath) { skipStats.value.noStudent++; continue }

      const parts = relativePath.split('/')
      if (parts.length < 2) { skipStats.value.noStudent++; continue }

      const studentName = parts[1]
      if (SKIP_FOLDERS.includes(studentName)) { skipStats.value.modifiedFolder++; continue }

      const ext = '.' + file.name.split('.').pop().toLowerCase()
      if (ext === '.doc') { skipStats.value.docOld++; continue }
      if (!SUPPORTED_EXTS.includes(ext)) { skipStats.value.unsupported++; continue }

      if (isImageFile(file) && file.size > IMAGE_UPLOAD_MAX_BYTES) { skipStats.value.oversize++; continue }

      pendingCompress.push({ file, studentName })
    }

    compressing.value = true
    compressTotal.value = pendingCompress.length
    compressDone.value = 0
    await runConcurrent(pendingCompress, async ({ file, studentName }) => {
      const out = await compressImageFile(file)
      if (!map[studentName]) map[studentName] = []
      map[studentName].push(out)
      compressDone.value++
    })
    compressing.value = false
    skipStats.value.total = skipStats.value.modifiedFolder + skipStats.value.unsupported + skipStats.value.noStudent + skipStats.value.oversize + skipStats.value.docOld

    if (Object.keys(map).length === 0) {
      showToast('未找到有效的学生文件')
      return
    }

    // 按学生分组构建作文条目：docx/txt 全部读取，按标题分组
    const groups = []
    for (const [studentName, studentFiles] of Object.entries(map)) {
      const docxTxt = []
      const images = []
      for (const f of studentFiles) {
        const ext = '.' + f.name.split('.').pop().toLowerCase()
        if (ext === '.docx' || ext === '.txt') docxTxt.push(f)
        else images.push(f)
      }

      if (!docxTxt.length) {
        groups.push({ studentName, title: '', before: '', after: '', files: [...studentFiles] })
        continue
      }

      const parsed = []
      for (const f of docxTxt) {
        try {
          const text = await readFileText(f)
          const { before, after } = splitBeforeAfterText(text)
          parsed.push({ file: f, title: extractTitleFromText(text), before, after })
        } catch {}
      }
      if (!parsed.length) {
        groups.push({ studentName, title: '', before: '', after: '', files: [...studentFiles] })
        continue
      }

      // 按标题分组：标题相同的合并（取含修改标记的版本），标题不同的各自保存
      const byTitle = new Map()
      for (const p of parsed) {
        const key = p.title || '__untitled__'
        if (!byTitle.has(key)) byTitle.set(key, [])
        byTitle.get(key).push(p)
      }

      let first = true
      for (const items of byTitle.values()) {
        const marked = items.find(i => i.after) || items[0]
        const itemFiles = [marked.file]
        if (first) itemFiles.unshift(...images)
        groups.push({
          studentName,
          title: marked.title,
          before: marked.before,
          after: marked.after,
          files: itemFiles,
        })
        first = false
      }
    }
    essayGroups.value = groups
    folderSelected.value = true

    if (onFolderSelected) onFolderSelected(files)
  }

  function removeEssay(idx) {
    essayGroups.value.splice(idx, 1)
    if (!essayGroups.value.length) folderSelected.value = false
  }

  function buildEssayFormData(item) {
    const ctx = contextRef.value
    const fd = new FormData()
    if (ctx.taskId) {
      fd.append('task_id', String(ctx.taskId))
    }
    if (ctx.courseId) {
      fd.append('course_id', String(ctx.courseId))
    }
    if (ctx.collectorId) {
      fd.append('collected_by', String(ctx.collectorId))
    }
    fd.append('grade', ctx.form.grade)
    const essayNumber = parseInt(ctx.form.essay_number)
    fd.append('essay_number', isNaN(essayNumber) || essayNumber <= 0 ? '0' : String(essayNumber))
    fd.append('student_name', item.studentName)
    fd.append('essay_title', item.title || '')
    fd.append('is_supplement', ctx.form.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', ctx.form.teaching_mode)
    fd.append('collector_note', ctx.form.collector_note || '')
    fd.append('content_text', '')
    if (ctx.form.collect_time) {
      fd.append('collect_time', ctx.form.collect_time)
    }
    if (ctx.markCorrected) {
      fd.append('mark_corrected', 'true')
    }
    item.files.forEach(f => fd.append('files', f))
    return fd
  }

  async function uploadEssays() {
    const items = essayGroups.value
    if (!items.length) { showToast('请先选择文件夹'); return }

    const existingNames = contextRef.value.existingNames || []
    const skipItems = items.filter(g => existingNames.includes(g.studentName))
    const toUpload = items.filter(g => !existingNames.includes(g.studentName))
    if (!toUpload.length) {
      showToast('所选学生均已存在，无需上传')
      return
    }

    const confirmed = await showConfirmDialog({
      title: '确认开始上传',
      message: `共 ${items.length} 篇作文（${studentCount.value} 位学生）\n将上传：${toUpload.length} 篇\n跳过已存在：${skipItems.length} 篇`,
      confirmButtonText: '开始上传',
      cancelButtonText: '取消',
    }).then(() => true).catch(() => false)
    if (!confirmed) return

    loading.value = true
    uploadedCount.value = skipItems.length
    essaysSuccess.value = 0
    essaysFail.value = 0
    essaysSkip.value = skipItems.length
    currentStudent.value = ''
    failedStudents.value = []

    await runConcurrent(toUpload, async (item) => {
      currentStudent.value = displayName(item)
      try {
        await api.post('/essays/upload', buildEssayFormData(item), { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 })
        essaysSuccess.value++
      } catch (err) {
        const status = err.response?.status
        if (status === 409) {
          essaysSkip.value++
        } else {
          essaysFail.value++
          failedStudents.value.push({ name: displayName(item), detail: err.response?.data?.detail || err.message })
        }
      } finally {
        uploadedCount.value++
      }
    })

    loading.value = false
    uploadFinished.value = failedStudents.value.length === 0

    const failed = failedStudents.value
    let body = `成功：${essaysSuccess.value} 篇\n跳过已存在：${essaysSkip.value} 篇`
    if (failed.length) {
      body += `\n失败：${failed.length} 篇\n\n` + failed.map(f => `· ${f.name}${f.detail ? '：' + f.detail : ''}`).join('\n')
    }
    if (onResult) onResult({
      title: failed.length ? '上传完成（有失败）' : '上传成功',
      body,
      canRetry: failed.length > 0,
      retryCount: failed.length,
      mode: 'essay',
      retryNames: failed.map(f => f.name),
    })
  }

  async function retryFailed(names) {
    const nameSet = new Set(names)
    essayGroups.value = essayGroups.value.filter(g => nameSet.has(displayName(g)))
    const remainingNames = new Set(essayGroups.value.map(g => g.studentName))
    contextRef.value.existingNames = (contextRef.value.existingNames || []).filter(n => remainingNames.has(n))
    await uploadEssays()
  }

  function reset() {
    essayGroups.value = []
    folderSelected.value = false
    loading.value = false
    uploadFinished.value = false
    compressing.value = false
    essaysSuccess.value = 0
    essaysFail.value = 0
    essaysSkip.value = 0
    failedStudents.value = []
    uploadedCount.value = 0
  }

  return {
    essayGroups, folderSelected, skipStats, loading, uploadedCount, currentStudent,
    essaysSuccess, essaysFail, essaysSkip, failedStudents, uploadFinished,
    compressing, compressTotal, compressDone, compressPercent,
    studentCount, essayTotal, totalFiles, essaysPercent, essayBeforeTotal, essayAfterTotal,
    onFolderChange, removeEssay, uploadEssays, retryFailed, reset,
  }
}
