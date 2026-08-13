<template>
  <div class="page detail-page" :class="{ 'desktop-layout': isDesktop }">
    <div v-if="loading" style="padding:40px;text-align:center;color:#999">加载中...</div>

    <template v-if="!loading && essay">
      <div v-if="isDesktop" class="breadcrumb">
        <router-link to="/essay/list" class="breadcrumb-link">作文列表</router-link>
        <span class="breadcrumb-sep">/</span>
        <span class="breadcrumb-current">作文详情 - {{ essay.student_name }}《{{ essay.essay_title || '无标题' }}》</span>
      </div>
      <div v-if="isDesktop" class="page-title">作文详情</div>

      <!-- ===== 桌面端：状态流转条 ===== -->
      <div v-if="isDesktop" class="status-strip" :class="'strip-' + essay.status">
        <span class="tag" :class="'tag-' + essay.status">{{ statusLabel(essay.status) }}</span>
        <span class="strip-hint">{{ statusHint }}</span>
        <div class="flow-bar">
          <span class="flow-item" :class="{ done: flowState.done >= 1 }">📤 提交</span>
          <span class="flow-arrow">→</span>
          <span class="flow-item" :class="{ done: flowState.done >= 2, active: flowState.active === 1 }">✏️ 批改</span>
          <span class="flow-arrow">→</span>
          <span class="flow-item" :class="{ done: flowState.done >= 3, active: flowState.active === 2 }">✅ 确认</span>
        </div>
      </div>

      <!-- ===== 桌面端：顶部行（基本信息 + 修改状态）===== -->
      <div v-if="isDesktop" class="top-row">
        <div class="card top-card">
          <div class="card-header">
            <h3>📝 基本信息</h3>
            <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" @click="saveEdit" :disabled="!canEdit">💾 保存</button>
          </div>

          <div class="info-section">
            <div class="info-section-title">👤 学生与作文</div>
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
            </div>
          </div>

          <div class="info-section">
            <div class="info-section-title">📋 任务信息</div>
            <div class="info-grid">
              <div ref="detailTaskFilterRef" class="info-item" style="position:relative">
                <span class="info-label">任务</span>
                <input v-model="detailTaskSearch" placeholder="搜索选择任务" class="edit-input" :disabled="!canEdit" @focus="showDetailTaskDropdown = true" @input="showDetailTaskDropdown = true" />
                <div v-if="showDetailTaskDropdown" class="task-dropdown-detail">
                  <div @mousedown.prevent @click="editForm.task_id = 0; detailTaskSearch = ''; showDetailTaskDropdown = false" :class="{ 'task-item-active': !editForm.task_id }" class="task-item">无任务</div>
                  <div v-for="t in filteredDetailTasks" :key="t.id" @mousedown.prevent @click="editForm.task_id = t.id; detailTaskSearch = t.name; showDetailTaskDropdown = false" :class="{ 'task-item-active': editForm.task_id == t.id }" class="task-item">{{ t.name }}</div>
                  <div v-if="!filteredDetailTasks.length" class="task-item" style="color:#999">无匹配任务</div>
                </div>
              </div>
              <div class="info-item"><span class="info-label">课程</span><span class="info-static">{{ essay.course_name || '-' }}</span></div>
              <div class="info-item"><span class="info-label">提交方式</span>
                <select v-model="editForm.teaching_mode" class="edit-input" :disabled="!canEdit">
                  <option value="线上">线上</option>
                  <option value="线下">线下</option>
                </select>
              </div>
              <div class="info-item"><span class="info-label">是否补交</span>
                <select v-model="editForm.is_supplement" class="edit-input" :disabled="!canEdit">
                  <option :value="false">否</option>
                  <option :value="true">是</option>
                </select>
              </div>
            </div>
          </div>

          <div class="info-section">
            <div class="info-section-title">👥 人员与统计</div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">收集者</span>
                <template v-if="isAdmin && !isReadonly">
                  <select v-model="editForm.collected_by" class="edit-input">
                    <option v-for="u in collectorList" :key="u.id" :value="u.id">{{ u.nickname || u.username }}</option>
                  </select>
                </template>
                <template v-else>
                  <span class="info-static">{{ essay.collector_name || '-' }}</span>
                </template>
              </div>
              <div class="info-item"><span class="info-label">修改者</span><span class="info-static">{{ essay.reviewer_name || '-' }}</span></div>
              <div class="info-item"><span class="info-label">修改前字数</span><span class="info-static">{{ essay.word_count || 0 }} 字</span></div>
              <div class="info-item"><span class="info-label">修改后字数</span><span class="info-static">{{ essay.corrected_word_count || 0 }} 字</span></div>
            </div>
          </div>

          <div class="info-section">
            <div class="info-section-title">💬 备注</div>
            <div class="info-grid">
              <div class="info-item"><span class="info-label">收集者备注</span><input v-model="editForm.collector_note" class="edit-input" :disabled="!canEdit" /></div>
              <div class="info-item"><span class="info-label">批改者备注</span><input v-model="editForm.reviewer_note" class="edit-input" disabled :placeholder="essay.reviewer_note ? '' : '暂无'" /></div>
            </div>
          </div>

          <div class="info-section">
            <div class="info-section-title">🕐 时间</div>
            <div class="info-grid">
              <div class="info-item"><span class="info-label">上传时间</span><span class="info-static">{{ formatDateTime(essay.created_at) }}</span></div>
              <div class="info-item"><span class="info-label">修改时间</span><span class="info-static">{{ essay.corrected_at ? formatDateTime(essay.corrected_at) : '未修改' }}</span></div>
            </div>
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
            <div class="form-group">
              <label>批改者备注</label>
                <textarea v-model="correctionNote" rows="2" placeholder="批改者自定义备注（可选）..."></textarea>
            </div>
            <button class="btn btn-primary" @click="uploadCorrection" :disabled="!selectedFile && !correctionText.trim()" style="width:100%">
                {{ uploading ? '提交中...' : '提交修改' }}
            </button>
            <button v-if="essay.status === 'confirming'" class="btn btn-success" @click="confirmEssay" style="width:100%;margin-top:8px">
              ✅ 确认修改
            </button>
            <button v-if="essay.status === 'confirming'" class="btn" @click="reworkEssay" style="width:100%;margin-top:8px;color:#fa8c16">
              🔄 重改（不达标需重新改正）
            </button>
          </template>
          <template v-else>
            <div class="card-header"><h3>✅ 已修改</h3></div>
            <p style="color:#52c41a">修改完成于 {{ essay.corrected_at?.substring(0,16) }}</p>
            <div class="form-group" style="margin-top:8px">
              <label>批改者备注</label>
              <div v-if="!editingNote && essay.reviewer_note" class="note-readonly">{{ essay.reviewer_note }}</div>
              <template v-else>
                <textarea v-model="editCorrectionNote" rows="2" :placeholder="essay.reviewer_note ? '批改者备注（可修改）...' : '批改者备注...'"></textarea>
                <button class="btn" style="margin-top:6px" @click="saveCorrectionNote" :disabled="savingNote">💾 保存备注</button>
              </template>
              <button v-if="!editingNote && essay.reviewer_note" class="btn" style="margin-top:6px" @click="editingNote = true">✏️ 编辑备注</button>
            </div>
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
            <button v-if="(essay.content_file || essay.content_text) && !isGuest" class="btn" style="font-size:12px;padding:4px 10px" @click="downloadOriginal">📥 下载原文</button>
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
                  <button v-if="(essay.content_file || essay.content_text) && !isGuest" class="btn-mini" @click="downloadOriginal">📥 下载原文</button>
                  <button class="btn-mini" @click="toggleReuploadOriginal" v-if="canEdit">📤 重新上传</button>
                  <button class="btn-mini" @click="doOcr" :disabled="ocrLoading" v-if="essay.file_type === 'image' && canEdit">
                    {{ ocrLoading ? '⏳ OCR中...' : '🔍 OCR识别' }}
                  </button>
                  <button class="btn-mini" @click="doAiCorrect" :disabled="aiLoading" v-if="essay.content_text && canEdit">
                    {{ aiLoading ? '⏳ AI修正中...' : '🤖 AI错别字修正' }}
                  </button>
                </div>
                <div style="display:flex;gap:4px">
                  <button class="btn-mini" @click="toggleEditOriginal" v-if="essay.content_text && canEdit">{{ editingOriginal ? '✕ 取消' : '✏️ 编辑' }}</button>
                  <button class="btn-mini" @click="toggleFullscreen('original')">{{ fullscreenMode === 'original' ? '⛶ 退出' : '⛶ 全屏' }}</button>
                </div>
              </div>
            <div class="pane-body">
              <div class="edit-wrapper">
                <div v-if="essay.content_text" class="content-text"
                  ref="originalContentRef"
                  :key="'orig-' + (editingOriginal ? 1 : 0)"
                  :contenteditable="editingOriginal"
                  :class="{ 'content-editing': editingOriginal }">
                  <p v-for="(para, i) in originalParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
                </div>
                <div v-else-if="essay.file_type !== 'image'" class="empty-state" style="padding:20px"><p>无文字内容</p></div>
                <div v-if="editingOriginal" class="edit-actions inline-actions">
                  <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" @click="saveOriginalEdit" :disabled="savingOriginalEdit">💾 保存</button>
                  <button class="btn" style="font-size:12px;padding:4px 12px" @click="cancelOriginalEdit">取消</button>
                </div>
                <div v-if="showWordCount" class="word-count">{{ countWords(essay.content_text) }} 字</div>
                <div v-if="essay.file_type === 'image' && images.length" class="image-gallery">
                  <img v-for="(img, i) in images" :key="i" :src="img" :class="['essay-image', { 'essay-image-selected': expandedImage === img }]" @click.stop="toggleExpandImage(img)" @dblclick="previewImage(img)" />
                </div>
                <img v-if="expandedImage" :src="expandedImage" class="expanded-image" @click="expandedImage = ''" />
              </div>
            </div>
            <!-- 重新上传面板（修改前） -->
            <div v-if="showReuploadOriginal" class="reupload-area">
              <div class="form-group">
                <label>上传文件（docx/图片，可多选，支持拖拽）</label>
                <div class="drop-zone" @dragover.prevent @dragenter.prevent @drop.prevent="onDropFiles">
                  <div v-if="desktopFileList.length === 0" class="drop-hint">拖拽文件到此处，或点击下方按钮选择</div>
                  <div class="upload-preview">
                    <div v-for="(item, i) in desktopFileList" :key="i" class="upload-preview-item">
                      <img v-if="previewable(item)" :src="item.url" class="upload-thumb" @click="previewDesktopImage(item)" />
                      <div v-else class="upload-file-icon">📄</div>
                      <span class="upload-name">{{ item.name }}</span>
                      <button class="upload-remove" @click="removeDesktopFile(i)">✕</button>
                    </div>
                  </div>
                  <label class="btn" style="cursor:pointer;display:inline-flex;margin-top:8px">
                    选择文件
                    <input type="file" multiple accept=".docx,.doc,.jpg,.jpeg,.png" style="display:none" @change="onDesktopFiles" />
                  </label>
                </div>
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
                <button class="btn-mini" @click="toggleReuploadCorrected" v-if="canReview">📤 重新上传</button>
                <button class="btn-mini" @click="doAiRewrite" :disabled="aiRewriteLoading" v-if="essay.content_text && canReview">
                  {{ aiRewriteLoading ? '⏳ AI改写中...' : '🤖 一键修改' }}
                </button>
              </div>
              <div style="display:flex;gap:4px">
                <button class="btn-mini" @click="toggleEditCorrected" v-if="essay.corrected_text && canReview">{{ editingCorrected ? '✕ 取消' : '✏️ 编辑' }}</button>
                <button class="btn-mini" @click="toggleFullscreen('corrected')">{{ fullscreenMode === 'corrected' ? '⛶ 退出' : '⛶ 全屏' }}</button>
              </div>
            </div>
            <div class="pane-body">
              <div class="edit-wrapper">
                <div v-if="essay.corrected_text" class="content-text corrected-content"
                  ref="correctedContentRef"
                  :key="'corr-' + (editingCorrected ? 1 : 0)"
                  :contenteditable="editingCorrected"
                  :class="{ 'content-editing': editingCorrected }">
                  <p v-for="(para, i) in correctedParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
                </div>
                <div v-else class="empty-state" style="padding:20px"><p>暂无修改内容</p></div>
                <div v-if="editingCorrected" class="edit-actions inline-actions">
                  <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" @click="saveCorrectedEdit" :disabled="savingCorrectedEdit">💾 保存</button>
                  <button class="btn" style="font-size:12px;padding:4px 12px" @click="cancelCorrectedEdit">取消</button>
                </div>
                <div v-if="showWordCount" class="word-count">{{ countWords(essay.corrected_text) }} 字</div>
              </div>
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
              <button v-if="essay.status === 'confirming'" class="btn btn-success" @click="confirmEssay" style="margin-top:8px;width:100%">
                ✅ 确认修改
              </button>
              <button v-if="essay.status === 'confirming'" class="btn" @click="reworkEssay" style="margin-top:8px;width:100%;color:#fa8c16">
                🔄 重改（不达标需重新改正）
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 手机端 ===== -->
      <template v-else>
        <div style="padding-top:10px">
          <div class="mobile-status">
            <span class="tag" :class="'tag-' + essay.status">{{ statusLabel(essay.status) }}</span>
            <span style="font-size:12px;color:#999">{{ statusHint }}</span>
          </div>

          <!-- 修改前 -->
          <van-cell-group style="margin-top:12px">
            <van-cell title="✏️ 修改前">
              <template #right-icon>
                <van-button v-if="essay.content_text && canEdit" size="mini" @click="toggleEditOriginal" style="margin-right:6px">{{ editingOriginal ? '✕ 取消' : '✏️ 编辑' }}</van-button>
                <van-button v-if="essay.file_type === 'image' && canEdit" size="mini" :loading="ocrLoading" @click="doOcr" style="margin-right:6px">🔍 OCR</van-button>
                <van-button v-if="essay.content_text && canEdit" size="mini" :loading="aiLoading" @click="doAiCorrect">🤖 修正</van-button>
              </template>
            </van-cell>
            <div v-if="essay.file_type === 'image' && images.length" class="image-gallery">
              <img v-for="(img, i) in images" :key="i" :src="img" :class="['essay-image', { 'essay-image-selected': expandedImage === img }]" @click.stop="toggleExpandImage(img)" @dblclick="previewImage(img)" />
            </div>
            <div v-if="essay.content_text" class="content-text"
              ref="originalContentRef"
              :key="'orig-' + (editingOriginal ? 1 : 0)"
              :contenteditable="editingOriginal"
              :class="{ 'content-editing': editingOriginal }">
              <p v-for="(para, i) in originalParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
            </div>
            <div v-else-if="essay.file_type !== 'image'" class="empty-state" style="padding:20px"><p>无文字内容</p></div>
            <img v-if="expandedImage" :src="expandedImage" class="expanded-image" @click="expandedImage = ''" />
            <div v-if="editingOriginal" class="mobile-edit-actions">
              <van-button size="small" type="primary" @click="saveOriginalEdit" :loading="savingOriginalEdit">💾 保存</van-button>
              <van-button size="small" @click="cancelOriginalEdit">取消</van-button>
            </div>
            <div v-if="essay.content_text && !editingOriginal" class="mobile-word-count">共 {{ countWords(essay.content_text) }} 字</div>
          </van-cell-group>

          <!-- 修改后 -->
          <van-cell-group style="margin-top:12px">
            <van-cell title="✅ 修改后">
              <template #right-icon>
                <van-button v-if="essay.content_text && canReview" size="mini" :loading="aiRewriteLoading" @click="doAiRewrite">🤖 一键修改</van-button>
              </template>
            </van-cell>
            <div v-if="essay.corrected_text" class="content-text corrected-content">
              <p v-for="(para, i) in correctedParagraphs" :key="i" :class="{ 'para-center-bold': i < 2 }">{{ para }}</p>
            </div>
            <div v-else class="empty-state" style="padding:20px"><p>暂无修改内容</p></div>
            <div v-if="essay.corrected_text" class="mobile-word-count">共 {{ countWords(essay.corrected_text) }} 字</div>
          </van-cell-group>

          <!-- 下载 -->
          <div style="margin:16px 0">
            <van-button v-if="(essay.content_file || essay.content_text) && !isGuest" round block type="primary" @click="downloadOriginal" style="margin-bottom:8px">📥 下载原文</van-button>
            <van-button v-if="!isGuest" round block @click="exportDocx" style="margin-bottom:8px">📥 导出修改前后docx</van-button>
            <van-button v-if="essay.has_correction" round block type="success" @click="downloadCorrection">📥 下载修改结果</van-button>
          </div>

          <!-- 基本信息 -->
          <van-cell-group>
            <van-cell title="📝 基本信息" />
            <van-field v-model="editForm.student_name" label="学生姓名" :disabled="!canEdit" />
            <van-field v-model="editForm.grade" label="年级" placeholder="选择" @click="canEdit && (showMobileGrade = true)" is-link readonly :disabled="!canEdit" />
            <van-field v-model.number="editForm.essay_number" label="第几次" type="digit" :disabled="!canEdit" />
            <van-field v-model="editForm.essay_title" label="作文标题" :disabled="!canEdit" />
            <van-field :model-value="selectedTaskName" label="任务" placeholder="选择" @click="canEdit && (showMobileTask = true)" is-link readonly />
            <van-field :model-value="essay.course_name || '-'" label="课程" readonly />
            <van-field v-model="editForm.collector_note" label="收集者备注" type="textarea" rows="2" :disabled="!canEdit" />
            <van-field v-if="editForm.reviewer_note" v-model="editForm.reviewer_note" label="批改者备注" type="textarea" rows="2" disabled />
            <van-field label="是否补交">
              <template #input>
                <van-radio-group v-model="editForm.is_supplement" :disabled="!canEdit" direction="horizontal">
                  <van-radio :name="false">否</van-radio>
                  <van-radio :name="true">是</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-cell title="收集者" :value="essay.collector_name" />
            <van-cell title="修改前/后字数" :value="`${essay.word_count || 0} / ${essay.corrected_word_count || 0}`" />
            <van-cell title="上传时间" :value="formatDateTime(essay.created_at)" />
            <van-cell title="修改时间" :value="essay.corrected_at ? formatDateTime(essay.corrected_at) : '未修改'" />
          </van-cell-group>

          <div style="margin:16px 0">
            <van-button round block @click="saveEdit" :loading="savingEdit" :disabled="!canEdit">💾 保存修改</van-button>
            <van-button v-if="canEdit" round block plain style="margin-top:8px" @click="showReupload = !showReupload">📤 重新上传</van-button>
          </div>

          <div v-if="showReupload" style="margin:0 0 16px;padding:16px;background:#fff;border-radius:8px">
            <van-field name="uploader" label="上传文件（可多选）">
              <template #input>
                <van-uploader v-model="reuploadFileList" :max-count="10" accept=".docx,.doc,.txt,.jpg,.jpeg,.png" multiple :before-read="beforeReuploadRead" />
              </template>
            </van-field>
            <van-field v-model="reuploadText" label="或粘贴文字" type="textarea" rows="3" placeholder="粘贴文字..." />
            <van-button round block type="primary" @click="doReupload" :loading="reuploading" style="margin-top:8px">确认上传</van-button>
          </div>

          <!-- 批改 -->
          <van-cell-group v-if="canReview && essay.status !== 'corrected'" style="margin-top:12px">
            <van-cell title="✅ 批改" />
            <van-field v-model="correctionFile" is-link readonly label="上传修改结果" placeholder="选择修改后的 docx 文件" @click="selectFile" />
            <van-field v-model="correctionText" label="文字修改" type="textarea" rows="3" placeholder="输入修改文字..." />
            <van-field v-model="correctionNote" label="批改者备注" type="textarea" rows="2" placeholder="批改者自定义备注（可选）..." />
            <div style="margin:16px">
              <van-button round block type="primary" @click="uploadCorrection" :loading="uploading">提交修改</van-button>
              <van-button v-if="essay.status === 'confirming'" round block type="success" style="margin-top:8px" @click="confirmEssay">✅ 确认修改</van-button>
              <van-button v-if="essay.status === 'confirming'" round block plain type="warning" style="margin-top:8px" @click="reworkEssay">🔄 重改</van-button>
            </div>
          </van-cell-group>
        </div>

        <van-action-sheet v-model:show="showMobileGrade" title="选择年级">
          <div class="picker-list">
            <van-cell v-for="g in grades" :key="g" :title="g" @click="editForm.grade = g; showMobileGrade = false" />
          </div>
        </van-action-sheet>

        <van-action-sheet v-model:show="showMobileTask" title="选择任务">
          <div style="padding:8px 16px">
            <input v-model="detailTaskSearch" placeholder="搜索任务..." style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;box-sizing:border-box" @input="showDetailTaskDropdown = true" />
          </div>
          <div class="picker-list" style="max-height:300px;overflow-y:auto">
            <van-cell title="无任务" @click="editForm.task_id = 0; detailTaskSearch = ''; showMobileTask = false" />
            <van-cell v-for="t in filteredDetailTasks" :key="t.id" :title="t.name" @click="editForm.task_id = t.id; detailTaskSearch = t.name; showMobileTask = false" />
            <van-cell v-if="!filteredDetailTasks.length && detailTaskSearch" title="无匹配任务" />
          </div>
        </van-action-sheet>

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
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRoute, onBeforeRouteLeave } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { useScreen } from '../composables/useScreen'
import api, { useAuth, getBaseUrl } from '../api'
import { formatDateTime, countWords } from '../utils/format'
import { compressImageFile } from '../utils/imageCompress'

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
const correctionNote = ref('')
const editCorrectionNote = ref('')
const savingNote = ref(false)
const editingNote = ref(false)
const selectedFile = ref(null)
const uploading = ref(false)
const fileInput = ref(null)
const images = ref([])
const expandedImage = ref('')
const showPreview = ref(false)
const previewIndex = ref(0)
const previewImages = ref([])
const savingEdit = ref(false)
const showMobileGrade = ref(false)
const showMobileTask = ref(false)
const mobileTab = ref(0)
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
const taskList = ref([])
const detailTaskSearch = ref('')
const showDetailTaskDropdown = ref(false)
const detailTaskFilterRef = ref(null)

