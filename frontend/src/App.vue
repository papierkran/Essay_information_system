<template>
  <div class="app-shell">
    <!-- 顶栏 -->
    <header v-if="!isLogin" class="app-header">
      <button class="menu-toggle" :title="isDesktop && sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'" @click="toggleSidebar">☰</button>
      <h1 class="app-title">📖 作文收集管理系统</h1>
      <div class="header-right">
        <span class="user-badge" v-if="user.username">
          <span class="user-name">{{ user.nickname || user.username }}</span>
          <span class="role-tag">{{ roleLabel }}</span>
        </span>
        <button v-if="!isLogin" class="btn-logout" @click="onLogout">退出</button>
      </div>
    </header>

    <!-- 遮罩 + 侧边栏 -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen=false"></div>
    <aside v-if="!isLogin" class="sidebar" :class="{ open: sidebarOpen, collapsed: isDesktop && sidebarCollapsed }">
      <nav>
        <router-link v-if="user.username" to="/dashboard" class="sidebar-link" @click="sidebarOpen=false">🏠 首页</router-link>
        <router-link v-if="user.username" to="/stats" class="sidebar-link" @click="sidebarOpen=false">📊 数据统计</router-link>
        <router-link v-if="canCollect" to="/essay/upload" class="sidebar-link" @click="sidebarOpen=false">✏️ 上传作文</router-link>
        <span v-else-if="isGuest" class="sidebar-link disabled" title="游客无上传权限" @click="showGuestToast">✏️ 上传作文</span>
        <router-link v-if="canCollect" to="/essay/batch-upload" class="sidebar-link" @click="sidebarOpen=false">📁 批量上传</router-link>
        <span v-else-if="isGuest" class="sidebar-link disabled" title="游客无上传权限" @click="showGuestToast">📁 批量上传</span>
        <router-link v-if="canViewList" to="/essay/list" class="sidebar-link" @click="sidebarOpen=false">📋 作文列表</router-link>
        <router-link v-if="canReview || isGuest" to="/review/pending" class="sidebar-link" @click="sidebarOpen=false">📝 未改列表</router-link>
        <router-link v-if="canViewTasks" to="/admin/tasks" class="sidebar-link" @click="sidebarOpen=false">📋 任务列表</router-link>
        <router-link v-if="isAdmin" to="/admin/course" class="sidebar-link" @click="sidebarOpen=false">📚 课程管理</router-link>
        <router-link v-if="user.username" to="/review/operations" class="sidebar-link" @click="sidebarOpen=false">🕐 操作历史</router-link>
        <router-link v-if="isAdmin" to="/admin/users" class="sidebar-link" @click="sidebarOpen=false">👥 用户管理</router-link>
        <router-link v-if="isAdmin" to="/admin/settings" class="sidebar-link" @click="sidebarOpen=false">⚙️ 系统设置</router-link>
      </nav>
    </aside>

    <!-- 主内容 -->
    <main :class="isLogin ? 'login-wrapper' : 'main-content' + (isDesktop && sidebarCollapsed ? ' sidebar-hidden' : '')">
      <router-view />
    </main>

    <TaskStatusBar v-if="!isLogin" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TaskStatusBar from './components/TaskStatusBar.vue'
import { showToast } from 'vant'
import { useAuth } from './api'
import { useScreen } from './composables/useScreen'

const route = useRoute()
const router = useRouter()
const { getAuth, clearAuth } = useAuth()
const { isDesktop } = useScreen()
const sidebarOpen = ref(false)
const sidebarCollapsed = ref(localStorage.getItem('appSidebarCollapsed') === '1')

function toggleSidebar() {
  if (isDesktop.value) {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('appSidebarCollapsed', sidebarCollapsed.value ? '1' : '0')
  } else {
    sidebarOpen.value = !sidebarOpen.value
  }
}

const isLogin = computed(() => route.path === '/login')

const auth = ref(getAuth())
const user = computed(() => auth.value?.user || {})

watch(() => route.path, () => {
  auth.value = getAuth()
  sidebarOpen.value = false
}, { immediate: true })

const userRole = computed(() => user.value.role || '')
const isAdmin = computed(() => userRole.value.includes('admin'))
const isGuest = computed(() => userRole.value.includes('guest'))
const canCollect = computed(() => userRole.value.includes('collector') || isAdmin.value)
const canReview = computed(() => userRole.value.includes('reviewer') || isAdmin.value)
const canViewList = computed(() => canCollect.value || canReview.value || isGuest.value)
const canViewTasks = computed(() => Boolean(userRole.value))
const roleLabel = computed(() => {
  const labels = { admin: '管理员', collector: '收集者', reviewer: '修改者', guest: '游客' }
  return (user.value.role || '').split(',').map(r => labels[r] || r).join(' + ')
})

function onLogout() {
  clearAuth()
  router.push('/login')
  showToast('已退出登录')
}

function showGuestToast() {
  showToast('游客无上传权限，仅可查看')
}
</script>

<style>
/* ===== Reset ===== */
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5;
  color: #333;
}

/* ===== 顶栏 ===== */
.app-header {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 48px;
  background: #1a1a2e;
  color: #fff;
  display: flex;
  align-items: center;
  padding: 0 16px;
  z-index: 200;
  gap: 12px;
}

