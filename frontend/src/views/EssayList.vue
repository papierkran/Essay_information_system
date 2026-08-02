<template>
  <div class="page">
    <div class="page-title">作文列表</div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-row"><span class="filter-label">学生姓名</span><input v-model="filters.name" placeholder="搜索姓名" class="filter-input" @keyup.enter="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">作文标题</span><input v-model="filters.essayTitle" placeholder="搜索标题" class="filter-input" @keyup.enter="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">年级</span>
        <select v-model="filters.grade" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">第几次</span><input v-model.number="filters.number" type="number" min="1" placeholder="不限制" class="filter-input" style="width:70px" @keyup.enter="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">是否修改</span>
        <select v-model="filters.status" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option value="pending">未修改</option>
          <option value="confirming">待确认</option>
          <option value="corrected">已修改</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">提交方式</span>
        <select v-model="filters.mode" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option value="线下">线下</option>
          <option value="线上">线上</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">收集者</span>
        <select v-model="filters.collectedBy" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option v-for="c in collectorList" :key="c.id" :value="c.id">{{ c.nickname }}</option>
        </select>
      </div>
      <div ref="taskFilterRef" class="filter-row" style="position:relative">
        <span class="filter-label">任务</span>
        <input v-model="filterTaskSearch" placeholder="搜索任务" class="filter-input" style="width:120px" @focus="showTaskDropdown = true" @input="showTaskDropdown = true" @keyup.enter="applyFilter" />
        <div v-if="showTaskDropdown" class="task-dropdown">
          <div @mousedown.prevent @click="filters.taskId = ''; filterTaskSearch = ''; showTaskDropdown = false; applyFilter()" :class="{ 'task-item-active': !filters.taskId }" class="task-item">全部</div>
          <div v-for="t in filteredTaskOptions" :key="t.id" @mousedown.prevent @click="filters.taskId = t.id; filterTaskSearch = t.name; showTaskDropdown = false; applyFilter()" :class="{ 'task-item-active': filters.taskId == t.id }" class="task-item">{{ t.name }}</div>
          <div v-if="!filteredTaskOptions.length" class="task-item" style="color:#999">无匹配任务</div>
        </div>
      </div>
      <div class="filter-row"><span class="filter-label">批改者</span>
        <select v-model="filters.reviewerId" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option v-for="r in reviewerList" :key="r.id" :value="r.id">{{ r.nickname || r.username }}</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">是否补交</span>
        <select v-model="filters.isSupplement" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option value="true">是</option>
          <option value="false">否</option>
        </select>
      </div>
      <div class="filter-row"><span class="filter-label">收集时间</span><input v-model="filters.dateFrom" type="date" class="filter-input" style="width:130px" @change="applyFilter" /><span style="color:#d9d9d9;font-size:12px">~</span><input v-model="filters.dateTo" type="date" class="filter-input" style="width:130px" @change="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">修改时间</span><input v-model="filters.correctedFrom" type="date" class="filter-input" style="width:130px" @change="applyFilter" /><span style="color:#d9d9d9;font-size:12px">~</span><input v-model="filters.correctedTo" type="date" class="filter-input" style="width:130px" @change="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">修改前字数</span><input v-model.number="filters.wordMin" type="number" min="0" placeholder="最少" class="filter-input" style="width:70px" /><span style="color:#d9d9d9;font-size:12px">~</span><input v-model.number="filters.wordMax" type="number" min="0" placeholder="最多" class="filter-input" style="width:70px" /></div>
      <div class="filter-row"><span class="filter-label">修改后字数</span><input v-model.number="filters.correctedMin" type="number" min="0" placeholder="最少" class="filter-input" style="width:70px" /><span style="color:#d9d9d9;font-size:12px">~</span><input v-model.number="filters.correctedMax" type="number" min="0" placeholder="最多" class="filter-input" style="width:70px" /></div>
      <div class="filter-row"><span class="filter-label">备注</span><input v-model="filters.remark" placeholder="搜备注" class="filter-input" @keyup.enter="applyFilter" /></div>
      <button class="btn btn-primary" style="font-size:13px;padding:6px 14px" @click="applyFilter">查询</button>
      <button class="btn" style="font-size:13px;padding:6px 14px" @click="clearFilter">重置</button>
      <button v-if="!isGuest" class="btn" style="font-size:13px;padding:6px 14px" @click="exportCSV">导出CSV</button>
    </div>

    <!-- 统计行 -->
    <div class="stats-bar">
      <span>共 <strong>{{ total }}</strong> 条</span>
      <span class="stat-pending">未改 <strong>{{ pendingTotal }}</strong></span>
      <span class="stat-corrected">已修改 <strong>{{ correctedTotal }}</strong></span>
      <template v-if="!isGuest">
        <span style="color:#d9d9d9">|</span>
        <span style="font-size:13px;color:#666">已选 {{ selectedIds.length }} 条</span>
        <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchExportDocx">📥 批量导出docx</button>
        <button class="btn btn-danger" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="batchDelete">批量删除</button>
        <button v-if="isAdmin" class="btn" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="showBatchCollector = true">修改收集者</button>
        <button v-if="isAdmin" class="btn" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="showBatchTask = true">修改任务</button>
        <button class="btn" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="selectedIds=[]">取消选择</button>
      </template>
      <span style="margin-left:auto;display:flex;align-items:center;gap:4px;font-size:13px;color:#666">
        <button class="btn" style="font-size:12px;padding:4px 10px" @click="showColumnSettings = true">⚙️ 列设置</button>
        每页
        <select v-model.number="pageSize" @change="applyFilter" style="padding:4px 8px;border:1px solid #d9d9d9;border-radius:4px;font-size:13px">
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
          <option :value="500">500</option>
          <option :value="1000">1000</option>
        </select>
        条
      </span>
    </div>

    <!-- 表格 -->
    <div ref="topScroll" class="scroll-sync" @scroll="syncScroll('top')">
      <div ref="topScrollContent" class="scroll-sync-content"></div>
    </div>
    <div ref="tableWrap" class="table-wrap" @scroll="syncScroll('bottom')">
      <table class="desktop-table" v-if="list.length">
        <thead>
          <tr>
            <th v-if="!isGuest" style="width:36px"><input type="checkbox" :checked="allSelected" @change="toggleAll" style="width:auto" /></th>
            <template v-for="col in visibleColumns" :key="col.key">
              <th :class="{ sortable: col.sortable, 'th-dragging': dragColKey === col.key }"
                draggable="true"
                @dragstart.stop="onColDragStart(col.key)"
                @dragover.prevent="onColDragOver(col.key)"
                @dragend="onColDragEnd"
                @drop.prevent="onColDrop"
                @click="col.sortable && toggleSort(col.sort)">
                {{ col.label }} <template v-if="col.sortable">{{ sortIcon(col.sort) }}</template>
              </th>
            </template>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in list" :key="e.id" :class="{ 'row-selected': selectedIds.includes(e.id), 'row-readonly': !isOwner(e) }">
            <td v-if="!isGuest"><input type="checkbox" :checked="selectedIds.includes(e.id)" @change="toggleSelect(e.id)" style="width:auto" /></td>
            <template v-for="col in visibleColumns" :key="col.key">
              <td v-if="col.key === 'status'"><span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span></td>
              <td v-else-if="col.key === 'file_saved'"><span class="tag" :class="e.file_saved ? 'tag-corrected' : 'tag-pending'">{{ e.file_saved ? '已存' : '丢失' }}</span></td>
              <td v-else-if="col.key === 'is_supplement'"><span :style="{ color: e.is_supplement ? '#fa8c16' : '#d9d9d9', fontSize: '16px' }">{{ e.is_supplement ? '🔄' : '' }}</span></td>
              <td v-else-if="col.key === 'word_count'">{{ e.word_count || 0 }}</td>
              <td v-else-if="col.key === 'corrected_word_count'">{{ e.corrected_word_count || 0 }}</td>
              <td v-else-if="col.key === 'created_at'">{{ formatDateTime(e.created_at) }}</td>
              <td v-else-if="col.key === 'corrected_at'">{{ formatDateTime(e.corrected_at) || '-' }}</td>
              <td v-else>{{ e[col.field] || '-' }}</td>
            </template>
            <td style="white-space:nowrap">
              <template v-if="!isGuest && isOwner(e)">
                <router-link :to="`/review/detail/${e.id}`" class="btn" style="font-size:12px;padding:4px 8px;text-decoration:none;color:#333">详情编辑</router-link>
                <button class="btn" style="font-size:12px;padding:4px 8px;color:#ff4d4f" @click="confirmDelete(e)">删除</button>
              </template>
              <router-link v-else :to="`/review/detail/${e.id}?readonly=1`" class="readonly-hint" style="text-decoration:none">
                <span class="text-readonly">仅查看</span>
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!list.length && !loading" class="empty-state"><div class="icon">📭</div><p>暂无作文</p></div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > 0">
      <button class="btn" :disabled="page <= 1" @click="goPage(1)">首页</button>
      <button class="btn" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
      <button class="btn" :disabled="page >= totalPages" @click="goPage(totalPages)">末页</button>
      <span class="page-jump" style="margin-left:12px">跳至
        <input v-model.number="jumpPage" type="number" min="1" :max="totalPages" class="page-jump-input" @keyup.enter="jumpToPage" />
        <button class="btn" style="font-size:12px;padding:4px 8px" @click="jumpToPage">GO</button>
      </span>
    </div>

    <!-- 删除确认弹窗 -->
    <van-dialog v-model:show="showDelete" :title="deletingEssay ? '确认删除' : `批量删除 ${selectedIds.length} 条`"
      :show-cancel-button="true" @confirm="doDelete" :close-on-click-overlay="false">
      <div style="padding:16px;font-size:14px;line-height:1.8">
        <p v-if="deletingEssay">学生：<strong>{{ deletingEssay.student_name }}</strong></p>
        <p v-else>确定删除已选的 <strong>{{ selectedIds.length }}</strong> 条作文吗？</p>
        <van-checkbox v-model="deleteFileChecked" :disabled="!isAdmin">
          <span :style="{ color: isAdmin ? '#333' : '#ccc' }">同时删除本地文件</span>
        </van-checkbox>
        <p v-if="!isAdmin" style="color:#999;font-size:12px;margin-top:8px">非管理员无法删除本地文件</p>
      </div>
    </van-dialog>

    <!-- 列设置弹窗 -->
    <van-dialog v-model:show="showColumnSettings" title="自定义表头" :show-cancel-button="false" :show-confirm-button="false" :close-on-click-overlay="true">
      <div style="padding:12px 16px">
        <div v-for="(col, i) in allColumns" :key="col.key"
          draggable="true"
          @dragstart="dragColIndex = i"
          @dragover.prevent="dragOverColIndex = i"
          @dragend="dragColIndex = -1; dragOverColIndex = -1"
          @drop="moveColumn"
          :style="{ display:'flex', alignItems:'center', padding:'8px 0', borderBottom:'1px solid #f5f5f5', cursor: col.fixed ? 'default' : 'grab', background: dragOverColIndex === i ? '#f0f0f0' : 'transparent' }">
          <span style="margin-right:8px;color:#ccc;font-size:14px">⠿</span>
          <van-checkbox v-model="col.visible" :disabled="col.fixed" style="flex:1">
            <span :style="{ color: col.fixed ? '#999' : '#333' }">{{ col.label }}</span>
          </van-checkbox>
          <span v-if="col.fixed" style="font-size:11px;color:#999">固定</span>
        </div>
      </div>
      <template #footer>
        <div style="display:flex;gap:8px;justify-content:flex-end;padding:8px 16px">
          <button class="btn" @click="resetColumns">恢复默认</button>
          <button class="btn btn-primary" @click="saveColumns">确定</button>
        </div>
      </template>
    </van-dialog>

    <!-- 批量修改收集者 -->
    <van-dialog v-model:show="showBatchCollector" title="修改收集者" :show-cancel-button="true" @confirm="doBatchCollector">
      <div style="padding:16px">
        <p style="font-size:13px;color:#666;margin-bottom:8px">将 {{ selectedIds.length }} 条作文的收集者修改为：</p>
        <select v-model.number="batchCollectorId" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px">
          <option value="">请选择</option>
          <option v-for="c in collectorList" :key="c.id" :value="c.id">{{ c.nickname }}</option>
        </select>
      </div>
    </van-dialog>

    <!-- 批量修改任务 -->
    <van-dialog v-model:show="showBatchTask" title="修改任务" :show-cancel-button="true" @confirm="doBatchTask" @open="taskSearch = ''">
      <div style="padding:16px">
        <p style="font-size:13px;color:#666;margin-bottom:8px">将 {{ selectedIds.length }} 条作文的任务修改为：</p>
        <input v-model="taskSearch" placeholder="搜索任务名称..." style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;box-sizing:border-box" />
        <div style="max-height:200px;overflow-y:auto;margin-top:4px;border:1px solid #d9d9d9;border-radius:6px">
          <div @click="batchTaskId = 0; taskSearch = ''" style="padding:8px 12px;cursor:pointer;border-bottom:1px solid #f5f5f5" :style="{ background: batchTaskId === 0 ? '#e6f4ff' : '#fff' }">
            <span style="color:#999">无任务</span>
          </div>
          <div v-for="t in filteredTasks" :key="t.id" @click="batchTaskId = t.id; taskSearch = t.name" style="padding:8px 12px;cursor:pointer;border-bottom:1px solid #f5f5f5" :style="{ background: batchTaskId === t.id ? '#e6f4ff' : '#fff' }">
            {{ t.name }}
          </div>
          <div v-if="!filteredTasks.length" style="padding:12px;text-align:center;color:#999">无匹配任务</div>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showDialog, showToast, showLoadingToast, closeToast, showSuccessToast, showFailToast } from 'vant'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'

