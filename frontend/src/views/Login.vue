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
        <div v-for="acct in savedAccounts" :key="acct.key" class="saved-account-item" @click="switchTo(acct)">
          <span class="account-info">{{ acct.user?.nickname || acct.user?.username || '未知' }}</span>
          <span class="account-role">{{ roleLabel(acct.user?.role) }}</span>
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
    </div>
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
const keyName = ref('')
const loading = ref(false)

const { saveAuth } = useAuth()

// 列出所有已保存的账号
const savedAccounts = computed(() => {
  const accounts = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key?.startsWith('auth_')) {
      try {
        const data = JSON.parse(localStorage.getItem(key))
        accounts.push({ key: key.replace('auth_', ''), ...data })
      } catch {}
    }
  }
  return accounts
})

function roleLabel(r) { const m = { admin:'管理员', collector:'收集者', reviewer:'批改者' }; return (r||'').split(',').map(x=>m[x]||x).join(' + ') }

function switchTo(acct) {
  setActiveAuth(acct.key)
  showToast(`切换到 ${acct.user?.nickname || acct.user?.username}`)
  router.push('/dashboard')
}

async function onLogin() {
  loading.value = true
  try {
    const res = await api.post('/auth/login', { username: username.value, password: password.value })
    const key = keyName.value.trim() || username.value
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

.account-info { font-size: 14px; font-weight: 500; }
.account-role { font-size: 12px; color: #999; }

.login-desktop .login-card { max-width: 420px; padding: 40px 32px; }
</style>
