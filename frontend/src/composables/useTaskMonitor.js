import { ref } from 'vue'
import api from '../api'
import { showSuccessToast } from 'vant'

const tasks = ref([])
let pollTimer = null

export function useTaskMonitor() {
  function addTask(taskId, type, total) {
    tasks.value.push({
      id: taskId,
      type,
      total,
      success: 0,
      errors: [],
      status: 'running',
      message: '',
      current: '',
      stage: '',
    })
    startPolling()
  }

  function addTasks(taskList) {
    for (const t of taskList) {
      tasks.value.push({
        id: t.id,
        type: t.type,
        total: t.total || 0,
        success: 0,
        errors: [],
        status: 'running',
        message: '',
        current: '',
        stage: '',
      })
    }
    startPolling()
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(async () => {
      const running = tasks.value.filter(t => t.status === 'running')
      if (!running.length) {
        stopPolling()
        return
      }
      for (const t of running) {
        try {
          const res = await api.get(`/essays/batch-task/${t.id}`)
          const d = res.data
          Object.assign(t, {
            status: d.status,
            success: d.success,
            errors: d.errors,
            total: d.total,
            message: d.message,
            current: d.current || '',
            stage: d.stage || '',
          })
          if (d.status === 'completed' && d.errors.length === 0) {
            showSuccessToast(`[${typeLabel(t.type)}] 完成：${d.success}/${d.total}`)
          }
        } catch {}
      }
    }, 2000)
  }

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  }

  function dismissTask(taskId) {
    const idx = tasks.value.findIndex(t => t.id === taskId)
    if (idx >= 0) tasks.value.splice(idx, 1)
  }

  function dismissAll() {
    tasks.value = []
  }

  return { tasks, addTask, addTasks, dismissTask, dismissAll }
}

export function typeLabel(type) {
  return { ocr: 'OCR识别', ai_correct: 'AI错别字修正', ai_rewrite: 'AI一键修改', pipeline: '流水线修改' }[type] || type
}