function closeDetailTaskDropdown(e) {
  if (detailTaskFilterRef.value && !detailTaskFilterRef.value.contains(e.target)) {
    showDetailTaskDropdown.value = false
  }
}
const filteredDetailTasks = computed(() => {
  if (!detailTaskSearch.value) return taskList.value
  const kw = detailTaskSearch.value
  const segments = kw.match(/[\u4e00-\u9fff]+|\d+/g)
  if (!segments || segments.length === 0) return taskList.value.filter(t => t.name.toLowerCase().includes(kw.toLowerCase()))
  const pattern = segments.map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('.*')
  const regex = new RegExp(pattern, 'i')
  return taskList.value.filter(t => regex.test(t.name))
})
const selectedTaskName = computed(() => {
  if (!editForm.value.task_id) return '无任务'
  const t = taskList.value.find(x => x.id === editForm.value.task_id)
  return t ? t.name : '无任务'
})
const desktopFileList = ref([])
const fullscreenMode = ref(null) // 'original' | 'corrected' | 'both' | null
const showWordCount = ref(true)
const ocrLoading = ref(false)
const aiLoading = ref(false)
const editingOriginal = ref(false)
const originalContentRef = ref(null)
const savingOriginalEdit = ref(false)
const editingCorrected = ref(false)
const correctedContentRef = ref(null)
const savingCorrectedEdit = ref(false)
const aiRewriteLoading = ref(false)

