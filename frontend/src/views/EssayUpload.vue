<template>
  <div class="page">
    <div v-if="isDesktop" class="page-title">上传作文</div>

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

    <van-action-sheet v-model:show="showGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectGrade(g)" />
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { showToast, showDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api from '../api'

const { isDesktop } = useScreen()
const fileList = ref([])
const loading = ref(false)
const showGradePicker = ref(false)
const selectedGrade = ref('')
const grades = ['初一','初二','初三','高一','高二','高三']

const form = ref({
  class_id: 1, grade: '', essay_number: '', essay_title: '',
  student_name: '', is_supplement: false, teaching_mode: '线上', remark: '', content_text: '',
})

function selectGrade(g) {
  form.value.grade = g
  selectedGrade.value = g
  showGradePicker.value = false
}

async function onSubmit() {
  if (!form.value.grade) { showToast('请选择年级'); return }
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('class_id', '1')
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
      message: `学生：${form.value.student_name}\n年级：${form.value.grade}\n第${form.value.essay_number || 1}次`,
      confirmButtonText: '继续上传',
      className: 'upload-success-dialog',
    })
    form.value = { class_id: 1, grade: '', essay_number: '', essay_title: '', student_name: '', is_supplement: false, remark: '', content_text: '' }
    fileList.value = []
    selectedGrade.value = ''
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
