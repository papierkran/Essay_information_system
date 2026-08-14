<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">个人信息</div>

    <!-- 统计信息 -->
    <div class="card" style="max-width:520px">
      <div class="card-header"><h3>📊 我的统计</h3></div>
      <div class="stats-grid">
        <div class="stat-item"><span class="stat-num">{{ stats.collected_total }}</span><span class="stat-label">我收集的作文</span></div>
        <div class="stat-item"><span class="stat-num">{{ stats.collected_pending }}</span><span class="stat-label">未修改</span></div>
        <div class="stat-item"><span class="stat-num">{{ stats.collected_corrected }}</span><span class="stat-label">已修改</span></div>
        <div class="stat-item"><span class="stat-num">{{ stats.reviewed_total }}</span><span class="stat-label">我批改的作文</span></div>
        <div class="stat-item"><span class="stat-num">{{ stats.reviewed_corrected }}</span><span class="stat-label">批改已确认</span></div>
        <div class="stat-item"><span class="stat-num">{{ stats.uploaded_today }}</span><span class="stat-label">今日上传</span></div>
      </div>
    </div>

    <!-- 桌面端 -->
    <template v-if="isDesktop">
      <div class="card" style="max-width:520px;margin-top:16px">
        <div class="card-header"><h3>👤 基本信息</h3></div>
        <div class="form-group"><label>用户名</label><input :value="info.username" disabled class="edit-input" /></div>
        <div class="form-group"><label>角色</label><input :value="roleLabel" disabled class="edit-input" /></div>
        <div class="form-group"><label>昵称</label><input v-model="form.nickname" class="edit-input" placeholder="输入昵称" /></div>
        <div class="form-group"><label>手机号</label><input v-model="form.phone" class="edit-input" placeholder="输入手机号" /></div>
        <button class="btn btn-primary" @click="saveProfile" :disabled="savingProfile">{{ savingProfile ? '保存中...' : '💾 保存资料' }}</button>
      </div>

      <div class="card" style="max-width:520px;margin-top:16px">
        <div class="card-header"><h3>🔒 修改密码</h3></div>
        <div class="form-group"><label>原密码</label><input v-model="pwd.old_password" type="password" class="edit-input" /></div>
        <div class="form-group"><label>新密码</label><input v-model="pwd.new_password" type="password" class="edit-input" placeholder="至少4位" /></div>
        <div class="form-group"><label>确认新密码</label><input v-model="pwd.confirm" type="password" class="edit-input" /></div>
        <button class="btn btn-primary" @click="savePassword" :disabled="savingPwd">{{ savingPwd ? '提交中...' : '🔒 修改密码' }}</button>
      </div>
    </template>

    <!-- 手机端 -->
    <template v-else>
      <van-cell-group inset style="margin-top:12px">
        <van-cell title="用户名" :value="info.username" />
        <van-cell title="角色" :value="roleLabel" />
        <van-field v-model="form.nickname" label="昵称" placeholder="输入昵称" />
        <van-field v-model="form.phone" label="手机号" placeholder="输入手机号" />
      </van-cell-group>
      <div style="margin:16px">
        <van-button round block type="primary" @click="saveProfile" :loading="savingProfile">💾 保存资料</van-button>
      </div>

      <van-cell-group inset>
        <van-field v-model="pwd.old_password" type="password" label="原密码" placeholder="输入原密码" />
        <van-field v-model="pwd.new_password" type="password" label="新密码" placeholder="至少4位" />
        <van-field v-model="pwd.confirm" type="password" label="确认新密码" placeholder="再次输入新密码" />
      </van-cell-group>
      <div style="margin:16px">
        <van-button round block type="primary" @click="savePassword" :loading="savingPwd">🔒 修改密码</van-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'

const { isDesktop } = useScreen()
const { getAuth, saveAuth } = useAuth()

const info = computed(() => getAuth()?.user || {})
const roleLabel = computed(() => {
  const labels = { admin: '管理员', collector: '收集者', reviewer: '修改者', guest: '游客' }
  return (info.value.role || '').split(',').map(r => labels[r] || r).join(' + ')
})

const stats = ref({ collected_total: 0, collected_pending: 0, collected_corrected: 0, reviewed_total: 0, reviewed_corrected: 0, uploaded_today: 0 })
const form = ref({ nickname: info.value.nickname || '', phone: info.value.phone || '' })
const pwd = ref({ old_password: '', new_password: '', confirm: '' })
const savingProfile = ref(false)
const savingPwd = ref(false)

onMounted(async () => {
  try {
    const res = await api.get('/essays/my-stats')
    stats.value = res.data
  } catch {}
})

async function saveProfile() {
  savingProfile.value = true
  try {
    const res = await api.put('/admin/profile', form.value)
    const auth = getAuth()
    if (auth) {
      saveAuth({ ...auth, user: { ...auth.user, ...res.data } })
    }
    showToast('保存成功')
  } catch (err) {
    showToast(err.response?.data?.detail || '保存失败')
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  if (!pwd.value.old_password) { showToast('请输入原密码'); return }
  if (!pwd.value.new_password || pwd.value.new_password.length < 4) { showToast('新密码至少4位'); return }
  if (pwd.value.new_password !== pwd.value.confirm) { showToast('两次输入的新密码不一致'); return }
  savingPwd.value = true
  try {
    await api.put('/admin/profile/password', { old_password: pwd.value.old_password, new_password: pwd.value.new_password })
    showToast('密码修改成功，请重新登录')
    setTimeout(() => {
      localStorage.removeItem(`auth_${localStorage.getItem('activeAuth') || 'default'}`)
      window.location.hash = '#/login'
    }, 1500)
  } catch (err) {
    showToast(err.response?.data?.detail || '修改失败')
  } finally {
    savingPwd.value = false
  }
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.stat-item {
  background: #f6f8fb;
  border-radius: 8px;
  padding: 14px 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: #1677ff;
}
.stat-label {
  font-size: 12px;
  color: #888;
}
@media (max-width: 600px) {
  .stats-grid {
    gap: 8px;
  }
  .stat-num {
    font-size: 20px;
  }
}
</style>

