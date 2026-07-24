<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">系统设置</div>

    <div class="card" style="max-width:600px">
      <div class="card-header"><h3>🗄️ 数据库连接</h3></div>
      <div class="form-group">
        <label>主机地址</label>
        <input v-model="dbHost" placeholder="192.168.31.245" class="input" />
      </div>
      <div class="form-group">
        <label>端口</label>
        <input v-model="dbPort" placeholder="5432" class="input" />
      </div>
      <div class="form-group">
        <label>用户名</label>
        <input v-model="dbUser" placeholder="postgres" class="input" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="dbPass" type="password" placeholder="数据库密码" class="input" />
      </div>
      <div class="form-group">
        <label>数据库名</label>
        <input v-model="dbName" placeholder="essay_system" class="input" />
      </div>
      <p style="font-size:12px;color:#999;margin-top:6px">
        修改后需重启后端服务生效。密码字段不会回显，留空则不修改。
      </p>
      <div class="form-actions" style="justify-content:flex-start">
        <button class="btn" @click="testDb" :disabled="dbTesting">
          {{ dbTesting ? '检测中...' : '🔍 检测连接' }}
        </button>
        <span v-if="dbTestResult" style="font-size:13px;margin-left:8px" :class="dbTestResult.includes('正常') ? 'success-text' : 'error-text'">{{ dbTestResult }}</span>
      </div>
    </div>

    <div class="card" style="max-width:600px;margin-top:20px">
      <div class="card-header"><h3>🌐 后端服务地址</h3></div>
      <div class="form-group">
        <label>API 地址</label>
        <input v-model="apiBaseUrl" placeholder="http://192.168.31.158:8000" class="input" />
        <p style="font-size:12px;color:#999;margin-top:6px">
          留空则使用默认地址（当前页面同源）。修改后刷新页面生效。
        </p>
      </div>
      <div class="form-actions" style="justify-content:flex-start">
        <button class="btn btn-primary" @click="saveApiUrl">
          {{ apiSaving ? '保存中...' : '保存' }}
        </button>
        <button class="btn" @click="testServer" :disabled="serverTesting" style="margin-left:8px">
          {{ serverTesting ? '检测中...' : '🔍 检测连接' }}
        </button>
        <span v-if="apiSaved" style="font-size:13px;color:#52c41a;margin-left:8px">✅ 已保存，请刷新页面</span>
        <span v-if="serverTestResult" style="font-size:13px;margin-left:8px" :class="serverTestResult.includes('正常') ? 'success-text' : 'error-text'">{{ serverTestResult }}</span>
      </div>
    </div>

    <div class="card" style="max-width:600px;margin-top:20px">
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

    <div class="card" style="max-width:600px;margin-top:20px">
      <div class="card-header"><h3>🗄️ 数据库备份</h3></div>
      <p style="font-size:13px;color:#666;margin-bottom:16px">导出当前全部数据为 SQL 文件，或导入 SQL 文件恢复数据。</p>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <button class="btn btn-primary" @click="exportDB" :disabled="exporting">
          {{ exporting ? '导出中...' : '📥 导出数据库' }}
        </button>
        <label class="btn" style="cursor:pointer">
          📤 导入数据库
          <input type="file" accept=".sql" style="display:none" @change="importDB" />
        </label>
      </div>
      <p v-if="dbMsg" style="font-size:13px;margin-top:12px" :class="dbMsg.includes('成功') ? 'success-text' : 'error-text'">{{ dbMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'

const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const uploadDir = ref('uploads')
const resolvedPath = ref('')
const dbHost = ref('')
const dbPort = ref('5432')
const dbUser = ref('')
const dbPass = ref('')
const dbName = ref('')
const saving = ref(false)
const saved = ref(false)
const exporting = ref(false)
const dbMsg = ref('')
const apiBaseUrl = ref(localStorage.getItem('apiBaseUrl') || '')
const apiSaving = ref(false)
const apiSaved = ref(false)
const serverTesting = ref(false)
const serverTestResult = ref('')
const dbTesting = ref(false)
const dbTestResult = ref('')

function saveApiUrl() {
  apiSaving.value = true
  apiSaved.value = false
  if (apiBaseUrl.value) {
    localStorage.setItem('apiBaseUrl', apiBaseUrl.value)
  } else {
    localStorage.removeItem('apiBaseUrl')
  }
  apiSaving.value = false
  apiSaved.value = true
  setTimeout(() => apiSaved.value = false, 3000)
}

async function testServer() {
  serverTesting.value = true
  serverTestResult.value = ''
  try {
    const saved = localStorage.getItem('apiBaseUrl')
    const baseUrl = saved ? saved.replace(/\/+$/, '') : ''
    const res = await fetch(baseUrl + '/api/admin/test-server')
    const data = await res.json()
    if (res.ok) {
      serverTestResult.value = '✅ ' + data.message
    } else {
      serverTestResult.value = '❌ ' + (data.detail || '连接失败')
    }
  } catch (err) {
    serverTestResult.value = '❌ 连接失败: ' + err.message
  } finally {
    serverTesting.value = false
  }
}

async function testDb() {
  dbTesting.value = true
  dbTestResult.value = ''
  try {
    const saved = localStorage.getItem('apiBaseUrl')
    const baseUrl = saved ? saved.replace(/\/+$/, '') : ''
    const res = await fetch(baseUrl + '/api/admin/test-db', {
      headers: { 'Authorization': 'Bearer ' + (getAuth()?.token || '') }
    })
    const data = await res.json()
    if (res.ok) {
      dbTestResult.value = '✅ ' + data.message
    } else {
      dbTestResult.value = '❌ ' + (data.detail || '连接失败')
    }
  } catch (err) {
    dbTestResult.value = '❌ 连接失败: ' + err.message
  } finally {
    dbTesting.value = false
  }
}

onMounted(async () => {
  try {
    const res = await api.get('/admin/settings')
    uploadDir.value = res.data.upload_dir || 'uploads'
    resolvedPath.value = res.data._resolved_path || ''
    const dbInfo = res.data._db_info || {}
    dbHost.value = dbInfo.host || ''
    dbPort.value = dbInfo.port || '5432'
    dbUser.value = dbInfo.user || ''
    dbName.value = dbInfo.database || ''
  } catch {}
})

async function saveSettings() {
  saving.value = true; saved.value = false
  const payload = { upload_dir: uploadDir.value, database: {} }
  if (dbHost.value) payload.database.host = dbHost.value
  if (dbPort.value) payload.database.port = dbPort.value
  if (dbUser.value) payload.database.user = dbUser.value
  if (dbPass.value) payload.database.password = dbPass.value
  if (dbName.value) payload.database.database = dbName.value
  try {
    await api.put('/admin/settings', payload)
    saved.value = true; showToast('设置已保存（重启后端生效）')
  } catch(err) { showToast(err.response?.data?.detail || '保存失败') }
  finally { saving.value = false; setTimeout(() => saved.value = false, 3000) }
}

async function exportDB() {
  exporting.value = true; dbMsg.value = ''
  try {
    const res = await api.get('/admin/database/export', { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url
    const ts = new Date().toISOString().slice(0,19).replace(/[:-]/g, '')
    a.download = `essay_system_backup_${ts}.sql`; a.click()
    URL.revokeObjectURL(url)
    dbMsg.value = '✅ 导出成功'
  } catch(err) { dbMsg.value = '❌ 导出失败: ' + (err.response?.data?.detail || err.message) }
  finally { exporting.value = false }
}

async function importDB(e) {
  const file = e.target.files[0]
  if (!file) return
  dbMsg.value = ''
  try {
    const fd = new FormData(); fd.append('file', file)
    const res = await api.post('/admin/database/import', fd)
    dbMsg.value = '✅ 导入成功，请重启后端'
  } catch(err) { dbMsg.value = '❌ 导入失败: ' + (err.response?.data?.detail || err.message) }
  finally { e.target.value = '' }
}
</script>

<style scoped>
.page { padding: 0; }
.input { width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px; }
.success-text { color: #52c41a; }
.error-text { color: #ff4d4f; }
@media (max-width: 767px) { .page { padding: 16px; } }
</style>