const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isGuest = computed(() => (currentUser.value.role || '').includes('guest'))
const isAdmin = computed(() => (currentUser.value.role || '').includes('admin'))
const isOwner = (essay) => currentUser.value.role?.includes('admin') || essay.collected_by === currentUser.value.id

const deletingEssay = ref(null)
const showDelete = ref(false)
const deleteFileChecked = ref(false)

const showBatchCollector = ref(false)
const batchCollectorId = ref('')
const showBatchTask = ref(false)
const batchTaskId = ref(0)
const taskSearch = ref('')
const taskList = ref([])
const reviewerList = ref([])
const filterTaskSearch = ref('')
const showTaskDropdown = ref(false)
const taskFilterRef = ref(null)

function closeTaskDropdown(e) {
  if (taskFilterRef.value && !taskFilterRef.value.contains(e.target)) {
    showTaskDropdown.value = false
  }
}

const filteredTasks = computed(() => {
  if (!taskSearch.value) return taskList.value
  const kw = taskSearch.value.toLowerCase()
  return taskList.value.filter(t => t.name.toLowerCase().includes(kw))
})

const filteredTaskOptions = computed(() => {
  if (!filterTaskSearch.value) return taskList.value
  const kw = filterTaskSearch.value
  // 智能分段匹配：将搜索词拆为 中文段 + 数字段，按顺序匹配（允许中间有任意字符）
  const segments = kw.match(/[\u4e00-\u9fff]+|\d+/g)
  if (!segments || segments.length === 0) return taskList.value.filter(t => t.name.toLowerCase().includes(kw.toLowerCase()))
  const pattern = segments.map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('.*')
  const regex = new RegExp(pattern, 'i')
  return taskList.value.filter(t => regex.test(t.name))
})

