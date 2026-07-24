<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">班级管理</div>

    <!-- 桌面端标签页 -->
    <div v-if="isDesktop" class="tabs" style="margin-bottom:16px">
      <button :class="['tab-btn', { active: activeTab === 'classes' }]" @click="activeTab = 'classes'">班级管理</button>
      <button :class="['tab-btn', { active: activeTab === 'tasks' }]" @click="activeTab = 'tasks'">收集任务</button>
    </div>

    <!-- 手机端标签页 -->
    <van-tabs v-else v-model:active="activeTab" style="margin-bottom:12px">
      <van-tab title="班级管理" name="classes" />
      <van-tab title="收集任务" name="tasks" />
    </van-tabs>

    <!-- 班级管理内容 -->
    <div v-show="activeTab === 'classes'">
      <div v-if="isDesktop" style="margin-bottom:16px;display:flex;gap:8px;align-items:center">
        <button class="btn btn-success" @click="openClassDialog()">+ 创建班级</button>
        <label class="btn btn-primary" style="cursor:pointer">📥 导入CSV<input type="file" accept=".csv" @change="previewCSV" style="display:none" /></label>
        <span v-if="importing" style="font-size:13px;color:#999">解析中...</span>
      </div>

      <!-- 导入预览弹窗 -->
      <div v-if="showImportPreview" class="modal-overlay" @click.self="showImportPreview=false">
        <div class="modal-box" style="max-width:600px">
          <h3>📥 选择要导入的班级</h3>
          <p style="font-size:13px;color:#999;margin-bottom:12px">共 {{ previewClasses.length }} 个班级，已存在 {{ previewClasses.filter(c => c.exists).length }} 个</p>
          <div style="max-height:400px;overflow-y:auto">
            <label v-for="(c, i) in previewClasses" :key="i"
              style="display:flex;align-items:center;gap:8px;padding:8px 4px;border-bottom:1px solid #f5f5f5;cursor:pointer">
              <input type="checkbox" :value="c.name" v-model="selectedNames" style="width:auto" />
              <span>{{ c.name }}</span>
              <span v-if="c.exists" class="tag tag-corrected" style="margin-left:auto">已存在</span>
            </label>
          </div>
          <div class="form-actions" style="margin-top:12px">
            <button class="btn" @click="showImportPreview=false">取消</button>
            <span style="font-size:13px;color:#999">已选 {{ selectedNames.length }} 个</span>
            <button class="btn btn-primary" @click="confirmImport" :disabled="selectedNames.length===0">确认导入</button>
          </div>
        </div>
      </div>

      <!-- 桌面端班级列表 -->
      <div v-if="isDesktop">
        <div v-for="org in orgs" :key="org.id" class="card" style="margin-bottom:16px">
          <div class="card-header">
            <h3>🏫 {{ org.name }}</h3>
            <div style="display:flex;gap:8px;align-items:center">
              <span style="font-size:13px;color:#999">{{ org.desc }}</span>
              <button class="btn" style="font-size:12px;padding:2px 8px;color:#ff4d4f" @click="confirmDelOrg(org)">删除</button>
            </div>
          </div>
          <table class="desktop-table" v-if="getClassesByOrg(org.id).length">
            <thead><tr><th>班级名称</th><th>创建时间</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="c in getClassesByOrg(org.id)" :key="c.id">
                <td>{{ c.name }}</td>
                <td>{{ c.created_at?.substring(0,10) }}</td>
                <td style="white-space:nowrap">
                  <button class="btn" style="font-size:12px;padding:2px 8px" @click="openClassDialog(c)">编辑</button>
                  <button class="btn" style="font-size:12px;padding:2px 8px;color:#ff4d4f" @click="confirmDelClass(c)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else style="padding:16px;color:#999;font-size:13px">暂无班级</div>
        </div>
      </div>

      <!-- 手机端班级列表 -->
      <template v-else>
        <van-button type="success" size="small" style="margin:12px" @click="openClassDialog()">创建班级</van-button>
        <van-button type="primary" size="small" style="margin:12px" @click="$refs.csvInput.click()">导入CSV</van-button>
        <input type="file" ref="csvInput" accept=".csv" style="display:none" @change="previewCSV" />
        <van-cell-group inset v-for="org in orgs" :key="org.id" style="margin-top:12px">
          <van-cell :title="org.name" :label="org.desc" />
          <van-cell v-for="c in getClassesByOrg(org.id)" :key="c.id" :title="c.name" />
        </van-cell-group>
      </template>
    </div>

    <!-- 收集模板内容 -->
    <div v-show="activeTab === 'tasks'">
      <div v-if="isDesktop" style="margin-bottom:16px">
        <button class="btn btn-success" @click="openTaskDialog()">+ 创建收集任务</button>
      </div>
      <div v-else style="margin:12px">
        <van-button type="success" size="small" @click="openTaskDialog()">创建收集任务</van-button>
      </div>

      <!-- 桌面端模板列表 -->
      <div v-if="isDesktop">
        <table class="desktop-table" v-if="tasks.length">
          <thead>
            <tr>
              <th>模板名称</th>
              <th>年级</th>
              <th>第几次</th>
              <th>文章主题</th>
              <th>课程名称</th>
              <th>提交方式</th>
              <th>截止时间</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tasks" :key="t.id">
              <td>{{ t.name }}</td>
              <td>{{ t.grade }}</td>
              <td>第{{ t.essay_number }}次</td>
              <td>{{ t.essay_topic || '-' }}</td>
              <td>{{ t.course_name || '-' }}</td>
              <td>{{ t.teaching_mode || '线下' }}</td>
              <td>{{ t.deadline ? formatDeadline(t.deadline) : '无限制' }}</td>
              <td>
                <span :class="['tag', t.is_active ? 'tag-pending' : 'tag-corrected']">
                  {{ t.is_active ? '收集中' : '已结束' }}
                </span>
              </td>
              <td style="white-space:nowrap">
                <button class="btn" style="font-size:12px;padding:2px 8px" @click="openTaskDialog(t)">编辑</button>
                <button class="btn" style="font-size:12px;padding:2px 8px" @click="toggleTaskActive(t)">
                  {{ t.is_active ? '结束收集' : '开始收集' }}
                </button>
                <button class="btn" style="font-size:12px;padding:2px 8px;color:#ff4d4f" @click="confirmDelTask(t)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="card" style="padding:32px;text-align:center;color:#999">
          暂无收集任务，点击上方按钮创建
        </div>
      </div>

      <!-- 手机端模板列表 -->
      <template v-else>
        <van-cell-group inset v-if="tasks.length" style="margin-top:12px">
          <van-cell v-for="t in tasks" :key="t.id"
            :title="t.name"
            :label="`${t.grade} 第${t.essay_number}次 ${t.essay_topic || ''}`"
            is-link @click="openTaskDialog(t)">
            <template #right-icon>
              <van-tag :type="t.is_active ? 'primary' : 'default'" style="margin-right:8px">
                {{ t.is_active ? '收集中' : '已结束' }}
              </van-tag>
            </template>
          </van-cell>
        </van-cell-group>
        <div v-else style="padding:32px;text-align:center;color:#999">
          暂无收集任务
        </div>
      </template>
    </div>

    <!-- 班级弹窗 -->
    <van-dialog v-model:show="showClassDialog" :title="editingClass.id ? '编辑班级' : '创建班级'" show-cancel-button @confirm="saveClass">
      <van-form>
        <van-field v-model="classForm.org_id" label="培训班ID" type="digit" :rules="[{required:true}]" />
        <van-field v-model="classForm.name" label="班级名称" :rules="[{required:true}]" />
      </van-form>
    </van-dialog>

    <!-- 模板弹窗 -->
    <div v-if="showTaskDialog" class="modal-overlay" @click.self="showTaskDialog=false">
      <div class="modal-box" style="max-width:500px">
        <h3>{{ editingTask.id ? '编辑收集任务' : '创建收集任务' }}</h3>
        <van-form @submit="saveTask">
          <van-cell-group inset>
            <van-field v-model="taskForm.name" label="模板名称" placeholder="如：高二第三次作文" :rules="[{required:true}]" />
            <van-field :model-value="taskForm.grade" is-link readonly label="年级" placeholder="请选择年级" @click="showTaskGradePicker=true" :rules="[{required:true}]" />
            <van-field v-model="taskForm.essay_number" label="第几次作文" type="digit" :rules="[{required:true}]" />
            <van-field v-model="taskForm.essay_topic" label="文章主题" placeholder="如：议论文写作" />
            <van-field v-model="taskForm.course_name" label="课程名称" placeholder="如：语文" />
            <van-field name="teaching_mode" label="提交方式">
              <template #input>
                <van-radio-group v-model="taskForm.teaching_mode" direction="horizontal">
                  <van-radio name="线下" style="margin-right:16px">线下</van-radio>
                  <van-radio name="线上">线上</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field v-model="taskForm.deadlineStr" label="截止时间" type="datetime-local" placeholder="可选" />
            <van-field name="is_active" label="立即开始收集">
              <template #input>
                <van-switch v-model="taskForm.is_active" size="24" />
              </template>
            </van-field>
          </van-cell-group>
          <div style="margin:16px;display:flex;gap:8px">
            <van-button block @click="showTaskDialog=false">取消</van-button>
            <van-button block type="primary" native-type="submit">保存</van-button>
          </div>
        </van-form>
      </div>
    </div>

    <!-- 年级选择器 -->
    <van-action-sheet v-model:show="showTaskGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectTaskGrade(g)" />
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showDialog, showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api from '../api'

