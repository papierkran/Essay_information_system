<template>
  <div class="page">
    <div v-if="isDesktop" class="page-title">上传作文</div>

    <!-- 模板选择区域 -->
    <van-cell-group inset style="margin-bottom:12px">
      <van-field :model-value="selectedTaskName" is-link readonly label="选择收集任务"
        placeholder="选择收集任务（自动填充年级等信息）" @click="showTaskPicker = true" />
      <!-- 显示选中模板的文章主题 -->
      <van-cell v-if="selectedTaskTopic" title="文章主题" :label="selectedTaskTopic" />
    </van-cell-group>

    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field :model-value="selectedGrade" is-link readonly label="年级"
          :placeholder="selectedGrade || '请选择年级（可暂不选择）'" @click="showGradePicker = true" />
        <van-field v-model="form.grade" v-show="false" />
        <van-field v-model="form.essay_number" label="第几次作文" placeholder="数字（不填表示无）" type="digit" />
        <van-field v-model="form.essay_title" label="作文标题" placeholder="输入标题" />
        <div v-if="recentTitles.length" style="padding:0 16px 8px;display:flex;flex-wrap:wrap;gap:6px">
          <van-tag v-for="t in recentTitles" :key="t" plain size="medium" @click="form.essay_title = t" style="cursor:pointer">{{ t }}</van-tag>
        </div>
        <van-field v-model="form.student_name" label="学生姓名" placeholder="输入姓名" :rules="[{ required: true }]" />
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
        <van-field name="uploader" label="上传文件（docx/图片，可多选）">
          <template #input>
            <div>
              <van-uploader v-model="fileList" :max-count="10" accept=".docx,.doc,.jpg,.jpeg,.png" multiple :before-read="beforeRead" :after-read="afterRead" />
              <div style="font-size:12px;color:#999;margin-top:4px">图片大小不超过 4MB</div>
            </div>
          </template>
        </van-field>
        <van-image-preview v-model:show="showPreview" :images="previewImages" :closeable="true" />
        <van-field v-model="form.content_text" label="或粘贴文字" type="textarea" placeholder="粘贴文字..." rows="4" autosize />
      </van-cell-group>
      <div style="margin:16px">
        <van-button round block type="primary" native-type="submit" :loading="loading">提交作文</van-button>
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
    <van-action-sheet v-model:show="showTaskPicker" title="选择收集任务">
      <div class="picker-list">
        <div style="padding:8px 16px">
          <input v-model="taskSearch" placeholder="搜索任务名称/主题/年级..." style="width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;outline:none" />
        </div>
        <van-cell title="不使用模板" @click="selectTask(null)" style="color:#999" />
        <div class="task-split">
          <div class="task-col">
            <div class="task-col-title">线上</div>
            <van-cell v-for="t in filteredOnlineTasks" :key="t.id"
              :title="t.name"
              :label="`${t.grade} 第${t.essay_number}次 ${t.essay_topic || ''}`"
              @click="selectTask(t)">
              <template #right-icon>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-right:8px">收集中</van-tag>
              </template>
            </van-cell>
            <div v-if="!filteredOnlineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线上任务</div>
          </div>
          <div class="task-col">
            <div class="task-col-title">线下</div>
            <van-cell v-for="t in filteredOfflineTasks" :key="t.id"
              :title="t.name"
              :label="`${t.grade} 第${t.essay_number}次 ${t.essay_topic || ''}`"
              @click="selectTask(t)">
              <template #right-icon>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-right:8px">收集中</van-tag>
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
import { useRoute } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'

const route = useRoute()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isAdmin = computed(() => (currentUser.value.role || '').includes('admin'))

const fileList = ref([])
const loading = ref(false)
const showGradePicker = ref(false)
const showTaskPicker = ref(false)
const showCollectorPicker = ref(false)
const showPreview = ref(false)
const previewImages = ref([])
const selectedGrade = ref('')
const selectedTaskName = ref('')
const selectedTaskTopic = ref('')
const selectedTaskId = ref(null)
const selectedCourseId = ref(null)
const selectedCollector = ref(null)
const selectedCollectorName = ref('')
const collectorList = ref([])
const recentTitles = ref([])
const grades = ['初一','初二','初三','高一','高二','高三']
const tasks = ref([])

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
  return t.is_active && (!t.deadline || new Date(t.deadline) >= new Date())
}

const form = ref({
  grade: '', essay_number: '', essay_title: '',
  student_name: '', is_supplement: false, teaching_mode: '线上', collector_note: '', content_text: '',
})

onMounted(async () => {
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

function beforeRead(file) {
  const imageExts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (imageExts.includes(ext) && file.size > 4 * 1024 * 1024) {
    showToast('图片大小不能超过 4MB')
    return false
  }
  return true
}

function afterRead(file) {
  previewImages.value = fileList.value
    .filter(item => item.file?.type?.startsWith('image/'))
    .map(item => item.objectUrl || URL.createObjectURL(item.file))
}

function selectTask(tpl) {
  if (tpl) {
    form.value.grade = tpl.grade
    selectedGrade.value = tpl.grade
    form.value.essay_number = String(tpl.essay_number)
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
    selectedTaskId.value = tpl.id
    selectedCourseId.value = tpl.course_id || null
    showToast(`已选择：${tpl.name}`)
  } else {
    selectedTaskName.value = ''
    selectedTaskTopic.value = ''
    selectedTaskId.value = null
    selectedCourseId.value = null
    showToast('已取消任务选择')
  }
  showTaskPicker.value = false
}

async function onSubmit() {
  if (!form.value.student_name) { showToast('请填写学生姓名'); return }
  loading.value = true
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
    fd.append('content_text', form.value.content_text)
    if (fileList.value.length > 0) {
      fileList.value.forEach(item => fd.append('files', item.file))
    }
    await api.post('/essays/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    showDialog({
      title: '✅ 上传成功',
      message: `学生：${form.value.student_name}\n年级：${form.value.grade || '暂不选择'}\n第${isNaN(essayNumber) || essayNumber <= 0 ? '无' : essayNumber}次\n提交方式：${form.value.teaching_mode}`,
      confirmButtonText: '继续上传',
      className: 'upload-success-dialog',
    })
    form.value = { grade: '', essay_number: '', essay_title: '', student_name: '', is_supplement: false, collector_note: '', content_text: '' }
    fileList.value = []
    selectedGrade.value = ''
    selectedTaskName.value = ''
    selectedTaskTopic.value = ''
    selectedTaskId.value = null
  } catch (err) {
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
          window.location.hash = '#/essays'
        }
      })
      return
    }

    showDialog({
      title: '❌ 上传失败',
      message: msg,
      confirmButtonText: '知道了',
      className: 'upload-msg-dialog',
    })
  }
  finally { loading.value = false }
}
</script>

<style scoped>
.page { padding: 16px; }
.picker-list { max-height: 70vh; overflow-y: auto; }

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

:deep(.upload-success-dialog .van-dialog__message) {
  white-space: pre-line;
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}
</style>
