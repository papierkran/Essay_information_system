<template>
  <div class="dashboard-page">
    <div class="dashboard-toolbar">
      <div v-if="isDesktop" class="page-title">工作台</div>
      <div class="mode-filter">
        <button class="filter-pill" :class="{ active: taskFilter === '' }" @click="taskFilter = ''">全部</button>
        <button class="filter-pill" :class="{ active: taskFilter === '线上' }" @click="taskFilter = '线上'">线上</button>
        <button class="filter-pill" :class="{ active: taskFilter === '线下' }" @click="taskFilter = '线下'">线下</button>
      </div>
    </div>

    <!-- 当前收集任务 -->
    <div v-if="sortedActiveTasks.length > 0">
      <div v-for="tpl in sortedActiveTasks" :key="tpl.id" class="card active-task-card" @click="goUploadWithTask(tpl)">
        <div class="card-header">
          <h3>📝 {{ tpl.name }}</h3>
          <span class="task-status">收集中</span>
        </div>
        <div v-if="tpl.essay_topic" class="task-topic-highlight">作文主题：{{ tpl.essay_topic }}</div>
        <div class="task-info">
            <div class="task-main">
              <div class="task-meta">
                <span class="badge-mini tag-grade">{{ tpl.grade }}</span>
                <span class="badge-mini tag-number">第{{ tpl.essay_number }}次</span>
                <span class="badge-mini" :class="tpl.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ tpl.teaching_mode || '线下' }}</span>
                <span v-if="tpl.course_name" class="badge-mini tag-course">{{ tpl.course_name }}</span>
              </div>
            </div>
          <div class="task-stats">
            <div class="stat-item">
              <div class="stat-value">{{ tpl._stats?.total || 0 }}</div>
              <div class="stat-label">已收集</div>
            </div>
            <div class="stat-item">
              <div class="stat-value stat-green">{{ tpl._stats?.corrected || 0 }}</div>
              <div class="stat-label">已修改</div>
            </div>
            <div class="stat-item">
              <div class="stat-value stat-pink">{{ tpl._stats?.rework || 0 }}</div>
              <div class="stat-label">待重改</div>
            </div>
          </div>
        </div>
        <div v-if="tpl.deadline" class="task-deadline">
          <span class="deadline-icon">⏰</span>
          <span class="deadline-text">截止时间：{{ formatDeadline(tpl.deadline) }}</span>
          <span v-if="getDeadlineDaysLeft(tpl.deadline) >= 0" :class="['deadline-days', { 'urgent': getDeadlineDaysLeft(tpl.deadline) <= 3 }]">
            {{ getDeadlineDaysLeft(tpl.deadline) === 0 ? '今天截止' : `还剩${getDeadlineDaysLeft(tpl.deadline)}天` }}
          </span>
          <span v-else class="deadline-days expired">已过期</span>
        </div>
        <div class="task-click-hint">点击上传作文</div>
      </div>
    </div>
    <div v-else-if="taskFilter && activeTasks.length > 0" class="card" style="padding:24px;text-align:center;color:#999">
      暂无「{{ taskFilter }}」方式的收集任务
    </div>

    <!-- 快捷按钮 -->
    <div class="quick-grid">
      <div class="quick-card upload-card" :class="{ 'quick-disabled': !canCollect }" @click="onUploadClick">
        <div class="quick-icon">📤</div>
        <div class="quick-text">开始上传</div>
        <div v-if="isGuest" class="quick-sub">游客无上传权限</div>
        <div v-else-if="!canCollect" class="quick-sub">无上传权限</div>
      </div>
      <div class="quick-card list-card" @click="goList">
        <div class="quick-icon">📋</div>
        <div class="quick-text">作文列表</div>
      </div>
    </div>

    <!-- 最近上传 -->
    <div class="card" v-if="recentList.length">
      <div class="card-header"><h3>🕐 最近上传</h3></div>
      <table v-if="isDesktop" class="desktop-table">
        <thead><tr>
          <th>学生</th><th>年级</th><th>作文</th><th>状态</th><th>时间</th>
        </tr></thead>
        <tbody>
          <tr v-for="e in recentList" :key="e.id">
            <td>{{ e.student_name }}</td>
            <td>{{ e.grade || '-' }}</td>
            <td>{{ e.corrected_title || e.essay_title || '无标题' }}</td>
            <td><span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span></td>
            <td>{{ formatDateTime(e.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <template v-else>
        <van-card
          v-for="e in recentList" :key="e.id"
          :title="e.student_name"
          :desc="`第${e.essay_number}次 · ${e.corrected_title || e.essay_title || '无标题'}`"
          :tag="statusLabel(e.status)"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isGuest = computed(() => (currentUser.value.role || '').includes('guest'))
const canCollect = computed(() => {
  const role = currentUser.value.role || ''
  return role.includes('collector') || role.includes('admin')
})

const recentList = ref([])
const activeTasks = ref([])
const taskFilter = ref('')

const sortedActiveTasks = computed(() => {
  let list = activeTasks.value
  if (taskFilter.value) {
    list = list.filter(t => (t.teaching_mode || '线下') === taskFilter.value)
  }
  return [...list].sort((a, b) => {
    const aOnline = (a.teaching_mode || '线下') === '线上'
    const bOnline = (b.teaching_mode || '线下') === '线上'
    if (aOnline !== bOnline) return aOnline ? -1 : 1
    return 0
  })
})

function formatDeadline(deadline) {
  if (!deadline) return '无限制'
  return formatDateTime(deadline)
}

function getDeadlineDaysLeft(deadline) {
  if (!deadline) return -1
  const now = new Date()
  const d = new Date(deadline)
  const diff = d - now
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function statusLabel(s) { return { pending: '未修改', confirming: '待确认', rework: '待重改', corrected: '已修改' }[s] || s }

function onUploadClick() {
  if (!canCollect.value) {
    showToast(isGuest.value ? '游客无上传权限，仅可查看' : '当前账号无上传权限')
    return
  }
  goUpload()
}
function goUpload() { router.push('/essay/upload') }
function goList() { router.push('/essay/list') }

function goUploadWithTask(tpl) {
  router.push({ path: '/essay/upload', query: { task_id: tpl.id } })
}

onMounted(async () => {
  try {
    const [essayRes, tasksRes] = await Promise.all([
      api.get('/essays', { params: { page_size: 10, sort_by: 'created_at', sort_order: 'desc' } }),
      api.get('/essays/tasks/active')
    ])
    recentList.value = (essayRes.data.items || essayRes.data).slice(0, 10)

    // 批量获取所有活跃任务的统计数据（一次请求）
    const templates = tasksRes.data || []
    if (templates.length) {
      const statsRes = await api.post('/essays/tasks/stats', templates.map(t => t.id))
      const statsMap = {}
      ;(statsRes.data || []).forEach(s => { statsMap[s.task_id] = s })
      templates.forEach(t => {
        t._stats = statsMap[t.id] || { total: 0, pending: 0, confirming: 0, corrected: 0, rework: 0 }
      })
    }
    activeTasks.value = templates
  } catch {}
})
</script>

<style scoped>
.dashboard-page { padding: 0; }

.dashboard-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}
.dashboard-toolbar .page-title { margin-bottom: 0; }
.mode-filter {
  display: flex;
  gap: 4px;
  background: #fff;
  border-radius: 16px;
  padding: 3px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.filter-pill {
  padding: 4px 14px;
  border: none;
  border-radius: 14px;
  background: transparent;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
}
.filter-pill:hover { color: #1677ff; }
.filter-pill.active { background: #1677ff; color: #fff; }

.active-task-card {
  border-left: 4px solid #1677ff;
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  position: relative;
}

.active-task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.active-task-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-status {
  background: #1677ff;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.task-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.task-main {
  flex: 1;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #666;
  margin-bottom: 6px;
}

.meta-divider {
  color: #ccc;
}

.task-topic-highlight {
  font-size: 15px;
  font-weight: 500;
  color: #1677ff;
  background: linear-gradient(135deg, #e6f4ff, #f0f5ff);
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 12px;
  border-left: 3px solid #1677ff;
}

.task-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1677ff;
}
.stat-value.stat-green { color: #52c41a; }
.stat-value.stat-pink { color: #eb2f96; }

.stat-label {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

.task-deadline {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.deadline-icon {
  font-size: 14px;
}

.deadline-text {
  color: #666;
}

.deadline-days {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: #f6ffed;
  color: #52c41a;
}

.deadline-days.urgent {
  background: #fff7e6;
  color: #d46b08;
}

.deadline-days.expired {
  background: #fff2f0;
  color: #ff4d4f;
}

.task-click-hint {
  position: absolute;
  right: 16px;
  bottom: 12px;
  font-size: 12px;
  color: #1677ff;
  opacity: 0;
  transition: opacity 0.2s;
}

.active-task-card:hover .task-click-hint {
  opacity: 1;
}

.quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.quick-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  cursor: pointer;
  text-align: center;
  transition: transform 0.15s, box-shadow 0.15s;
}

.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.quick-card:active {
  transform: translateY(0);
}

.quick-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.quick-text {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.quick-sub {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}

.quick-disabled { opacity: 0.5; cursor: not-allowed; }
.quick-disabled:hover { transform: none; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.quick-disabled .quick-text { color: #999; }

.upload-card { border-left: 4px solid #1677ff; }
.list-card { border-left: 4px solid #52c41a; }

.card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}

.card-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header h3 { font-size: 16px; font-weight: 600; margin: 0; }

.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.tag-pending { background: #fff7e6; color: #d46b08; }
.tag-correcting { background: #e6f4ff; color: #1677ff; }
.tag-corrected { background: #f6ffed; color: #52c41a; }

@media (max-width: 767px) {
  .dashboard-toolbar { margin-bottom: 12px; }
  .mode-filter { margin-left: auto; }
  .task-info {
    flex-direction: column;
  }
  .task-stats {
    width: 100%;
    justify-content: space-around;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
  }
  .task-click-hint {
    opacity: 1;
    position: static;
    text-align: center;
    margin-top: 12px;
    padding-top: 8px;
    border-top: 1px dashed #e8e8e8;
  }
}
</style>
