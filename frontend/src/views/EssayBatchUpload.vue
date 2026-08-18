<template>
  <div class="page">
    <div v-if="isDesktop" class="page-title">批量上传</div>

    <!-- 模板选择区域 -->
    <van-cell-group inset style="margin-bottom:12px">
      <van-field :model-value="selectedTaskName" is-link readonly label="选择收集任务"
        placeholder="选择收集任务（自动填充年级等信息）" @click="showTaskPicker = true" />
      <van-cell v-if="selectedTaskTopic" title="文章主题" :label="selectedTaskTopic" />
    </van-cell-group>

    <!-- 模式选择（含各自上传说明） -->
    <div class="mode-boxes">
      <div class="mode-box" :class="{ active: mode === 'essay' }" @click="switchMode('essay')">
        <div class="mode-icon">📁</div>
        <div class="mode-title">批量上传文件夹作文</div>
        <div class="mode-desc">按学生文件夹结构上传原文</div>
        <div class="mode-tip">
          <div class="tip-label">文件夹结构：</div>
          <div class="tip-content">
            根文件/<br>
            &nbsp;&nbsp;├── 学生1/<br>
            &nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── 1.jpg<br>
            &nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── 2.jpg<br>
            &nbsp;&nbsp;├── 学生2/<br>
            &nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── 1.png<br>
            &nbsp;&nbsp;└── 学生3/<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── 作文.docx
          </div>
          <div class="tip-note">* 二级目录名称作为学生姓名</div>
          <div class="tip-note">* 支持格式：jpg/jpeg/png/gif/webp/docx/txt（不支持 .doc 旧版格式）</div>
          <div class="tip-note">* docx/txt 自动读取内容；含「修改前/修改后」则拆分，否则全部作修改前</div>
          <div class="tip-note">* 一个学生文件夹有多个 docx：全部读取并按标题分组——标题相同只保留一篇（修改版优先），标题不同分别展示、各存一篇；图片归入第一篇</div>
          <div class="tip-note">* docx/txt 自动分析标题（首个非「修改前/修改后」行），预览可见</div>
          <div class="tip-note">* 文件夹名可含「{年级}第{次数}次」自动填充（如：高二第三次作文）</div>
        </div>
      </div>
      <div class="mode-box" :class="{ active: mode === 'correction' }" @click="switchMode('correction')">
        <div class="mode-icon">📄</div>
        <div class="mode-title">批量上传修改后docx</div>
        <div class="mode-desc">上传批改后的 docx 文件</div>
        <div class="mode-tip">
          <div class="tip-label">文件名（推荐）：</div>
          <div class="tip-content">
            2026-08-14_改_原文件名——学生姓名.docx<br>
            改_作文——张三.docx<br>
            改_作文——李四.docx
          </div>
          <div class="tip-note">* 文件名开头含「年-月-日」时自动作为该篇收集时间（如 2026-08-14_改_作文——张三.docx）</div>
          <div class="tip-note">* 不要求必须按此命名：文件名无「——学生名」时，自动读取文档内「——姓名」行</div>
          <div class="tip-note">* 仍无法识别姓名时，可在下方预览中手动填写</div>
          <div class="tip-note">* 内容需含「修改前：/修改后：」关键字，自动拆分修改前/修改后文章</div>
          <div class="tip-note">* 支持格式：docx（不支持 .doc 旧版格式）</div>
        </div>
      </div>
    </div>

    <!-- 共用表单 -->
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field :model-value="selectedGrade" is-link readonly label="年级" placeholder="请选择（可不选）"
          @click="showGradePicker = true" />
        <van-field v-model="activeForm.essay_number" label="第几次" placeholder="数字（可不填）" type="digit" />
        <van-field name="teaching_mode" label="提交方式">
          <template #input>
            <van-radio-group v-model="activeForm.teaching_mode" direction="horizontal">
              <van-radio name="线下" style="margin-right:16px">线下</van-radio>
              <van-radio name="线上">线上</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field name="is_supplement" label="是否补交">
          <template #input><van-switch v-model="activeForm.is_supplement" size="24" /></template>
        </van-field>
        <van-field v-model="activeForm.collector_note" label="统一收集者备注" placeholder="应用到本批所有作文（可选）" />
        <van-field v-if="isAdmin" :model-value="selectedCollectorName" is-link readonly label="收集者" placeholder="默认当前用户"
          @click="showCollectorPicker = true" />
        <van-field name="pre_check_existing" label="跳过已存在的学生">
          <template #input><van-switch v-model="preCheckExisting" size="24" @change="onPreCheckChange" /></template>
        </van-field>
        <van-cell title="选择文件夹" :label="folderLabel" is-link @click="openFolderPicker" />
      </van-cell-group>
      <input ref="folderInput" type="file" webkitdirectory style="display:none" @change="onFolderChange" />
      <input ref="corFolderInput" type="file" webkitdirectory style="display:none" @change="onCorFolderChange" />

      <!-- 预检工具栏 -->
      <div v-if="(mode === 'essay' && folderSelected) || (mode === 'correction' && corFolderSelected && !corParsing)" class="preview-toolbar">
        <button class="btn" style="font-size:12px;padding:4px 10px" @click="checkExisting" :disabled="checkingExisting">
          {{ checkingExisting ? '检查中...' : '🔍 检查已存在' }}
        </button>
        <span v-if="!selectedTaskId" style="font-size:12px;color:#999">未选择任务，无法预检（重复学生将自动跳过）</span>
        <span v-else-if="existingNames.length" style="font-size:12px;color:#d46b08">已有 {{ existingNames.length }} 位学生，将自动跳过</span>
        <span v-else-if="checkedExisting" style="font-size:12px;color:#52c41a">无已存在学生</span>
      </div>

      <!-- 图片压缩进度 -->
      <div v-if="compressing" class="progress-box" style="margin:12px 16px 0">
        <van-progress :percentage="compressPercent" stroke-width="8" />
        <div class="progress-text">正在处理文件 {{ compressDone }}/{{ compressTotal }}</div>
      </div>

      <!-- 预览：作文模式 -->
      <div v-if="mode === 'essay' && folderSelected" class="preview-box">
        <div class="preview-head">
          <span class="preview-head-title">📋 上传预览</span>
          <span class="preview-head-count">{{ studentCount }} 位学生 · {{ essayTotal }} 篇 · {{ totalFiles }} 个文件 · 修改前 {{ essayBeforeTotal }} 字 / 修改后 {{ essayAfterTotal }} 字</span>
        </div>
        <div class="preview-table-wrap">
          <table class="preview-table">
            <thead>
              <tr>
                <th style="width:110px">学生姓名</th>
                <th>标题</th>
                <th style="width:76px">修改前字数</th>
                <th style="width:76px">修改后字数</th>
                <th style="width:70px">文件</th>
                <th style="width:96px">收集时间</th>
                <th style="width:80px">状态</th>
                <th style="width:44px"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in essayGroups" :key="idx" :class="{ 'row-existing': existingNames.includes(item.studentName) }">
                <td class="cell-name">
                  {{ item.studentName }}
                  <span v-if="essayIsMulti(idx)" class="chip chip-blue">第{{ essayOrdinal(idx) }}篇</span>
                </td>
                <td class="cell-title" :title="item.title">{{ item.title || '-' }}</td>
                <td class="cell-num">{{ item.before ? item.before.length : '-' }}</td>
                <td class="cell-num">{{ item.after ? item.after.length : '-' }}</td>
                <td class="cell-meta">{{ item.files.length }} 个</td>
                <td class="cell-meta">{{ item.collectTime || '-' }}</td>
                <td>
                  <span v-if="existingNames.includes(item.studentName)" class="chip chip-warn">已存在</span>
                  <span v-else class="chip chip-ok">正常</span>
                </td>
                <td><button class="row-remove" title="移除该作文" @click="removeEssay(idx)">✕</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="skipStats.total > 0" class="skip-note">
          ⚠️ 已跳过 {{ skipStats.total }} 个文件（修改后目录 {{ skipStats.modifiedFolder }} / 不支持格式 {{ skipStats.unsupported }} / 非学生目录 {{ skipStats.noStudent }} / 图片超8MB {{ skipStats.oversize }} / 旧版doc {{ skipStats.docOld }}）
        </div>
      </div>

      <!-- 预览：修改后模式 -->
      <div v-if="mode === 'correction' && corFolderSelected" class="preview-box">
        <div v-if="corParsing" class="progress-box">
          <van-progress :percentage="corParsePercent" stroke-width="8" />
          <div class="progress-text">正在解析文件 {{ corParsedCount }}/{{ corFileTotal }}</div>
        </div>
        <template v-else>
          <div class="preview-head">
            <span class="preview-head-title">📄 上传预览</span>
            <span class="preview-head-count">
              可上传 {{ corValidCount }} 个 · 修改前 {{ corBeforeTotal }} 字 / 修改后 {{ corAfterTotal }} 字
              <template v-if="corParseFailCount"> · 失败 {{ corParseFailCount }}</template>
              <template v-if="corUnnamedCount"> · 待填姓名 {{ corUnnamedCount }}</template>
            </span>
          </div>
          <div class="preview-table-wrap">
            <table class="preview-table">
              <thead>
                <tr>
                  <th style="width:130px">学生姓名</th>
                  <th>标题</th>
                  <th style="width:76px">修改前字数</th>
                  <th style="width:76px">修改后字数</th>
                  <th style="width:96px">收集时间</th>
                  <th style="width:90px">状态</th>
                  <th style="width:44px"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in corFiles" :key="idx" :class="{ 'row-existing': item.ok && existingNames.includes(item.studentName) }">
                  <td>
                    <input v-if="item.ok" v-model="item.studentName" class="name-input" :class="{ 'name-input-empty': !item.studentName }"
                      placeholder="填写姓名" />
                    <span v-else class="cell-name">{{ item.studentName || '未识别' }}</span>
                  </td>
                  <td class="cell-title" :title="item.title">{{ item.title || '无标题' }}</td>
                  <td class="cell-num">{{ (item.before || '').length }}</td>
                  <td class="cell-num">{{ (item.after || '').length }}</td>
                  <td class="cell-meta">{{ item.collectTime || '-' }}</td>
                  <td>
                    <span v-if="!item.ok" class="chip chip-danger">解析失败</span>
                    <span v-else-if="existingNames.includes(item.studentName)" class="chip chip-warn">已存在</span>
                    <span v-else-if="!item.studentName" class="chip chip-danger">待填姓名</span>
                    <span v-else class="chip chip-ok">正常</span>
                  </td>
                  <td><button class="row-remove" title="移除该文件" @click="removeCorFile(idx)">✕</button></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="corParseFailCount" class="skip-note">⚠️ {{ corParseFailCount }} 个文件解析失败，将不会上传，请检查格式或移除</div>
          <div v-if="corUnnamedCount" class="skip-note" style="color:#d46b08;background:#fffbe6;border-top:1px dashed #ffe58f">
            ✏️ 有 {{ corUnnamedCount }} 个文件未识别学生姓名，请在预览中填写后再上传
          </div>
        </template>
      </div>

      <!-- 提交 -->
      <div style="margin:16px">
        <van-button round block type="primary" native-type="submit" :loading="loading || corLoading" :disabled="submitDisabled">
          {{ submitLabel }}
        </van-button>
      </div>

      <!-- 进度：作文模式 -->
      <div v-if="loading" class="progress-box">
        <van-progress :percentage="essaysPercent" stroke-width="8" />
        <div class="progress-text">正在上传：{{ currentStudent }}</div>
        <div class="progress-stats">
          <span class="stat-success">成功 {{ essaysSuccess }}</span>
          <span class="stat-skip" v-if="essaysSkip">跳过 {{ essaysSkip }}</span>
          <span class="stat-fail">失败 {{ essaysFail }}</span>
        </div>
      </div>

      <!-- 进度：修改后模式 -->
      <div v-if="corLoading" class="progress-box">
        <van-progress :percentage="corPercent" stroke-width="8" />
        <div class="progress-text">正在上传：{{ corCurrentStudent }}</div>
        <div class="progress-stats">
          <span class="stat-success">成功 {{ corSuccess }}</span>
          <span class="stat-skip" v-if="corSkipExisting">跳过 {{ corSkipExisting }}</span>
          <span class="stat-fail">失败 {{ corFail }}</span>
        </div>
      </div>
    </van-form>

    <!-- 结果弹窗 -->
    <van-dialog v-model:show="resultDialog.show" :title="resultDialog.title" :show-cancel-button="false" :show-confirm-button="false" :close-on-click-overlay="true">
      <div style="padding:16px">
        <div class="result-body">{{ resultDialog.body }}</div>
        <div style="display:flex;gap:8px;margin-top:12px;justify-content:flex-end;flex-wrap:wrap">
          <button class="btn" @click="copyResult">📋 复制明细</button>
          <button class="btn" @click="goUploadList">📋 去列表查看</button>
          <button class="btn" @click="resetAfterUpload">📁 上传下一批</button>
          <button class="btn" @click="resultDialog.show = false">关闭</button>
          <button v-if="resultDialog.canRetry" class="btn btn-primary" @click="retryFailed">仅重试失败 {{ resultDialog.retryCount }}</button>
        </div>
      </div>
    </van-dialog>

    <van-action-sheet v-model:show="showGradePicker" title="选择年级">
      <div class="picker-list">
        <van-cell v-for="g in grades" :key="g" :title="g" @click="selectGrade(g)" />
      </div>
    </van-action-sheet>

    <!-- 模板选择器 -->
    <van-action-sheet v-model:show="showTaskPicker" title="选择收集任务" class="task-picker-sheet">
      <div class="picker-list">
        <div style="padding:8px 16px">
          <input v-model="taskSearch" placeholder="搜索任务名称/主题/年级..." style="width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;outline:none" />
        </div>
        <div style="padding:0 16px 8px;display:flex;align-items:center;gap:6px;font-size:13px;color:#666">
          <van-checkbox v-model="showActiveOnly" icon-size="16px" shape="square">只看收集中</van-checkbox>
          <span style="color:#999;font-size:12px">（关闭可查看全部 {{ sortedTasks.length }} 个任务）</span>
        </div>
        <van-cell title="不使用模板" @click="selectTask(null)" style="color:#999" />
        <div class="task-split">
          <div class="task-col">
            <div class="task-col-title">线上</div>
            <van-cell v-for="t in filteredOnlineTasks" :key="t.id" @click="selectTask(t)">
              <template #title>
                <span style="font-weight:500">{{ t.name }}</span>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
              </template>
              <template #label>
                <span class="badge-mini tag-grade">{{ t.grade }}</span>
                <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
                <span v-if="t.essay_topic" style="color:#999">{{ t.essay_topic }}</span>
              </template>
            </van-cell>
            <div v-if="!filteredOnlineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线上任务</div>
          </div>
          <div class="task-col">
            <div class="task-col-title">线下</div>
            <van-cell v-for="t in filteredOfflineTasks" :key="t.id" @click="selectTask(t)">
              <template #title>
                <span style="font-weight:500">{{ t.name }}</span>
                <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
              </template>
              <template #label>
                <span class="badge-mini tag-grade">{{ t.grade }}</span>
                <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
                <span v-if="t.essay_topic" style="color:#999">{{ t.essay_topic }}</span>
              </template>
            </van-cell>
            <div v-if="!filteredOfflineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线下任务</div>
          </div>
        </div>
      </div>
    </van-action-sheet>

    <!-- 收集者选择器 -->
    <van-action-sheet v-model:show="showCollectorPicker" title="选择收集者">
      <div class="picker-list">
        <van-cell title="默认（当前用户）" @click="selectCollector(null)" />
        <van-cell v-for="c in collectorList" :key="c.id" :title="c.nickname || c.username" @click="selectCollector(c)" />
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth } from '../api'
import { useEssayFolderUpload } from '../composables/useEssayFolderUpload'
import { useCorrectionUpload } from '../composables/useCorrectionUpload'