const router = useRouter()
const route = useRoute()
const topScroll = ref(null)
const topScrollContent = ref(null)
const tableWrap = ref(null)
const list = ref([])
const loading = ref(false)
const total = ref(0)
const pendingTotal = ref(0)
const correctedTotal = ref(0)
const page = ref(1)
const pageSize = ref(100)
const jumpPage = ref(1)
const sortBy = ref('created_at')
const sortOrder = ref('desc')
const selectedIds = ref([])
const grades = ['初一','初二','初三','高一','高二','高三']
const collectorList = ref([])

// 初始化收集者筛选：管理员默认全部，其他角色默认自己
const defaultCollectedBy = computed(() => {
  if (isAdmin.value) return ''
  return currentUser.value.id || ''
})
const filters = ref({ name: '', essayTitle: '', grade: '', number: '', status: '', mode: '', collectedBy: '', remark: '', taskId: '', reviewerId: '', isSupplement: '', dateFrom: '', dateTo: '', correctedFrom: '', correctedTo: '', wordMin: '', wordMax: '', correctedMin: '', correctedMax: '' })

// ===== 筛选持久化 =====
const FILTER_KEY = 'essay_list_filters'
function saveFilters() {
  localStorage.setItem(FILTER_KEY, JSON.stringify(filters.value))
}
function loadFilters() {
  try {
    const saved = localStorage.getItem(FILTER_KEY)
    if (saved) {
      const data = JSON.parse(saved)
      Object.keys(filters.value).forEach(k => {
        if (data[k] !== undefined) filters.value[k] = data[k]
      })
      return true
    }
  } catch {}
  return false
}

