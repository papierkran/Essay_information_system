<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">系统设置</div>

    <div class="card" style="max-width:600px">
      <div class="card-header"><h3>⚙️ 上传存储目录</h3></div>
      <div class="form-group">
        <label>文件存储路径（相对或绝对）</label>
        <input v-model="uploadDir" placeholder="uploads" style="width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px" />
        <p style="font-size:12px;color:#999;margin-top:6px">
          当前实际路径：<code style="background:#f5f5f5;padding:2px 6px;border-radius:4px">{{ resolvedPath }}</code>
        </p>
      </div>
      <div class="form-actions" style="justify-content:flex-start">
        <button class="btn btn-primary" @click="saveSettings" :disabled="saving">
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
        <span v-if="saved" style="font-size:13px;color:#52c41a;margin-left:8px">✅ 已保存</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api from '../api'

const { isDesktop } = useScreen()
const uploadDir = ref('uploads')
const resolvedPath = ref('')
const saving = ref(false)
const saved = ref(false)

onMounted(async () => {
  try {
    const res = await api.get('/admin/settings')
    uploadDir.value = res.data.upload_dir || 'uploads'
    resolvedPath.value = res.data._resolved_path || ''
  } catch {}
})

async function saveSettings() {
  saving.value = true
  saved.value = false
  try {
    await api.put('/admin/settings', { upload_dir: uploadDir.value })
    saved.value = true
    showToast('设置已保存（重启后端生效）')
  } catch(err) {
    showToast(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
    setTimeout(() => { saved.value = false }, 3000)
  }
}
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { padding: 16px; } }
</style>