const route = useRoute()
const router = useRouter()
const { isDesktop } = useScreen()
const { getAuth } = useAuth()
const currentUser = computed(() => getAuth()?.user || {})
const isAdmin = computed(() => (currentUser.value.role || '').includes('admin'))
const isGuest = computed(() => (currentUser.value.role || '').includes('guest'))

const mode = ref('essay')

// 共用表单
const form = ref({ grade: '', essay_number: '', teaching_mode: '线上', is_supplement: false, collector_note: '' })
const corForm = ref({ grade: '', essay_number: '', teaching_mode: '线上', is_supplement: false, collector_note: '' })
const activeForm = computed(() => mode.value === 'essay' ? form.value : corForm.value)
const selectedGrade = ref('')
const selectedTaskName = ref('')
const selectedTaskTopic = ref('')
const selectedTaskId = ref(null)
const selectedCourseId = ref(null)
const selectedCollector = ref(null)
const selectedCollectorName = ref('')
const collectorList = ref([])
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']
const folderInput = ref(null)
const corFolderInput = ref(null)
const tasks = ref([])
const showGradePicker = ref(false)
const showTaskPicker = ref(false)
const showCollectorPicker = ref(false)

// 预检
const preCheckExisting = ref(false)
const existingNames = ref([])
const checkingExisting = ref(false)
const checkedExisting = ref(false)

