<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">待修改作文</div>

    <!-- 桌面端：表格 -->
    <table v-if="isDesktop && list.length" class="desktop-table">
      <thead><tr>
        <th>学生</th><th>年级</th><th>作文</th><th>收集者</th><th>上传时间</th><th>操作</th>
      </tr></thead>
      <tbody>
        <tr v-for="e in list" :key="e.id">
          <td>{{ e.student_name }}</td>
          <td>{{ e.grade || '-' }}</td>
          <td>{{ e.essay_title || '无标题' }}</td>
          <td>{{ e.collector_name }}</td>
          <td>{{ formatDateTime(e.created_at) }}</td>
          <td>
            <button v-if="!isGuest" class="btn btn-primary" @click="claimAndGo(e)" style="font-size:12px;padding:4px 12px">
              认领修改
            </button>
            <router-link v-else :to="`/review/detail/${e.id}?readonly=1`" class="readonly-hint" style="text-decoration:none;font-size:12px">仅查看</router-link>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="isDesktop && !list.length && !loading" class="empty-state">
      <div class="icon">✅</div><p>没有待批作文</p>
    </div>

    <!-- 手机端：卡片列表 -->
    <van-list v-if="!isDesktop" v-model:loading="loading" finished-text="没有待批作文" @load="load">
      <van-card v-for="e in list" :key="e.id"
        :title="e.student_name"
        :desc="`第${e.essay_number}次 · ${e.essay_title || ''}`"
        @click="goDetail(e)">
        <template #tags>
          <van-tag plain>{{ e.collector_name }}</van-tag>
          <van-tag plain type="primary">{{ e.grade || '未知' }}</van-tag>
        </template>
        <template #footer>
          <van-button v-if="!isGuest" size="small" type="primary" @click.stop="claimAndGo(e)">认领修改</van-button>
          <span v-else style="font-size:12px;color:#999">仅查看</span>
        </template>
      </van-card>
    </van-list>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const isGuest = computed(() => ((getAuth()?.user?.role) || '').includes('guest'))
const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try { const res = await api.get('/essays/pending'); list.value = res.data }
  catch { showToast('加载失败') }
  finally { loading.value = false }
}
async function claimAndGo(e) {
  try { await api.post(`/essays/${e.id}/claim`); showToast('认领成功'); router.push(`/review/detail/${e.id}`) }
  catch (err) { showToast(err.response?.data?.detail || '认领失败') }
}
function goDetail(e) { router.push(`/review/detail/${e.id}`) }
onMounted(load)
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }
</style>
