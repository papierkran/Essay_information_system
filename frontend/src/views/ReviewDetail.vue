<template>
  <div class="page detail-page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="loading" style="padding:40px;text-align:center;color:#999">加载中...</div>

    <template v-if="!loading && essay">
      <div v-if="isDesktop" class="page-title">作文详情</div>

      <!-- 桌面端：左右分栏 -->
      <div v-if="isDesktop" class="detail-split">
        <div class="detail-left">
          <div class="card">
            <div class="card-header">
              <h3>📝 基本信息</h3>
              <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" @click="saveEdit">💾 保存</button>
            </div>
            <div class="info-grid">
              <div class="info-item"><span class="info-label">学生</span><input v-model="editForm.student_name" class="edit-input" /></div>
              <div class="info-item"><span class="info-label">年级</span>
                <select v-model="editForm.grade" class="edit-input">
                  <option value="">-</option>
                  <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
                </select>
              </div>
              <div class="info-item"><span class="info-label">第几次</span><input v-model.number="editForm.essay_number" type="number" min="1" class="edit-input" /></div>
              <div class="info-item"><span class="info-label">标题</span><input v-model="editForm.essay_title" class="edit-input" /></div>
              <div class="info-item"><span class="info-label">收集者</span><span>{{ essay.collector_name }}</span></div>
              <div class="info-item"><span class="info-label">上传时间</span><span>{{ essay.created_at?.substring(0,16) }}</span></div>
              <div class="info-item"><span class="info-label">备注</span><input v-model="editForm.remark" class="edit-input" /></div>
              <div class="info-item"><span class="info-label">提交方式</span>
                <select v-model="editForm.teaching_mode" class="edit-input">
                  <option value="线上">线上</option>
                  <option value="线下">线下</option>
                </select>
              </div>
              <div v-if="essay.is_supplement" class="info-item"><span class="info-label">状态</span><span><van-tag type="warning">补交</van-tag></span></div>
            </div>
          </div>

          <div class="card">
            <div class="card-header"><h3>📄 作文内容</h3></div>
            <div v-if="essay.file_type === 'image' && images.length" class="image-gallery">
              <img v-for="(img, i) in images" :key="i" :src="img" @click="previewImage(img)" class="essay-image" />
            </div>
            <div v-if="essay.content_text" class="content-text"><pre>{{ essay.content_text }}</pre></div>
            <div v-else-if="essay.file_type !== 'image'" class="empty-state" style="padding:20px"><p>无文字内容</p></div>
            <div class="action-btns">
              <button v-if="essay.content_file" class="btn btn-primary" @click="downloadOriginal">下载原文</button>
              <button v-if="essay.has_correction" class="btn btn-success" @click="downloadCorrection" style="margin-left:8px">下载批改结果</button>
              <button class="btn" style="margin-left:8px" @click="showReupload = !showReupload">📤 重新上传</button>
            </div>
            <div v-if="showReupload" class="reupload-area">
              <div class="form-group">
                <label>上传文件（docx/图片，可多选）</label>
                <div class="upload-preview">
                  <div v-for="(item, i) in desktopFileList" :key="i" class="upload-preview-item">
                    <img v-if="previewable(item)" :src="item.url" class="upload-thumb" @click="previewDesktopImage(item)" />
                    <div v-else class="upload-file-icon">📄</div>
                    <span class="upload-name">{{ item.name }}</span>
                    <button class="upload-remove" @click="removeDesktopFile(i)">✕</button>
                  </div>
                </div>
                <label class="btn" style="cursor:pointer;display:inline-flex">
                  选择文件
                  <input type="file" multiple accept=".docx,.doc,.jpg,.jpeg,.png" style="display:none" @change="onDesktopFiles" />
                </label>
              </div>
              <div class="form-group">
                <label>或粘贴文字</label>
                <textarea v-model="reuploadText" rows="3" placeholder="粘贴文字内容..."></textarea>
              </div>
              <button class="btn btn-primary" @click="doReuploadDesktop" :disabled="reuploading">
                {{ reuploading ? '上传中...' : '确认上传' }}
              </button>
            </div>
          </div>
        </div>

        <div class="detail-right">
          <div class="card" v-if="canReview && essay.status !== 'corrected'">
            <div class="card-header"><h3>📤 上传批改结果</h3></div>
            <div class="form-group">
              <label>选择批改后的 docx 文件</label>
              <input type="file" ref="fileInput" accept=".docx,.doc" @change="onFileSelected" />
              <p v-if="selectedFile" style="margin-top:8px;color:#52c41a">已选择: {{ selectedFile.name }}</p>
            </div>
            <button class="btn btn-primary" @click="uploadCorrection" :disabled="!selectedFile" style="width:100%">
              {{ uploading ? '提交中...' : '提交批改' }}
            </button>
          </div>

          <div class="card" v-else>
            <div class="card-header"><h3>✅ 已批改</h3></div>
            <p style="color:#52c41a">批改完成于 {{ essay.corrected_at?.substring(0,16) }}</p>
            <button v-if="essay.has_correction" class="btn btn-success" @click="downloadCorrection" style="margin-top:12px;width:100%">下载批改结果</button>
          </div>
        </div>
      </div>

      <!-- 手机端 -->
      <template v-else>
        <van-cell-group inset>
          <van-field v-model="editForm.student_name" label="学生姓名" />
          <van-field v-model="editForm.grade" label="年级" placeholder="选择" @click="showMobileGrade = true" is-link readonly />
          <van-field v-model.number="editForm.essay_number" label="第几次" type="digit" />
          <van-field v-model="editForm.essay_title" label="作文标题" />
          <van-field v-model="editForm.remark" label="备注" type="textarea" rows="2" />
          <van-cell title="收集者" :value="essay.collector_name" />
          <van-cell title="上传时间" :value="essay.created_at?.substring(0,16)" />
          <van-cell v-if="essay.is_supplement" title="状态" value="补交" />
        </van-cell-group>
        <div style="margin:16px">
          <van-button v-if="essay.content_file" round block type="primary" @click="downloadOriginal" style="margin-bottom:8px">下载原文</van-button>
          <van-button v-if="essay.has_correction" round block type="success" @click="downloadCorrection" style="margin-bottom:8px">下载批改结果</van-button>
          <van-button round block @click="showReupload = !showReupload" style="margin-bottom:8px">📤 重新上传</van-button>
          <van-button round block @click="saveEdit" :loading="savingEdit">💾 保存修改</van-button>
        </div>

        <div v-if="showReupload" style="margin:16px;padding:16px;background:#fff;border-radius:8px">
          <van-field name="uploader" label="上传文件（可多选）">
            <template #input>
              <van-uploader v-model="reuploadFileList" :max-count="10" accept=".docx,.doc,.jpg,.jpeg,.png" multiple />
            </template>
          </van-field>
          <van-field v-model="reuploadText" label="或粘贴文字" type="textarea" rows="3" placeholder="粘贴文字..." />
          <van-button round block type="primary" @click="doReupload" :loading="reuploading" style="margin-top:8px">确认上传</van-button>
        </div>

        <van-action-sheet v-model:show="showMobileGrade" title="选择年级">
          <div class="picker-list">
            <van-cell v-for="g in grades" :key="g" :title="g" @click="editForm.grade = g; showMobileGrade = false" />
          </div>
        </van-action-sheet>

        <van-cell-group inset style="margin-top:12px">
          <van-cell title="作文内容" />
          <div v-if="essay.file_type === 'image' && images.length" class="image-gallery">
            <img v-for="(img, i) in images" :key="i" :src="img" @click="previewImage(img)" class="essay-image" />
          </div>
          <div v-if="essay.content_text" class="content-text"><pre>{{ essay.content_text }}</pre></div>
        </van-cell-group>

        <van-cell-group inset style="margin-top:12px" v-if="canReview && essay.status !== 'corrected'">
          <van-field v-model="correctionFile" is-link readonly label="上传批改结果" placeholder="选择批改后的 docx 文件" @click="selectFile" />
          <div style="margin:16px">
            <van-button round block type="primary" @click="uploadCorrection" :loading="uploading">提交批改</van-button>
          </div>
        </van-cell-group>

        <input type="file" ref="fileInput" accept=".docx,.doc" style="display:none" @change="onFileSelected" />
      </template>
    </template>

    <van-image-preview v-model:show="showPreview" :images="previewImages" :start-position="previewIndex" :closeable="true" close-icon-position="top-right" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'