const { isDesktop } = useScreen()
const activeTab = ref('classes')

// 班级相关
const orgs = ref([])
const classes = ref([])
const showClassDialog = ref(false)
const editingClass = ref({})
const classForm = ref({ org_id:'', name:'' })
const importing = ref(false)
const showImportPreview = ref(false)
const previewClasses = ref([])
const selectedNames = ref([])
let pendingFile = null

// 任务相关
const tasks = ref([])
const showTaskDialog = ref(false)
const editingTask = ref({})
const showTaskGradePicker = ref(false)
const grades = ['初一','初二','初三','高一','高二','高三']
const taskForm = ref({
  name: '', grade: '', essay_number: 1, essay_topic: '', course_name: '',
  teaching_mode: '线下', deadlineStr: '', is_active: false
})

onMounted(loadData)

async function loadData() {
  try {
    const [orgRes, clsRes, taskRes] = await Promise.all([
      api.get('/admin/organizations'),
      api.get('/admin/classes'),
      api.get('/admin/tasks')
    ])
    orgs.value = orgRes.data
    classes.value = clsRes.data
    tasks.value = taskRes.data
  } catch {}
}

// ===== 班级相关函数 =====
function getClassesByOrg(orgId) { return classes.value.filter(c => c.org_id === orgId) }

