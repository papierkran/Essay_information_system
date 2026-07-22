<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">批改历史</div>

    <!-- 桌面端：表格 -->
    <table v-if="isDesktop && list.length" class="desktop-table">
      <thead><tr>
        <th>学生</th><th>年级</th><th>作文</th><th>收集者</th><th>批改时间</th><th>状态</th>
      </tr></thead>
      <tbody>
        <tr v-for="e in list" :key="e.id">
          <td>{{ e.student_name }}</td>
          <td>{{ e.grade || '-' }}</td>
          <td>{{ e.essay_title || '无标题' }}</td>
          <td>{{ e.collector_name }}</td>
          <td>{{ e.corrected_at?.substring(0,16) || e.created_at?.substring(0,16) }}</td>
          <td><span class="tag" :class="e.has_correction ? 'tag-corrected' : 'tag-pending'">{{ e.has_correction ? '已批' : '待批' }}</span></td>
        </tr>
      </tbody>
    </table>
    <div v-if="isDesktop && !list.length && !loading" class="empty-state">
      <div class="icon">📭</div><p>没有批改记录</p>
    </div>

    <!-- 手机端：卡片列表 -->
    <van-list v-if="!isDesktop" v-model:loading="loading" finished-text="没有更多了" @load="load">
      <van-card v-for="e in list" :key="e.id"
        :title="e.student_name"
        :desc="`第${e.essay_number}次 · ${e.essay_title || ''}`"
        :tag="e.has_correction ? '已批' : '待批'"
        @click="goDetail(e)">
        <template #tags><van-tag plain>{{ e.collector_name }}</van-tag></template>
        <template #footer>{{ e.corrected_at?.substring(0,16) || e.created_at?.substring(0,16) }}</template>
      </van-card>
    </van-list>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api from '../api'

const router = useRouter()
const { isDesktop } = useScreen()
const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try { const res = await api.get('/essays?status=corrected'); list.value = res.data }
  catch { showToast('加载失败') }
  finally { loading.value = false }
}
function goDetail(e) { router.push(`/review/detail/${e.id}`) }
onMounted(load)
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }
</style>
