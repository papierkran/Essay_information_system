<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">课程管理</div>

    <div v-if="isDesktop" style="margin-bottom:16px;display:flex;gap:8px;align-items:center">
      <button class="btn btn-success" @click="openCourseDialog()">+ 创建课程</button>
      <label class="btn btn-primary" style="cursor:pointer">📥 导入CSV<input type="file" accept=".csv" @change="previewCSV" style="display:none" /></label>
      <span v-if="importing" style="font-size:13px;color:#999">解析中...</span>
    </div>

    <!-- 导入预览弹窗 -->
    <div v-if="showImportPreview" class="modal-overlay" @click.self="showImportPreview=false">
      <div class="modal-box" style="max-width:600px">
        <h3>📥 选择要导入的课程</h3>
        <p style="font-size:13px;color:#999;margin-bottom:12px">共 {{ previewCourses.length }} 个，已存在 {{ previewCourses.filter(c => c.exists).length }} 个</p>
        <div style="max-height:400px;overflow-y:auto">
          <label v-for="(c, i) in previewCourses" :key="i"
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

    <!-- 手机端操作按钮 -->
    <template v-if="!isDesktop">
      <van-button type="success" size="small" style="margin:12px" @click="openCourseDialog()">创建课程</van-button>
      <van-button type="primary" size="small" style="margin:12px" @click="$refs.csvInput.click()">导入CSV</van-button>
      <input type="file" ref="csvInput" accept=".csv" style="display:none" @change="previewCSV" />
    </template>

    <!-- 桌面端课程列表 -->
    <div v-if="isDesktop">
      <table class="desktop-table" v-if="courses.length">
        <thead>
          <tr>
            <th>课程名称</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in courses" :key="c.id">
            <td>{{ c.name }}</td>
            <td>{{ c.created_at?.substring(0,10) }}</td>
            <td style="white-space:nowrap">
              <button class="btn" style="font-size:12px;padding:2px 8px" @click="openCourseDialog(c)">编辑</button>
              <button class="btn" style="font-size:12px;padding:2px 8px;color:#ff4d4f" @click="confirmDelCourse(c)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="card" style="padding:32px;text-align:center;color:#999">暂无课程</div>
    </div>

    <!-- 手机端课程列表 -->
    <van-cell-group v-if="!isDesktop" inset style="margin-top:12px">
      <van-cell v-for="c in courses" :key="c.id" :title="c.name"
        :label="c.created_at?.substring(0,10)"
        is-link @click="openCourseDialog(c)" />
    </van-cell-group>

    <!-- 课程弹窗 -->
    <van-dialog v-model:show="showCourseDialog" :title="editingCourse.id ? '编辑课程' : '创建课程'" show-cancel-button @confirm="saveCourse">
      <van-form>
        <van-field v-model="courseForm.name" label="课程名称" :rules="[{required:true}]" />
      </van-form>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showDialog, showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api from '../api'

const { isDesktop } = useScreen()
const courses = ref([])
const showCourseDialog = ref(false)
const editingCourse = ref({})
const courseForm = ref({ name:'' })
const importing = ref(false)
const showImportPreview = ref(false)
const previewCourses = ref([])
const selectedNames = ref([])
let pendingFile = null

onMounted(loadData)

async function loadData() {
  try {
    const res = await api.get('/admin/courses')
    courses.value = res.data
  } catch {}
}

function openCourseDialog(cls) {
  if (cls) { editingCourse.value = cls; courseForm.value = { name: cls.name } }
  else { editingCourse.value = {}; courseForm.value = { name:'' } }
  showCourseDialog.value = true
}

async function saveCourse() {
  try {
    const payload = { name: courseForm.value.name }
    if (editingCourse.value.id) {
      await api.put(`/admin/courses/${editingCourse.value.id}`, payload)
      showToast('更新成功')
    } else {
      await api.post('/admin/courses', payload)
      showToast('创建成功')
    }
    showCourseDialog.value = false; loadData()
  } catch(err) { showToast(err.response?.data?.detail || '操作失败') }
}

function confirmDelCourse(cls) {
  showDialog({ title: '确认删除', message: `删除课程「${cls.name}」？`, showCancelButton: true })
    .then(async () => {
      await api.delete(`/admin/courses/${cls.id}`)
      courses.value = courses.value.filter(x => x.id !== cls.id)
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
    const res = await api.post('/admin/import-courses-csv/preview', fd)
    previewCourses.value = res.data.courses
    selectedNames.value = res.data.courses.filter(c => !c.exists).map(c => c.name)
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
    const res = await api.post('/admin/import-courses-csv/confirm', fd)
    showToast(`导入 ${res.data.imported} 个，跳过 ${res.data.skipped} 个`)
    showImportPreview.value = false
    loadData()
  } catch(err) {
    showToast('导入失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }
</style>