function openClassDialog(cls) {
  if (cls) { editingClass.value = cls; classForm.value = { org_id: String(cls.org_id), name: cls.name } }
  else { editingClass.value = {}; classForm.value = { org_id:'', name:'' } }
  showClassDialog.value = true
}

async function saveClass() {
  try {
    const payload = { ...classForm.value, org_id: parseInt(classForm.value.org_id) }
    if (editingClass.value.id) {
      await api.put(`/admin/classes/${editingClass.value.id}`, payload)
      showToast('更新成功')
    } else {
      await api.post('/admin/classes', payload)
      showToast('创建成功')
    }
    showClassDialog.value = false; loadData()
  } catch(err) { showToast(err.response?.data?.detail || '操作失败') }
}

function confirmDelClass(cls) {
  showDialog({ title: '确认删除', message: `删除班级「${cls.name}」？`, showCancelButton: true })
    .then(async () => {
      await api.delete(`/admin/classes/${cls.id}`)
      classes.value = classes.value.filter(x => x.id !== cls.id)
      showToast('已删除')
    }).catch(() => {})
}

function confirmDelOrg(org) {
  showDialog({ title: '确认删除', message: `删除培训班「${org.name}」？其下班级不会被删`, showCancelButton: true })
    .then(async () => {
      await api.delete(`/admin/organizations/${org.id}`)
      orgs.value = orgs.value.filter(x => x.id !== org.id)
      showToast('已删除')
    }).catch(() => {})
}

