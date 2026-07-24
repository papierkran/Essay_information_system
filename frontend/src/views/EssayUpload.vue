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
          :placeholder="selectedGrade || '请选择年级'" @click="showGradePicker = true" :rules="[{ required: true }]" />
        <van-field v-model="form.grade" v-show="false" />
        <van-field v-model="form.essay_number" label="第几次作文" placeholder="数字" type="digit" :rules="[{ required: true }]" />
        <van-field v-model="form.essay_title" label="作文标题" placeholder="输入标题" />
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
        <van-field v-model="form.remark" label="备注" placeholder="备注信息（可选）" />
      </van-cell-group>
      <van-cell-group inset style="margin-top:12px">
        <van-field name="uploader" label="上传文件（docx/图片，可多选）">
          <template #input>
            <van-uploader v-model="fileList" :max-count="10" accept=".docx,.doc,.jpg,.jpeg,.png" multiple />
          </template>
        </van-field>
        <van-field v-model="form.content_text" label="或粘贴文字" type="textarea" placeholder="粘贴文字..." rows="4" autosize />
      </van-cell-group>
      <div style="margin:16px">
        <van-button round block type="primary" native-type="submit" :loading="loading">提交作文</van-button>
      </div>
    </van-form>

    <!-- 年级选择器 -->
    <van-action-sheet v-model:show="showGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectGrade(g)" />
      </div>
    </van-action-sheet>

    <!-- 模板选择器 -->
    <van-action-sheet v-model:show="showTaskPicker" title="选择收集任务">
      <div class="picker-list">
        <van-cell title="不使用模板" @click="selectTask(null)" style="color:#999" />
        <van-cell v-for="t in tasks" :key="t.id"
          :title="t.name"
          :label="`${t.grade} 第${t.essay_number}次 ${t.essay_topic || ''}`"
          @click="selectTask(t)">
          <template #right-icon>
            <van-tag v-if="t.is_active" type="primary" style="margin-right:8px">收集中</van-tag>
          </template>
        </van-cell>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showToast, showDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api from '../api'

const route = useRoute()
const { isDesktop } = useScreen()
const fileList = ref([])
const loading = ref(false)
const showGradePicker = ref(false)
const showTaskPicker = ref(false)
const selectedGrade = ref('')
const selectedTaskName = ref('')
const selectedTaskTopic = ref('')
const selectedTaskId = ref(null)
const grades = ['初一','初二','初三','高一','高二','高三']
const tasks = ref([])

const form = ref({
  class_id: 1, grade: '', essay_number: '', essay_title: '',
  student_name: '', is_supplement: false, teaching_mode: '线上', remark: '', content_text: '',
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
})

function selectGrade(g) {
  form.value.grade = g
  selectedGrade.value = g
  showGradePicker.value = false
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
    selectedTaskName.value = tpl.name
    selectedTaskTopic.value = tpl.essay_topic || ''
    selectedTaskId.value = tpl.id
    showToast(`已选择：${tpl.name}`)
  } else {
    selectedTaskName.value = ''
    selectedTaskTopic.value = ''
    selectedTaskId.value = null
    showToast('已取消任务选择')
  }
  showTaskPicker.value = false
}

async function onSubmit() {
  if (!form.value.grade) { showToast('请选择年级'); return }
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('class_id', '1')
    if (selectedTaskId.value) {
      fd.append('task_id', String(selectedTaskId.value))
    }
    fd.append('grade', form.value.grade)
    fd.append('essay_number', form.value.essay_number || 1)
    fd.append('essay_title', form.value.essay_title)
    fd.append('student_name', form.value.student_name)
    fd.append('is_supplement', form.value.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', form.value.teaching_mode)
    fd.append('remark', form.value.remark)
    fd.append('content_text', form.value.content_text)
    if (fileList.value.length > 0) {
      fileList.value.forEach(item => fd.append('files', item.file))
    }
    await api.post('/essays/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    showDialog({
      title: '✅ 上传成功',
      message: `学生：${form.value.student_name}\n年级：${form.value.grade}\n第${form.value.essay_number || 1}次\n提交方式：${form.value.teaching_mode}`,
      confirmButtonText: '继续上传',
      className: 'upload-success-dialog',
    })
    form.value = { class_id: 1, grade: '', essay_number: '', essay_title: '', student_name: '', is_supplement: false, remark: '', content_text: '' }
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
.picker-list { max-height: 300px; overflow-y: auto; }

:deep(.upload-msg-dialog) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
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
