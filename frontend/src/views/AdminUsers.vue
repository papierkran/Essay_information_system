<template>
  <div class="page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="isDesktop" class="page-title">用户管理</div>

    <button v-if="isDesktop" class="btn btn-primary" style="margin-bottom:16px" @click="showAdd = true">+ 添加用户</button>
    <van-button v-else type="primary" size="small" style="margin:12px" @click="showAdd = true">添加用户</van-button>

    <!-- 桌面端：表格 -->
    <table v-if="isDesktop && list.length" class="desktop-table">
      <thead>
        <tr>
          <th>用户名</th><th>姓名</th><th>手机号</th><th>角色</th><th>状态</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in list" :key="u.id">
          <td>{{ u.username }}</td>
          <td>{{ u.nickname || '-' }}</td>
          <td>{{ u.phone || '-' }}</td>
          <td>{{ roleLabel(u.role) }}</td>
          <td><span :class="u.is_active ? 'tag tag-corrected' : 'tag tag-pending'">{{ u.is_active ? '启用' : '禁用' }}</span></td>
          <td style="white-space:nowrap">
            <template v-if="u.username === 'admin'">
              <template v-if="u.id === currentUserId">
                <button class="btn" style="font-size:12px;padding:4px 8px" @click="changePassword(u)">改密</button>
                <span style="color:#999;font-size:12px">不可编辑</span>
              </template>
              <span v-else style="color:#999;font-size:12px">无法修改</span>
            </template>
            <template v-else>
              <button class="btn" style="font-size:12px;padding:4px 8px" @click="editUser(u)">编辑</button>
              <button class="btn" style="font-size:12px;padding:4px 8px" @click="changePassword(u)">改密</button>
              <button class="btn" style="font-size:12px;padding:4px 8px;color:#ff4d4f" @click="confirmDelete(u)">删除</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 手机端 -->
    <van-list v-if="!isDesktop" v-model:loading="loading" :finished="finished" @load="load">
      <van-cell v-for="u in list" :key="u.id" :title="u.nickname || u.username"
        :label="`${u.username} · ${roleLabel(u.role)}`">
        <template #right-icon>
          <template v-if="u.username === 'admin' && u.id === currentUserId">
            <van-icon name="edit" @click="changePassword(u)" />
            <span style="color:#999;font-size:12px;margin-left:4px">改密</span>
          </template>
          <template v-else-if="u.username !== 'admin'">
            <van-icon name="edit" @click="editUser(u)" />
          </template>
          <span v-else style="color:#999;font-size:12px">无法修改</span>
        </template>
      </van-cell>
    </van-list>

    <!-- 添加用户弹窗 -->
    <van-dialog v-model:show="showAdd" title="添加用户" show-cancel-button :before-close="onAddClose">
      <van-form ref="addFormRef">
        <van-field v-model="newUser.username" label="用户名" placeholder="必填" :rules="[{required:true}]" />
        <van-field v-model="newUser.password" label="密码" type="password" placeholder="必填" :rules="[{required:true}]" />
        <van-field v-model="newUser.nickname" label="姓名" placeholder="选填" />
        <van-field name="role" label="角色">
          <template #input>
            <van-checkbox-group v-model="selectedRoles" direction="horizontal">
              <van-checkbox v-for="r in roleOptions" :key="r.value" :name="r.value" shape="square" style="margin-right:12px">{{ r.label }}</van-checkbox>
            </van-checkbox-group>
          </template>
        </van-field>
      </van-form>
    </van-dialog>

    <!-- 编辑弹窗 -->
    <div v-if="showEdit" class="modal-overlay" @click.self="showEdit=false">
      <div class="modal-box">
        <h3>编辑用户</h3>
        <div class="form-group">
          <label>用户名</label>
          <input :value="editForm.username" disabled style="background:#f5f5f5" />
        </div>
        <div class="form-group">
          <label>姓名</label>
          <input v-model="editForm.nickname" />
        </div>
        <div class="form-group">
          <label>手机号</label>
          <input v-model="editForm.phone" />
        </div>
        <div class="form-group">
          <label>角色</label>
          <div style="display:flex;gap:16px">
            <label v-for="r in roleOptions" :key="r.value" style="display:flex;align-items:center;gap:4px;font-size:14px;font-weight:normal;cursor:pointer">
              <input type="checkbox" :value="r.value" :checked="editRoles.includes(r.value)" @change="toggleEditRole(r.value)" style="width:auto" />
              {{ r.label }}
            </label>
          </div>
        </div>
        <div class="form-group">
          <label>新密码（留空不改）</label>
          <input v-model="editForm.password" type="password" style="width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px" />
        </div>
        <div class="form-actions">
          <button class="btn" @click="showEdit=false">取消</button>
          <button class="btn btn-primary" @click="saveEdit">保存</button>
        </div>
      </div>
    </div>

    <!-- 修改密码弹窗 -->
    <van-dialog v-model:show="showPwd" :title="'修改密码 - ' + (pwdUser?.nickname || pwdUser?.username)" show-cancel-button @confirm="savePassword">
      <van-form>
        <van-field v-if="pwdUser && pwdUser.id === currentUserId" v-model="pwdForm.old_password" label="原密码" type="password" :rules="[{required:true,message:'请输入原密码'}]" />
        <van-field v-model="pwdForm.new_password" label="新密码" type="password" placeholder="至少4位" :rules="[{required:true,message:'请输入新密码'}]" />
      </van-form>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showDialog, showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'