async function previewCSV(e) {
  const file = e.target.files[0]
  if (!file) return
  pendingFile = file
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await api.post('/admin/import-classes-csv/preview', fd)
    previewClasses.value = res.data.classes
    selectedNames.value = res.data.classes.filter(c => !c.exists).map(c => c.name)
    showImportPreview.value = true
  } catch(err) {
    showToast('解析失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    importing.value = false
    e.target.value = ''
  }
}

async function confirmImport() {
  if (!pendingFile || selectedNames.value.length === 0) return
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', pendingFile)
    fd.append('selected', JSON.stringify(selectedNames.value))
    const res = await api.post('/admin/import-classes-csv/confirm', fd)
    showToast(`导入 ${res.data.imported} 个，跳过 ${res.data.skipped} 个`)
    showImportPreview.value = false
    loadData()
  } catch(err) {
    showToast('导入失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    importing.value = false
  }
}

// ===== 模板相关函数 =====
function formatDeadline(deadline) {
  if (!deadline) return '无限制'
  const d = new Date(deadline)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

function openTaskDialog(tpl) {
  if (tpl) {
    editingTask.value = tpl
    const deadlineStr = tpl.deadline ? new Date(tpl.deadline).toISOString().slice(0, 16) : ''
    taskForm.value = {
      name: tpl.name, grade: tpl.grade, essay_number: tpl.essay_number,
      essay_topic: tpl.essay_topic || '', course_name: tpl.course_name || '',
      teaching_mode: tpl.teaching_mode || '线下', deadlineStr, is_active: tpl.is_active
    }
  } else {
    editingTask.value = {}
    taskForm.value = {
      name: '', grade: '', essay_number: 1, essay_topic: '', course_name: '',
      teaching_mode: '线下', deadlineStr: '', is_active: false
    }
  }
  showTaskDialog.value = true
}

function selectTaskGrade(g) {
  taskForm.value.grade = g
  showTaskGradePicker.value = false
}

async function saveTask() {
  try {
    const payload = {
      name: taskForm.value.name,
      grade: taskForm.value.grade,
      essay_number: parseInt(taskForm.value.essay_number) || 1,
      essay_topic: taskForm.value.essay_topic,
      course_name: taskForm.value.course_name,
      teaching_mode: taskForm.value.teaching_mode,
      deadline: taskForm.value.deadlineStr ? new Date(taskForm.value.deadlineStr).toISOString() : null,
      is_active: taskForm.value.is_active,
    }
    if (editingTask.value.id) {
      await api.put(`/admin/tasks/${editingTask.value.id}`, payload)
      showToast('更新成功')
    } else {
      await api.post('/admin/tasks', payload)
      showToast('创建成功')
    }
    showTaskDialog.value = false
    loadData()
  } catch(err) { showToast(err.response?.data?.detail || '操作失败') }
}

async function toggleTaskActive(tpl) {
  try {
    const res = await api.put(`/admin/tasks/${tpl.id}/activate`)
    showToast(res.data?.is_active ? '已开始收集' : '已结束收集')
    loadData()
  } catch(err) { showToast(err.response?.data?.detail || '操作失败') }
}

function confirmDelTask(tpl) {
  showDialog({ title: '确认删除', message: `删除收集模板「${tpl.name}」？`, showCancelButton: true })
    .then(async () => {
      await api.delete(`/admin/tasks/${tpl.id}`)
      tasks.value = tasks.value.filter(x => x.id !== tpl.id)
      showToast('已删除')
    }).catch(() => {})
}
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }

.tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e8e8e8;
}
.tab-btn {
  padding: 8px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}
.tab-btn:hover { color: #1890ff; }
.tab-btn.active {
  color: #1890ff;
  border-bottom-color: #1890ff;
  font-weight: 500;
}
.picker-list { max-height: 300px; overflow-y: auto; }
</style>