const originalParagraphs = computed(() => {
  return (essay.value?.content_text || '').split('\n').filter(s => s.trim())
})
const correctedParagraphs = computed(() => {
  return (essay.value?.corrected_text || '').split('\n').filter(s => s.trim())
})

function statusLabel(s) { return { pending: '未修改', confirming: '待确认', rework: '待重改', corrected: '已修改' }[s] || s }

const statusHint = computed(() => {
  return { pending: '未修改，等待批改者处理', confirming: '已批改，等待确认', rework: '批改不达标，需重新批改', corrected: '已修改完成' }[essay.value?.status] || ''
})

const flowState = computed(() => {
  const s = essay.value?.status
  if (s === 'confirming') return { done: 2, active: 2 }
  if (s === 'rework') return { done: 1, active: 1 }
  if (s === 'corrected') return { done: 3, active: -1 }
  return { done: 1, active: 1 }
})

// ===== 未保存修改保护 =====
const isDirty = computed(() => {
  if (!essay.value) return false
  const f = editForm.value
  const e = essay.value
  return f.student_name !== e.student_name
    || f.grade !== (e.grade || '')
    || f.essay_number !== e.essay_number
    || f.essay_title !== (e.essay_title || '')
    || f.collector_note !== (e.collector_note || '')
    || f.teaching_mode !== (e.teaching_mode || '线下')
    || f.is_supplement !== (e.is_supplement || false)
    || f.collected_by !== e.collected_by
    || f.task_id !== (e.task_id || 0)
    || editingOriginal.value
    || editingCorrected.value
    || desktopFileList.value.length > 0
    || reuploadText.value.trim() !== ''
})