// ===== 列配置 =====
const COLUMN_KEY = 'essay_list_columns_v2'
const allColumns = ref([
  { key: 'student_name', label: '学生姓名', field: 'student_name', sortable: true, sort: 'student_name', visible: true, fixed: true },
  { key: 'grade', label: '年级', field: 'grade', sortable: false, visible: true },
  { key: 'essay_title', label: '作文标题', field: 'essay_title', sortable: false, visible: true },
  { key: 'essay_number', label: '第几次', field: 'essay_number', sortable: true, sort: 'essay_number', visible: true },
  { key: 'teaching_mode', label: '提交方式', field: 'teaching_mode', sortable: false, visible: true },
  { key: 'status', label: '是否修改', field: 'status', sortable: true, sort: 'status', visible: true },
  { key: 'collector_name', label: '收集者', field: 'collector_name', sortable: true, sort: 'collector_name', visible: true },
  { key: 'reviewer_name', label: '批改者', field: 'reviewer_name', sortable: true, sort: 'reviewer_name', visible: false },
  { key: 'task_name', label: '任务名称', field: 'task_name', sortable: false, visible: false },
  { key: 'remark', label: '备注', field: 'remark', sortable: true, sort: 'remark', visible: true },
  { key: 'is_supplement', label: '是否补交', field: 'is_supplement', sortable: true, sort: 'is_supplement', visible: false },
  { key: 'word_count', label: '修改前字数', field: 'word_count', sortable: true, sort: 'word_count', visible: false },
  { key: 'corrected_word_count', label: '修改后字数', field: 'corrected_word_count', sortable: true, sort: 'corrected_word_count', visible: false },
  { key: 'created_at', label: '收集时间', field: 'created_at', sortable: true, sort: 'created_at', visible: true },
  { key: 'corrected_at', label: '修改时间', field: 'corrected_at', sortable: true, sort: 'corrected_at', visible: true },
  { key: 'file_saved', label: '文件', field: 'file_saved', sortable: false, visible: true },
])
const showColumnSettings = ref(false)
const dragColIndex = ref(-1)
const dragOverColIndex = ref(-1)
const dragColKey = ref('')
const dragOverColKey = ref('')

