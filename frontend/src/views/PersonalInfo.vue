<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">个人信息</div>

    <!-- 用户信息卡 -->
    <div class="card profile-card">
      <div class="profile-avatar">{{ avatarEmoji }}</div>
      <div class="profile-info">
        <div class="profile-name">{{ info.nickname || info.username }}</div>
        <div class="profile-meta">
          <span class="role-tag" :class="'role-' + r" v-for="r in roleList" :key="r">{{ roleLabel(r) }}</span>
          <span class="profile-username">@{{ info.username }}</span>
        </div>
        <div class="profile-sub" v-if="info.created_at">加入时间：{{ formatDate(info.created_at) }}</div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="quick-links">
      <router-link v-if="canCollect" to="/essay/upload" class="quick-link">📤 上传作文</router-link>
      <router-link v-if="canReview" to="/review/pending" class="quick-link">📝 未改列表</router-link>
      <router-link to="/essay/list" class="quick-link">📋 作文列表</router-link>
      <router-link to="/stats" class="quick-link">📊 数据统计</router-link>
    </div>

    <!-- 收集统计（收集者/管理员） -->
    <div class="card" v-if="canCollect">
      <div class="card-header"><h3>📤 我的收集</h3></div>
      <div class="stats-grid">
        <div class="stat-item"><span class="stat-num">{{ stats.collected_total || 0 }}</span><span class="stat-label">共收集</span></div>
        <div class="stat-item"><span class="stat-num num-orange">{{ stats.collected_pending || 0 }}</span><span class="stat-label">未修改</span></div>
        <div class="stat-item"><span class="stat-num num-blue">{{ stats.collected_confirming || 0 }}</span><span class="stat-label">待确认</span></div>
        <div class="stat-item"><span class="stat-num num-pink">{{ stats.collected_rework || 0 }}</span><span class="stat-label">待重改</span></div>
        <div class="stat-item"><span class="stat-num num-green">{{ stats.collected_corrected || 0 }}</span><span class="stat-label">已修改</span></div>
        <div class="stat-item"><span class="stat-num">{{ stats.uploaded_today || 0 }}</span><span class="stat-label">今日上传</span></div>
      </div>
    </div>

    <!-- 批改统计（批改者/管理员） -->
    <div class="card" v-if="canReview">
      <div class="card-header"><h3>✏️ 我的批改</h3></div>
      <div class="stats-grid">
        <div class="stat-item"><span class="stat-num">{{ stats.reviewed_total || 0 }}</span><span class="stat-label">共批改</span></div>
        <div class="stat-item"><span class="stat-num num-blue">{{ stats.reviewed_confirming || 0 }}</span><span class="stat-label">待确认</span></div>
        <div class="stat-item"><span class="stat-num num-pink">{{ stats.reviewed_rework || 0 }}</span><span class="stat-label">待重改</span></div>
        <div class="stat-item"><span class="stat-num num-green">{{ stats.reviewed_corrected || 0 }}</span><span class="stat-label">已确认</span></div>
        <div class="stat-item"><span class="stat-num">{{ stats.reviewed_today || 0 }}</span><span class="stat-label">今日批改</span></div>
      </div>
      <div v-if="stats.todo_total > 0" class="todo-hint">
        <span>📝 当前全系统还有 <strong>{{ stats.todo_total }}</strong> 篇待处理作文</span>
        <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" @click="goPending">去未改列表</button>
      </div>
    </div>

    <!-- 系统总览（管理员/游客） -->
    <div class="card" v-if="isAdmin || isGuest">
      <div class="card-header"><h3>🏫 系统总览</h3></div>
      <div class="stats-grid">
        <div class="stat-item"><span class="stat-num">{{ stats.sys_total || 0 }}</span><span class="stat-label">作文总数</span></div>
        <div class="stat-item"><span class="stat-num num-orange">{{ stats.sys_pending || 0 }}</span><span class="stat-label">未修改</span></div>
        <div class="stat-item"><span class="stat-num num-blue">{{ stats.sys_confirming || 0 }}</span><span class="stat-label">待确认</span></div>
        <div class="stat-item"><span class="stat-num num-pink">{{ stats.sys_rework || 0 }}</span><span class="stat-label">待重改</span></div>
        <div class="stat-item"><span class="stat-num num-green">{{ stats.sys_corrected || 0 }}</span><span class="stat-label">已修改</span></div>
      </div>
    </div>

    <!-- 近期操作 -->
    <div class="card">
      <div class="card-header">
        <h3>🕐 我的近期操作</h3>
        <router-link to="/review/operations" class="link-more">查看全部 ›</router-link>
      </div>
      <div v-if="recentOps.length" class="ops-list">
        <div v-for="op in recentOps" :key="op.id" class="op-item">
          <span class="tag" :class="opActionClass(op.action)">{{ op.action }}</span>
          <span class="op-text">{{ op.student_name ? op.student_name + ' · ' : '' }}{{ op.essay_title || op.detail || '作文操作' }}</span>
          <span class="op-time">{{ formatDateTime(op.created_at) }}</span>
        </div>
      </div>
      <div v-else class="empty-hint">暂无操作记录</div>
    </div>

    <!-- 桌面端 -->
    <template v-if="isDesktop">
      <div class="card" style="max-width:520px;margin-top:16px">
        <div class="card-header"><h3>👤 基本信息</h3></div>
        <div class="form-group"><label>用户名</label><input :value="info.username" disabled class="edit-input" /></div>
        <div class="form-group"><label>角色</label><input :value="info.role || ''" disabled class="edit-input" /></div>
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
        <van-cell title="角色" :value="roleList.map(roleLabel).join(' + ')" />
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
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDateTime, formatDate } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth, saveAuth } = useAuth()

