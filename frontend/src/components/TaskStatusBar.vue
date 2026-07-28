<template>
  <div v-if="tasks.length" class="task-status-bar">
    <div v-for="t in tasks" :key="t.id" class="task-item">
      <span class="task-type">{{ typeLabel(t.type) }}</span>
      <div class="task-progress-wrap">
        <div class="task-progress-bar" :style="{ width: progressPercent(t) + '%' }" :class="'progress-' + t.status"></div>
      </div>
      <span class="task-count">{{ t.success }}/{{ t.total }}</span>
      <span class="task-status" :class="'status-' + t.status">
        {{ t.status === 'running' ? '⏳' : t.status === 'completed' ? '✅' : '❌' }}
      </span>
      <button v-if="t.status !== 'running'" class="task-dismiss" @click="dismissTask(t.id)">✕</button>
      <span v-if="t.message" class="task-msg">{{ t.message }}</span>
    </div>
  </div>
</template>

<script setup>
import { useTaskMonitor, typeLabel } from '../composables/useTaskMonitor'

const { tasks, dismissTask } = useTaskMonitor()

function progressPercent(t) {
  if (!t.total) return 0
  return Math.round((t.success + (t.errors ? t.errors.length : 0)) / t.total * 100)
}
</script>

<style scoped>
.task-status-bar {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 360px;
  width: 100%;
}
.task-item {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 10px 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  font-size: 13px;
}
.task-type { font-weight: 600; color: #333; display: block; margin-bottom: 4px; }
.task-progress-wrap {
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  margin: 4px 0;
  overflow: hidden;
}
.task-progress-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}
.progress-running { background: #1677ff; }
.progress-completed { background: #52c41a; }
.progress-failed { background: #ff4d4f; }
.task-count { font-size: 12px; color: #666; }
.task-status { margin-left: 8px; }
.task-dismiss {
  float: right;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #999;
  padding: 0 4px;
}
.task-msg { font-size: 11px; color: #999; display: block; margin-top: 2px; }
@media (max-width: 767px) {
  .task-status-bar { right: 8px; bottom: 8px; max-width: 280px; }
}
</style>
