<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">未改列表</div>

    <!-- 批量操作工具栏 -->
    <div v-if="isDesktop && list.length" class="batch-bar">
      <span style="font-size:13px;color:#666">已选 {{ selectedIds.length }} 条</span>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchOcr">🔍 批量OCR识别</button>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchAiCorrect">🤖 批量AI错别字修正</button>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchAiRewrite">🤖 批量一键修改</button>
      <button class="btn btn-primary" style="font-size:12px;padding:4px 12px;background:#52c41a;border-color:#52c41a" :disabled="!selectedIds.length" @click="batchConfirm">✅ 批量确认修改</button>
      <button class="btn" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="selectedIds = []">取消选择</button>
    </div>

    <!-- 桌面端：表格 -->
    <table v-if="isDesktop && list.length" class="desktop-table">
      <thead><tr>
        <th style="width:36px"><input type="checkbox" :checked="allSelected" @change="toggleAll" style="width:auto" /></th>
        <th>状态</th>
        <th>学生姓名</th>
        <th>作文标题</th>
        <th>任务名称</th>
        <th>提交方式</th>
        <th>第几次作文</th>
        <th>修改前字数</th>
        <th>修改后字数</th>
        <th>收集者</th>
        <th>类型</th>
        <th>上传时间</th>
        <th>操作</th>
      </tr></thead>
      <tbody>
        <tr v-for="e in list" :key="e.id" :class="{ 'row-selected': selectedIds.includes(e.id) }">
          <td><input type="checkbox" :checked="selectedIds.includes(e.id)" @change="toggleSelect(e.id)" style="width:auto" /></td>
          <td><span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span></td>
          <td>{{ e.student_name }}</td>
          <td>{{ e.essay_title || '无标题' }}</td>
          <td>{{ e.task_name || '-' }}</td>
          <td>{{ e.teaching_mode || '-' }}</td>
          <td>{{ e.essay_number || '-' }}</td>
          <td>{{ e.word_count || 0 }}</td>
          <td>{{ e.corrected_word_count || 0 }}</td>
          <td>{{ e.collector_name }}</td>
          <td>{{ e.file_type === 'image' ? '图片' : e.file_type === 'docx' ? '文档' : '文本' }}</td>
          <td>{{ formatDateTime(e.created_at) }}</td>
          <td style="white-space:nowrap">
            <router-link :to="`/review/detail/${e.id}`" class="btn" style="font-size:12px;padding:4px 8px;text-decoration:none;color:#333">详情编辑</router-link>
            <button v-if="e.status === 'confirming' && !isGuest" class="btn" style="font-size:12px;padding:4px 8px;color:#52c41a;margin-left:4px" @click="confirmSingle(e)">✅ 确认修改</button>
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
          <van-tag :type="e.status === 'confirming' ? 'warning' : 'default'">{{ statusLabel(e.status) }}</van-tag>
          <van-tag plain>{{ e.collector_name }}</van-tag>
          <van-tag plain type="primary">{{ e.grade || '未知' }}</van-tag>
        </template>
        <template #footer>
          <span style="font-size:12px;color:#1677ff">点击查看详情</span>
        </template>
      </van-card>
    </van-list>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showSuccessToast, showFailToast, showDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const isGuest = computed(() => ((getAuth()?.user?.role) || '').includes('guest'))
const list = ref([])
const loading = ref(false)
const selectedIds = ref([])

function statusLabel(s) { return { pending: '未修改', confirming: '待确认', corrected: '已修改' }[s] || s }

const allSelected = computed(() => list.value.length > 0 && selectedIds.value.length === list.value.length)

function toggleAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = list.value.map(e => e.id)
  }
}
function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

async function load() {
  loading.value = true
  try { const res = await api.get('/essays/pending'); list.value = res.data }
  catch { showToast('加载失败') }
  finally { loading.value = false }
}
function goDetail(e) { router.push(`/review/detail/${e.id}`) }

async function batchOcr() {
  if (!selectedIds.value.length) return
  const toast = showLoadingToast({ message: 'OCR 识别中...', duration: 0, forbidClick: true })
  try {
    const res = await api.post('/essays/batch-ocr', { ids: selectedIds.value })
    const d = res.data
    closeToast()
    showSuccessToast(`OCR 完成：成功 ${d.success} 条${d.errors.length ? `，失败 ${d.errors.length} 条` : ''}`)
    if (d.errors.length) console.warn('OCR 失败明细:', d.errors)
    selectedIds.value = []
    await load()
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '批量 OCR 失败')
  }
}

async function batchAiCorrect() {
  if (!selectedIds.value.length) return
  const toast = showLoadingToast({ message: 'AI 错别字修正中...', duration: 0, forbidClick: true })
  try {
    const res = await api.post('/essays/batch-ai-correct', { ids: selectedIds.value })
    const d = res.data
    closeToast()
    showSuccessToast(`AI 修正完成：成功 ${d.success} 条${d.errors.length ? `，失败 ${d.errors.length} 条` : ''}`)
    if (d.errors.length) console.warn('AI 修正失败明细:', d.errors)
    selectedIds.value = []
    await load()
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '批量 AI 修正失败')
  }
}

async function batchAiRewrite() {
  if (!selectedIds.value.length) return
  const toast = showLoadingToast({ message: 'AI 一键修改中...', duration: 0, forbidClick: true })
  try {
    const res = await api.post('/essays/batch-ai-rewrite', { ids: selectedIds.value })
    const d = res.data
    closeToast()
    showSuccessToast(`AI 改写完成：成功 ${d.success} 条${d.errors.length ? `，失败 ${d.errors.length} 条` : ''}`)
    if (d.errors.length) console.warn('AI 改写失败明细:', d.errors)
    selectedIds.value = []
    await load()
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '批量 AI 改写失败')
  }
}

async function batchConfirm() {
  if (!selectedIds.value.length) return
  const confirmingIds = list.value.filter(e => selectedIds.value.includes(e.id) && e.status === 'confirming').map(e => e.id)
  if (!confirmingIds.length) { showToast('选中的条目中没有待确认的作文'); return }
  try {
    const res = await api.post('/essays/batch-confirm', { ids: confirmingIds })
    const d = res.data
    showSuccessToast(`确认完成：成功 ${d.success} 条`)
    selectedIds.value = []
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '批量确认失败')
  }
}

async function confirmSingle(e) {
  try {
    await api.post(`/essays/${e.id}/confirm`)
    showSuccessToast('已确认修改')
    await load()
  } catch (err) {
    showFailToast(err.response?.data?.detail || '确认失败')
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }
.batch-bar { display: flex; align-items: center; gap: 8px; padding: 8px 0; flex-wrap: wrap; }
.row-selected { background-color: #e6f4ff !important; }
</style>
