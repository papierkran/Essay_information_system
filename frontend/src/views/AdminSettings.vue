<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">系统设置</div>

    <div v-if="isDesktop" class="settings-nav">
      <button class="btn nav-btn" @click="scrollToSection('sec-db')">🗄️ 数据库</button>
      <button class="btn nav-btn" @click="scrollToSection('sec-server')">🌐 服务地址</button>
      <button class="btn nav-btn" @click="scrollToSection('sec-upload')">📁 存储目录</button>
      <button class="btn nav-btn" @click="scrollToSection('sec-ocr')">🔍 OCR</button>
      <button class="btn nav-btn" @click="scrollToSection('sec-fix')">✏️ 错别字修正</button>
      <button class="btn nav-btn" @click="scrollToSection('sec-edit')">✅ AI改作文</button>
      <button class="btn nav-btn" @click="scrollToSection('sec-backup')">🗄️ 备份</button>
    </div>

    <div class="settings-layout">
      <div class="card" id="sec-db">
        <div class="card-header"><h3>🗄️ 数据库连接</h3></div>
        <div class="form-group">
          <label>主机地址</label>
          <input v-model="dbHost" placeholder="192.168.31.245" />
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label>端口</label>
            <input v-model="dbPort" placeholder="5432" />
          </div>
          <div class="form-group">
            <label>数据库名</label>
            <input v-model="dbName" placeholder="essay_system" />
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="dbUser" placeholder="postgres" />
          </div>
          <div class="form-group">
            <label>密码</label>
            <input v-model="dbPass" type="password" placeholder="数据库密码" />
          </div>
        </div>
        <div class="form-group">
          <label>Docker 容器名</label>
          <input v-model="dockerContainer" placeholder="pg" />
          <p class="hint-text">数据库备份/恢复使用的 Docker 容器名称，留空则不使用 Docker</p>
        </div>
        <p class="hint-text" style="color:#999">修改后需重启后端服务生效。密码字段不会回显，留空则不修改。</p>
        <div class="form-actions" style="justify-content:flex-start">
          <button class="btn" @click="testDb" :disabled="dbTesting">
            {{ dbTesting ? '检测中...' : '🔍 检测连接' }}
          </button>
          <span v-if="dbTestResult" class="result-text" :class="dbTestResult.includes('正常') ? 'success-text' : 'error-text'">{{ dbTestResult }}</span>
        </div>
      </div>

      <div class="card" id="sec-server">
        <div class="card-header"><h3>🌐 后端服务地址</h3></div>
        <div class="form-group">
          <label>API 地址</label>
          <input v-model="apiBaseUrl" placeholder="http://192.168.31.158:8000" />
          <p class="hint-text">留空则使用默认地址（当前页面同源）。修改后刷新页面生效。</p>
        </div>
        <div class="form-actions" style="justify-content:flex-start">
          <button class="btn btn-primary" @click="saveApiUrl">
            {{ apiSaving ? '保存中...' : '保存' }}
          </button>
          <button class="btn" @click="testServer" :disabled="serverTesting">
            {{ serverTesting ? '检测中...' : '🔍 检测连接' }}
          </button>
          <span v-if="apiSaved" class="result-text success-text">✅ 已保存，请刷新页面</span>
          <span v-if="serverTestResult" class="result-text" :class="serverTestResult.includes('正常') ? 'success-text' : 'error-text'">{{ serverTestResult }}</span>
        </div>
      </div>

      <div class="card" id="sec-upload">
        <div class="card-header"><h3>📁 上传存储目录</h3></div>
        <div class="form-group">
          <label>文件存储路径（相对或绝对）</label>
          <input v-model="uploadDir" placeholder="uploads" />
          <p class="hint-text">
            当前实际路径：<code class="code-text">{{ resolvedPath }}</code>
          </p>
        </div>
        <div class="form-actions" style="justify-content:flex-start">
          <button class="btn btn-primary" @click="saveSettings" :disabled="saving">
            {{ saving ? '保存中...' : '保存设置' }}
          </button>
          <span v-if="saved" class="result-text success-text">✅ 已保存</span>
        </div>
      </div>

      <div class="card" id="sec-ocr">
        <div class="card-header"><h3>🔍 OCR 识别配置</h3></div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="ocrEnabled" />
            <span>启用 OCR 识别</span>
          </label>
        </div>
        <div class="form-group">
          <label>服务商</label>
          <select v-model="ocrProvider">
            <option value="xfyun">讯飞 OCR</option>
          </select>
        </div>
        <div class="form-group">
          <label>接口地址</label>
          <input v-model="ocrUrl" placeholder="https://api.xfyun.cn/v1/service/v1/ocr" />
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label>APPID</label>
            <input v-model="ocrAppid" placeholder="讯飞应用 APPID" />
          </div>
          <div class="form-group">
            <label>识别语言</label>
            <input v-model="ocrLanguage" placeholder="cn|en" />
          </div>
        </div>
        <div class="form-group">
          <label>API Key</label>
          <input v-model="ocrApiKey" type="password" placeholder="讯飞 API Key" />
        </div>
        <div class="form-actions" style="justify-content:flex-start">
          <button class="btn btn-primary" @click="saveOcrConfig" :disabled="ocrSaving">
            {{ ocrSaving ? '保存中...' : '💾 保存 OCR 配置' }}
          </button>
          <span v-if="ocrSaved" class="result-text success-text">✅ 已保存</span>
        </div>
      </div>

      <div class="card" id="sec-fix">
        <div class="card-header"><h3>✏️ 修改前 - AI 错别字修正</h3></div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="fixEnabled" />
            <span>启用</span>
          </label>
        </div>
        <div class="form-group">
          <label>服务商</label>
          <select v-model="fixProvider">
            <option value="deepseek">DeepSeek</option>
            <option value="openai">OpenAI</option>
          </select>
        </div>
        <div class="form-group">
          <label>API 地址</label>
          <input v-model="fixBaseUrl" :placeholder="fixProvider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'https://api.openai.com/v1'" />
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label>API Key</label>
            <input v-model="fixApiKey" type="password" placeholder="API Key" />
          </div>
          <div class="form-group">
            <label>模型</label>
            <input v-model="fixModel" :placeholder="fixProvider === 'deepseek' ? 'deepseek-chat' : 'gpt-4o-mini'" />
          </div>
        </div>
        <div class="form-group">
          <label>提示词</label>
          <textarea v-model="fixPrompt" rows="4" class="mono-textarea"></textarea>
          <p class="hint-text"><code class="code-text">{text}</code> 为文章占位符</p>
        </div>
        <div class="form-actions" style="justify-content:flex-start">
          <button class="btn btn-primary" @click="saveFixConfig" :disabled="fixSaving">{{ fixSaving ? '保存中...' : '💾 保存' }}</button>
          <span v-if="fixSaved" class="result-text success-text">✅ 已保存</span>
        </div>
      </div>

      <div class="card" id="sec-edit">
        <div class="card-header"><h3>✅ 修改后 - AI 改作文</h3></div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="editEnabled" />
            <span>启用</span>
          </label>
        </div>
        <div class="form-group">
          <label>服务商</label>
          <select v-model="editProvider">
            <option value="deepseek">DeepSeek</option>
            <option value="openai">OpenAI</option>
          </select>
        </div>
        <div class="form-group">
          <label>API 地址</label>
          <input v-model="editBaseUrl" :placeholder="editProvider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'https://api.openai.com/v1'" />
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label>API Key</label>
            <input v-model="editApiKey" type="password" placeholder="API Key" />
          </div>
          <div class="form-group">
            <label>模型</label>
            <input v-model="editModel" :placeholder="editProvider === 'deepseek' ? 'deepseek-chat' : 'gpt-4o-mini'" />
          </div>
        </div>
        <div class="form-group">
          <label>提示词</label>
          <textarea v-model="editPrompt" rows="4" class="mono-textarea"></textarea>
          <p class="hint-text"><code class="code-text">{text}</code> 为文章占位符</p>
        </div>
        <div class="form-group">
          <label>字数范围（留空则不限制）</label>
          <div class="range-group">
            <input v-model="editMinCount" type="number" min="0" placeholder="最小字数" />
            <span class="range-sep">~</span>
            <input v-model="editMaxCount" type="number" min="0" placeholder="最大字数" />
          </div>
        </div>
        <div class="form-actions" style="justify-content:flex-start">
          <button class="btn btn-primary" @click="saveEditConfig" :disabled="editSaving">{{ editSaving ? '保存中...' : '💾 保存' }}</button>
          <span v-if="editSaved" class="result-text success-text">✅ 已保存</span>
        </div>
      </div>

      <div class="card" id="sec-backup">
        <div class="card-header"><h3>🗄️ 数据库备份</h3></div>

        <div class="form-group">
          <label>备份频率</label>
          <select v-model="backupFrequency">
            <option value="never">停用</option>
            <option value="daily">每天</option>
            <option value="weekly">每周</option>
            <option value="manual">仅手动</option>
          </select>
          <p class="hint-text">自动备份需要后端常驻运行，定时任务由后端进程内调度</p>
        </div>

        <div class="form-group">
          <label>备份文件夹</label>
          <div class="folder-row">
            <input v-model="backupFolder" placeholder="留空则不启用服务器端备份" />
            <button class="btn" @click="resolveBackupFolder" :disabled="resolvingFolder">
              {{ resolvingFolder ? '检测中...' : '🔍 检测路径' }}
            </button>
          </div>
          <p v-if="resolvedBackupPath" class="hint-text">
            实际路径：<code class="code-text">{{ resolvedBackupPath }}</code>
          </p>
        </div>

        <div class="form-actions" style="justify-content:flex-start">
          <button class="btn btn-primary" @click="saveBackupConfig" :disabled="backupSaving">
            {{ backupSaving ? '保存中...' : '💾 保存备份配置' }}
          </button>
          <span v-if="backupSaved" class="result-text success-text">✅ 已保存</span>
        </div>

        <div style="border-top:1px solid #f0f0f0;margin:16px -24px 0;padding:16px 24px 0">
          <div class="backup-actions">
            <button class="btn btn-primary" @click="triggerBackup" :disabled="backingUp">
              {{ backingUp ? '备份中...' : '📥 立即备份' }}
            </button>
            <button class="btn" @click="exportDB" :disabled="exporting">
              {{ exporting ? '导出中...' : '⬇️ 下载备份' }}
            </button>
            <label class="btn import-btn">
              📤 导入恢复
              <input type="file" accept=".sql" style="display:none" @change="importDB" />
            </label>
          </div>
          <div class="checkbox-group">
            <input type="checkbox" id="backupExcludeImages" v-model="backupExcludeImages" />
            <label for="backupExcludeImages">不导出图片数据库（essay_images）</label>
          </div>
          <p v-if="backupMsg" class="result-text" style="margin-top:8px" :class="backupMsg.includes('失败') ? 'error-text' : 'success-text'">{{ backupMsg }}</p>
        </div>

        <div v-if="backupFiles.length > 0" style="border-top:1px solid #f0f0f0;margin:16px -24px 0;padding:16px 24px 0">
          <div style="font-size:13px;font-weight:600;color:#333;margin-bottom:12px">📂 已有备份文件</div>
          <table class="backup-table" v-if="isDesktop">
            <thead>
              <tr>
                <th>文件名</th>
                <th>大小</th>
                <th>备份时间</th>
                <th style="width:120px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in backupFiles" :key="f.filename">
                <td class="backup-filename">{{ f.filename }}</td>
                <td>{{ formatSize(f.size) }}</td>
                <td>{{ formatTime(f.modified) }}</td>
                <td>
                  <button class="btn" style="padding:3px 10px;font-size:12px" @click="downloadBackup(f.filename)">⬇️</button>
                  <button class="btn" style="padding:3px 10px;font-size:12px;margin-left:4px" @click="deleteBackup(f.filename)">🗑️</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else>
            <div v-for="f in backupFiles" :key="f.filename" class="backup-mobile-item">
              <div class="backup-mobile-info">
                <div class="backup-mobile-name">{{ f.filename }}</div>
                <div style="font-size:12px;color:#999">{{ formatSize(f.size) }} · {{ formatTime(f.modified) }}</div>
              </div>
              <div style="display:flex;gap:6px">
                <button class="btn" style="padding:3px 10px;font-size:12px" @click="downloadBackup(f.filename)">⬇️</button>
                <button class="btn" style="padding:3px 10px;font-size:12px" @click="deleteBackup(f.filename)">🗑️</button>
              </div>
            </div>
          </div>
          <p v-if="backupListMsg" style="font-size:12px;color:#999;margin-top:8px">{{ backupListMsg }}</p>
        </div>
      </div>
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
const backupMsg = ref('')
const backupExcludeImages = ref(false)
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

