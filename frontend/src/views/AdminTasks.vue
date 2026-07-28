<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">任务列表</div>

    <div v-if="isDesktop" style="margin-bottom:16px">
      <button class="btn btn-success" @click="openTaskDialog()">+ 创建收集任务</button>
    </div>
    <div v-else style="margin:12px">
      <van-button type="success" size="small" @click="openTaskDialog()">创建收集任务</van-button>
    </div>

    <!-- 桌面端任务列表 -->
    <div v-if="isDesktop">
      <table class="desktop-table" v-if="tasks.length">
        <thead>
          <tr>
            <th>任务名称</th>
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

    <!-- 手机端任务列表 -->
    <template v-else>
      <van-cell-group inset v-if="tasks.length" style="margin-top:12px">
        <van-cell v-for="t in tasks" :key="t.id"
          :title="t.name"
          :label="`${t.grade} 第${t.essay_number}次 ${t.course_name ? '· ' + t.course_name : ''} ${t.essay_topic || ''}`"
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

    <!-- 任务弹窗 -->
    <div v-if="showTaskDialog" class="modal-overlay" @click.self="showTaskDialog=false">
      <div class="modal-box" style="max-width:500px">
        <h3>{{ editingTask.id ? '编辑收集任务' : '创建收集任务' }}</h3>
        <van-form @submit="saveTask">
          <van-cell-group inset>
            <van-field v-model="taskForm.name" label="任务名称" placeholder="如：高二第三次作文" :rules="[{required:true}]" />
            <van-field :model-value="taskForm.grade" is-link readonly label="年级" placeholder="请选择年级" @click="showTaskGradePicker=true" :rules="[{required:true}]" />
            <van-field v-model="taskForm.essay_number" label="第几次作文" type="digit" :rules="[{required:true}]" />
            <van-field v-model="taskForm.essay_topic" label="文章主题" placeholder="如：议论文写作" />
            <van-field :model-value="taskForm.course_name || '请选择课程'" is-link readonly label="课程名称" placeholder="请选择课程" @click="showCoursePicker=true" />
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

    <!-- 课程选择器 -->
    <van-action-sheet v-model:show="showCoursePicker" title="选择课程">
      <div class="picker-list">
        <van-cell title="不选择课程" @click="selectCourse(null)" style="color:#999" />
        <van-cell v-for="c in courses" :key="c.id"
          :title="c.name"
          :label="c.org_name || ''"
          @click="selectCourse(c)" />
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

const tasks = ref([])
const courses = ref([])
const showTaskDialog = ref(false)
const editingTask = ref({})
const showTaskGradePicker = ref(false)
const showCoursePicker = ref(false)
const grades = ['初一','初二','初三','高一','高二','高三']
const taskForm = ref({
  name: '', grade: '', essay_number: 1, essay_topic: '', course_name: '',
  teaching_mode: '线下', deadlineStr: '', is_active: false
})

onMounted(loadData)

async function loadData() {
  try {
    const [taskRes, classRes, orgRes] = await Promise.all([
      api.get('/admin/tasks'),
      api.get('/admin/classes'),
      api.get('/admin/organizations')
    ])
    tasks.value = taskRes.data
    const orgs = orgRes.data || []
    const orgMap = {}
    orgs.forEach(o => { orgMap[o.id] = o.name })
    courses.value = (classRes.data || []).map(c => ({
      ...c,
      org_name: orgMap[c.org_id] || ''
    }))
  } catch {}
}

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

function selectCourse(c) {
  taskForm.value.course_name = c ? c.name : ''
  showCoursePicker.value = false
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
  showDialog({ title: '确认删除', message: `删除收集任务「${tpl.name}」？`, showCancelButton: true })
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
.picker-list { max-height: 300px; overflow-y: auto; }
</style>
