import { ref, computed } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import api from '../api'
import { readDocxText, extractTitleFromText, extractNameFromText, splitBeforeAfterText } from '../utils/docxParse'

const CONCURRENCY = 3

export function useCorrectionUpload(contextRef, { onResult, onFolderSelected } = {}) {
  const corFiles = ref([])
  const corFolderSelected = ref(false)
  const corParsing = ref(false)
  const corParsedCount = ref(0)
  const corFileTotal = ref(0)
  const corLoading = ref(false)
  const corUploadedCount = ref(0)
  const corCurrentStudent = ref('')
  const corSuccess = ref(0)
  const corFail = ref(0)
  const corFailed = ref([])
  const corSkipExisting = ref(0)
  const uploadFinished = ref(false)

  const corParsePercent = computed(() => corFileTotal.value ? Math.round(corParsedCount.value / corFileTotal.value * 100) : 0)
  const corValidCount = computed(() => corFiles.value.filter(i => i.ok).length)
  const corParseFailCount = computed(() => corFiles.value.filter(i => !i.ok).length)
  const corUnnamedCount = computed(() => corFiles.value.filter(i => i.ok && !(i.studentName || '').trim()).length)
  const corPercent = computed(() => corValidCount.value ? Math.round(corUploadedCount.value / corValidCount.value * 100) : 0)
  const corBeforeTotal = computed(() => corFiles.value.filter(i => i.ok).reduce((s, i) => s + (i.before || '').length, 0))
  const corAfterTotal = computed(() => corFiles.value.filter(i => i.ok).reduce((s, i) => s + (i.after || '').length, 0))

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

  async function parseDocxContent(file) {
    const fullText = await readDocxText(file)
    const { before, after } = splitBeforeAfterText(fullText)
    return {
      title: extractTitleFromText(fullText),
      studentName: extractNameFromText(fullText),
      before,
      after,
    }
  }

  function studentNameFromFilename(file) {
    const nameWithoutExt = file.name.replace(/\.(docx|doc)$/i, '')
    let dashIndex = nameWithoutExt.indexOf('——')
    if (dashIndex === -1) dashIndex = nameWithoutExt.indexOf('-')
    if (dashIndex === -1) return ''
    return nameWithoutExt.substring(dashIndex + (nameWithoutExt.charAt(dashIndex) === '—' ? 2 : 1)).trim()
  }

  async function onCorFolderChange(e) {
    const files = Array.from(e.target.files)
    if (files.length === 0) return
    uploadFinished.value = false

    const parsed = []
    let docRejected = 0
    const docxFiles = files.filter(f => {
      const ext = '.' + f.name.split('.').pop().toLowerCase()
      if (ext === '.doc') { docRejected++; return false }
      return ext === '.docx'
    })
    if (docxFiles.length === 0) {
      showToast(docRejected ? `${docRejected} 个 .doc 旧版文件不支持，请另存为 .docx` : '未找到 docx 文件')
      return
    }

    corParsing.value = true
    corParsedCount.value = 0
    corFileTotal.value = docxFiles.length

    for (const file of docxFiles) {
      const fnameName = studentNameFromFilename(file)
      try {
        const { title, studentName: docName, before, after } = await parseDocxContent(file)
        if (!before && !after) {
          parsed.push({ file, studentName: fnameName || docName || '', ok: false, error: '未识别到「修改前：/修改后：」内容' })
        } else {
          parsed.push({ file, studentName: fnameName || docName || '', title, before, after, ok: true })
        }
      } catch (err) {
        parsed.push({ file, studentName: fnameName || '', ok: false, error: '文件解析失败（不支持 .doc 旧格式或文件损坏）' })
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

    if (onFolderSelected) onFolderSelected(files)
  }

  function removeCorFile(idx) {
    corFiles.value.splice(idx, 1)
    if (!corFiles.value.length) corFolderSelected.value = false
  }

  function buildCorrectionFormData(item) {
    const ctx = contextRef.value
    const fd = new FormData()
    if (ctx.taskId) {
      fd.append('task_id', String(ctx.taskId))
    }
    if (ctx.courseId) {
      fd.append('course_id', String(ctx.courseId))
    }
    fd.append('grade', ctx.form.grade)
    const essayNumber = parseInt(ctx.form.essay_number)
    fd.append('essay_number', isNaN(essayNumber) || essayNumber <= 0 ? '0' : String(essayNumber))
    fd.append('teaching_mode', ctx.form.teaching_mode)
    fd.append('student_name', item.studentName)
    fd.append('essay_title', item.title || '')
    fd.append('content_text', item.before || '')
    fd.append('corrected_text', item.after || '')
    fd.append('is_supplement', ctx.form.is_supplement ? 'true' : 'false')
    fd.append('collector_note', ctx.form.collector_note || '')
    if (ctx.form.collect_time) {
      fd.append('collect_time', ctx.form.collect_time)
    }
    if (ctx.markCorrected) {
      fd.append('mark_corrected', 'true')
    }
    fd.append('file', item.file)
    if (ctx.collectorId) {
      fd.append('collected_by', String(ctx.collectorId))
    }
    return fd
  }

  async function uploadCorrections(items, skipCount = 0) {
    corLoading.value = true
    corUploadedCount.value = skipCount
    corSuccess.value = 0
    corFail.value = 0
    corSkipExisting.value = skipCount
    corCurrentStudent.value = ''
    corFailed.value = []
    uploadFinished.value = false

    await runConcurrent(items, async (item) => {
      corCurrentStudent.value = item.studentName
      try {
        await api.post('/essays/upload-correction-docx', buildCorrectionFormData(item), { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 })
        corSuccess.value++
      } catch (err) {
        corFail.value++
        corFailed.value.push({ studentName: item.studentName, detail: err.response?.data?.detail || err.message })
      } finally {
        corUploadedCount.value++
      }
    })

    corLoading.value = false
    uploadFinished.value = corFailed.value.length === 0

    const failed = corFailed.value
    let body = `成功：${corSuccess.value} 个\n跳过已存在：${corSkipExisting.value} 个` + (corParseFailCount.value ? `\n解析失败跳过：${corParseFailCount.value} 个` : '')
    if (failed.length) {
      body += `\n失败：${failed.length} 个\n\n` + failed.map(f => `· ${f.studentName}${f.detail ? '：' + f.detail : ''}`).join('\n')
    }
    if (onResult) onResult({
      title: failed.length ? '上传完成（有失败）' : '上传成功',
      body,
      canRetry: failed.length > 0,
      retryCount: failed.length,
      mode: 'correction',
      retryNames: failed.map(f => f.studentName),
    })
  }

  async function upload() {
    let items = corFiles.value.filter(i => i.ok)
    const unnamed = items.filter(i => !(i.studentName || '').trim())
    if (unnamed.length) {
      showToast(`有 ${unnamed.length} 个文件未识别学生姓名，请在预览中填写后再上传`)
      return
    }
    let skipCount = 0
    const existingNames = contextRef.value.existingNames || []
    if (contextRef.value.preCheckExisting && existingNames.length) {
      skipCount = items.filter(i => existingNames.includes(i.studentName)).length
      items = items.filter(i => !existingNames.includes(i.studentName))
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

  async function retryFailed(names) {
    const nameSet = new Set(names)
    await uploadCorrections(corFiles.value.filter(i => nameSet.has(i.studentName)))
  }

  function reset() {
    corFiles.value = []
    corFolderSelected.value = false
    corParsing.value = false
    corLoading.value = false
    uploadFinished.value = false
    corSuccess.value = 0
    corFail.value = 0
    corFailed.value = []
    corSkipExisting.value = 0
  }

  return {
    corFiles, corFolderSelected, corParsing, corParsedCount, corFileTotal, corParsePercent,
    corValidCount, corParseFailCount, corUnnamedCount, corBeforeTotal, corAfterTotal,
    corLoading, corUploadedCount,
    corCurrentStudent, corSuccess, corFail, corFailed, corSkipExisting, corPercent, uploadFinished,
    onCorFolderChange, removeCorFile, upload, uploadCorrections, retryFailed, reset,
  }
}