const route = useRoute()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const canReview = computed(() => {
  const role = currentUser.value.role || ''
  return role.includes('reviewer') || role.includes('admin')
})
const essay = ref(null)
const correctionFile = ref('')
const selectedFile = ref(null)
const uploading = ref(false)
const fileInput = ref(null)
const images = ref([])
const showPreview = ref(false)
const previewIndex = ref(0)
const previewImages = ref([])
const savingEdit = ref(false)
const showMobileGrade = ref(false)
const loading = ref(true)
const reuploadFileList = ref([])
const reuploadText = ref('')
const reuploading = ref(false)
const showReupload = ref(false)
const editForm = ref({})
const grades = ['初一','初二','初三','高一','高二','高三']
const desktopFileList = ref([])

function previewable(item) { return item.type?.startsWith('image/') }

function onDesktopFiles(e) {
  const files = Array.from(e.target.files)
  files.forEach(f => {
    const url = URL.createObjectURL(f)
    desktopFileList.value.push({ file: f, name: f.name, type: f.type, url })
  })
  e.target.value = ''
}

function removeDesktopFile(i) {
  URL.revokeObjectURL(desktopFileList.value[i].url)
  desktopFileList.value.splice(i, 1)
}

function previewDesktopImage(item) {
  const desktopUrls = desktopFileList.value.filter(x => previewable(x)).map(x => x.url)
  previewImages.value = [...images.value, ...desktopUrls]
  const idx = previewImages.value.findIndex(u => u === item.url)
  previewIndex.value = idx >= 0 ? idx : 0
  showPreview.value = true
}