function onColDragStart(key) {
  dragColKey.value = key
}
function onColDragOver(key) {
  dragOverColKey.value = key
}
function onColDragEnd() {
  dragColKey.value = ''
  dragOverColKey.value = ''
}
function onColDrop() {
  const fromKey = dragColKey.value
  const toKey = dragOverColKey.value
  if (!fromKey || !toKey || fromKey === toKey) return
  const cols = allColumns.value
  const fromIdx = cols.findIndex(c => c.key === fromKey)
  const toIdx = cols.findIndex(c => c.key === toKey)
  if (fromIdx < 0 || toIdx < 0) return
  const col = cols[fromIdx]
  if (col.fixed) return
  cols.splice(fromIdx, 1)
  cols.splice(toIdx, 0, col)
  // 持久化列顺序
  saveColumnOrder()
  dragColKey.value = ''
  dragOverColKey.value = ''
}
function saveColumnOrder() {
  const keys = allColumns.value.map(c => c.key)
  localStorage.setItem('essay_list_column_order', JSON.stringify(keys))
}

function loadColumnSettings() {
  try {
    // 恢复列顺序
    const orderSaved = localStorage.getItem('essay_list_column_order')
    if (orderSaved) {
      const orderKeys = JSON.parse(orderSaved)
      if (Array.isArray(orderKeys) && orderKeys.length) {
        const sorted = []
        const remaining = [...allColumns.value]
        for (const key of orderKeys) {
          const idx = remaining.findIndex(c => c.key === key)
          if (idx >= 0) sorted.push(remaining.splice(idx, 1)[0])
        }
        sorted.push(...remaining)
        allColumns.value = sorted
      }
    }
    // 恢复列显隐
    const saved = localStorage.getItem(COLUMN_KEY)
    if (saved) {
      const map = JSON.parse(saved)
      allColumns.value.forEach(c => { if (map[c.key] !== undefined) c.visible = map[c.key] })
    }
  } catch {}
}
function saveColumns() {
  const map = {}
  allColumns.value.forEach(c => { map[c.key] = c.visible })
  localStorage.setItem(COLUMN_KEY, JSON.stringify(map))
  showColumnSettings.value = false
}
function resetColumns() {
  const defaults = { student_name: true, grade: true, essay_title: true, essay_number: true, teaching_mode: true, status: true, collector_name: true, reviewer_name: false, task_name: false, remark: true, is_supplement: false, word_count: false, corrected_word_count: false, created_at: true, corrected_at: true, file_saved: true }
  allColumns.value.forEach(c => { c.visible = defaults[c.key] !== undefined ? defaults[c.key] : false })
}
function moveColumn() {
  const from = dragColIndex.value
  const to = dragOverColIndex.value
  if (from < 0 || to < 0 || from === to) return
  const col = allColumns.value[from]
  // 不允许拖动固定列
  if (col.fixed) return
  // 不允许拖动到固定列之前
  if (allColumns.value[to]?.fixed) return
  allColumns.value.splice(from, 1)
  allColumns.value.splice(to, 0, col)
  dragColIndex.value = -1
  dragOverColIndex.value = -1
}
const visibleColumns = computed(() => allColumns.value.filter(c => c.visible))

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const allSelected = computed(() => list.value.length > 0 && selectedIds.value.length === list.value.length)

