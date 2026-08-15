<template>
  <div class="login-page" :class="{ 'login-desktop': isDesktop }">
    <div class="login-card">
      <div class="login-header">
        <h1>📖 作文收集管理系统</h1>
        <p>登录后开始使用</p>
      </div>

      <!-- 已有账号列表 -->
      <div v-if="savedAccounts.length > 0" style="margin-bottom:16px">
        <div class="saved-accounts-title">已保存的账号</div>
        <div v-for="acct in savedAccounts" :key="acct.key" class="saved-account-item" :class="{ 'account-expired-item': acct.expired }" @click="switchTo(acct)">
          <span class="account-info">{{ acct.user?.nickname || acct.user?.username || '未知' }}</span>
          <span class="account-role">{{ roleLabel(acct.user?.role) }}</span>
          <span v-if="acct.expired" class="account-expired-tag">已过期</span>
          <span class="account-remove" title="删除该账号记录" @click.stop="removeAccount(acct.key)">✕</span>
        </div>
      </div>

      <van-form @submit="onLogin">
        <van-cell-group inset>
          <van-field v-model="username" name="username" label="用户名" placeholder="请输入用户名" :rules="[{required:true,message:'请输入用户名'}]" />
          <van-field v-model="password" type="password" name="password" label="密码" placeholder="请输入密码" :rules="[{required:true,message:'请输入密码'}]" />
        </van-cell-group>
        <div style="margin:16px">
          <van-button round block type="primary" native-type="submit" :loading="loading">登录</van-button>
        </div>
      </van-form>

      <div class="server-config" @click="showServerConfig = true">
        ⚙️ 设置服务器地址
      </div>

      <div v-if="serverUrl" class="server-hint">
        当前：{{ serverUrl }}
      </div>
    </div>

    <van-dialog v-model:show="showServerConfig" title="设置服务器地址">
      <div style="padding:16px">
        <div style="font-size:13px;color:#666;margin-bottom:12px">
          如果无法连接服务器，请在此设置后端地址。
        </div>
        <input v-model="serverUrlInput" placeholder="https://zwhd.papierkran.top" style="width:100%;padding:10px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px" />
        <div style="font-size:12px;color:#999;margin-top:8px">留空则使用默认地址</div>
        <div style="display:flex;gap:12px;margin-top:16px">
          <button class="btn" style="flex:1" @click="showServerConfig = false">取消</button>
          <button class="btn btn-primary" style="flex:1" @click="saveServerUrl">保存</button>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth, setActiveAuth } from '../api'

const router = useRouter()
const { isDesktop } = useScreen()
const username = ref('')
const password = ref('')
const loading = ref(false)
const showServerConfig = ref(false)
const serverUrlInput = ref(localStorage.getItem('apiBaseUrl') || '')
const serverUrl = ref(localStorage.getItem('apiBaseUrl') || '')

const { saveAuth } = useAuth()

function saveServerUrl() {
  let url = (serverUrlInput.value || '').trim()
  if (url) {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'http://' + url
    }
    localStorage.setItem('apiBaseUrl', url)
  } else {
    localStorage.removeItem('apiBaseUrl')
  }
  serverUrl.value = url
  showServerConfig.value = false
  window.location.reload()
}

// 列出所有已保存的账号
const savedAccounts = computed(() => {
  const accounts = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key?.startsWith('auth_')) {
      try {
        const data = JSON.parse(localStorage.getItem(key))
        accounts.push({ key: key.replace('auth_', ''), ...data, expired: accountExpired(data) })
      } catch {}
    }
  }
  return accounts
})

function roleLabel(r) { const m = { admin:'管理员', collector:'收集者', reviewer:'修改者' }; return (r||'').split(',').map(x=>m[x]||x).join(' + ') }

function jwtExpiryMs(token) {
  if (!token || typeof token !== 'string') return null
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    let b64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    while (b64.length % 4) b64 += '='
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0))
    const data = JSON.parse(new TextDecoder().decode(bytes))
    return typeof data.exp === 'number' ? data.exp * 1000 : null
  } catch { return null }
}

function accountExpired(acct) {
  const exp = jwtExpiryMs(acct?.token)
  return exp ? Date.now() > exp : false
}

function switchTo(acct) {
  if (acct.expired) {
    showToast('该账号登录已过期，请重新登录')
    return
  }
  setActiveAuth(acct.key)
  showToast(`切换到 ${acct.user?.nickname || acct.user?.username}`)
  router.push('/dashboard')
}

function removeAccount(key) {
  localStorage.removeItem('auth_' + key)
  if ((localStorage.getItem('activeAuth') || 'default') === key) {
    localStorage.removeItem('activeAuth')
  }
  showToast('已删除该账号记录')
}

async function onLogin() {
  loading.value = true
  try {
    const res = await api.post('/auth/login', { username: username.value, password: password.value })
    const key = username.value
    setActiveAuth(key)
    saveAuth({ token: res.data.access_token, user: res.data.user })
    showToast('登录成功')
    router.push('/dashboard')
  } catch(err) { showToast(err.response?.data?.detail || '登录失败') }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 36px 28px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.login-header { text-align: center; margin-bottom: 28px; }
.login-header h1 { font-size: 22px; margin-bottom: 6px; color: #1a1a1a; }
.login-header p { color: #999; font-size: 13px; }

.saved-accounts-title { font-size: 13px; color: #999; margin-bottom: 8px; }

.saved-account-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.saved-account-item:hover { background: #eef1f5; }

.account-info { font-size: 14px; font-weight: 500; flex: 1; }
.account-role { font-size: 12px; color: #999; }

.account-remove {
  width: 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  border-radius: 50%;
  color: #999;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.account-remove:hover { background: #ff4d4f; color: #fff; }

.account-expired-tag {
  font-size: 11px;
  color: #fff;
  background: #ff4d4f;
  border-radius: 4px;
  padding: 1px 6px;
  margin-right: 4px;
}
.account-expired-item { opacity: 0.6; }

.login-desktop .login-card { max-width: 420px; padding: 40px 32px; }

.server-config {
  text-align: center;
  font-size: 13px;
  color: #1677ff;
  cursor: pointer;
  margin-top: 12px;
  padding: 8px;
}

.server-config:hover { text-decoration: underline; }

.server-hint {
  text-align: center;
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  word-break: break-all;
}
</style>