// 上传上下文（供组合式函数读取）
const ctx = ref({ taskId: null, courseId: null, collectorId: null, form: form.value, existingNames: [], preCheckExisting: false })

function syncCtx() {
  ctx.value = {
    taskId: selectedTaskId.value,
    courseId: selectedCourseId.value,
    collectorId: selectedCollector.value,
    form: activeForm.value,
    existingNames: existingNames.value,
    preCheckExisting: preCheckExisting.value,
  }
}

watch([selectedTaskId, selectedCourseId, selectedCollector, mode, form, corForm, existingNames, preCheckExisting], syncCtx, { deep: true })

// 结果弹窗
const resultDialog = ref({ show: false, title: '', body: '', canRetry: false, retryCount: 0, retryMode: '', retryNames: [] })

function onModeResult(res) {
  resultDialog.value = { show: true, title: res.title, body: res.body, canRetry: res.canRetry, retryCount: res.retryCount, retryMode: res.mode, retryNames: res.retryNames || [] }
}

// 组合式函数（两个上传模式）
const {
  essayGroups, folderSelected, skipStats, loading, uploadedCount, currentStudent,
  essaysSuccess, essaysFail, essaysSkip, failedStudents, uploadFinished: essayUploadFinished,
  compressing, compressTotal, compressDone, compressPercent,
  studentCount, essayTotal, totalFiles, essaysPercent, essayBeforeTotal, essayAfterTotal,
  onFolderChange, removeEssay, uploadEssays, retryFailed: retryEssay, reset: resetEssay,
} = useEssayFolderUpload(ctx, { onResult: onModeResult, onFolderSelected: handleFolderSelected })

