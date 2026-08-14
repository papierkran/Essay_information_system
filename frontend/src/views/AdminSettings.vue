<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">系统设置</div>

    <!-- 分区锚点导航 -->
    <div v-if="isDesktop" class="settings-nav">
      <button class="nav-btn" @click="scrollToSection('sec-db')">🗄️ 数据库</button>
      <button class="nav-btn" @click="scrollToSection('sec-server')">🌐 服务地址</button>
      <button class="nav-btn" @click="scrollToSection('sec-upload')">📁 存储目录</button>
      <button class="nav-btn" @click="scrollToSection('sec-ocr')">🔍 OCR</button>
      <button class="nav-btn" @click="scrollToSection('sec-fix')">✏️ 错别字修正</button>
      <button class="nav-btn" @click="scrollToSection('sec-edit')">✅ AI改作文</button>
      <button class="nav-btn" @click="scrollToSection('sec-backup')">🗄️ 备份</button>
    </div>

    <div class="card" id="sec-db" style="max-width:600px">
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
      <div class="form-group">
        <label>Docker 容器名</label>
        <input v-model="dockerContainer" placeholder="pg" class="input" />
        <p style="font-size:12px;color:#999;margin-top:6px">
          数据库备份/恢复使用的 Docker 容器名称，默认为 pg
        </p>
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

    <div class="card" id="sec-server" style="max-width:600px;margin-top:20px">
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

    <div class="card" id="sec-upload" style="max-width:600px;margin-top:20px">
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

    <div class="card" id="sec-ocr" style="max-width:600px;margin-top:20px">
      <div class="card-header"><h3>🔍 OCR 识别配置</h3></div>
      <div class="form-group">
        <label>
          <input type="checkbox" v-model="ocrEnabled" />
          启用 OCR 识别
        </label>
      </div>
      <div class="form-group">
        <label>服务商</label>
        <select v-model="ocrProvider" class="input">
          <option value="xfyun">讯飞 OCR</option>
        </select>
      </div>
      <div class="form-group">
        <label>接口地址（URL）</label>
        <input v-model="ocrUrl" placeholder="https://api.xfyun.cn/v1/service/v1/ocr" class="input" />
      </div>
      <div class="form-group">
        <label>APPID</label>
        <input v-model="ocrAppid" placeholder="讯飞应用 APPID" class="input" />
      </div>
      <div class="form-group">
        <label>API Key</label>
        <input v-model="ocrApiKey" type="password" placeholder="讯飞 API Key" class="input" />
      </div>
      <div class="form-group">
        <label>识别语言</label>
        <input v-model="ocrLanguage" placeholder="cn|en" class="input" />
      </div>
      <div class="form-actions" style="justify-content:flex-start">
        <button class="btn btn-primary" @click="saveOcrConfig" :disabled="ocrSaving">
          {{ ocrSaving ? '保存中...' : '💾 保存 OCR 配置' }}
        </button>
        <span v-if="ocrSaved" style="font-size:13px;color:#52c41a;margin-left:8px">✅ 已保存</span>
      </div>
    </div>

    <div class="card" id="sec-fix" style="max-width:600px;margin-top:20px">
      <div class="card-header"><h3>✏️ 修改前 - AI 错别字修正</h3></div>
      <div class="form-group">
        <label><input type="checkbox" v-model="fixEnabled" /> 启用</label>
      </div>
      <div class="form-group">
        <label>服务商</label>
        <select v-model="fixProvider" class="input">
          <option value="deepseek">DeepSeek</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      <div class="form-group">
        <label>API 地址</label>
        <input v-model="fixBaseUrl" :placeholder="fixProvider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'https://api.openai.com/v1'" class="input" />
      </div>
      <div class="form-group">
        <label>API Key</label>
        <input v-model="fixApiKey" type="password" placeholder="API Key" class="input" />
      </div>
      <div class="form-group">
        <label>模型</label>
        <input v-model="fixModel" :placeholder="fixProvider === 'deepseek' ? 'deepseek-chat' : 'gpt-4o-mini'" class="input" />
      </div>
      <div class="form-group">
        <label>提示词</label>
        <textarea v-model="fixPrompt" rows="4" class="input" style="resize:vertical;font-family:monospace"></textarea>
        <p style="font-size:12px;color:#999;margin-top:4px"><code>{text}</code> 为文章占位符</p>
      </div>
      <div class="form-actions" style="justify-content:flex-start">
        <button class="btn btn-primary" @click="saveFixConfig" :disabled="fixSaving">{{ fixSaving ? '保存中...' : '💾 保存' }}</button>
        <span v-if="fixSaved" style="font-size:13px;color:#52c41a;margin-left:8px">✅ 已保存</span>
      </div>
    </div>

    <div class="card" id="sec-edit" style="max-width:600px;margin-top:20px">
      <div class="card-header"><h3>✅ 修改后 - AI 改作文</h3></div>
      <div class="form-group">
        <label><input type="checkbox" v-model="editEnabled" /> 启用</label>
      </div>
      <div class="form-group">
        <label>服务商</label>
        <select v-model="editProvider" class="input">
          <option value="deepseek">DeepSeek</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
      <div class="form-group">
        <label>API 地址</label>
        <input v-model="editBaseUrl" :placeholder="editProvider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'https://api.openai.com/v1'" class="input" />
      </div>
      <div class="form-group">
        <label>API Key</label>
        <input v-model="editApiKey" type="password" placeholder="API Key" class="input" />
      </div>
      <div class="form-group">
        <label>模型</label>
        <input v-model="editModel" :placeholder="editProvider === 'deepseek' ? 'deepseek-chat' : 'gpt-4o-mini'" class="input" />
      </div>
      <div class="form-group">
        <label>提示词</label>
        <textarea v-model="editPrompt" rows="4" class="input" style="resize:vertical;font-family:monospace"></textarea>
        <p style="font-size:12px;color:#999;margin-top:4px"><code>{text}</code> 为文章占位符</p>
      </div>
      <div class="form-group">
        <label>字数范围（留空则不限制）</label>
        <div style="display:flex;gap:8px;align-items:center">
          <input v-model="editMinCount" type="number" min="0" placeholder="最小字数" class="input" style="width:120px;flex:none" />
          <span style="color:#999">~</span>
          <input v-model="editMaxCount" type="number" min="0" placeholder="最大字数" class="input" style="width:120px;flex:none" />
        </div>
      </div>
      <div class="form-actions" style="justify-content:flex-start">
        <button class="btn btn-primary" @click="saveEditConfig" :disabled="editSaving">{{ editSaving ? '保存中...' : '💾 保存' }}</button>
        <span v-if="editSaved" style="font-size:13px;color:#52c41a;margin-left:8px">✅ 已保存</span>
      </div>
    </div>

    <div class="card" id="sec-backup" style="max-width:600px;margin-top:20px">
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
      <div style="margin-top:12px;display:flex;align-items:center;gap:6px">
        <input type="checkbox" id="excludeImages" v-model="excludeImages" />
        <label for="excludeImages" style="font-size:13px;color:#666">不导出图片数据库（essay_images）</label>
      </div>
      <p v-if="dbMsg" style="font-size:13px;margin-top:12px" :class="dbMsg.includes('成功') ? 'success-text' : 'error-text'">{{ dbMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'

const { isDesktop } = useScreen()
const { getAuth } = useAuth()

function scrollToSection(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
const uploadDir = ref('uploads')
const resolvedPath = ref('')
const dbHost = ref('')
const dbPort = ref('5432')
const dbUser = ref('')
const dbPass = ref('')
const dbName = ref('')
const dockerContainer = ref('pg')
const saving = ref(false)
const saved = ref(false)
const exporting = ref(false)
const dbMsg = ref('')
const excludeImages = ref(false)
const apiBaseUrl = ref(localStorage.getItem('apiBaseUrl') || '')
const apiSaving = ref(false)
const apiSaved = ref(false)
const serverTesting = ref(false)
const serverTestResult = ref('')
const dbTesting = ref(false)
const dbTestResult = ref('')
const ocrEnabled = ref(false)
const ocrProvider = ref('xfyun')
const ocrUrl = ref('')
const ocrAppid = ref('')
const ocrApiKey = ref('')
const ocrLanguage = ref('cn|en')
const ocrSaved = ref(false)
const ocrSaving = ref(false)

const fixEnabled = ref(false)
const fixProvider = ref('deepseek')
const fixBaseUrl = ref('')
const fixApiKey = ref('')
const fixModel = ref('')
const fixPrompt = ref('')
const fixSaved = ref(false)
const fixSaving = ref(false)

const editEnabled = ref(false)
const editProvider = ref('deepseek')
const editBaseUrl = ref('')
const editApiKey = ref('')
const editModel = ref('')
const editPrompt = ref('')
const editMinCount = ref('')
const editMaxCount = ref('')
const editSaved = ref(false)
const editSaving = ref(false)

function saveApiUrl() {
  apiSaving.value = true
  apiSaved.value = false
  let url = apiBaseUrl.value.trim()
  if (url) {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'http://' + url
    }
    localStorage.setItem('apiBaseUrl', url)
    apiBaseUrl.value = url
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

async function loadOcrConfig() {
  try {
    const res = await api.get('/admin/config/ocr')
    const cfg = res.data.config_value || {}
    ocrEnabled.value = !!cfg.enabled
    ocrProvider.value = cfg.provider || 'xfyun'
    const xf = cfg.xfyun || {}
    ocrUrl.value = xf.url || ''
    ocrAppid.value = xf.appid || ''
    ocrApiKey.value = xf.api_key || ''
    ocrLanguage.value = xf.language || 'cn|en'
  } catch {}
}

async function saveOcrConfig() {
  ocrSaving.value = true
  ocrSaved.value = false
  try {
    const cfg = {
      enabled: ocrEnabled.value,
      provider: ocrProvider.value,
      xfyun: {
        url: ocrUrl.value,
        appid: ocrAppid.value,
        api_key: ocrApiKey.value,
        language: ocrLanguage.value,
        location: "false",
      },
    }
    await api.put('/admin/config/ocr', { config_key: 'ocr', config_value: cfg })
    ocrSaved.value = true
    showToast('OCR 配置已保存')
    setTimeout(() => ocrSaved.value = false, 3000)
  } catch(err) {
    showToast(err.response?.data?.detail || '保存失败')
  } finally {
    ocrSaving.value = false
  }
}

async function loadFixConfig() {
  try {
    const res = await api.get('/admin/config/llm_typo_fix')
    const cfg = res.data.config_value || {}
    fixEnabled.value = !!cfg.enabled
    fixProvider.value = cfg.provider || 'deepseek'
    fixBaseUrl.value = cfg.base_url || ''
    fixApiKey.value = cfg.api_key || ''
    fixModel.value = cfg.model || ''
    fixPrompt.value = cfg.prompt || ''
  } catch {}
}

async function saveFixConfig() {
  fixSaving.value = true; fixSaved.value = false
  try {
    await api.put('/admin/config/llm_typo_fix', {
      config_key: 'llm_typo_fix',
      config_value: { enabled: fixEnabled.value, provider: fixProvider.value, base_url: fixBaseUrl.value, api_key: fixApiKey.value, model: fixModel.value, prompt: fixPrompt.value },
    })
    fixSaved.value = true; showToast('错别字修正配置已保存')
    setTimeout(() => fixSaved.value = false, 3000)
  } catch(err) { showToast(err.response?.data?.detail || '保存失败') }
  finally { fixSaving.value = false }
}

async function loadEditConfig() {
  try {
    const res = await api.get('/admin/config/llm_editor')
    const cfg = res.data.config_value || {}
    editEnabled.value = !!cfg.enabled
    editProvider.value = cfg.provider || 'deepseek'
    editBaseUrl.value = cfg.base_url || ''
    editApiKey.value = cfg.api_key || ''
    editModel.value = cfg.model || ''
    editPrompt.value = cfg.prompt || ''
    editMinCount.value = cfg.count_min !== undefined && cfg.count_min !== null ? String(cfg.count_min) : ''
    editMaxCount.value = cfg.count_max !== undefined && cfg.count_max !== null ? String(cfg.count_max) : ''
  } catch {}
}

async function saveEditConfig() {
  editSaving.value = true; editSaved.value = false
  const cfg = {
    enabled: editEnabled.value,
    provider: editProvider.value,
    base_url: editBaseUrl.value,
    api_key: editApiKey.value,
    model: editModel.value,
    prompt: editPrompt.value,
  }
  if (editMinCount.value !== '' && editMinCount.value !== null) {
    cfg.count_min = parseInt(editMinCount.value, 10)
  }
  if (editMaxCount.value !== '' && editMaxCount.value !== null) {
    cfg.count_max = parseInt(editMaxCount.value, 10)
  }
  try {
    await api.put('/admin/config/llm_editor', {
      config_key: 'llm_editor',
      config_value: cfg,
    })
    editSaved.value = true; showToast('改作文配置已保存')
    setTimeout(() => editSaved.value = false, 3000)
  } catch(err) { showToast(err.response?.data?.detail || '保存失败') }
  finally { editSaving.value = false }
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
    dockerContainer.value = dbInfo.docker_container || 'pg'
  } catch {}
  await loadOcrConfig()
  await loadFixConfig()
  await loadEditConfig()
})

async function saveSettings() {
  saving.value = true; saved.value = false
  const payload = { upload_dir: uploadDir.value, database: {} }
  if (dbHost.value) payload.database.host = dbHost.value
  if (dbPort.value) payload.database.port = dbPort.value
  if (dbUser.value) payload.database.user = dbUser.value
  if (dbPass.value) payload.database.password = dbPass.value
  if (dbName.value) payload.database.database = dbName.value
  if (dockerContainer.value) payload.database.docker_container = dockerContainer.value
  try {
    await api.put('/admin/settings', payload)
    saved.value = true; showToast('设置已保存（重启后端生效）')
  } catch(err) { showToast(err.response?.data?.detail || '保存失败') }
  finally { saving.value = false; setTimeout(() => saved.value = false, 3000) }
}

async function exportDB() {
  exporting.value = true; dbMsg.value = ''
  try {
    const res = await api.get('/admin/database/export', { params: { exclude_images: excludeImages.value }, responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url
    const ts = new Date().toISOString().slice(0,19).replace(/[:-]/g, '')
    a.download = `essay_system_backup_${ts}.sql`; a.click()
    URL.revokeObjectURL(url)
    dbMsg.value = excludeImages.value ? '✅ 导出成功（不含图片数据库）' : '✅ 导出成功'
  } catch(err) { dbMsg.value = '❌ 导出失败: ' + (err.response?.data?.detail || err.message) }
  finally { exporting.value = false }
}

async function importDB(e) {
  const file = e.target.files[0]
  if (!file) return
  dbMsg.value = ''
  const confirmed = await showConfirmDialog({
    title: '确认导入数据库？',
    message: '将使用所选 SQL 文件恢复数据库，现有数据可能被覆盖。建议先导出备份，再执行导入。',
  }).catch(() => false)
  if (!confirmed) { e.target.value = ''; return }
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

.settings-nav {
  position: sticky;
  top: 56px;
  z-index: 20;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
  margin-bottom: 8px;
  background: #f0f2f5;
}
.nav-btn {
  padding: 5px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 16px;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
  color: #555;
  transition: all 0.15s;
}
.nav-btn:hover { border-color: #1677ff; color: #1677ff; }
.card { scroll-margin-top: 70px; }
@media (max-width: 767px) { .page { padding: 0; } }
</style>