const backupFrequency = ref('never')
const backupFolder = ref('')
const resolvedBackupPath = ref('')
const resolvingFolder = ref(false)
const backupSaving = ref(false)
const backupSaved = ref(false)
const backingUp = ref(false)
const backupFiles = ref([])
const backupListMsg = ref('')

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

function normalizeTestUrl(u) {
  let url = (u || '').trim()
  if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'http://' + url
  }
  return url.replace(/\/+$/, '')
}

async function testServer() {
  serverTesting.value = true
  serverTestResult.value = ''
  const baseUrl = normalizeTestUrl(apiBaseUrl.value)
  try {
    const res = await fetch(baseUrl + '/api/admin/test-server', {
      headers: { 'Authorization': 'Bearer ' + (getAuth()?.token || '') }
    })
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
  const baseUrl = normalizeTestUrl(apiBaseUrl.value)
  try {
    const params = new URLSearchParams()
    if (dbHost.value) params.set('host', dbHost.value)
    if (dbPort.value) params.set('port', dbPort.value)
    if (dbUser.value) params.set('user', dbUser.value)
    if (dbPass.value) params.set('password', dbPass.value)
    if (dbName.value) params.set('database', dbName.value)
    const res = await fetch(baseUrl + '/api/admin/test-db?' + params.toString(), {
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

async function loadBackupConfig() {
  try {
    const res = await api.get('/admin/config/backup')
    const cfg = res.data.config_value || {}
    backupFrequency.value = cfg.frequency || 'never'
    backupFolder.value = cfg.folder || ''
    backupExcludeImages.value = !!cfg.exclude_images
  } catch {}
}

async function saveBackupConfig() {
  backupSaving.value = true; backupSaved.value = false
  try {
    await api.put('/admin/config/backup', {
      config_key: 'backup',
      config_value: {
        frequency: backupFrequency.value,
        folder: backupFolder.value,
        exclude_images: backupExcludeImages.value,
      },
    })
    backupSaved.value = true; showToast('备份配置已保存')
    setTimeout(() => backupSaved.value = false, 3000)
    await loadBackupList()
  } catch(err) { showToast(err.response?.data?.detail || '保存失败') }
  finally { backupSaving.value = false }
}

async function resolveBackupFolder() {
  resolvingFolder.value = true
  try {
    const res = await api.post('/admin/backup/resolve-folder', null, {
      params: { folder: backupFolder.value || '' },
    })
    resolvedBackupPath.value = res.data.resolved_path || ''
    if (res.data.exists) {
      showToast('✅ 路径有效')
    } else if (backupFolder.value) {
      showToast('⚠️ 路径不存在，将自动创建')
    }
  } catch(err) {
    showToast(err.response?.data?.detail || '检测路径失败')
  } finally {
    resolvingFolder.value = false
  }
}

async function triggerBackup() {
  backingUp.value = true; backupMsg.value = ''
  try {
    const res = await api.post('/admin/backup/trigger', null, {
      params: { exclude_images: backupExcludeImages.value },
    })
    backupMsg.value = '✅ ' + (res.data.message || '备份成功')
    await loadBackupList()
  } catch(err) {
    backupMsg.value = '❌ ' + (err.response?.data?.detail || err.message)
  } finally {
    backingUp.value = false
  }
}

async function loadBackupList() {
  try {
    const res = await api.get('/admin/backup/list')
    backupFiles.value = res.data.files || []
    backupListMsg.value = backupFiles.value.length === 0 ? '暂无备份文件' : ''
  } catch(err) {
    backupListMsg.value = '加载失败'
  }
}

async function downloadBackup(filename) {
  try {
    const res = await api.get(`/admin/backup/download/${filename}`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
    URL.revokeObjectURL(url)
  } catch(err) {
    showToast(err.response?.data?.detail || '下载失败')
  }
}

async function deleteBackup(filename) {
  const confirmed = await showConfirmDialog({
    title: '确认删除',
    message: `确定删除备份文件 ${filename} 吗？`,
  }).catch(() => false)
  if (!confirmed) return
  try {
    await api.delete(`/admin/backup/delete/${filename}`)
    showToast('已删除')
    await loadBackupList()
  } catch(err) {
    showToast(err.response?.data?.detail || '删除失败')
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return size.toFixed(1) + ' ' + units[i]
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(async () => {
  try {
    const res = await api.get('/admin/settings')
    uploadDir.value = res.data.upload_dir || 'uploads'
    resolvedPath.value = res.data._resolved_path || ''
    resolvedBackupPath.value = res.data._resolved_backup_path || ''
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
  await loadBackupConfig()
  await loadBackupList()
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
  exporting.value = true; backupMsg.value = ''
  try {
    const res = await api.get('/admin/database/export', { params: { exclude_images: backupExcludeImages.value }, responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url
    const ts = new Date().toISOString().slice(0,19).replace(/[:-]/g, '')
    a.download = `essay_system_backup_${ts}.sql`; a.click()
    URL.revokeObjectURL(url)
    backupMsg.value = backupExcludeImages.value ? '✅ 导出成功（不含图片数据库）' : '✅ 导出成功'
  } catch(err) { backupMsg.value = '❌ 导出失败: ' + (err.response?.data?.detail || err.message) }
  finally { exporting.value = false }
}

async function importDB(e) {
  const file = e.target.files[0]
  if (!file) return
  backupMsg.value = ''
  const confirmed = await showConfirmDialog({
    title: '确认导入数据库？',
    message: '将使用所选 SQL 文件恢复数据库，现有数据可能被覆盖。建议先导出备份，再执行导入。',
  }).catch(() => false)
  if (!confirmed) { e.target.value = ''; return }
  try {
    const fd = new FormData(); fd.append('file', file)
    const res = await api.post('/admin/database/import', fd)
    backupMsg.value = '✅ 导入成功，请重启后端'
  } catch(err) { backupMsg.value = '❌ 导入失败: ' + (err.response?.data?.detail || err.message) }
  finally { e.target.value = '' }
}
</script>

<style scoped>
.page { padding: 0; }

.settings-layout {
  max-width: 720px;
}

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
  font-size: 13px;
  padding: 5px 14px;
  border-radius: 16px;
  color: #555;
}
.nav-btn:hover { border-color: #1677ff; color: #1677ff; }

.card { scroll-margin-top: 70px; }

.hint-text {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
  line-height: 1.5;
}

.code-text {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}

.success-text { color: #52c41a; }
.error-text { color: #ff4d4f; }

.result-text {
  font-size: 13px;
  margin-left: 8px;
}

.checkbox-label {
  display: inline-flex !important;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.checkbox-label input[type="checkbox"] {
  width: auto;
  margin: 0;
}

.mono-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  font-family: monospace;
  outline: none;
  resize: vertical;
  transition: border-color 0.2s;
}
.mono-textarea:focus {
  border-color: #4096ff;
  box-shadow: 0 0 0 2px rgba(24,144,255,0.1);
}

.range-group {
  display: flex;
  gap: 8px;
  align-items: center;
}
.range-group input {
  width: 140px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  flex: none;
}
.range-group input:focus {
  border-color: #4096ff;
  box-shadow: 0 0 0 2px rgba(24,144,255,0.1);
}
.range-sep {
  color: #999;
  font-size: 14px;
}

.backup-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 16px;
  line-height: 1.5;
}

.backup-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.import-btn {
  cursor: pointer;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}
.checkbox-group label {
  font-size: 13px;
  color: #666;
  cursor: pointer;
}

.folder-row {
  display: flex;
  gap: 8px;
}
.folder-row input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.folder-row input:focus {
  border-color: #4096ff;
  box-shadow: 0 0 0 2px rgba(24,144,255,0.1);
}

.backup-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.backup-table th {
  text-align: left;
  padding: 8px 12px;
  background: #fafafa;
  font-weight: 600;
  color: #666;
  border-bottom: 1px solid #f0f0f0;
}
.backup-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f5f5f5;
}
.backup-table tr:hover td {
  background: #fafafa;
}
.backup-filename {
  font-family: monospace;
  font-size: 12px;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.backup-mobile-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}
.backup-mobile-item:last-child {
  border-bottom: none;
}
.backup-mobile-info {
  flex: 1;
  min-width: 0;
  margin-right: 12px;
}
.backup-mobile-name {
  font-size: 13px;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .settings-layout {
    max-width: none;
  }
  .range-group input {
    width: 100px;
  }
}
</style>