const {
  corFiles, corFolderSelected, corParsing, corParsedCount, corFileTotal, corParsePercent,
  corValidCount, corParseFailCount, corUnnamedCount, corBeforeTotal, corAfterTotal, corLoading, corUploadedCount,
  corCurrentStudent, corSuccess, corFail, corFailed, corSkipExisting, corPercent,
  uploadFinished: corUploadFinished,
  onCorFolderChange, removeCorFile, upload: uploadCorrectionsMode, retryFailed: retryCor, reset: resetCor,
} = useCorrectionUpload(ctx, { onResult: onModeResult, onFolderSelected: handleFolderSelected })

const uploadFinished = computed(() => mode.value === 'essay' ? essayUploadFinished.value : corUploadFinished.value)

// 文件夹辅助
function chineseToNumber(str) {
  const map = { '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10 }
  if (map[str] !== undefined) return map[str]
  if (str.startsWith('十')) {
    const rest = str.substring(1)
    return 10 + (map[rest] || 0)
  }
  if (str.endsWith('十')) {
    const first = str.charAt(0)
    return (map[first] || 0) * 10
  }
  if (str.includes('十')) {
    const parts = str.split('十')
    return (map[parts[0]] || 0) * 10 + (map[parts[1]] || 0)
  }
  return 0
}

function parseFolderName(folderName) {
  const result = { grade: '', essay_number: '' }
  const gradeMatch = folderName.match(/(初一|初二|初三|高一|高二|高三)/)
  if (gradeMatch) {
    result.grade = gradeMatch[1]
  }
  const numberMatch = folderName.match(/第([一二三四五六七八九十百零\d]+)次/)
  if (numberMatch) {
    const numStr = numberMatch[1]
    if (/^\d+$/.test(numStr)) {
      result.essay_number = numStr
    } else {
      const num = chineseToNumber(numStr)
      if (num > 0) result.essay_number = String(num)
    }
  }
  return result
}

function getFolderPath(files) {
  for (const file of files) {
    const relativePath = file.webkitRelativePath
    if (relativePath) {
      return relativePath.split('/')[0]
    }
  }
  return ''
}

function handleFolderSelected(files) {
  const folderName = getFolderPath(files)
  const targetForm = mode.value === 'essay' ? form.value : corForm.value
  if (folderName) {
    const parsed = parseFolderName(folderName)
    if (parsed.grade && !targetForm.grade) {
      targetForm.grade = parsed.grade
      selectedGrade.value = parsed.grade
    }
    if (parsed.essay_number && !targetForm.essay_number) {
      targetForm.essay_number = parsed.essay_number
    }
  }
  if (preCheckExisting.value && selectedTaskId.value) {
    checkExisting()
  } else {
    existingNames.value = []
    checkedExisting.value = false
  }
  syncCtx()
}

function essayIsMulti(idx) {
  const g = essayGroups.value[idx]
  if (!g) return false
  return essayGroups.value.filter(x => x.studentName === g.studentName).length > 1
}

function essayOrdinal(idx) {
  const g = essayGroups.value[idx]
  if (!g) return 1
  let n = 0
  for (let i = 0; i <= idx; i++) {
    if (essayGroups.value[i].studentName === g.studentName) n++
  }
  return n
}

// 选择器
function switchMode(m) {
  if (m === mode.value) return
  mode.value = m
  resetEssay()
  resetCor()
  existingNames.value = []
  checkedExisting.value = false
}

function openFolderPicker() {
  if (mode.value === 'essay') folderInput.value?.click()
  else corFolderInput.value?.click()
}

function selectGrade(g) {
  form.value.grade = g
  corForm.value.grade = g
  selectedGrade.value = g
  showGradePicker.value = false
}

function selectCollector(c) {
  if (c) {
    selectedCollector.value = c.id
    selectedCollectorName.value = c.nickname || c.username
  } else {
    selectedCollector.value = null
    selectedCollectorName.value = ''
  }
  showCollectorPicker.value = false
}

function selectTask(tpl) {
  if (tpl) {
    form.value.grade = tpl.grade
    corForm.value.grade = tpl.grade
    selectedGrade.value = tpl.grade
    form.value.essay_number = tpl.essay_number ? String(tpl.essay_number) : ''
    corForm.value.essay_number = tpl.essay_number ? String(tpl.essay_number) : ''
    if (tpl.teaching_mode) {
      form.value.teaching_mode = tpl.teaching_mode
      corForm.value.teaching_mode = tpl.teaching_mode
    }
    selectedTaskName.value = tpl.name
    selectedTaskTopic.value = tpl.essay_topic || ''
    selectedTaskId.value = tpl.id
    selectedCourseId.value = tpl.course_id || null
    if (preCheckExisting.value && (folderSelected.value || corFolderSelected.value)) checkExisting()
    showToast(`已选择：${tpl.name}`)
  } else {
    selectedTaskName.value = ''
    selectedTaskTopic.value = ''
    selectedTaskId.value = null
    selectedCourseId.value = null
    existingNames.value = []
    checkedExisting.value = false
    showToast('已取消模板选择')
  }
  showTaskPicker.value = false
}

const taskSearch = ref('')
const showActiveOnly = ref(true)
const sortedTasks = computed(() => {
  return [...tasks.value].sort((a, b) => {
    // 迁移任务排到末尾
    const aMig = (a.course_name || '').includes('迁移')
    const bMig = (b.course_name || '').includes('迁移')
    if (aMig !== bMig) return aMig ? 1 : -1
    const aActive = taskIsActive(a)
    const bActive = taskIsActive(b)
    if (aActive !== bActive) return aActive ? -1 : 1
    return 0
  })
})
const onlineTasks = computed(() => sortedTasks.value.filter(t => t.teaching_mode === '线上'))
const offlineTasks = computed(() => sortedTasks.value.filter(t => t.teaching_mode !== '线上'))
const filteredOnlineTasks = computed(() => {
  const kw = taskSearch.value.trim().toLowerCase()
  let list = onlineTasks.value
  if (showActiveOnly.value && !kw) list = list.filter(taskIsActive)
  if (!kw) return list
  return list.filter(t => (t.name || '').toLowerCase().includes(kw) || (t.essay_topic || '').toLowerCase().includes(kw) || (t.grade || '').includes(kw))
})
const filteredOfflineTasks = computed(() => {
  const kw = taskSearch.value.trim().toLowerCase()
  let list = offlineTasks.value
  if (showActiveOnly.value && !kw) list = list.filter(taskIsActive)
  if (!kw) return list
  return list.filter(t => (t.name || '').toLowerCase().includes(kw) || (t.essay_topic || '').toLowerCase().includes(kw) || (t.grade || '').includes(kw))
})

function taskIsActive(t) {
  const now = new Date()
  return t.is_active
    && (!t.deadline || new Date(t.deadline) >= now)
    && (!t.start_time || new Date(t.start_time) <= now)
}

onMounted(async () => {
  if (isGuest.value) {
    router.replace('/dashboard')
    showToast('游客无上传权限')
    return
  }
  try {
    const res = await api.get('/essays/tasks')
    tasks.value = res.data
    const taskIdFromQuery = Number(route.query.task_id)
    if (taskIdFromQuery) {
      const target = tasks.value.find(t => t.id === taskIdFromQuery)
      if (target) selectTask(target)
    }
  } catch {}
  if (isAdmin.value) {
    try {
      const res = await api.get('/essays/collectors')
      collectorList.value = res.data || []
    } catch {}
  }
  syncCtx()
})

// 预检
async function checkExisting() {
  if (!selectedTaskId.value) { showToast('请先选择收集任务'); return }
  checkingExisting.value = true
  try {
    const params = { task_id: selectedTaskId.value }
    if (activeForm.value.essay_number) params.essay_number = parseInt(activeForm.value.essay_number)
    if (activeForm.value.is_supplement) params.is_supplement = activeForm.value.is_supplement
    const res = await api.get('/essays/existing-students', { params })
    existingNames.value = res.data.students || []
    checkedExisting.value = true
    syncCtx()
  } catch {
    existingNames.value = []
    showToast('检查失败，请稍后重试')
  } finally {
    checkingExisting.value = false
  }
}

function onPreCheckChange(val) {
  existingNames.value = []
  checkedExisting.value = false
  if (val && (folderSelected.value || corFolderSelected.value) && selectedTaskId.value) {
    checkExisting()
  } else {
    syncCtx()
  }
}

// 上传提交
const folderLabel = computed(() => {
  if (mode.value === 'essay') {
    return folderSelected.value ? `${studentCount.value} 位学生，${totalFiles.value} 个文件` : '点击选择（学生文件夹）'
  }
  return corFolderSelected.value ? `${corValidCount.value} 个可上传文件` : '点击选择（docx 文件夹）'
})

const submitDisabled = computed(() => {
  if (uploadFinished.value) return true
  if (mode.value === 'essay') return !folderSelected.value
  return !corFolderSelected.value || corParsing.value || corValidCount.value === 0
})

const submitLabel = computed(() => {
  if (uploadFinished.value) return '✅ 已上传完成，选择下一批'
  if (loading.value) return `上传中 ${uploadedCount.value}/${essayTotal.value}`
  if (corLoading.value) return `上传中 ${corUploadedCount.value}/${corValidCount.value}`
  return mode.value === 'essay' ? '开始上传文件夹作文' : '开始上传修改后docx'
})

async function onSubmit() {
  if (!activeForm.value.grade) {
    const ok = await showConfirmDialog({
      title: '提示',
      message: '未选择年级，将按「未定年级」归档。确定继续上传吗？',
      confirmButtonText: '继续上传',
      cancelButtonText: '取消',
    }).then(() => true).catch(() => false)
    if (!ok) return
  }
  if (!activeForm.value.essay_number) {
    const ok = await showConfirmDialog({
      title: '提示',
      message: '未填写第几次，将按「无第几次」归档。确定继续上传吗？',
      confirmButtonText: '继续上传',
      cancelButtonText: '取消',
    }).then(() => true).catch(() => false)
    if (!ok) return
  }
  if (mode.value === 'essay') {
    await uploadEssays()
  } else {
    await uploadCorrectionsMode()
  }
}

function retryFailed() {
  const d = resultDialog.value
  resultDialog.value.show = false
  if (d.retryMode === 'essay') {
    retryEssay(d.retryNames).then(() => {
      existingNames.value = ctx.value.existingNames
      syncCtx()
    })
  } else {
    retryCor(d.retryNames)
  }
}

function goUploadList() {
  resultDialog.value.show = false
  router.push('/essay/list')
}

function resetAfterUpload() {
  resetEssay()
  resetCor()
  existingNames.value = []
  checkedExisting.value = false
  resultDialog.value.show = false
  syncCtx()
}

function copyResult() {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(resultDialog.value.body).then(() => showToast('已复制明细')).catch(() => showToast('复制失败'))
  } else {
    showToast('当前浏览器不支持一键复制')
  }
}
</script>

