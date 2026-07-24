<template>
  <div class="page detail-page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="loading" style="padding:40px;text-align:center;color:#999">加载中...</div>

    <template v-if="!loading && essay">
      <div v-if="isDesktop" class="page-title">作文详情</div>

      <!-- ===== 桌面端：顶部行（基本信息 + 修改状态）===== -->
      <div v-if="isDesktop" class="top-row">
        <div class="card top-card">
          <div class="card-header">
            <h3>📝 基本信息</h3>
            <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" @click="saveEdit" :disabled="!canEdit">💾 保存</button>
          </div>
          <div class="info-grid">
            <div class="info-item"><span class="info-label">学生</span><input v-model="editForm.student_name" class="edit-input" :disabled="!canEdit" /></div>
            <div class="info-item"><span class="info-label">年级</span>
              <select v-model="editForm.grade" class="edit-input" :disabled="!canEdit">
                <option value="">-</option>
                <option v-for="g in grades" :key="g" :value="g">{{ g }}</option>
              </select>
            </div>
            <div class="info-item"><span class="info-label">第几次</span><input v-model.number="editForm.essay_number" type="number" min="1" class="edit-input" :disabled="!canEdit" /></div>
            <div class="info-item"><span class="info-label">标题</span><input v-model="editForm.essay_title" class="edit-input" :disabled="!canEdit" /></div>
            <div class="info-item">
              <span class="info-label">收集者</span>
              <template v-if="isAdmin && !isReadonly">
                <select v-model="editForm.collected_by" class="edit-input">
                  <option v-for="u in collectorList" :key="u.id" :value="u.id">{{ u.nickname || u.username }}</option>
                </select>
              </template>
              <template v-else>
                <span>{{ essay.collector_name }}</span>
              </template>
            </div>
            <div class="info-item"><span class="info-label">上传时间</span><span>{{ formatDateTime(essay.created_at) }}</span></div>
            <div class="info-item"><span class="info-label">备注</span><input v-model="editForm.remark" class="edit-input" :disabled="!canEdit" /></div>
            <div class="info-item"><span class="info-label">提交方式</span>
              <select v-model="editForm.teaching_mode" class="edit-input" :disabled="!canEdit">
                <option value="线上">线上</option>
                <option value="线下">线下</option>
              </select>
            </div>
            <div v-if="essay.is_supplement" class="info-item"><span class="info-label">状态</span><span><van-tag type="warning">补交</van-tag></span></div>
          </div>
        </div>

        <div class="card top-card">
          <template v-if="canReview && essay.status !== 'corrected'">
            <div class="card-header"><h3>📤 上传修改结果</h3></div>
            <div class="form-group">
              <label>选择修改后的 docx 文件</label>
              <input type="file" ref="fileInput" accept=".docx,.doc" @change="onFileSelected" />
              <p v-if="selectedFile" style="margin-top:8px;color:#52c41a">已选择: {{ selectedFile.name }}</p>
            </div>
            <div class="form-group">
              <label>文字修改内容</label>
                <textarea v-model="correctionText" rows="4" placeholder="输入修改文字..."></textarea>
            </div>
            <button class="btn btn-primary" @click="uploadCorrection" :disabled="!selectedFile && !correctionText.trim()" style="width:100%">
                {{ uploading ? '提交中...' : '提交修改' }}
            </button>
          </template>
          <template v-else>
            <div class="card-header"><h3>✅ 已修改</h3></div>
            <p style="color:#52c41a">修改完成于 {{ essay.corrected_at?.substring(0,16) }}</p>
            <button v-if="essay.has_correction" class="btn btn-success" @click="downloadCorrection" style="margin-top:12px;width:100%">📥 下载修改结果</button>
          </template>
        </div>
      </div>

      <!-- ===== 桌面端：底部大卡片 📄 作文内容 ===== -->
      <div v-if="isDesktop" class="card essay-content-card">
        <div class="card-header essay-card-header">
          <div class="header-left">
            <h3>📄 作文内容</h3>
            <label class="word-count-toggle">
              <input type="checkbox" v-model="showWordCount" /> 🔢 字数
            </label>
          </div>
          <div class="header-right">
            <button class="btn" style="font-size:12px;padding:4px 10px" @click="toggleFullscreen('both')">⛶ 双全屏</button>
            <button v-if="essay.content_file && !isGuest" class="btn" style="font-size:12px;padding:4px 10px" @click="downloadOriginal">📥 下载原文</button>
            <button v-if="!isGuest" class="btn" style="font-size:12px;padding:4px 10px" @click="exportDocx">📥 导出修改前后docx</button>
          </div>
        </div>
        <div class="essay-split">
          <!-- 左：修改前 -->
          <div class="essay-pane" :class="{ 'fullscreen-pane': fullscreenMode === 'original' }">
            <div class="pane-header">
              <div class="pane-header-left">
                <span class="pane-title">✏️ 修改前</span>
                <button class="btn-mini" @click="showOriginalImages" v-if="essay.file_type === 'image' && images.length">📷 查看原文图片</button>
                <button v-if="essay.content_file && !isGuest" class="btn-mini" @click="downloadOriginal">📥 下载原文</button>
                <button class="btn-mini" @click="toggleReuploadOriginal" v-if="canEdit">📤 重新上传</button>
              </div>
              <button class="btn-mini" @click="toggleFullscreen('original')">{{ fullscreenMode === 'original' ? '⛶ 退出' : '⛶ 全屏' }}</button>
            </div>
            <div class="pane-body">
              <div v-if="essay.file_type === 'image' && images.length" class="image-gallery">
                <img v-for="(img, i) in images" :key="i" :src="img" @click="previewImage(img, 'original')" class="essay-image" />
              </div>
              <div v-if="essay.content_text" class="content-text">
                <p v-for="(para, i) in originalParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
              </div>
              <div v-else-if="essay.file_type !== 'image'" class="empty-state" style="padding:20px"><p>无文字内容</p></div>
              <div v-if="showWordCount" class="word-count">{{ (essay.content_text || '').length }} 字</div>
            </div>
            <!-- 重新上传面板（修改前） -->
            <div v-if="showReuploadOriginal" class="reupload-area">
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

          <!-- 右：修改后 -->
          <div class="essay-pane" :class="{ 'fullscreen-pane': fullscreenMode === 'corrected' }">
            <div class="pane-header">
              <div class="pane-header-left">
                <span class="pane-title">✅ 修改后</span>
                <button class="btn-mini" @click="toggleReuploadCorrected" v-if="canEdit">📤 重新上传</button>
              </div>
              <button class="btn-mini" @click="toggleFullscreen('corrected')">{{ fullscreenMode === 'corrected' ? '⛶ 退出' : '⛶ 全屏' }}</button>
            </div>
            <div class="pane-body">
              <div v-if="essay.corrected_text" class="content-text corrected-content">
                <p v-for="(para, i) in correctedParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
              </div>
              <div v-else class="empty-state" style="padding:20px"><p>暂无修改内容</p></div>
              <div v-if="showWordCount" class="word-count">{{ (essay.corrected_text || '').length }} 字</div>
            </div>
            <!-- 重新上传面板（修改后：仅文字输入） -->
            <div v-if="showReuploadCorrected" class="reupload-area">
              <div class="form-group">
                <label>修改文字内容</label>
              <textarea v-model="correctionText" rows="4" placeholder="输入修改文字..."></textarea>
              </div>
              <div class="form-group">
                <label>或上传修改文件</label>
                <input type="file" accept=".docx,.doc" @change="onFileSelected" />
                <p v-if="selectedFile" style="margin-top:8px;color:#52c41a">已选择: {{ selectedFile.name }}</p>
              </div>
              <button class="btn btn-primary" @click="uploadCorrection" :disabled="!selectedFile && !correctionText.trim()">
              {{ uploading ? '提交中...' : '提交修改' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 手机端 ===== -->
      <template v-else>
        <van-cell-group inset>
          <van-field v-model="editForm.student_name" label="学生姓名" />
          <van-field v-model="editForm.grade" label="年级" placeholder="选择" @click="showMobileGrade = true" is-link readonly />
          <van-field v-model.number="editForm.essay_number" label="第几次" type="digit" />
          <van-field v-model="editForm.essay_title" label="作文标题" />
          <van-field v-model="editForm.remark" label="备注" type="textarea" rows="2" />
          <van-cell title="收集者" :value="essay.collector_name" />
          <van-cell title="上传时间" :value="formatDateTime(essay.created_at)" />
          <van-cell v-if="essay.is_supplement" title="状态" value="补交" />
        </van-cell-group>

        <div style="margin:16px">
          <van-button v-if="essay.content_file && !isGuest" round block type="primary" @click="downloadOriginal" style="margin-bottom:8px">📥 下载原文</van-button>
          <van-button v-if="!isGuest" round block @click="exportDocx" style="margin-bottom:8px">📥 导出修改前后docx</van-button>
          <van-button v-if="essay.has_correction" round block type="success" @click="downloadCorrection" style="margin-bottom:8px">📥 下载修改结果</van-button>
          <van-button v-if="canEdit" round block @click="showReupload = !showReupload" style="margin-bottom:8px">📤 重新上传</van-button>
          <van-button round block @click="saveEdit" :loading="savingEdit" :disabled="!canEdit">💾 保存修改</van-button>
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

        <!-- 修改前 -->
        <van-cell-group inset style="margin-top:12px">
          <van-cell title="✏️ 修改前" />
          <div v-if="essay.file_type === 'image' && images.length" class="image-gallery">
            <img v-for="(img, i) in images" :key="i" :src="img" @click="previewImage(img, 'original')" class="essay-image" />
          </div>
          <div v-if="essay.content_text" class="content-text">
            <p v-for="(para, i) in originalParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
          </div>
        </van-cell-group>

        <!-- 修改后 -->
        <van-cell-group inset style="margin-top:12px">
          <van-cell title="✅ 修改后" />
          <div v-if="essay.corrected_text" class="content-text corrected-content">
            <p v-for="(para, i) in correctedParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
          </div>
          <div v-else class="empty-state" style="padding:20px"><p>暂无修改内容</p></div>
        </van-cell-group>

        <!-- 手机端修改上传 -->
        <van-cell-group inset style="margin-top:12px" v-if="canReview && essay.status !== 'corrected'">
          <van-field v-model="correctionFile" is-link readonly label="上传修改结果" placeholder="选择修改后的 docx 文件" @click="selectFile" />
          <van-field v-model="correctionText" label="文字修改" type="textarea" rows="3" placeholder="输入修改文字..." />
          <div style="margin:16px">
            <van-button round block type="primary" @click="uploadCorrection" :loading="uploading">提交修改</van-button>
          </div>
        </van-cell-group>

        <input type="file" ref="fileInput" accept=".docx,.doc" style="display:none" @change="onFileSelected" />
      </template>
    </template>

    <!-- 全屏遮罩 -->
    <div v-if="fullscreenMode" class="fullscreen-overlay" @click.self="fullscreenMode = null">
      <div class="fullscreen-content">
        <div class="fullscreen-header">
          <span>{{ fullscreenMode === 'both' ? '⛶ 双屏全屏' : fullscreenMode === 'original' ? '✏️ 修改前' : '✅ 修改后' }}</span>
          <button class="btn" @click="fullscreenMode = null">✕ 关闭</button>
        </div>
        <div v-if="fullscreenMode === 'both'" class="fullscreen-split">
          <div class="fullscreen-pane">
            <div class="content-text">
              <p v-for="(para, i) in originalParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
            </div>
          </div>
          <div class="fullscreen-pane">
            <div class="content-text corrected-content">
              <p v-for="(para, i) in correctedParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
            </div>
          </div>
        </div>
        <div v-else class="fullscreen-pane">
          <div v-if="fullscreenMode === 'original'" class="content-text">
            <p v-for="(para, i) in originalParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
          </div>
          <div v-else class="content-text corrected-content">
            <p v-for="(para, i) in correctedParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
          </div>
        </div>
      </div>
    </div>

    <van-image-preview v-model:show="showPreview" :images="previewImages" :start-position="previewIndex" :closeable="true" close-icon-position="top-right" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { formatDateTime } from '../utils/format'

const route = useRoute()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isAdmin = computed(() => {
  const role = currentUser.value.role || ''
  return role.includes('admin')
})
const isGuest = computed(() => {
  const role = currentUser.value.role || ''
  return role.includes('guest')
})
const isOwner = computed(() => {
  if (isAdmin.value) return true
  return essay.value?.collected_by === currentUser.value.id
})
const isReadonly = computed(() => isGuest.value || route.query.readonly === '1')
const canReview = computed(() => {
  if (isGuest.value) return false
  const role = currentUser.value.role || ''
  return role.includes('reviewer') || role.includes('admin')
})
const canEdit = computed(() => !isReadonly.value && isOwner.value)
const essay = ref(null)
const correctionFile = ref('')
const correctionText = ref('')
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
const showReuploadOriginal = ref(false)
const showReuploadCorrected = ref(false)
const editForm = ref({})
const grades = ['初一','初二','初三','高一','高二','高三']
const collectorList = ref([])
const desktopFileList = ref([])
const fullscreenMode = ref(null) // 'original' | 'corrected' | 'both' | null
const showWordCount = ref(true)

const originalParagraphs = computed(() => {
  return (essay.value?.content_text || '').split('\n').filter(s => s.trim())
})
const correctedParagraphs = computed(() => {
  return (essay.value?.corrected_text || '').split('\n').filter(s => s.trim())
})

function toggleFullscreen(mode) {
  fullscreenMode.value = fullscreenMode.value === mode ? null : mode
}

function toggleReuploadOriginal() {
  showReuploadCorrected.value = false
  showReuploadOriginal.value = !showReuploadOriginal.value
}

function toggleReuploadCorrected() {
  showReuploadOriginal.value = false
  showReuploadCorrected.value = !showReuploadCorrected.value
}

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

async function showOriginalImages() {
  previewImages.value = [...images.value]
  previewIndex.value = 0
  showPreview.value = true
}

async function doReuploadDesktop() {
  if (!canEdit.value) {
    showToast('无权修改此作文')
    return
  }
  if (desktopFileList.value.length === 0 && !reuploadText.value.trim()) {
    showToast('请选择文件或输入文字')
    return
  }
  reuploading.value = true
  try {
    const fd = new FormData()
    fd.append('essay_id', String(essay.value.id))
    fd.append('class_id', String(essay.value.class_id || 1))
    fd.append('grade', editForm.value.grade || essay.value.grade || '')
    fd.append('essay_number', String(editForm.value.essay_number || essay.value.essay_number || 1))
    fd.append('essay_title', editForm.value.essay_title || essay.value.essay_title || '')
    fd.append('student_name', editForm.value.student_name || essay.value.student_name)
    fd.append('is_supplement', essay.value.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', editForm.value.teaching_mode || essay.value.teaching_mode || '线下')
    fd.append('remark', editForm.value.remark || essay.value.remark || '')
    desktopFileList.value.forEach(item => fd.append('files', item.file))
    if (reuploadText.value.trim()) {
      fd.append('content_text', reuploadText.value)
    }
    await api.post('/essays/upload', fd)
    showToast('重新上传成功')
    await loadEssay()
    desktopFileList.value.forEach(item => URL.revokeObjectURL(item.url))
    desktopFileList.value = []
    reuploadText.value = ''
    showReuploadOriginal.value = false
  } catch(err) {
    showToast(err.response?.data?.detail || '上传失败')
  } finally {
    reuploading.value = false
  }
}

onMounted(async () => {
  await loadEssay()
  if (isAdmin.value) {
    await loadCollectors()
  }
})

async function loadEssay() {
  try {
    const res = await api.get(`/essays/${route.params.id}`)
    essay.value = res.data
    loading.value = false
    editForm.value = {
      student_name: essay.value.student_name,
      grade: essay.value.grade,
      essay_title: essay.value.essay_title,
      essay_number: essay.value.essay_number,
      teaching_mode: essay.value.teaching_mode || '线下',
      remark: essay.value.remark,
      collected_by: essay.value.collected_by,
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
}

async function loadCollectors() {
  try {
    const res = await api.get('/admin/users')
    collectorList.value = res.data.filter(u => u.role && (u.role.includes('collector') || u.role.includes('admin')))
  } catch {}
}

function previewImage(url) {
  previewImages.value = [...images.value]
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
    // 从 Content-Disposition 解析文件名
    const disposition = res.headers['content-disposition']
    let filename = '作文.docx'
    if (disposition) {
      const match = disposition.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i)
      if (match) filename = decodeURIComponent(match[1])
    }
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
    window.URL.revokeObjectURL(url)
  } catch { showToast('下载失败') }
}

async function downloadCorrection() {
  try {
    const res = await api.get(`/essays/${route.params.id}/download-correction`, { responseType: 'blob' })
    const disposition = res.headers['content-disposition']
    let filename = '修改结果.docx'
    if (disposition) {
      const match = disposition.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i)
      if (match) filename = decodeURIComponent(match[1])
    }
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
    window.URL.revokeObjectURL(url)
  } catch { showToast('下载失败') }
}

async function exportDocx() {
  try {
    const res = await api.get(`/essays/${route.params.id}/export-docx`, { responseType: 'blob' })
    const disposition = res.headers['content-disposition']
    let filename = '导出.docx'
    if (disposition) {
      const match = disposition.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i)
      if (match) filename = decodeURIComponent(match[1])
    }
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
    window.URL.revokeObjectURL(url)
  } catch { showToast('导出失败') }
}

async function uploadCorrection() {
  if (!selectedFile.value && !correctionText.value.trim()) {
    showToast('请选择文件或输入修改文字')
    return
  }
  uploading.value = true
  try {
    const fd = new FormData()
    if (selectedFile.value) fd.append('file', selectedFile.value)
    fd.append('corrected_text', correctionText.value)
    await api.post(`/essays/${route.params.id}/upload-correction`, fd)
    showToast('修改提交成功')
    await loadEssay()
    selectedFile.value = null; correctionFile.value = ''
    correctionText.value = ''
    showReuploadCorrected.value = false
  } catch (err) { showToast(err.response?.data?.detail || '上传失败') }
  finally { uploading.value = false }
}

async function saveEdit() {
  if (!canEdit.value) {
    showToast('无权修改此作文')
    return
  }
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

async function doReupload() {
  if (!canEdit.value) {
    showToast('无权修改此作文')
    return
  }
  const files = reuploadFileList.value.length > 0
    ? reuploadFileList.value.map(x => x.file)
    : []
  if (files.length === 0 && !reuploadText.value.trim()) {
    showToast('请选择文件或输入文字')
    return
  }
  reuploading.value = true
  try {
    const fd = new FormData()
    fd.append('essay_id', String(essay.value.id))
    fd.append('class_id', String(essay.value.class_id || 1))
    fd.append('grade', editForm.value.grade || essay.value.grade || '')
    fd.append('essay_number', String(editForm.value.essay_number || essay.value.essay_number || 1))
    fd.append('essay_title', editForm.value.essay_title || essay.value.essay_title || '')
    fd.append('student_name', editForm.value.student_name || essay.value.student_name)
    fd.append('is_supplement', essay.value.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', editForm.value.teaching_mode || essay.value.teaching_mode || '线下')
    fd.append('remark', editForm.value.remark || essay.value.remark || '')
    for (const f of files) {
      fd.append('files', f)
    }
    if (reuploadText.value.trim()) {
      fd.append('content_text', reuploadText.value)
    }
    await api.post('/essays/upload', fd)
    showToast('重新上传成功')
    await loadEssay()
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
.content-text p { font-size: 14px; line-height: 1.8; margin: 0 0 8px 0; text-indent: 2em; }
.content-text .para-center-bold { text-indent: 0; text-align: center; font-weight: bold; }
.corrected-content { background: #f6ffed; border-radius: 8px; }

/* ===== 桌面端顶部行 ===== */
.top-row {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
  margin-bottom: 20px;
}
.top-card { margin: 0; }

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.info-item { display: flex; flex-direction: column; gap: 4px; }
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

/* ===== 作文内容大卡片 ===== */
.essay-content-card { margin: 0; }
.essay-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.header-right { display: flex; gap: 8px; }
.word-count-toggle {
  font-size: 13px;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.word-count-toggle input { width: auto; }

/* ===== 左右分栏 ===== */
.essay-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.essay-pane {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.pane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}
.pane-header-left { display: flex; align-items: center; gap: 8px; }
.pane-title { font-weight: 600; font-size: 14px; }
.btn-mini {
  font-size: 12px;
  padding: 2px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  white-space: nowrap;
}
.btn-mini:hover { border-color: #4096ff; color: #4096ff; }

.pane-body {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  min-height: 200px;
  position: relative;
}

.word-count {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 12px;
  color: #999;
}

/* ===== 图片画廊 ===== */
.image-gallery { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 0 8px 0; }
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

/* ===== 重新上传区域 ===== */
.reupload-area {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}
.reupload-area .form-group { margin-bottom: 12px; }
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
.reupload-area textarea { resize: vertical; font-family: inherit; }

.upload-preview { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.upload-preview-item { position: relative; width: 80px; text-align: center; }
.upload-thumb { width: 80px; height: 80px; object-fit: cover; border-radius: 6px; border: 1px solid #eee; }
.upload-file-icon {
  width: 80px; height: 80px;
  display: flex; align-items: center; justify-content: center;
  background: #f5f5f5; border-radius: 6px; font-size: 28px;
}
.upload-name { display: block; font-size: 11px; color: #666; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.upload-remove {
  position: absolute; top: -6px; right: -6px;
  width: 18px; height: 18px; border-radius: 50%;
  background: #ff4d4f; color: #fff; border: none; font-size: 11px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}

.picker-list { max-height: 300px; overflow-y: auto; }

/* ===== 全屏遮罩 ===== */
.fullscreen-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.85);
  z-index: 9999;
  display: flex;
  flex-direction: column;
}
.fullscreen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}
.fullscreen-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.fullscreen-split {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: #444;
}
.fullscreen-pane {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fff;
}
.fullscreen-pane .content-text p { font-size: 16px; line-height: 2; }
.fullscreen-pane .corrected-content { background: #f6ffed; }

/* ===== 全屏模式下的 pane 样式 ===== */
.fullscreen-pane:not(.fullscreen-overlay .fullscreen-pane) {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 9998;
  background: #fff;
  overflow-y: auto;
  padding: 20px;
}

@media (max-width: 767px) {
  .detail-page { padding: 16px; }
  .top-row { grid-template-columns: 1fr; }
  .essay-split { grid-template-columns: 1fr; }
  .fullscreen-split { grid-template-columns: 1fr; }
}
</style>
