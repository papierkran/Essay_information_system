<template>
  <div class="dashboard-page">
    <div v-if="isDesktop" class="page-title">工作台</div>

    <!-- 当前收集任务 -->
    <div v-if="activeTasks.length > 0">
      <div v-for="tpl in activeTasks" :key="tpl.id" class="card active-task-card" @click="goUploadWithTask(tpl)">
        <div class="card-header">
          <h3>📝 {{ tpl.name }}</h3>
          <span class="task-status">收集中</span>
        </div>
        <div v-if="tpl.essay_topic" class="task-topic-highlight">作文主题：{{ tpl.essay_topic }}</div>
        <div class="task-info">
          <div class="task-main">
            <div class="task-meta">
              <span class="meta-item">{{ tpl.grade }}</span>
              <span class="meta-divider">·</span>
              <span class="meta-item">第{{ tpl.essay_number }}次</span>
              <span class="meta-divider">·</span>
              <span class="meta-item">{{ tpl.teaching_mode || '线下' }}</span>
              <span v-if="tpl.course_name" class="meta-divider">·</span>
              <span v-if="tpl.course_name" class="meta-item">{{ tpl.course_name }}</span>
            </div>
          </div>
          <div class="task-stats">
            <div class="stat-item">
              <div class="stat-value">{{ tpl._stats?.total || 0 }}</div>
              <div class="stat-label">已收集</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ tpl._stats?.pending || 0 }}</div>
              <div class="stat-label">待批改</div>
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

    <!-- 快捷按钮 -->
    <div class="quick-grid">
      <div class="quick-card upload-card" @click="goUpload">
        <div class="quick-icon">📤</div>
        <div class="quick-text">开始上传</div>
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
            <td>{{ e.essay_title || '无标题' }}</td>
            <td><span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span></td>
            <td>{{ formatDateTime(e.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <template v-else>
        <van-card
          v-for="e in recentList" :key="e.id"
          :title="e.student_name"
          :desc="`第${e.essay_number}次 · ${e.essay_title || '无标题'}`"
          :tag="statusLabel(e.status)"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScreen } from '../composables/useScreen'
import api from '../api'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()

const recentList = ref([])
const activeTasks = ref([])

function formatDeadline(deadline) {
  if (!deadline) return '无限制'
  const d = new Date(deadline)
  const month = d.getMonth() + 1
  const day = d.getDate()
  const hours = d.getHours()
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${month}月${day}日 ${hours}:${minutes}`
}

function getDeadlineDaysLeft(deadline) {
  if (!deadline) return -1
  const now = new Date()
  const d = new Date(deadline)
  const diff = d - now
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function statusLabel(s) { return { pending: '待修改', correcting: '修改中', corrected: '已修改' }[s] || s }

function goUpload() { router.push('/essay/upload') }
function goList() { router.push('/essay/list') }

function goUploadWithTask(tpl) {
  router.push({ path: '/essay/upload', query: { task_id: tpl.id } })
}

onMounted(async () => {
  try {
    const [essayRes, tasksRes] = await Promise.all([
      api.get('/essays'),
      api.get('/essays/tasks/active')
    ])
    recentList.value = (essayRes.data.items || essayRes.data).slice(0, 10)
    
    // 获取每个模板的统计数据
    const templates = tasksRes.data || []
    for (const tpl of templates) {
      try {
        const statsRes = await api.get(`/essays/tasks/${tpl.id}/stats`)
        tpl._stats = statsRes.data
      } catch {
        tpl._stats = { total: 0, pending: 0, corrected: 0 }
      }
    }
    activeTasks.value = templates
  } catch {}
})
</script>

<style scoped>
.dashboard-page { padding: 0; }

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