<style scoped>
.page { padding: 16px; }
.picker-list { max-height: 70vh; overflow-y: auto; }
@media (max-width: 767px) { .page { padding: 0; } }

/* 任务选择面板：避免双重滚动容器导致无法回拉 */
:deep(.task-picker-sheet) {
  max-height: 90vh;
}
:deep(.task-picker-sheet .van-action-sheet__content) {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
:deep(.task-picker-sheet .picker-list) {
  max-height: none;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.mode-boxes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}
.mode-box {
  background: #fff;
  border: 2px solid #f0f0f0;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
}
.mode-box:hover { border-color: #bcd6ff; }
.mode-box.active { border-color: #1677ff; background: #eef5ff; }
.mode-icon { font-size: 26px; }
.mode-title { font-weight: 600; font-size: 14px; margin-top: 6px; color: #333; }
.mode-desc { font-size: 12px; color: #999; margin-top: 4px; }

.mode-tip {
  text-align: left;
  background: #f8f9fb;
  border-radius: 8px;
  padding: 10px;
  margin-top: 10px;
  font-size: 12px;
  max-height: 260px;
  overflow-y: auto;
}
.mode-box.active .mode-tip { background: #fff; }

.task-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-top: 1px solid #f0f0f0;
}

.task-col {
  max-height: 65vh;
  overflow-y: auto;
  padding: 8px 0;
}

.task-col + .task-col {
  border-left: 1px solid #f0f0f0;
}

.task-col-title {
  padding: 8px 16px;
  font-size: 13px;
  color: #888;
  font-weight: 500;
}

.tip-label {
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.tip-content {
  background: #fff;
  padding: 10px 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.8;
  color: #555;
  border: 1px solid #e8e8e8;
}

.tip-note {
  margin-top: 8px;
  color: #888;
  font-size: 12px;
}

.preview-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 0 4px;
  font-size: 12px;
  flex-wrap: wrap;
}

.preview-box {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-top: 8px;
  background: #fff;
  overflow: hidden;
}

.preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 14px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}
.preview-head-title { font-weight: 600; font-size: 13px; color: #333; }
.preview-head-count { font-size: 12px; color: #888; }

.preview-table-wrap {
  overflow-x: auto;
  max-height: 260px;
  overflow-y: auto;
}

.preview-table {
  width: 100%;
  min-width: 520px;
  border-collapse: collapse;
  font-size: 13px;
}
.preview-table th {
  background: #fafafa;
  padding: 8px 10px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: #666;
  border-bottom: 1px solid #f0f0f0;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 1;
}
.preview-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #f5f5f5;
  vertical-align: middle;
}
.preview-table tbody tr:hover td { background: #fafafa; }
.preview-table tr.row-existing td { background: #fafafa; }
.preview-table tr.row-existing .cell-name { color: #999; text-decoration: line-through; }

.cell-name { font-weight: 600; color: #333; white-space: nowrap; }
.cell-title {
  color: #1677ff;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cell-meta { color: #888; font-size: 12px; white-space: nowrap; }
.cell-num { color: #555; text-align: center; white-space: nowrap; }

.chip {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  line-height: 18px;
  white-space: nowrap;
}
.chip-ok { background: #f6ffed; color: #52c41a; }
.chip-warn { background: #fff7e6; color: #d46b08; }
.chip-danger { background: #fff1f0; color: #ff4d4f; }
.chip-blue { background: #e6f4ff; color: #1677ff; }

.row-remove {
  width: 22px;
  height: 22px;
  line-height: 20px;
  text-align: center;
  border: none;
  border-radius: 50%;
  background: #f5f5f5;
  color: #999;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.row-remove:hover { background: #ff4d4f; color: #fff; }

.name-input {
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 13px;
  width: 118px;
  outline: none;
  transition: border-color 0.15s;
}
.name-input:focus { border-color: #4096ff; }
.name-input-empty { border-color: #ffa940; background: #fffbe6; }

.skip-note {
  padding: 8px 12px;
  font-size: 12px;
  color: #d46b08;
  background: #fffbe6;
  border-top: 1px dashed #ffe58f;
}

.progress-box {
  margin-top: 12px;
  padding: 12px;
  background: #f6f8fa;
  border-radius: 6px;
}

.progress-text {
  margin-top: 8px;
  font-size: 13px;
  color: #555;
}

.progress-stats {
  margin-top: 6px;
  font-size: 12px;
  display: flex;
  gap: 16px;
}

.stat-success {
  color: #52c41a;
}

.stat-skip {
  color: #fa8c16;
}

.stat-fail {
  color: #ff4d4f;
}

.result-body {
  max-height: 40vh;
  overflow-y: auto;
  white-space: pre-line;
  font-size: 13px;
  line-height: 1.7;
}
</style>