function onBeforeUnload(e) {
  if (isDirty.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onBeforeRouteLeave(async () => {
  if (!isDirty.value) return true
  const ok = await showConfirmDialog({
    title: '提示',
    message: '有未保存的修改，确定要离开吗？',
    confirmButtonText: '放弃修改',
    cancelButtonText: '留下编辑',
    showCancelButton: true,
  }).catch(() => false)
  return !!ok
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

async function beforeReuploadRead(file) {
  if (Array.isArray(file)) {
    const compressed = await Promise.all(file.map(f => compressImageFile(f)))
    return compressed
  }
  return compressImageFile(file)
}

async function onDesktopFiles(e) {
  const files = Array.from(e.target.files)
  for (const f of files) {
    const out = await compressImageFile(f)
    const url = URL.createObjectURL(out)
    desktopFileList.value.push({ file: out, name: out.name, type: out.type, url })
  }
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

async function onDropFiles(e) {
  const files = Array.from(e.dataTransfer.files)
  for (const f of files) {
    const out = await compressImageFile(f)
    const url = URL.createObjectURL(out)
    desktopFileList.value.push({ file: out, name: out.name, type: out.type, url })
  }
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
    fd.append('grade', editForm.value.grade || essay.value.grade || '')
    fd.append('essay_number', String(editForm.value.essay_number || essay.value.essay_number || 1))
    fd.append('essay_title', editForm.value.essay_title || essay.value.essay_title || '')
    fd.append('student_name', editForm.value.student_name || essay.value.student_name)
    fd.append('is_supplement', essay.value.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', editForm.value.teaching_mode || essay.value.teaching_mode || '线下')
    fd.append('collector_note', editForm.value.collector_note || essay.value.collector_note || '')
    desktopFileList.value.forEach(item => fd.append('files', item.file))
    if (reuploadText.value.trim()) {
      fd.append('content_text', reuploadText.value)
    }
    await api.post('/essays/upload', fd, { timeout: 120000 })
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

async function doOcr() {
  ocrLoading.value = true
  try {
    const res = await api.post(`/essays/${route.params.id}/ocr`)
    showToast(`OCR 完成，识别到 ${res.data.word_count} 字`)
    await loadEssay()
  } catch(err) {
    showToast(err.response?.data?.detail || 'OCR 识别失败')
  } finally {
    ocrLoading.value = false
  }
}

async function doAiCorrect() {
  aiLoading.value = true
  try {
    const res = await api.post(`/essays/${route.params.id}/ai-correct`, null, { timeout: 120000 })
    showToast(`AI 修正完成（当前 ${countWords(res.data.content_text)} 字）`)
    await loadEssay()
  } catch(err) {
    showToast(err.response?.data?.detail || 'AI 修正失败')
  } finally {
    aiLoading.value = false
  }
}

function toggleEditOriginal() {
  if (editingOriginal.value) {
    cancelOriginalEdit()
  } else {
    editingOriginal.value = true
    nextTick(() => originalContentRef.value?.focus())
  }
}

function cancelOriginalEdit() {
  editingOriginal.value = false
}

async function saveOriginalEdit() {
  if (!canEdit.value) {
    showToast('无权修改')
    return
  }
  savingOriginalEdit.value = true
  try {
    const text = (originalContentRef.value?.innerText || '').replace(/\n+$/, '')
    await api.put(`/essays/${route.params.id}`, null, { params: { content_text: text } })
    showToast('保存成功')
    editingOriginal.value = false
    await loadEssay()
  } catch(err) {
    showToast(err.response?.data?.detail || '保存失败')
  } finally {
    savingOriginalEdit.value = false
  }
}

function toggleEditCorrected() {
  if (editingCorrected.value) {
    cancelCorrectedEdit()
  } else {
    editingCorrected.value = true
    nextTick(() => correctedContentRef.value?.focus())
  }
}

function cancelCorrectedEdit() {
  editingCorrected.value = false
}

async function doAiRewrite() {
  aiRewriteLoading.value = true
  try {
    const res = await api.post(`/essays/${route.params.id}/ai-rewrite`, null, { timeout: 180000 })
    console.log('AI 改写返回:', res.data)
    const msg = res.data.char_count ? `AI 改写完成（${res.data.char_count}字）` : 'AI 改写完成'
    showToast(msg)
    await loadEssay()
  } catch(err) {
    console.error('AI 改写失败:', err)
    const detail = err.response?.data?.detail || err.message || 'AI 改写失败'
    showToast(detail)
  } finally {
    aiRewriteLoading.value = false
  }
}

async function saveCorrectedEdit() {
  if (!canReview.value) {
    showToast('无权修改')
    return
  }
  savingCorrectedEdit.value = true
  try {
    const text = (correctedContentRef.value?.innerText || '').replace(/\n+$/, '')
    await api.put(`/essays/${route.params.id}`, null, { params: { corrected_text: text } })
    showToast('保存成功')
    editingCorrected.value = false
    await loadEssay()
  } catch(err) {
    showToast(err.response?.data?.detail || '保存失败')
  } finally {
    savingCorrectedEdit.value = false
  }
}

onMounted(async () => {
  await loadTasks()
  await loadEssay()
  if (isAdmin.value) {
    await loadCollectors()
  }
  // 点击外部关闭任务下拉框
  document.addEventListener('click', closeDetailTaskDropdown)
  window.addEventListener('beforeunload', onBeforeUnload)
})
onUnmounted(() => {
  document.removeEventListener('click', closeDetailTaskDropdown)
  window.removeEventListener('beforeunload', onBeforeUnload)
})

async function loadEssay() {
  try {
    const res = await api.get(`/essays/${route.params.id}`)
    essay.value = res.data
    loading.value = false
    const t = essay.value.essay_title || '无标题'
    document.title = essay.value.student_name + '《' + t + '》'
    editCorrectionNote.value = essay.value.reviewer_note || ''
    editingNote.value = false
    editForm.value = {
      student_name: essay.value.student_name,
      grade: essay.value.grade,
      essay_title: essay.value.essay_title,
      essay_number: essay.value.essay_number,
      teaching_mode: essay.value.teaching_mode || '线下',
      collector_note: essay.value.collector_note || '',
      reviewer_note: essay.value.reviewer_note || '',
      collected_by: essay.value.collected_by,
      is_supplement: essay.value.is_supplement || false,
      task_id: essay.value.task_id || 0,
    }
    // 初始化任务搜索框文字
    if (essay.value.task_id && taskList.value.length) {
      const t = taskList.value.find(x => x.id === essay.value.task_id)
      if (t) detailTaskSearch.value = t.name
    }
    if (essay.value.file_type === 'image') {
      const imgRes = await api.get(`/essays/${route.params.id}/images`)
      const baseUrl = getBaseUrl().replace(/\/api\/?$/, '')
      const origin = baseUrl.startsWith('http') ? baseUrl : window.location.origin
      const t = Date.now()
      images.value = imgRes.data.images.map(u => origin + u + '?t=' + t)
    }
  } catch {
    showToast('加载失败')
    loading.value = false
  }
}

async function loadCollectors() {
  try {
    const res = await api.get('/essays/collectors')
    collectorList.value = res.data || []
  } catch {}
}

async function loadTasks() {
  try {
    const res = await api.get('/essays/tasks')
    taskList.value = res.data
  } catch {}
}

function toggleExpandImage(url) {
  expandedImage.value = expandedImage.value === url ? '' : url
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
    const disposition = res.headers['content-disposition']
    let filename = '作文.docx'
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
    fd.append('reviewer_note', correctionNote.value || '')
    await api.post(`/essays/${route.params.id}/upload-correction`, fd)
    showToast('修改提交成功')
    await loadEssay()
    selectedFile.value = null; correctionFile.value = ''
    correctionText.value = ''
    correctionNote.value = ''
    showReuploadCorrected.value = false
  } catch (err) { showToast(err.response?.data?.detail || '上传失败') }
  finally { uploading.value = false }
}

async function confirmEssay() {
  try {
    await api.post(`/essays/${route.params.id}/confirm`)
    showToast('已确认修改')
    mobileTab.value = 0
    await loadEssay()
  } catch (err) { showToast(err.response?.data?.detail || '确认失败') }
}

async function reworkEssay() {
  try {
    await api.post(`/essays/${route.params.id}/rework`)
    showToast('已标记为待重改')
    mobileTab.value = 0
    await loadEssay()
  } catch (err) { showToast(err.response?.data?.detail || '标记重改失败') }
}

async function saveCorrectionNote() {
  savingNote.value = true
  try {
    const res = await api.put(`/essays/${route.params.id}`, null, { params: { reviewer_note: editCorrectionNote.value } })
    essay.value = { ...essay.value, ...res.data }
    editingNote.value = false
    showToast('备注已保存')
  } catch (err) { showToast(err.response?.data?.detail || '保存失败') }
  finally { savingNote.value = false }
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
    // 同步 editForm 全部字段
    Object.assign(editForm.value, {
      student_name: res.data.student_name,
      grade: res.data.grade,
      essay_title: res.data.essay_title,
      essay_number: res.data.essay_number,
      teaching_mode: res.data.teaching_mode || '线下',
      collector_note: res.data.collector_note || '',
      reviewer_note: res.data.reviewer_note || '',
      collected_by: res.data.collected_by,
      is_supplement: res.data.is_supplement || false,
      task_id: res.data.task_id || 0,
    })
    // 同步任务搜索框文字
    if (res.data.task_id && taskList.value.length) {
      const t = taskList.value.find(x => x.id === res.data.task_id)
      if (t) detailTaskSearch.value = t.name
    } else {
      detailTaskSearch.value = ''
    }
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
    fd.append('grade', editForm.value.grade || essay.value.grade || '')
    fd.append('essay_number', String(editForm.value.essay_number || essay.value.essay_number || 1))
    fd.append('essay_title', editForm.value.essay_title || essay.value.essay_title || '')
    fd.append('student_name', editForm.value.student_name || essay.value.student_name)
    fd.append('is_supplement', essay.value.is_supplement ? 'true' : 'false')
    fd.append('teaching_mode', editForm.value.teaching_mode || essay.value.teaching_mode || '线下')
    fd.append('collector_note', editForm.value.collector_note || essay.value.collector_note || '')
    for (const f of files) {
      fd.append('files', f)
    }
    if (reuploadText.value.trim()) {
      fd.append('content_text', reuploadText.value)
    }
    await api.post('/essays/upload', fd, { timeout: 120000 })
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
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  font-size: 13px;
  color: #666;
}
.breadcrumb-link {
  color: #1677ff;
  text-decoration: none;
  cursor: pointer;
}
.breadcrumb-link:hover { text-decoration: underline; }
.breadcrumb-sep { color: #d9d9d9; }
.breadcrumb-current { color: #333; }
.content-text { padding: 12px 16px; }

.content-text[contenteditable="true"] {
  outline: 2px dashed #1677ff;
  outline-offset: 3px;
  border-radius: 6px;
  min-height: 60px;
  cursor: text;
  background: #fffef5;
}
.content-text[contenteditable="true"]:focus { outline-style: solid; }
.inline-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
.note-readonly {
  white-space: pre-wrap;
  word-break: break-word;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}
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

.info-section { margin-bottom: 14px; }
.info-section:last-child { margin-bottom: 0; }
.info-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #999;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed #f0f0f0;
}
.info-static {
  font-size: 14px;
  color: #333;
  line-height: 30px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag { display: inline-block; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: 500; white-space: nowrap; }
.tag-pending { background: #fff7e6; color: #d46b08; }
.tag-confirming { background: #e6f4ff; color: #1677ff; }
.tag-rework { background: #fff1f0; color: #ff4d4f; }
.tag-corrected { background: #f6ffed; color: #52c41a; }

/* ===== 状态流转条 ===== */
.status-strip {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border-left: 4px solid #1677ff;
  flex-wrap: wrap;
}
.strip-pending { border-left-color: #d46b08; }
.strip-confirming { border-left-color: #1677ff; }
.strip-rework { border-left-color: #ff4d4f; }
.strip-corrected { border-left-color: #52c41a; }
.strip-hint { font-size: 13px; color: #666; }
.flow-bar { display: flex; align-items: center; gap: 6px; margin-left: auto; font-size: 12px; color: #999; }
.flow-item { padding: 2px 10px; border-radius: 10px; background: #f5f5f5; }
.flow-item.done { background: #f6ffed; color: #52c41a; }
.flow-item.active { background: #1677ff; color: #fff; }
.flow-arrow { color: #d9d9d9; }

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

.task-dropdown-detail {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  max-height: 200px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-top: 4px;
}
.task-dropdown-detail .task-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  border-bottom: 1px solid #f5f5f5;
}
.task-dropdown-detail .task-item:hover { background: #f0f0f0; }
.task-dropdown-detail .task-item-active { background: #e6f4ff; color: #1677ff; }

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
.essay-image-selected { border-color: #1677ff; box-shadow: 0 0 0 2px rgba(22,119,255,0.3); }

.expanded-image {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 8px;
  margin-bottom: 8px;
}

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

.mobile-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px;
  font-size: 12px;
}
.mobile-word-count {
  padding: 8px 16px;
  font-size: 12px;
  color: #999;
  text-align: right;
  border-top: 1px dashed #f0f0f0;
}
.mobile-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px dashed #f0f0f0;
}

.edit-wrapper { position: relative; }
.edit-actions { display: flex; gap: 8px; margin-top: 8px; }

.drop-zone {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  background: #fafafa;
  transition: border-color 0.2s, background 0.2s;
  cursor: default;
}
.drop-zone:hover { border-color: #4096ff; background: #f0f5ff; }
.drop-hint { color: #999; font-size: 13px; padding: 12px 0; }
.drop-zone .upload-preview { margin-top: 0; }

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