async function doReuploadDesktop() {
  if (desktopFileList.value.length === 0 && !reuploadText.value.trim()) {
    showToast('请选择文件或输入文字')
    return
  }
  reuploading.value = true
  try {
    const fd = new FormData()
    fd.append('class_id', String(essay.value.class_id || 1))
    fd.append('grade', editForm.value.grade || essay.value.grade || '')
    fd.append('essay_number', String(editForm.value.essay_number || essay.value.essay_number || 1))
    fd.append('essay_title', editForm.value.essay_title || essay.value.essay_title || '')
    fd.append('student_name', editForm.value.student_name || essay.value.student_name)
    fd.append('is_supplement', essay.value.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', essay.value.teaching_mode || '线下')
    desktopFileList.value.forEach(item => fd.append('files', item.file))
    if (reuploadText.value.trim()) {
      fd.append('content_text', reuploadText.value)
    }
    await api.post('/essays/upload', fd)
    showToast('重新上传成功')
    const res = await api.get(`/essays/${route.params.id}`)
    essay.value = res.data
    if (essay.value.file_type === 'image') {
      const imgRes = await api.get(`/essays/${route.params.id}/images`)
      const base = window.location.origin
      images.value = imgRes.data.images.map(u => base + u)
    }
    desktopFileList.value.forEach(item => URL.revokeObjectURL(item.url))
    desktopFileList.value = []
    reuploadText.value = ''
    showReupload.value = false
  } catch(err) {
    showToast(err.response?.data?.detail || '上传失败')
  } finally {
    reuploading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await api.get(`/essays/${route.params.id}`)
    essay.value = res.data
    loading.value = false
    editForm.value = {
      student_name: essay.value.student_name,
      grade: essay.value.grade,
      essay_title: essay.value.essay_title,
      essay_number: essay.value.essay_number,
      teaching_mode: essay.value.teaching_mode || '线上',
      remark: essay.value.remark,
    }
    if (essay.value.file_type === 'image') {
      const imgRes = await api.get(`/essays/${route.params.id}/images`)
      const base = window.location.origin
      images.value = imgRes.data.images.map(u => base + u)
    }
  } catch {
    showToast('加载失败')
    loading.value = false
  }
})

function previewImage(url) {
  const desktopUrls = desktopFileList.value.filter(x => previewable(x)).map(x => x.url)
  previewImages.value = [...images.value, ...desktopUrls]
  const idx = previewImages.value.findIndex(u => u === url)
  previewIndex.value = idx >= 0 ? idx : 0
  showPreview.value = true
}

function selectFile() { fileInput.value?.click() }
function onFileSelected(e) {
  const f = e.target.files[0]
  if (f) { selectedFile.value = f; correctionFile.value = f.name }
}