function statusLabel(s) { return { pending:'未修改', confirming:'待确认', corrected:'已修改' }[s] || s }
function sortIcon(field) { if (sortBy.value !== field) return '⇅'; return sortOrder.value === 'asc' ? '↑' : '↓' }

function toggleSort(field) {
  if (sortBy.value === field) { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc' }
  else { sortBy.value = field; sortOrder.value = 'desc' }
  applyFilter()
}

function buildParams() {
  const p = { page: page.value, page_size: pageSize.value, sort_by: sortBy.value, sort_order: sortOrder.value }
  if (filters.value.name) p.name = filters.value.name
  if (filters.value.essayTitle) p.essay_title = filters.value.essayTitle
  if (filters.value.grade) p.grade = filters.value.grade
  if (filters.value.number) p.essay_number = filters.value.number
  if (filters.value.status) p.status = filters.value.status
  if (filters.value.mode) p.teaching_mode = filters.value.mode
  if (filters.value.collectedBy) p.collected_by = Number(filters.value.collectedBy)
  if (filters.value.remark) p.remark = filters.value.remark
  if (filterTaskSearch.value) p.task_name = filterTaskSearch.value
  if (filters.value.reviewerId) p.reviewer_id = Number(filters.value.reviewerId)
  if (filters.value.isSupplement) p.is_supplement = filters.value.isSupplement === 'true'
  if (filters.value.dateFrom) p.date_from = filters.value.dateFrom
  if (filters.value.dateTo) p.date_to = filters.value.dateTo
  if (filters.value.correctedFrom) p.corrected_from = filters.value.correctedFrom
  if (filters.value.correctedTo) p.corrected_to = filters.value.correctedTo
  if (filters.value.wordMin) p.word_count_min = Number(filters.value.wordMin)
  if (filters.value.wordMax) p.word_count_max = Number(filters.value.wordMax)
  if (filters.value.correctedMin) p.corrected_word_count_min = Number(filters.value.correctedMin)
  if (filters.value.correctedMax) p.corrected_word_count_max = Number(filters.value.correctedMax)
  return p
}

function syncScroll(source) {
  if (source === 'top' && tableWrap.value) {
    tableWrap.value.scrollLeft = topScroll.value.scrollLeft
  } else if (source === 'bottom' && topScroll.value) {
    topScroll.value.scrollLeft = tableWrap.value.scrollLeft
  }
}

function updateTopScrollWidth() {
  if (topScrollContent.value && tableWrap.value) {
    const table = tableWrap.value.querySelector('table')
    if (table) {
      topScrollContent.value.style.width = table.scrollWidth + 'px'
    }
  }
}

async function applyFilter() {
  page.value = 1; selectedIds.value = []
  saveFilters()
  await loadData()
}

async function loadData() {
  loading.value = true
  try {
    const res = await api.get('/essays', { params: buildParams() })
    list.value = res.data.items
    total.value = res.data.total
    pendingTotal.value = res.data.pending
    correctedTotal.value = res.data.corrected
    if (res.data.collectors) {
      collectorList.value = res.data.collectors
    }
  } catch { showToast('查询失败') }
  finally {
    loading.value = false
    await nextTick()
    updateTopScrollWidth()
  }
}

function goPage(p) { page.value = p; loadData() }
function jumpToPage() {
  const p = parseInt(jumpPage.value)
  if (isNaN(p) || p < 1 || p > totalPages.value) {
    showToast('请输入有效的页码')
    return
  }
  goPage(p)
}
function clearFilter() { filters.value = { name: '', essayTitle: '', grade: '', number: '', status: '', mode: '', collectedBy: defaultCollectedBy.value, remark: '', taskId: '', reviewerId: '', isSupplement: '', dateFrom: '', dateTo: '', correctedFrom: '', correctedTo: '', wordMin: '', wordMax: '', correctedMin: '', correctedMax: '' }; filterTaskSearch.value = ''; applyFilter() }

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}
function toggleAll() {
  if (allSelected.value) selectedIds.value = []
  else selectedIds.value = list.value.map(e => e.id)
}

