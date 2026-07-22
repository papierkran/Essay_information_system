<template>
  <div class="dashboard-page">
    <div v-if="isDesktop" class="page-title">工作台</div>

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
            <td>{{ e.created_at?.substring(0, 16) }}</td>
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

const router = useRouter()
const { isDesktop } = useScreen()

const recentList = ref([])

function statusLabel(s) { return { pending: '待批', correcting: '批改中', corrected: '已批' }[s] || s }

function goUpload() { router.push('/essay/upload') }
function goList() { router.push('/essay/list') }

onMounted(async () => {
  try {
    const res = await api.get('/essays')
    recentList.value = res.data.slice(0, 10)
  } catch {}
})
</script>

<style scoped>
.dashboard-page { padding: 0; }

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
</style>