async function downloadOriginal() {
  try {
    const res = await api.get(`/essays/${route.params.id}/download`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url; a.download = '作文.docx'; a.click()
  } catch { showToast('下载失败') }
}

async function downloadCorrection() {
  try {
    const res = await api.get(`/essays/${route.params.id}/download-correction`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url; a.download = '批改结果.docx'; a.click()
  } catch { showToast('下载失败') }
}

async function uploadCorrection() {
  if (!selectedFile.value) { showToast('请选择文件'); return }
  uploading.value = true
  try {
    const fd = new FormData(); fd.append('file', selectedFile.value)
    await api.post(`/essays/${route.params.id}/upload-correction`, fd)
    showToast('批改提交成功')
    essay.value.status = 'corrected'; essay.value.has_correction = true
    selectedFile.value = null; correctionFile.value = ''
  } catch (err) { showToast(err.response?.data?.detail || '上传失败') }
  finally { uploading.value = false }
}

async function saveEdit() {
  savingEdit.value = true
  try {
    const res = await api.put(`/essays/${route.params.id}`, null, { params: editForm.value })
    essay.value = { ...essay.value, ...res.data }
    showToast('保存成功')
  } catch(err) {
    showToast(err.response?.data?.detail || '保存失败')
  } finally {
    savingEdit.value = false
  }
}

let reuploadReaddFileList = null

function onReuploadFiles(e) {
  reuploadReaddFileList = Array.from(e.target.files)
}

async function doReupload() {
  const files = reuploadFileList.value.length > 0
    ? reuploadFileList.value.map(x => x.file)
    : (reuploadReaddFileList || [])
  if (files.length === 0 && !reuploadText.value.trim()) {
    showToast('请选择文件或输入文字')
    return
  }
  reuploading.value = true
  try {
    const fd = new FormData()
    fd.append('class_id', String(essay.value.class_id || 1))
    fd.append('grade', editForm.value.grade || essay.value.grade || '')
    fd.append('essay_number', String(editForm.value.essay_number || essay.value.essay_number || 1))
    fd.append('essay_title', editForm.value.essay_title || essay.value.essay_title || '')
    fd.append('student_name', editForm.value.student_name || essay.value.student_name)
    fd.append('is_supplement', essay.value.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', essay.value.teaching_mode || '线下')
    for (const f of files) {
      fd.append('files', f)
    }
    if (reuploadText.value.trim()) {
      fd.append('content_text', reuploadText.value)
    }
    await api.post('/essays/upload', fd)
    showToast('重新上传成功')
    const res = await api.get(`/essays/${route.params.id}`)
    essay.value = res.data
    if (essay.value.file_type === 'image') {
      const imgRes = await api.get(`/essays/${route.params.id}/images`)
      const base = window.location.origin
      images.value = imgRes.data.images.map(u => base + u)
    }
    reuploadFileList.value = []
    reuploadText.value = ''
    showReupload.value = false
  } catch(err) {
    showToast(err.response?.data?.detail || '上传失败')
  } finally {
    reuploading.value = false
  }
}
</script>

<style scoped>
.detail-page { padding: 0; }
.content-text { padding: 12px 16px; }
.content-text pre { white-space: pre-wrap; font-size: 14px; line-height: 1.8; margin: 0; font-family: inherit; }
.action-btns { padding: 8px 16px 16px; }

.detail-split {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.info-full { grid-column: 1 / -1; }
.info-label { font-size: 12px; color: #999; }

.edit-input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.edit-input:focus { border-color: #4096ff; }

.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
}

.essay-image {
  width: 150px;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #eee;
  cursor: pointer;
  transition: transform 0.2s;
}

.essay-image:hover { transform: scale(1.05); }

.picker-list { max-height: 300px; overflow-y: auto; }

.reupload-area {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

.reupload-area .form-group {
  margin-bottom: 12px;
}

.reupload-area .form-group label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.reupload-area input[type="file"],
.reupload-area textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
}

.reupload-area textarea {
  resize: vertical;
  font-family: inherit;
}

.upload-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.upload-preview-item {
  position: relative;
  width: 80px;
  text-align: center;
}

.upload-thumb {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #eee;
}

.upload-file-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 28px;
}

.upload-name {
  display: block;
  font-size: 11px;
  color: #666;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-remove {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ff4d4f;
  color: #fff;
  border: none;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 767px) {
  .detail-page { padding: 16px; }
}
</style>