const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const list = ref([])
const loading = ref(false)
const finished = ref(false)
const addFormRef = ref(null)
const showAdd = ref(false)
const showEdit = ref(false)
const editForm = ref({})
const editRoles = ref([])
const newUser = ref({ username:'', password:'', nickname:'', role:'collector' })
const selectedRoles = ref(['collector'])
const roleOptions = [
  { value: 'collector', label: '收集者' },
  { value: 'reviewer', label: '修改者' },
  { value: 'admin', label: '管理员' },
  { value: 'guest', label: '游客' },
]
const showPwd = ref(false)
const pwdUser = ref(null)
const pwdForm = ref({ old_password: '', new_password: '' })
const currentUserId = ref(0)

async function load() {
  loading.value = true
  try { const res = await api.get('/admin/users'); list.value = res.data }
  catch { showToast('加载失败') }
  finally { loading.value = false; finished.value = true }
}

function roleLabel(r) {
  const labels = { admin:'管理员', collector:'收集者', reviewer:'修改者', guest:'游客' }
  return (r||'').split(',').map(x=>labels[x]||x).join(' + ')
}

async function addUser() {
  try {
    await api.post('/admin/users', { ...newUser.value, role: selectedRoles.value.join(',') })
    showToast('添加成功'); showAdd.value = false
    newUser.value = { username:'', password:'', nickname:'', role:'collector' }
    selectedRoles.value = ['collector']
    load()
  } catch(err) { showToast(err.response?.data?.detail || '添加失败') }
}

function onAddClose(action) {
  if (action !== 'confirm') return true
  return addFormRef.value.validate().then(() => addUser().then(() => true)).catch(() => false)
}

function editUser(u) {
  editForm.value = { ...u, password: '' }
  editRoles.value = (u.role || '').split(',').filter(Boolean)
  showEdit.value = true
}

function toggleEditRole(val) {
  const idx = editRoles.value.indexOf(val)
  if (idx > -1) editRoles.value.splice(idx, 1)
  else editRoles.value.push(val)
}

function changePassword(u) {
  pwdUser.value = u
  pwdForm.value = { old_password: '', new_password: '' }
  showPwd.value = true
}

async function savePassword() {
  const isSelf = pwdUser.value.id === currentUserId.value
  if (isSelf && !pwdForm.value.old_password) {
    showToast('请输入原密码')
    return
  }
  if (!pwdForm.value.new_password || pwdForm.value.new_password.length < 4) {
    showToast('新密码至少4位')
    return
  }
  try {
    if (isSelf) {
      await api.put('/admin/profile/password', pwdForm.value)
    } else {
      await api.put(`/admin/users/${pwdUser.value.id}`, { password: pwdForm.value.new_password })
    }
    showPwd.value = false
    if (isSelf) {
      showToast('密码修改成功，请重新登录')
      setTimeout(() => {
        localStorage.removeItem(`auth_${localStorage.getItem('activeAuth') || 'default'}`)
        window.location.hash = '#/login'
      }, 1500)
    } else {
      showToast('密码修改成功')
    }
  } catch(err) {
    showToast(err.response?.data?.detail || '修改失败')
  }
}

async function saveEdit() {
  try {
    const payload = { nickname: editForm.value.nickname, role: editRoles.value.join(',') }
    if (editForm.value.password) payload.password = editForm.value.password
    await api.put(`/admin/users/${editForm.value.id}`, payload)
    showToast('更新成功')
    showEdit.value = false
    load()
  } catch(err) { showToast(err.response?.data?.detail || '更新失败') }
}

function confirmDelete(u) {
  showDialog({
    title: '确认删除',
    message: `确定删除用户 ${u.username} 吗？`,
    showCancelButton: true,
  }).then(async () => {
    try {
      await api.delete(`/admin/users/${u.id}`)
      list.value = list.value.filter(x => x.id !== u.id)
      showToast('删除成功')
    } catch(err) { showToast(err.response?.data?.detail || '删除失败') }
  }).catch(() => {})
}

onMounted(() => {
  const auth = getAuth()
  currentUserId.value = auth?.user?.id || 0
  load()
})
</script>

<style scoped>
.page { padding: 0; }
@media (max-width: 767px) { .page { min-height: 100vh; } }
</style>
