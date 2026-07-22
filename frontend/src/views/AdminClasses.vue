<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">班级管理</div>

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

    <!-- 桌面端 -->
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

    <!-- 手机端 -->
    <template v-else>
      <van-button type="success" size="small" style="margin:12px" @click="openClassDialog()">创建班级</van-button>
      <van-button type="primary" size="small" style="margin:12px" @click="$refs.csvInput.click()">导入CSV</van-button>
      <input type="file" ref="csvInput" accept=".csv" style="display:none" @change="previewCSV" />
      <van-cell-group inset v-for="org in orgs" :key="org.id" style="margin-top:12px">
        <van-cell :title="org.name" :label="org.desc" />
        <van-cell v-for="c in getClassesByOrg(org.id)" :key="c.id" :title="c.name" />
      </van-cell-group>
    </template>

    <!-- 弹窗 -->
    <van-dialog v-model:show="showOrgDialog" :title="editingOrg.id ? '编辑培训班' : '创建培训班'" show-cancel-button @confirm="saveOrg">
      <van-form><van-field v-model="orgForm.name" label="名称" :rules="[{required:true}]" />
      <van-field v-model="orgForm.desc" label="简介" /></van-form>
    </van-dialog>

    <van-dialog v-model:show="showClassDialog" :title="editingClass.id ? '编辑班级' : '创建班级'" show-cancel-button @confirm="saveClass">
      <van-form>
        <van-field v-model="classForm.org_id" label="培训班ID" type="digit" :rules="[{required:true}]" />
        <van-field v-model="classForm.name" label="班级名称" :rules="[{required:true}]" />
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
const orgs = ref([])
const classes = ref([])
const showOrgDialog = ref(false)
const showClassDialog = ref(false)
const editingOrg = ref({})
const editingClass = ref({})
const orgForm = ref({ name:'', desc:'' })
const classForm = ref({ org_id:'', name:'' })
const importing = ref(false)
const importResult = ref('')
const showImportPreview = ref(false)
const previewClasses = ref([])
const selectedNames = ref([])
let pendingFile = null

onMounted(loadData)

async function loadData() {
  try {
    const [orgRes, clsRes] = await Promise.all([api.get('/admin/organizations'), api.get('/admin/classes')])
    orgs.value = orgRes.data; classes.value = clsRes.data
  } catch {}
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

function getClassesByOrg(orgId) { return classes.value.filter(c => c.org_id === orgId) }

function openOrgDialog(org) {
  if (org) { editingOrg.value = org; orgForm.value = { name: org.name, desc: org.desc || '' } }
  else { editingOrg.value = {}; orgForm.value = { name:'', desc:'' } }
  showOrgDialog.value = true
}
function openClassDialog(cls) {
  if (cls) { editingClass.value = cls; classForm.value = { org_id: String(cls.org_id), name: cls.name } }
  else { editingClass.value = {}; classForm.value = { org_id:'', name:'' } }
  showClassDialog.value = true
}

async function saveOrg() {
  try {
    if (editingOrg.value.id) {
      await api.put(`/admin/organizations/${editingOrg.value.id}`, orgForm.value)
      showToast('更新成功')
    } else {
      await api.post('/admin/organizations', orgForm.value)
      showToast('创建成功')
    }
    showOrgDialog.value = false; loadData()
  } catch(err) { showToast(err.response?.data?.detail || '操作失败') }
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

function confirmDelOrg(org) {
  showDialog({ title: '确认删除', message: `删除培训班「${org.name}」？其下班级不会被删`, showCancelButton: true })
    .then(async () => {
      await api.delete(`/admin/organizations/${org.id}`)
      orgs.value = orgs.value.filter(x => x.id !== org.id)
      showToast('已删除')
    }).catch(() => {})
}
function confirmDelClass(cls) {
  showDialog({ title: '确认删除', message: `删除班级「${cls.name}」？`, showCancelButton: true })
    .then(async () => {
      await api.delete(`/admin/classes/${cls.id}`)
      classes.value = classes.value.filter(x => x.id !== cls.id)
      showToast('已删除')
    }).catch(() => {})
}
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }
</style>