.menu-toggle {
  background: none;
  border: none;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  display: block;
}
.menu-toggle:hover { color: #4096ff; }

.app-title { font-size: 16px; font-weight: 600; flex: 1; }

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-badge { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.user-name { color: rgba(255,255,255,0.9); }
.role-tag { font-size: 11px; color: rgba(255,255,255,0.5); }

.btn-logout {
  padding: 4px 12px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.3);
  background: transparent;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  font-size: 12px;
}
.btn-logout:hover { background: rgba(255,255,255,0.1); }

/* ===== 侧边栏 ===== */
.sidebar {
  position: fixed;
  top: 48px; left: 0; bottom: 0;
  width: 200px;
  background: #1a1a2e;
  z-index: 150;
  padding: 12px 0;
  overflow-y: auto;
  transition: transform 0.25s;
}

.sidebar-link {
  display: block;
  padding: 12px 20px;
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.15s;
  border-left: 3px solid transparent;
}
.sidebar-link:hover { background: rgba(255,255,255,0.06); color: #fff; }
.sidebar-link.router-link-exact-active { background: rgba(255,255,255,0.1); color: #fff; border-left-color: #4096ff; }
.sidebar-link.disabled { opacity: 0.4; cursor: not-allowed; }
.sidebar-link.disabled:hover { background: none; color: rgba(255,255,255,0.7); }

.sidebar-overlay {
  display: none;
  position: fixed;
  top: 48px; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 149;
}

@media (min-width: 768px) {
  .sidebar.collapsed { transform: translateX(-100%); }
}

/* ===== 主内容 ===== */
.main-content {
  margin-top: 48px;
  margin-left: 200px;
  min-height: calc(100vh - 48px);
  padding: 24px 32px;
  transition: margin-left 0.25s;
}

.main-content.sidebar-hidden { margin-left: 0; }

.login-wrapper {
  min-height: 100vh;
}

/* ===== 响应式：手机端 ===== */
@media (max-width: 767px) {
  .menu-toggle { display: block; }
  .sidebar {
    transform: translateX(-100%);
  }
  .sidebar.open {
    transform: translateX(0);
  }
  .sidebar-overlay { display: block; }
  .main-content {
    margin-left: 0;
    padding: 16px;
  }
  .user-name { display: none; }
}

/* ===== 公共组件样式 ===== */
.page-title { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #1a1a1a; }

.card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}
.card-header h3 { font-size: 15px; font-weight: 600; margin: 0; }

.desktop-table {
  width: 100%;
  min-width: max-content;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.desktop-table th {
  background: #fafafa;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: #666;
  border-bottom: 1px solid #f0f0f0;
  white-space: nowrap;
}
.desktop-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f5f5f5;
  font-size: 14px;
  white-space: nowrap;
}
.desktop-table tr:hover td { background: #fafafa; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #d9d9d9;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}
.btn:hover { border-color: #4096ff; color: #4096ff; }
.btn-primary { background: #1677ff; color: #fff; border-color: #1677ff; }
.btn-primary:hover { background: #4096ff; color: #fff; }
.btn-success { background: #52c41a; color: #fff; border-color: #52c41a; }
.btn-success:hover { background: #73d13d; color: #fff; }
.btn-danger { background: #ff4d4f; color: #fff; border-color: #ff4d4f; }
.btn-danger:hover { background: #ff7875; color: #fff; }

.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.tag-pending { background: #fff7e6; color: #d46b08; }
.tag-correcting { background: #e6f4ff; color: #1677ff; }
.tag-corrected { background: #f6ffed; color: #52c41a; }

/* 迷你徽标：年级/第几次/线上线下 可读性区分 */
.badge-mini {
  display: inline-block;
  padding: 0 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  line-height: 18px;
  margin-right: 4px;
}
.tag-grade { background: #f9f0ff; color: #722ed1; }
.tag-number { background: #fff7e6; color: #d46b08; }
.tag-mode-online { background: #f6ffed; color: #389e0d; }
.tag-mode-offline { background: #e6f4ff; color: #1677ff; }
.tag-course { background: #f0f5ff; color: #2f54eb; }

.form-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: #333; }
.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus { border-color: #4096ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.1); }
.form-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 16px; }

.empty-state { text-align: center; padding: 60px 20px; color: #999; }
.empty-state .icon { font-size: 48px; margin-bottom: 16px; }
.empty-state p { font-size: 14px; }

.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.45);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-box {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 520px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

/* ===== 手机端公共适配 ===== */
@media (max-width: 767px) {
  .page-title { font-size: 17px; margin-bottom: 16px; }
  .card { padding: 16px; }
  .form-grid-2 { grid-template-columns: 1fr; }
  .desktop-table { font-size: 13px; }
  .desktop-table th, .desktop-table td { padding: 8px 8px; }
  .modal-box { width: 95%; padding: 16px; }
}

/* ===== 全局 toast 样式加强 ===== */
.van-toast {
  font-size: 15px !important;
  font-weight: 500 !important;
  color: #333 !important;
  background: rgba(255,255,255,0.96) !important;
  box-shadow: 0 2px 12px rgba(0,0,0,0.12) !important;
  border-radius: 8px !important;
  padding: 16px 24px !important;
  min-width: 160px;
}

.van-toast__text {
  font-size: 15px !important;
  color: #333 !important;
}

/* ===== 桌面端覆盖 Vant 弹窗居中 ===== */
@media (min-width: 768px) {
  .van-popup--bottom {
    top: 50% !important;
    bottom: auto !important;
    left: 50% !important;
    right: auto !important;
    width: 90%;
    max-width: 680px;
    transform: translate(-50%, -50%);
    border-radius: 12px;
    max-height: 85vh;
  }
  .van-action-sheet { max-height: 85vh; }
  .van-action-sheet__header { text-align: center; }
  .van-dialog { width: 90%; max-width: 560px; }
}
</style>