async function inlineEdit(e, field, val) {
  try {
    const res = await api.put(`/essays/${e.id}`, null, { params: { [field]: val } })
    Object.assign(e, res.data)
    showToast('已更新')
  } catch(err) { showToast(err.response?.data?.detail || '更新失败') }
}

async function batchDelete() {
  if (!selectedIds.value.length) return
  deletingEssay.value = null  // 批量模式
  deleteFileChecked.value = false
  showDelete.value = true
}

async function batchExportDocx() {
  if (!selectedIds.value.length) return
  try {
    showLoadingToast({ message: '正在导出...', forbidClick: true, duration: 0 })
    const res = await api.post('/essays/batch-export-docx', selectedIds.value, { responseType: 'blob' })
    
    // 从响应头解析文件名
    const disposition = res.headers['content-disposition']
    let filename = '作文导出.zip'
    if (disposition) {
      const p = disposition.split(';')
      for (const part of p) {
        const trim = part.trim()
        if (trim.startsWith('filename*=')) {
          const val = trim.split("''").pop()
          if (val) filename = decodeURIComponent(val.replace(/"/g, ''))
          break
        } else if (trim.startsWith('filename=')) {
          const val = trim.split('=')[1]
          if (val) filename = val.replace(/"/g, '')
        }
      }
    }
    
    // 创建 Blob URL 并下载
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
    
    closeToast()
    showSuccessToast('导出成功')
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '导出失败')
  }
}

async function doBatchCollector() {
  if (!batchCollectorId.value) { showToast('请选择收集者'); return }
  try {
    await api.post('/essays/batch-update', { ids: selectedIds.value, collected_by: batchCollectorId.value })
    showSuccessToast('修改成功')
    selectedIds.value = []
    batchCollectorId.value = ''
    await loadData()
  } catch (err) { showFailToast(err.response?.data?.detail || '修改失败') }
}

async function doBatchTask() {
  try {
    await api.post('/essays/batch-update', { ids: selectedIds.value, task_id: batchTaskId.value || null })
    showSuccessToast('修改成功')
    selectedIds.value = []
    batchTaskId.value = 0
    await loadData()
  } catch (err) { showFailToast(err.response?.data?.detail || '修改失败') }
}

async function loadTasks() {
  try {
    const res = await api.get('/essays/tasks')
    taskList.value = res.data
  } catch {}
}

async function loadReviewers() {
  try {
    const res = await api.get('/essays/reviewers')
    reviewerList.value = res.data || []
  } catch {}
}

function confirmDelete(e) {
  deletingEssay.value = e
  deleteFileChecked.value = false
  showDelete.value = true
}

async function doDelete() {
  const e = deletingEssay.value
  // 批量模式
  if (!e && selectedIds.value.length) {
    let done = 0
    for (const id of selectedIds.value) {
      try { await api.delete(`/essays/${id}`, { params: { delete_file: deleteFileChecked.value, permanent: deleteFileChecked.value } }) ; done++ } catch {}
    }
    showToast(`已处理 ${done}/${selectedIds.value.length} 条`)
    selectedIds.value = []
    applyFilter()
    return
  }
  // 单条模式
  if (!e) return
  try {
    await api.delete(`/essays/${e.id}`, { params: { delete_file: deleteFileChecked.value, permanent: deleteFileChecked.value } })
    applyFilter()
    showToast(deleteFileChecked.value ? '已彻底删除（含文件）' : '已移入回收站')
  } catch (err) { showToast(err.response?.data?.detail || '删除失败') }
  deletingEssay.value = null
}

function goDetail(e) { router.push(`/review/detail/${e.id}`) }

function exportCSV() {
  const headers = ['学生','年级','作文','第几次','提交方式','状态','收集者','备注','收集时间','修改时间']
  const rows = list.value.map(e => [
    e.student_name, e.grade, e.essay_title, `第${e.essay_number}次`,
    e.teaching_mode, statusLabel(e.status), e.collector_name, e.remark,
    e.created_at ? formatDateTime(e.created_at) : '', e.corrected_at ? formatDateTime(e.corrected_at) : '',
  ])
  const csv = [headers.join(','), ...rows.map(r => r.map(v => `"${v}"`).join(','))].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = '作文列表.csv'; a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  loadColumnSettings()
  await loadTasks()
  loadReviewers()
  // 点击外部关闭任务下拉框
  document.addEventListener('click', closeTaskDropdown)
  // 从URL参数读取task_id（优先：重置筛选后再按任务筛选）
  const taskIdFromQuery = Number(route.query.task_id)
  if (taskIdFromQuery) {
    // 重置所有筛选
    Object.keys(filters.value).forEach(k => { filters.value[k] = '' })
    filters.value.collectedBy = defaultCollectedBy.value
    filters.value.taskId = taskIdFromQuery
    const t = taskList.value.find(x => x.id === taskIdFromQuery)
    if (t) filterTaskSearch.value = t.name
  } else {
    // 恢复之前保存的筛选，如果没有则设置默认值
    const hasSaved = loadFilters()
    if (!hasSaved) {
      filters.value.collectedBy = defaultCollectedBy.value
    }
    // 同步任务搜索框文字
    if (filters.value.taskId && taskList.value.length) {
      const t = taskList.value.find(x => x.id == filters.value.taskId)
      if (t) filterTaskSearch.value = t.name
    }
  }
  await applyFilter()
})
onUnmounted(() => {
  document.removeEventListener('click', closeTaskDropdown)
})
</script>

<style scoped>
.page { padding: 0; }

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.filter-row { display: flex; align-items: center; gap: 4px; }
.filter-label { font-size: 13px; color: #666; white-space: nowrap; }
.filter-input { padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 13px; outline: none; }
.filter-input:focus { border-color: #4096ff; }
.filter-input[type="number"] { width: 60px; }

.task-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 100;
  min-width: 200px;
  max-height: 200px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-top: 4px;
}
.task-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  border-bottom: 1px solid #f5f5f5;
}
.task-item:hover { background: #f0f0f0; }
.task-item-active { background: #e6f4ff; color: #1677ff; }

.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stats-bar {
  display: flex;
  gap: 20px;
  padding: 8px 0;
  font-size: 13px;
  color: #666;
}
.stats-bar strong { font-size: 15px; }
.stat-pending { color: #d46b08; }
.stat-corrected { color: #52c41a; }

  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.inline-select {
  padding: 2px 4px;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  background: transparent;
}
.inline-select:hover { border-color: #d9d9d9; background: #fff; }
.inline-select:focus { border-color: #4096ff; outline: none; }

.row-selected { background: #e6f4ff !important; }

.sortable { cursor: pointer; user-select: none; }
.sortable:hover { background: #f0f0f0; }
.th-dragging { opacity: 0.5; background: #e6f4ff !important; }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 20px 0;
}
.page-info { font-size: 14px; color: #333; }
.page-jump { display: flex; align-items: center; gap: 4px; font-size: 13px; color: #666; }
.page-jump-input { width: 50px; padding: 4px 6px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; text-align: center; }
.page-jump-input:focus { border-color: #4096ff; outline: none; }
.page-size { display: flex; align-items: center; gap: 4px; font-size: 13px; color: #666; }
.page-size select { padding: 4px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; }

.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.tag-pending { background: #fff7e6; color: #d46b08; }
.tag-confirming { background: #e6f4ff; color: #1677ff; }
.tag-correcting { background: #e6f4ff; color: #1677ff; }
.tag-corrected { background: #f6ffed; color: #52c41a; }

.btn-disabled { opacity: 0.5; cursor: not-allowed; pointer-events: none; }
.row-readonly { background: #fafafa; }
.readonly-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #e6f4ff;
  border-radius: 4px;
  color: #1677ff;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.readonly-hint:hover { background: #bae0ff; }
.icon-readonly { font-size: 14px; }
.text-readonly { font-size: 11px; }

.scroll-sync {
  overflow-x: auto;
  height: 0;
}
.scroll-sync-content {
  height: 1px;
}
.scroll-sync::-webkit-scrollbar { height: 6px; }
.scroll-sync::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 3px; }
.scroll-sync::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 3px; }
.scroll-sync::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }

@media (max-width: 767px) {
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-row { width: 100%; }
  .filter-input { flex: 1; }
  .stats-bar { flex-wrap: wrap; }
  .pagination { flex-wrap: wrap; justify-content: center; }
}
</style>