const info = computed(() => getAuth()?.user || {})
const roles = computed(() => (info.value.role || '').split(',').filter(Boolean))
const isAdmin = computed(() => roles.value.includes('admin'))
const isGuest = computed(() => roles.value.includes('guest'))
const canCollect = computed(() => isAdmin.value || roles.value.includes('collector'))
const canReview = computed(() => isAdmin.value || roles.value.includes('reviewer'))
const roleList = computed(() => roles.value.length ? roles.value : ['collector'])

function roleLabel(r) {
  const labels = { admin: '管理员', collector: '收集者', reviewer: '修改者', guest: '游客' }
  return labels[r] || r
}

const avatarEmoji = computed(() => {
  if (isAdmin.value) return '👑'
  if (isGuest.value) return '👀'
  if (canReview.value) return '✏️'
  if (canCollect.value) return '📤'
  return '👤'
})

const stats = ref({})
const recentOps = ref([])
const form = ref({ nickname: info.value.nickname || '', phone: info.value.phone || '' })
const pwd = ref({ old_password: '', new_password: '', confirm: '' })
const savingProfile = ref(false)
const savingPwd = ref(false)

function opActionClass(action) {
  const m = { '上传': 'tag-pending', '认领': 'tag-correcting', '修改': 'tag-corrected', '编辑': 'tag-correcting', '删除': 'tag-pending', '恢复': 'tag-corrected', '批改': 'tag-corrected', 'OCR': 'tag-correcting' }
  return m[action] || ''
}

function goPending() {
  router.push('/review/pending')
}

onMounted(async () => {
  try {
    const res = await api.get('/essays/my-stats')
    stats.value = res.data
  } catch {}
  try {
    const res = await api.get('/essays/operations', { params: { user_id: info.value.id, page_size: 10 } })
    recentOps.value = res.data.items || []
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
.profile-card {
  display: flex;
  align-items: center;
  gap: 16px;
}
.profile-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #eef4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  flex: none;
}
.profile-info {
  min-width: 0;
}
.profile-name {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 6px;
}
.profile-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 4px;
}
.role-tag {
  font-size: 12px;
  padding: 1px 10px;
  border-radius: 10px;
  line-height: 20px;
}
.role-admin { background: #fff1f0; color: #ff4d4f; }
.role-collector { background: #e6f4ff; color: #1677ff; }
.role-reviewer { background: #f9f0ff; color: #722ed1; }
.role-guest { background: #f5f5f5; color: #666; }
.profile-username { font-size: 12px; color: #999; }
.profile-sub { font-size: 12px; color: #aaa; }

.quick-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}
.quick-link {
  flex: 1;
  min-width: 110px;
  background: #fff;
  border-radius: 10px;
  padding: 12px 8px;
  text-align: center;
  font-size: 13px;
  color: #333;
  text-decoration: none;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: all 0.15s;
}
.quick-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  color: #1677ff;
}

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
.num-orange { color: #d46b08; }
.num-blue { color: #1677ff; }
.num-pink { color: #eb2f96; }
.num-green { color: #52c41a; }
.stat-label {
  font-size: 12px;
  color: #888;
}

.todo-hint {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fff7e6;
  border-radius: 8px;
  font-size: 13px;
  color: #d46b08;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.link-more {
  font-size: 13px;
  color: #1677ff;
  text-decoration: none;
}
.ops-list {
  display: flex;
  flex-direction: column;
}
.op-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 0;
  border-bottom: 1px dashed #f0f0f0;
  font-size: 13px;
}
.op-item:last-child { border-bottom: none; }
.op-text {
  flex: 1;
  min-width: 0;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.op-time {
  font-size: 12px;
  color: #aaa;
  flex: none;
}
.empty-hint {
  padding: 24px 0;
  text-align: center;
  color: #999;
  font-size: 13px;
}

@media (max-width: 600px) {
  .stats-grid {
    gap: 8px;
  }
  .stat-num {
    font-size: 20px;
  }
  .quick-link {
    min-width: 90px;
  }
}
</style>
