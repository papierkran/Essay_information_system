<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">操作历史</div>

    <!-- 统计行 -->
    <div class="stats-bar" v-if="isDesktop">
      <span>共 <strong>{{ total }}</strong> 条记录</span>
    </div>

    <!-- 桌面端：表格 -->
    <table v-if="isDesktop && list.length" class="desktop-table">
      <thead><tr>
        <th>时间</th><th>学生</th><th>作文</th><th>操作</th><th>操作者</th><th>详情</th>
      </tr></thead>
      <tbody>
        <tr v-for="op in list" :key="op.id" style="cursor:pointer" @click="goDetail(op)">
          <td>{{ formatDateTime(op.created_at) }}</td>
          <td>{{ op.student_name || '-' }}</td>
          <td>{{ op.essay_title || '无标题' }}<span v-if="op.essay_number"> #{{ op.essay_number }}</span></td>
          <td><span class="tag" :class="actionClass(op.action)">{{ op.action }}</span></td>
          <td>{{ op.user_name }}</td>
          <td>{{ op.detail || '-' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="isDesktop && !list.length && !loading" class="empty-state">
      <div class="icon">📭</div><p>暂无操作记录</p>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="isDesktop && totalPages > 1">
      <button class="btn" :disabled="page <= 1" @click="goPage(1)">首页</button>
      <button class="btn" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(totalPages)">末页</button>
    </div>

    <!-- 手机端：卡片列表 -->
    <van-list v-if="!isDesktop" v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="loadMore">
      <van-cell v-for="op in list" :key="op.id"
        :title="`${op.action} · ${op.student_name || '?'}`"
        :label="op.essay_title || '无标题'"
        :value="formatDateTime(op.created_at)"
        @click="goDetail(op)">
        <template #extra>
          <span class="tag" :class="actionClass(op.action)" style="font-size:11px">{{ op.action }}</span>
        </template>
      </van-cell>
    </van-list>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api from '../api'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()
const list = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(40)
const finished = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

function actionClass(action) {
  const m = { '上传': 'tag-pending', '认领': 'tag-correcting', '修改': 'tag-corrected', '编辑': 'tag-correcting', '删除': 'tag-pending', '恢复': 'tag-corrected' }
  return m[action] || ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.get('/essays/operations', { params: { page: page.value, page_size: pageSize.value } })
    list.value = res.data.items
    total.value = res.data.total
    finished.value = list.value.length >= total.value
  } catch { showToast('加载失败') }
  finally { loading.value = false }
}

function goPage(p) { page.value = p; loadData() }

async function loadMore() {
  page.value++
  try {
    const res = await api.get('/essays/operations', { params: { page: page.value, page_size: pageSize.value } })
    list.value.push(...res.data.items)
    total.value = res.data.total
    finished.value = list.value.length >= total.value
  } catch { showToast('加载失败') }
  finally { loading.value = false }
}

function goDetail(op) { router.push(`/review/detail/${op.essay_id}`) }

onMounted(loadData)
</script>

<style scoped>
.page { padding: 0; }

.stats-bar {
  display: flex;
  gap: 20px;
  padding: 8px 0;
  font-size: 13px;
  color: #666;
}
.stats-bar strong { font-size: 15px; }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 20px 0;
}
.page-info { font-size: 14px; color: #333; }

@media (max-width: 767px) { .page { min-height: 100vh; } }
</style>
