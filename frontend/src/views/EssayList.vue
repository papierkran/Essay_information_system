<template>
  <div class="page">
    <div class="page-title">
      作文列表
      <span v-if="!isAdmin && filters.collectedBy === defaultCollectedBy" class="title-hint">⚠️ 首次进入默认筛选收集者为当前用户，如需查看其他作文，请点击「重置」或手动将收集者调整为「全部」</span>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-row"><span class="filter-label">学生姓名</span><input v-model="filters.name" placeholder="搜索姓名" class="filter-input" @keyup.enter="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">作文标题</span><input v-model="filters.essayTitle" placeholder="搜索标题" class="filter-input" @keyup.enter="applyFilter" /></div>
      <div class="filter-row"><span class="filter-label">作文内容</span><input v-model="filters.content" placeholder="搜索正文，多个关键词用空格分隔" class="filter-input" style="min-width:160px" @keyup.enter="applyFilter" /></div>
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
          <option value="rework">待重改</option>
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
      <div class="filter-row">
        <span class="filter-label">任务</span>
        <button class="filter-input task-select-btn" @click="taskPickerMode = 'filter'; showTaskPicker = true" :style="{ width: '160px', textAlign: 'left', cursor: 'pointer', color: filterTaskSearch ? '#333' : '#999' }">
          {{ filterTaskSearch || '搜索任务' }}
        </button>
      </div>
      <div class="filter-row"><span class="filter-label">课程</span>
        <select v-model="filters.courseId" class="filter-input" @change="applyFilter">
          <option value="">全部</option>
          <option v-for="c in courseList" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
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
      <div class="filter-row"><span class="filter-label">收集者备注</span><input v-model="filters.remark" placeholder="搜索收集者备注" class="filter-input" @keyup.enter="applyFilter" /></div>
      <button class="btn btn-primary" style="font-size:13px;padding:6px 14px" @click="applyFilter">查询</button>
      <button class="btn" style="font-size:13px;padding:6px 14px" @click="clearFilter">重置</button>
      <button v-if="!isGuest" class="btn" style="font-size:13px;padding:6px 14px" @click="exportXlsx" :title="`导出当前页 ${list.length} 条`">📥 导出Excel(当前页)</button>
      <button v-if="!isGuest" class="btn" style="font-size:13px;padding:6px 14px" :disabled="!selectedIds.length" @click="exportXlsxSelected">📤 导出已选xlsx{{ selectedIds.length ? `（${selectedIds.length}）` : '' }}</button>
    </div>

    <!-- 统计行 -->
    <div class="stats-bar">
      <span>共 <strong>{{ total }}</strong> 条</span>
      <span class="stat-pending">未改 <strong>{{ pendingTotal }}</strong></span>
      <span class="stat-corrected">已修改 <strong>{{ correctedTotal }}</strong></span>
      <template v-if="!isGuest && isDesktop">
        <span style="color:#d9d9d9">|</span>
        <span style="font-size:13px;color:#666">已选 {{ selectedIds.length }} 条<span v-if="selectedIds.length > list.length" style="color:#999">（含其他页/筛选）</span></span>
        <button class="btn btn-primary" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="showBatchOps = true">批量操作</button>
        <button class="btn" style="font-size:12px;padding:4px 12px" :disabled="!selectedIds.length" @click="clearSelection">取消选择</button>
      </template>
      <span v-if="isDesktop" style="margin-left:auto;display:flex;align-items:center;gap:4px;font-size:13px;color:#666">
        <button class="btn btn-primary" style="font-size:12px;padding:4px 10px" :disabled="!selectedIds.length" @click="batchExportDocx">📥 批量导出docx</button>
        <button class="btn" style="font-size:12px;padding:4px 10px" @click="showDocxSettings = true">📄 导出docx设置</button>
        <button class="btn" style="font-size:12px;padding:4px 10px" @click="showColumnSettings = true">⚙️ 列设置</button>
        每页
        <select v-model.number="pageSize" @change="applyFilter" style="padding:4px 8px;border:1px solid #d9d9d9;border-radius:4px;font-size:13px">
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
          <option :value="500">500</option>
          <option :value="1000">1000</option>
          <option :value="2000">2000</option>
        </select>
        条
      </span>
    </div>

    <!-- 手机端批量工具栏 -->
    <div v-if="!isGuest && !isDesktop" class="mobile-batch-bar">
      <label class="m-sel-all"><input type="checkbox" :checked="allSelected" @change="toggleAll" style="width:auto" /> 全选本页</label>
      <span class="m-sel-count">已选 {{ selectedIds.length }} 条</span>
      <button class="btn" style="font-size:12px;padding:3px 8px" :disabled="!selectedIds.length" @click="showBatchOps = true">批量操作</button>
      <button class="btn" style="font-size:12px;padding:3px 8px" :disabled="!selectedIds.length" @click="clearSelection">取消</button>
    </div>

    <div v-if="loading" style="padding:24px;text-align:center;color:#999">⏳ 加载中...</div>

    <!-- 桌面端：表格 -->
    <template v-if="isDesktop">
      <div ref="topScroll" class="scroll-sync" @scroll="syncScroll('top')">
        <div ref="topScrollContent" class="scroll-sync-content"></div>
      </div>
      <div ref="tableWrap" class="table-wrap" @scroll="syncScroll('bottom')">
        <table class="desktop-table" :class="{ 'table-dragging': tableDragging }" v-if="list.length">
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
              <th class="sticky-col">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in list" :key="e.id"
              :class="{ 'row-selected': isRowSelected(e.id), 'row-readonly': !isOwner(e) }"
              @click="onRowClick(e.id)"
              @mousedown="dragStart(e.id, $event)"
              @mouseenter="dragMove(e.id)"
              @mouseup="dragEnd">
              <td v-if="!isGuest" @click.stop><input type="checkbox" :checked="selectedIds.includes(e.id)" @change="toggleSelect(e.id)" style="width:auto" /></td>
              <template v-for="col in visibleColumns" :key="col.key">
                <td v-if="col.key === 'status'"><span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span></td>
                <td v-else-if="col.key === 'file_saved'"><span v-if="hasFile(e)" class="tag" :class="e.file_saved ? 'tag-corrected' : 'tag-pending'">{{ e.file_saved ? '已存' : '丢失' }}</span><span v-else>-</span></td>
                <td v-else-if="col.key === 'is_supplement'"><span :style="{ color: e.is_supplement ? '#fa8c16' : '#d9d9d9', fontSize: '16px' }">{{ e.is_supplement ? '🔄' : '' }}</span></td>
                <td v-else-if="col.key === 'grade'"><span class="badge-mini tag-grade">{{ e.grade || '-' }}</span></td>
                <td v-else-if="col.key === 'essay_number'"><span class="badge-mini tag-number">{{ e.essay_number ? '第' + e.essay_number + '次' : '-' }}</span></td>
                <td v-else-if="col.key === 'teaching_mode'"><span class="badge-mini" :class="e.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ e.teaching_mode || '-' }}</span></td>
                <td v-else-if="col.key === 'word_count'">{{ e.word_count || 0 }}</td>
                <td v-else-if="col.key === 'corrected_word_count'">{{ e.corrected_word_count || 0 }}</td>
                <td v-else-if="col.key === 'created_at'">{{ formatDateTime(e.created_at) }}</td>
                <td v-else-if="col.key === 'corrected_at'">{{ formatDateTime(e.corrected_at) || '-' }}</td>
                <td v-else-if="col.key === 'collector_note' || col.key === 'reviewer_note'" class="td-note" :title="e[col.field] || ''">{{ e[col.field] || '-' }}</td>
              <td v-else-if="col.key === 'corrected_title'">{{ e.corrected_title || '-' }}</td>
              <td v-else>{{ e[col.field] || '-' }}</td>
              </template>
              <td class="sticky-col" style="white-space:nowrap" @click.stop>
                <template v-if="!isGuest && isOwner(e)">
                  <router-link :to="`/review/detail/${e.id}`" class="btn" style="font-size:12px;padding:4px 8px;text-decoration:none;color:#333">详情编辑</router-link>
                  <button v-if="e.status === 'corrected'" class="btn" style="font-size:12px;padding:4px 8px;color:#1677ff" @click.stop="exportSingleDocx(e)">导出docx</button>
                  <button class="btn" style="font-size:12px;padding:4px 8px;color:#ff4d4f" @click.stop="confirmDelete(e)">删除</button>
                </template>
                <template v-else>
                  <router-link v-if="canReview" :to="`/review/detail/${e.id}`" class="readonly-hint" style="text-decoration:none">
                    <span class="text-readonly">查看</span>
                  </router-link>
                  <router-link v-else :to="`/review/detail/${e.id}?readonly=1`" class="readonly-hint" style="text-decoration:none">
                    <span class="text-readonly">仅查看</span>
                  </router-link>
                  <button v-if="e.status === 'corrected' && !isGuest" class="btn" style="font-size:12px;padding:4px 8px;color:#1677ff;margin-left:4px" @click.stop="exportSingleDocx(e)">导出docx</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- 手机端：卡片列表 -->
    <template v-else>
      <div class="mobile-list" v-if="list.length">
        <div v-for="e in list" :key="e.id" class="mobile-card" :class="{ 'row-selected': selectedIds.includes(e.id) }">
          <div class="mobile-card-head" @click="goDetail(e)">
            <div class="mobile-card-name-wrap">
              <input v-if="!isGuest" type="checkbox" :checked="selectedIds.includes(e.id)" @click.stop @change="toggleSelect(e.id)" style="width:auto" />
              <span class="mobile-card-name">{{ e.student_name }}</span>
              <span v-if="e.is_supplement" style="color:#fa8c16;font-size:14px" title="补交">🔄</span>
            </div>
            <span class="tag" :class="'tag-' + e.status">{{ statusLabel(e.status) }}</span>
          </div>
          <div class="mobile-card-title" @click="goDetail(e)">{{ e.essay_title || '无标题' }}</div>
          <div class="mobile-card-title" style="color:#1677ff" @click="goDetail(e)">{{ e.corrected_title || '' }}</div>
          <div class="mobile-card-meta" @click="goDetail(e)">
            <span class="badge-mini tag-grade">{{ e.grade || '-' }}</span>
            <span class="badge-mini tag-number">{{ e.essay_number ? '第' + e.essay_number + '次' : '-' }}</span>
            <span class="badge-mini" :class="e.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ e.teaching_mode || '-' }}</span>
            <span>👤 {{ e.collector_name || '未知' }}</span>
            <span>{{ e.task_name || '无任务' }}</span>
          </div>
          <div class="mobile-card-foot">
            <span>{{ formatDateTime(e.created_at) }}</span>
            <div class="mobile-card-actions">
              <span v-if="hasFile(e) && e.file_saved === false" class="tag tag-pending">文件丢失</span>
              <router-link v-if="!isGuest && isOwner(e)" :to="`/review/detail/${e.id}`" class="btn" style="font-size:12px;padding:3px 10px;text-decoration:none;color:#333" @click.stop>详情</router-link>
              <router-link v-else-if="canReview" :to="`/review/detail/${e.id}`" class="btn" style="font-size:12px;padding:3px 10px;text-decoration:none;color:#1677ff" @click.stop>查看</router-link>
              <router-link v-else :to="`/review/detail/${e.id}?readonly=1`" class="btn" style="font-size:12px;padding:3px 10px;text-decoration:none;color:#1677ff" @click.stop>仅查看</router-link>
              <button v-if="e.status === 'corrected' && !isGuest" class="btn" style="font-size:12px;padding:3px 10px;color:#1677ff" @click.stop="exportSingleDocx(e)">导出docx</button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="!list.length && !loading" class="empty-state"><div class="icon">📭</div><p>没有符合条件的作文，请调整筛选条件</p></div>

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
        <div v-if="!deletingEssay && selectedIds.length" class="batch-preview">
          <div class="batch-preview-title">本次将删除：</div>
          <div class="batch-preview-body">{{ previewText() }}</div>
        </div>
        <van-checkbox v-model="deleteFileChecked" :disabled="!isAdmin">
          <span :style="{ color: isAdmin ? '#ff4d4f' : '#ccc' }">彻底删除（同时删除本地文件，不可恢复）</span>
        </van-checkbox>
        <p v-if="isAdmin && deleteFileChecked" style="color:#ff4d4f;font-size:12px;margin-top:8px">⚠️ 勾选后将彻底删除记录（不进回收站）且无法恢复！</p>
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

    <!-- 批量操作 -->
    <van-action-sheet v-model:show="showBatchOps" title="批量操作">
      <div class="batch-ops-list">
        <div class="batch-ops-item" @click="doBatchDelete">
          <span class="batch-ops-icon" style="color:#ff4d4f">🗑️</span>
          <span class="batch-ops-name">批量删除</span>
        </div>
        <div v-if="isAdmin" class="batch-ops-item" @click="showBatchCollector = true; showBatchOps = false">
          <span class="batch-ops-icon">👤</span>
          <span class="batch-ops-name">修改收集者</span>
        </div>
        <div v-if="isAdmin" class="batch-ops-item" @click="showBatchTask = true; showBatchOps = false">
          <span class="batch-ops-icon">📋</span>
          <span class="batch-ops-name">修改任务</span>
        </div>
        <div class="batch-ops-cancel" @click="showBatchOps = false">取消</div>
      </div>
    </van-action-sheet>

    <!-- 导出docx设置 -->
    <van-dialog v-model:show="showDocxSettings" title="导出docx设置" :show-cancel-button="false" :show-confirm-button="false" :close-on-click-overlay="true">
      <div style="padding:16px">
        <div class="settings-section">
          <div class="settings-section-title">文件名包含</div>
          <van-checkbox v-model="docxSettings.filenameTitle" shape="square" style="margin-bottom:8px">标题</van-checkbox>
          <van-checkbox v-model="docxSettings.filenameStudent" shape="square" style="margin-bottom:8px">学生姓名</van-checkbox>
          <van-checkbox v-model="docxSettings.filenameGrade" shape="square" style="margin-bottom:8px">年级</van-checkbox>
          <van-checkbox v-model="docxSettings.filenameNumber" shape="square" style="margin-bottom:8px">第几次</van-checkbox>
          <van-checkbox v-model="docxSettings.filenameMode" shape="square" style="margin-bottom:8px">提交方式</van-checkbox>
          <van-checkbox v-model="docxSettings.filenameSupplement" shape="square">补交标记</van-checkbox>
        </div>
        <div class="settings-section" style="margin-top:16px">
          <div class="settings-section-title">下载方式</div>
          <van-radio-group v-model="docxSettings.downloadMode" direction="vertical" style="margin-bottom:8px">
            <van-radio name="zip" shape="square" style="margin-bottom:6px">打成zip包（每个作文一个docx）</van-radio>
            <van-radio name="merged" shape="square" style="margin-bottom:6px">合并为一个docx</van-radio>
            <van-radio name="queue" shape="square">排队逐个下载</van-radio>
          </van-radio-group>
        </div>
        <div class="settings-section" style="margin-top:16px">
          <div class="settings-section-title">文档内容</div>
          <van-radio-group v-model="docxSettings.exportMode" direction="vertical" style="margin-bottom:8px">
            <van-radio name="both" shape="square" style="margin-bottom:6px">修改前后</van-radio>
            <van-radio name="corrected" shape="square" style="margin-bottom:6px">仅修改后</van-radio>
            <van-radio name="original" shape="square">仅修改前</van-radio>
          </van-radio-group>
          <van-checkbox v-model="docxSettings.includeStudentName" shape="square">包含学生姓名</van-checkbox>
        </div>
      </div>
      <template #footer>
        <div style="display:flex;gap:8px;justify-content:flex-end;padding:8px 16px">
          <button class="btn" @click="resetDocxSettings">恢复默认</button>
          <button class="btn btn-primary" @click="saveDocxSettings">确定</button>
        </div>
      </template>
    </van-dialog>

    <!-- 批量修改收集者 -->
    <van-dialog v-model:show="showBatchCollector" title="修改收集者" :show-cancel-button="true" @confirm="doBatchCollector">
      <div style="padding:16px">
        <p style="font-size:13px;color:#666;margin-bottom:8px">将 {{ selectedIds.length }} 条作文的收集者修改为：</p>
        <div class="batch-preview" style="margin-bottom:8px">
          <div class="batch-preview-title">涉及作文：</div>
          <div class="batch-preview-body">{{ previewText() }}</div>
        </div>
        <select v-model.number="batchCollectorId" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px">
          <option value="">请选择</option>
          <option v-for="c in collectorList" :key="c.id" :value="c.id">{{ c.nickname }}</option>
        </select>
      </div>
    </van-dialog>

    <!-- 批量修改任务 -->
    <van-dialog v-model:show="showBatchTask" title="修改任务" :show-cancel-button="true" @confirm="doBatchTask" @open="batchTaskId = ''; batchTaskSearch = ''">
      <div style="padding:16px">
        <p style="font-size:13px;color:#666;margin-bottom:8px">将 {{ selectedIds.length }} 条作文的任务修改为（必选）：</p>
        <div class="batch-preview" style="margin-bottom:8px">
          <div class="batch-preview-title">涉及作文：</div>
          <div class="batch-preview-body">{{ previewText() }}</div>
        </div>
        <button class="task-select-btn" style="width:100%;text-align:left" @click="openBatchTaskPicker">{{ batchTaskSearch || '请选择任务' }}</button>
      </div>
    </van-dialog>

    <!-- 任务选择器 -->
    <van-action-sheet v-model:show="showTaskPicker" title="选择任务筛选" class="task-picker-sheet"
      :style="{ maxHeight: '88vh', display: 'flex', flexDirection: 'column' }">
      <div class="picker-list">
        <div style="padding:8px 16px">
          <input v-model="pickerTaskSearch" placeholder="搜索任务名称/主题/年级..." style="width:100%;padding:8px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;outline:none" />
        </div>
        <div style="padding:0 16px 8px;display:flex;align-items:center;gap:6px;font-size:13px;color:#666">
          <van-checkbox v-model="showActiveOnly" icon-size="16px" shape="square">只看收集中</van-checkbox>
          <span style="color:#999;font-size:12px">（关闭可查看全部 {{ sortedTaskList.length }} 个任务）</span>
        </div>
        <div class="task-item-option" @click="selectTask(null)" :class="{ active: filters.taskId === '' || filters.taskId === null || filters.taskId === undefined }">
          <span style="font-weight:500">全部</span>
        </div>
        <div class="task-item-option" style="color:#999" @click="selectTask(0)" :class="{ active: filters.taskId === 0 }">
          <span>无任务</span>
        </div>
        <div class="task-split">
          <div class="task-col">
            <div class="task-col-title">线上</div>
            <template v-for="t in pagedOnlineTasks" :key="t.id">
              <div class="task-item-option" @click="selectTask(t)" :class="{ active: filters.taskId == t.id }">
                <div class="task-item-title">
                  <span style="font-weight:500">{{ t.name }}</span>
                  <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
                </div>
                <div class="task-item-meta">
                  <span class="badge-mini tag-grade">{{ t.grade }}</span>
                  <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                  <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                  <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
                  <span v-if="t.essay_topic" style="color:#999;font-size:12px">{{ t.essay_topic }}</span>
                </div>
              </div>
            </template>
            <div v-if="filteredOnlineTasks.length > PAGE_SIZE" class="pagination-row">
              <button class="btn" :disabled="pageOnline <= 1" @click="pageOnline--">上一页</button>
              <span class="page-info">{{ pageOnline }} / {{ onlineTotalPages }}</span>
              <button class="btn" :disabled="pageOnline >= onlineTotalPages" @click="pageOnline++">下一页</button>
            </div>
            <div v-if="!filteredOnlineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线上任务</div>
          </div>
          <div class="task-col">
            <div class="task-col-title">线下</div>
            <template v-for="t in pagedOfflineTasks" :key="t.id">
              <div class="task-item-option" @click="selectTask(t)" :class="{ active: filters.taskId == t.id }">
                <div class="task-item-title">
                  <span style="font-weight:500">{{ t.name }}</span>
                  <van-tag v-if="taskIsActive(t)" type="primary" style="margin-left:6px">收集中</van-tag>
                </div>
                <div class="task-item-meta">
                  <span class="badge-mini tag-grade">{{ t.grade }}</span>
                  <span class="badge-mini tag-number">第{{ t.essay_number }}次</span>
                  <span class="badge-mini" :class="t.teaching_mode === '线上' ? 'tag-mode-online' : 'tag-mode-offline'">{{ t.teaching_mode || '线下' }}</span>
                  <span v-if="t.course_name" class="badge-mini tag-course">{{ t.course_name }}</span>
                  <span v-if="t.essay_topic" style="color:#999;font-size:12px">{{ t.essay_topic }}</span>
                </div>
              </div>
            </template>
            <div v-if="filteredOfflineTasks.length > PAGE_SIZE" class="pagination-row">
              <button class="btn" :disabled="pageOffline <= 1" @click="pageOffline--">上一页</button>
              <span class="page-info">{{ pageOffline }} / {{ offlineTotalPages }}</span>
              <button class="btn" :disabled="pageOffline >= offlineTotalPages" @click="pageOffline++">下一页</button>
            </div>
            <div v-if="!filteredOfflineTasks.length" style="padding:16px;text-align:center;color:#999;font-size:13px">暂无线下任务</div>
          </div>
        </div>
      </div>
    </van-action-sheet>

    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showDialog, showToast, showLoadingToast, closeToast, showSuccessToast, showFailToast } from 'vant'
import api, { useAuth } from '../api'
import { useScreen } from '../composables/useScreen'
import { formatDateTime } from '../utils/format'
import { exportXlsxFile } from '../utils/xlsx'
import { downloadBlobResponse } from '../utils/download'

const { getAuth } = useAuth()
const { isDesktop } = useScreen()
const currentUser = computed(() => getAuth()?.user || {})
const isGuest = computed(() => (currentUser.value.role || '').includes('guest'))
const isAdmin = computed(() => (currentUser.value.role || '').includes('admin'))
const isReviewer = computed(() => (currentUser.value.role || '').includes('reviewer'))
const canReview = computed(() => !isGuest.value && (isReviewer.value || isAdmin.value))
const isOwner = (essay) => currentUser.value.role?.includes('admin') || essay.collected_by === currentUser.value.id

const deletingEssay = ref(null)
const showDelete = ref(false)
const deleteFileChecked = ref(false)

const showBatchCollector = ref(false)
const batchCollectorId = ref('')
const showBatchTask = ref(false)
const batchTaskId = ref('')
const batchTaskSearch = ref('')
const taskList = ref([])
const reviewerList = ref([])
const filterTaskSearch = ref('')
const showTaskPicker = ref(false)
const pickerTaskSearch = ref('')
const showActiveOnly = ref(false)

const sortedTaskList = computed(() => {
  return [...taskList.value].sort((a, b) => {
    const aMig = (a.course_name || '').includes('迁移')
    const bMig = (b.course_name || '').includes('迁移')
    if (aMig !== bMig) return aMig ? 1 : -1
    const aActive = taskIsActive(a)
    const bActive = taskIsActive(b)
    if (aActive !== bActive) return aActive ? -1 : 1
    return 0
  })
})

const filteredOnlineTasks = computed(() => {
  let list = sortedTaskList.value.filter(t => t.teaching_mode === '线上')
  if (showActiveOnly.value && !pickerTaskSearch.value.trim()) list = list.filter(t => taskIsActive(t))
  if (pickerTaskSearch.value.trim()) {
    const kw = pickerTaskSearch.value.toLowerCase()
    list = list.filter(t => (t.name + (t.essay_topic || '') + (t.grade || '')).toLowerCase().includes(kw))
  }
  return list
})

const filteredOfflineTasks = computed(() => {
  let list = sortedTaskList.value.filter(t => t.teaching_mode !== '线上')
  if (showActiveOnly.value && !pickerTaskSearch.value.trim()) list = list.filter(t => taskIsActive(t))
  if (pickerTaskSearch.value.trim()) {
    const kw = pickerTaskSearch.value.toLowerCase()
    list = list.filter(t => (t.name + (t.essay_topic || '') + (t.grade || '')).toLowerCase().includes(kw))
  }
  return list
})

const PAGE_SIZE = 10
const pageOnline = ref(1)
const pageOffline = ref(1)
const onlineTotalPages = computed(() => Math.max(1, Math.ceil(filteredOnlineTasks.value.length / PAGE_SIZE)))
const offlineTotalPages = computed(() => Math.max(1, Math.ceil(filteredOfflineTasks.value.length / PAGE_SIZE)))
const pagedOnlineTasks = computed(() => {
  const start = (pageOnline.value - 1) * PAGE_SIZE
  return filteredOnlineTasks.value.slice(start, start + PAGE_SIZE)
})
const pagedOfflineTasks = computed(() => {
  const start = (pageOffline.value - 1) * PAGE_SIZE
  return filteredOfflineTasks.value.slice(start, start + PAGE_SIZE)
})

function taskIsActive(t) {
  const now = new Date()
  return t.is_active
    && (!t.deadline || new Date(t.deadline) >= now)
    && (!t.start_time || new Date(t.start_time) <= now)
}

const taskPickerMode = ref('filter')

function selectTask(task) {
  if (taskPickerMode.value === 'batch') {
    if (task === null) {
      batchTaskId.value = ''
      batchTaskSearch.value = ''
    } else if (task === 0) {
      batchTaskId.value = 0
      batchTaskSearch.value = '无任务'
    } else {
      batchTaskId.value = task.id
      batchTaskSearch.value = task.name
    }
  } else {
    if (task === null) {
      filters.value.taskId = ''
      filterTaskSearch.value = ''
    } else if (task === 0) {
      filters.value.taskId = 0
      filterTaskSearch.value = '无任务'
    } else {
      filters.value.taskId = task.id
      filterTaskSearch.value = task.name
    }
    applyFilter()
  }
  showTaskPicker.value = false
  pickerTaskSearch.value = ''
}

function openBatchTaskPicker() {
  taskPickerMode.value = 'batch'
  showTaskPicker.value = true
}

watch([pickerTaskSearch, showActiveOnly], () => {
  pageOnline.value = 1
  pageOffline.value = 1
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
const selectedMeta = ref(new Map())
const grades = ['初一','初二','初三','高一','高二','高三']
const collectorList = ref([])
const courseList = ref([])

async function loadCourseList() {
  try {
    const res = await api.get('/essays/courses')
    courseList.value = res.data || []
  } catch {}
}

function syncSelectMeta(id, e) {
  if (e) selectedMeta.value.set(id, e)
}
function clearSelection() {
  selectedIds.value = []
  selectedMeta.value = new Map()
}
function selectedPreviewList() {
  return selectedIds.value.map(id => selectedMeta.value.get(id)).filter(Boolean)
}
function previewText(maxShow = 8) {
  const items = selectedPreviewList()
  if (!items.length) return ''
  const lines = items.slice(0, maxShow).map(i => `· ${i.student_name}《${i.essay_title || '无标题'}》`)
  const more = items.length - maxShow
  if (more > 0) lines.push(`…等共 ${items.length} 条`)
  return lines.join('\n')
}

// 初始化收集者筛选：管理员默认全部，其他角色默认自己
const defaultCollectedBy = computed(() => {
  if (isAdmin.value) return ''
  return currentUser.value.id || ''
})
const filters = ref({ name: '', essayTitle: '', content: '', grade: '', number: '', status: '', mode: '', collectedBy: '', remark: '', taskId: '', reviewerId: '', isSupplement: '', dateFrom: '', dateTo: '', correctedFrom: '', correctedTo: '', wordMin: '', wordMax: '', correctedMin: '', correctedMax: '', courseId: '' })

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
const COLUMN_KEY = 'essay_list_columns_v3'
const allColumns = ref([
  { key: 'student_name', label: '学生姓名', field: 'student_name', sortable: true, sort: 'student_name', visible: true, fixed: true },
  { key: 'grade', label: '年级', field: 'grade', sortable: false, visible: true },
  { key: 'essay_title', label: '作文标题', field: 'essay_title', sortable: false, visible: true },
  { key: 'corrected_title', label: '修改后标题', field: 'corrected_title', sortable: false, visible: false },
  { key: 'essay_number', label: '第几次', field: 'essay_number', sortable: true, sort: 'essay_number', visible: true },
  { key: 'teaching_mode', label: '提交方式', field: 'teaching_mode', sortable: false, visible: true },
  { key: 'status', label: '是否修改', field: 'status', sortable: true, sort: 'status', visible: true },
  { key: 'collector_name', label: '收集者', field: 'collector_name', sortable: true, sort: 'collector_name', visible: true },
  { key: 'reviewer_name', label: '批改者', field: 'reviewer_name', sortable: true, sort: 'reviewer_name', visible: false },
  { key: 'task_name', label: '任务名称', field: 'task_name', sortable: false, visible: true },
  { key: 'course_name', label: '课程名称', field: 'course_name', sortable: false, visible: false },
  { key: 'collector_note', label: '收集者备注', field: 'collector_note', sortable: false, visible: false },
  { key: 'reviewer_note', label: '批改者备注', field: 'reviewer_note', sortable: false, visible: false },
  { key: 'is_supplement', label: '是否补交', field: 'is_supplement', sortable: true, sort: 'is_supplement', visible: true },
  { key: 'word_count', label: '修改前字数', field: 'word_count', sortable: true, sort: 'word_count', visible: false },
  { key: 'corrected_word_count', label: '修改后字数', field: 'corrected_word_count', sortable: true, sort: 'corrected_word_count', visible: false },
  { key: 'created_at', label: '收集时间', field: 'created_at', sortable: true, sort: 'created_at', visible: true },
  { key: 'corrected_at', label: '修改时间', field: 'corrected_at', sortable: true, sort: 'corrected_at', visible: true },
  { key: 'file_saved', label: '文件', field: 'file_saved', sortable: false, visible: false },
])
const showColumnSettings = ref(false)
const showBatchOps = ref(false)
const showDocxSettings = ref(false)
const DOCX_SETTINGS_KEY = 'essay_list_docx_settings'
const defaultDocxSettings = {
  exportMode: 'both',
  downloadMode: 'zip',
  filenameTitle: true,
  filenameStudent: true,
  filenameGrade: true,
  filenameNumber: true,
  filenameMode: true,
  filenameSupplement: true,
  includeStudentName: true,
}
const docxSettings = ref(loadDocxSettings())

function loadDocxSettings() {
  try {
    const saved = localStorage.getItem(DOCX_SETTINGS_KEY)
    return saved ? { ...defaultDocxSettings, ...JSON.parse(saved) } : { ...defaultDocxSettings }
  } catch { return { ...defaultDocxSettings } }
}

function saveDocxSettings() {
  localStorage.setItem(DOCX_SETTINGS_KEY, JSON.stringify(docxSettings.value))
  showDocxSettings.value = false
}

function resetDocxSettings() {
  docxSettings.value = { ...defaultDocxSettings }
}
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
  localStorage.setItem('essay_list_column_order_v3', JSON.stringify(keys))
}

function loadColumnSettings() {
  try {
    // 恢复列顺序
    const orderSaved = localStorage.getItem('essay_list_column_order_v3')
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
  const defaults = { student_name: true, grade: true, essay_title: true, corrected_title: false, essay_number: true, teaching_mode: true, status: true, collector_name: true, reviewer_name: false, task_name: true, course_name: false, collector_note: false, reviewer_note: false, is_supplement: true, word_count: false, corrected_word_count: false, created_at: true, corrected_at: true, file_saved: false }
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
const allSelected = computed(() => list.value.length > 0 && list.value.every(e => selectedIds.value.includes(e.id)))

function statusLabel(s) { return { pending:'未修改', confirming:'待确认', rework:'待重改', corrected:'已修改' }[s] || s }

function hasFile(e) { return !!(e.content_file && e.file_type !== 'text') }
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
  if (filters.value.content) p.content = filters.value.content
  if (filters.value.taskId === 0 || filters.value.taskId) p.task_id = Number(filters.value.taskId)
  else if (filterTaskSearch.value) p.task_name = filterTaskSearch.value
  if (filters.value.courseId) p.course_id = Number(filters.value.courseId)
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
  page.value = 1
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

function goPage(p) { page.value = p; window.scrollTo(0, 0); loadData() }
function jumpToPage() {
  const p = parseInt(jumpPage.value)
  if (isNaN(p) || p < 1 || p > totalPages.value) {
    showToast('请输入有效的页码')
    return
  }
  goPage(p)
}
function clearFilter() { filters.value = { name: '', essayTitle: '', content: '', grade: '', number: '', status: '', mode: '', collectedBy: defaultCollectedBy.value, remark: '', taskId: '', reviewerId: '', isSupplement: '', dateFrom: '', dateTo: '', correctedFrom: '', correctedTo: '', wordMin: '', wordMax: '', correctedMin: '', correctedMax: '', courseId: '' }; filterTaskSearch.value = ''; applyFilter() }

function toggleSelect(id) {
  if (isGuest.value) return
  const idx = selectedIds.value.indexOf(id)
  const e = list.value.find(x => x.id === id)
  if (idx > -1) {
    selectedIds.value.splice(idx, 1)
    selectedMeta.value.delete(id)
  } else {
    selectedIds.value.push(id)
    syncSelectMeta(id, e)
  }
}
function toggleAll() {
  if (isGuest.value) return
  const pageIds = list.value.map(e => e.id)
  const allOnPageSelected = pageIds.length > 0 && pageIds.every(id => selectedIds.value.includes(id))
  if (allOnPageSelected) {
    // 取消本页勾选（保留其他页/其他筛选下的勾选）
    const removeSet = new Set(pageIds)
    selectedIds.value = selectedIds.value.filter(id => !removeSet.has(id))
    const m = new Map(selectedMeta.value)
    pageIds.forEach(id => m.delete(id))
    selectedMeta.value = m
  } else {
    // 勾选本页全部（追加到已有勾选，不清空其他页）
    selectedIds.value = Array.from(new Set([...selectedIds.value, ...pageIds]))
    const m = new Map(selectedMeta.value)
    list.value.forEach(e => m.set(e.id, e))
    selectedMeta.value = m
  }
}

const dragState = ref({ active: false, startId: null, moved: false, min: -1, max: -1 })
const tableDragging = ref(false)
let suppressClickUntil = 0
function isRowSelected(id) {
  if (dragState.value.active) {
    const idx = list.value.findIndex(e => e.id === id)
    if (idx >= dragState.value.min && idx <= dragState.value.max) {
      // 起始行已勾选 → 拖拽预览为取消，否则为勾选
      return !selectedIds.value.includes(dragState.value.startId)
    }
  }
  return selectedIds.value.includes(id)
}
function onRowClick(id) {
  if (isGuest.value) return
  if (dragState.value.active) return
  if (Date.now() < suppressClickUntil) return
  toggleSelect(id)
}
function dragStart(id, evt) {
  if (isGuest.value) return
  if (evt.button !== 0) return
  const startIdx = list.value.findIndex(e => e.id === id)
  dragState.value = { active: true, startId: id, moved: false, min: startIdx, max: startIdx }
  document.addEventListener('mouseup', dragEnd)
}
function dragMove(id) {
  if (!dragState.value.active) return
  const startIdx = list.value.findIndex(e => e.id === dragState.value.startId)
  const curIdx = list.value.findIndex(e => e.id === id)
  if (startIdx === -1 || curIdx === -1) return
  if (startIdx === curIdx) return
  // 已拖入其他行：进入行选择模式，清除已产生的文本选区并禁止继续选中
  if (!dragState.value.moved) {
    window.getSelection()?.removeAllRanges()
    tableDragging.value = true
  }
  const min = Math.min(startIdx, curIdx)
  const max = Math.max(startIdx, curIdx)
  if (min === dragState.value.min && max === dragState.value.max) return
  dragState.value.moved = true
  dragState.value.min = min
  dragState.value.max = max
}
function dragEnd() {
  if (!dragState.value.active) return
  const { min, max, moved, startId } = dragState.value
  tableDragging.value = false
  if (moved) {
    const startSelected = selectedIds.value.includes(startId)
    const rangeIds = list.value.slice(min, max + 1).map(e => e.id)
    if (!startSelected) {
      const m = new Map(selectedMeta.value)
      list.value.slice(min, max + 1).forEach(e => m.set(e.id, e))
      selectedMeta.value = m
      selectedIds.value = Array.from(new Set([...selectedIds.value, ...rangeIds]))
    } else {
      const rangeSet = new Set(rangeIds)
      selectedIds.value = selectedIds.value.filter(id => !rangeSet.has(id))
      const m = new Map(selectedMeta.value)
      rangeIds.forEach(id => m.delete(id))
      selectedMeta.value = m
    }
    suppressClickUntil = Date.now() + 120
  } else {
    // 未跨行拖拽：若产生了文本选区则视为复制操作，抑制随后的行点击选择
    const sel = window.getSelection()
    if (sel && sel.toString().trim()) {
      suppressClickUntil = Date.now() + 300
    }
  }
  dragState.value = { active: false, startId: null, moved: false, min: -1, max: -1 }
  document.removeEventListener('mouseup', dragEnd)
}

async function exportSingleDocx(e) {
  try {
    showLoadingToast({ message: '正在导出...', forbidClick: true, duration: 0 })
    const params = { ...docxSettings.value }
    const res = await api.get(`/essays/${e.id}/export-docx`, { params, responseType: 'blob' })
    const disposition = res.headers['content-disposition']
    let filename = '作文导出.docx'
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

async function doBatchDelete() {
  showBatchOps.value = false
  setTimeout(() => batchDelete(), 200)
}

async function batchDelete() {
  if (!selectedIds.value.length) return
  deletingEssay.value = null  // 批量模式
  deleteFileChecked.value = false
  showDelete.value = true
}

async function batchExportDocx() {
  if (!selectedIds.value.length) return
  const action = docxSettings.value.exportMode
  const downloadMode = docxSettings.value.downloadMode
  if (downloadMode !== 'queue' && action !== 'both' && selectedIds.value.length > 200) {
    showToast('合并导出一次最多 200 篇，请分批选择导出')
    return
  }
  const modeLabel = {
    both: '修改前后',
    corrected: '仅修改后',
    original: '仅修改前',
  }[action]
  const downloadLabel = {
    zip: '打成zip包（每个作文一个docx）',
    merged: '合并为一个docx',
    queue: '排队逐个下载',
  }[downloadMode]
  const msgChildren = [
    h('div', {}, `文档内容：${modeLabel} · 下载方式：${downloadLabel}`),
    h('div', {}, `将导出已选的 ${selectedIds.value.length} 篇作文：`),
    h('div', { style: { color: '#999', whiteSpace: 'pre-line' } }, previewText()),
  ]
  const confirmed = await showDialog({
    title: '确认导出',
    message: h('div', { style: { textAlign: 'left', fontSize: '13px', lineHeight: '1.8' } }, msgChildren),
    showCancelButton: true,
  }).catch(() => false)
  if (!confirmed) return
  try {
    showLoadingToast({ message: '正在导出...', forbidClick: true, duration: 0 })
    const bp = { includeStudentName: docxSettings.value.includeStudentName, filenameTitle: docxSettings.value.filenameTitle, filenameStudent: docxSettings.value.filenameStudent, filenameGrade: docxSettings.value.filenameGrade, filenameNumber: docxSettings.value.filenameNumber, filenameMode: docxSettings.value.filenameMode, filenameSupplement: docxSettings.value.filenameSupplement }
    if (downloadMode === 'queue') {
      await exportDocxQueue(selectedIds.value, action, bp)
      closeToast()
      showSuccessToast('导出成功')
      return
    }
    let res
    if (downloadMode === 'zip' || action === 'both') {
      res = await api.post('/essays/batch-export-docx', selectedIds.value, { responseType: 'blob', params: { simple_name: false, ...bp } })
    } else if (action === 'corrected') {
      res = await api.post('/essays/batch-export-docx-corrected-merged', selectedIds.value, { responseType: 'blob', params: bp })
    } else {
      res = await api.post('/essays/batch-export-docx-original-merged', selectedIds.value, { responseType: 'blob', params: bp })
    }
    downloadBlobResponse(res, downloadMode === 'zip' ? '作文导出.zip' : '作文导出.docx')
    closeToast()
    showSuccessToast('导出成功')
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '导出失败')
  }
}

async function exportDocxQueue(ids, exportMode, bp) {
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i]
    showLoadingToast({ message: `正在导出 ${i + 1}/${ids.length}...`, forbidClick: true, duration: 0 })
    const params = { exportMode, ...bp }
    try {
      const res = await api.get(`/essays/${id}/export-docx`, { params, responseType: 'blob' })
      const disposition = res.headers['content-disposition']
      let filename = `作文${i + 1}.docx`
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
      await new Promise(r => setTimeout(r, 500))
    } catch (err) {
      showToast(`第 ${i + 1} 篇导出失败`)
    }
  }
}

async function doBatchCollector() {
  if (!batchCollectorId.value) { showToast('请选择收集者'); return }
  try {
    await api.post('/essays/batch-update', { ids: selectedIds.value, collected_by: batchCollectorId.value })
    showSuccessToast('修改成功')
    clearSelection()
    batchCollectorId.value = ''
    await loadData()
  } catch (err) { showFailToast(err.response?.data?.detail || '修改失败') }
}

async function doBatchTask() {
  if (batchTaskId.value === '') { showToast('请先选择要修改为的任务'); return }
  const targetName = batchTaskId.value === 0
    ? '无任务'
    : (taskList.value.find(t => t.id === batchTaskId.value)?.name || '')
  const targetTask = taskList.value.find(t => t.id === batchTaskId.value)
  const targetGrade = batchTaskId.value === 0
    ? '无'
    : (targetTask?.grade ? targetTask.grade : '无')
  const targetNumber = batchTaskId.value === 0
    ? '无'
    : (targetTask?.essay_number ? `第${targetTask.essay_number}次` : '无')
  const targetCourse = batchTaskId.value === 0
    ? '无'
    : (targetTask?.course_name ? targetTask.course_name : '无')
  const confirmed = await showDialog({
    title: '确认修改任务',
    message: `确定将 ${selectedIds.value.length} 条作文的任务修改为「${targetName}」吗？\n作文的年级将同步为「${targetGrade}」，第几次将同步为「${targetNumber}」，课程将同步为「${targetCourse}」。`,
    showCancelButton: true,
  }).catch(() => false)
  if (!confirmed) return
  try {
    await api.post('/essays/batch-update', { ids: selectedIds.value, task_id: batchTaskId.value || null })
    showSuccessToast('修改成功')
    clearSelection()
    batchTaskId.value = ''
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
    try {
      const res = await api.post('/essays/batch-delete', {
        ids: selectedIds.value,
        delete_file: deleteFileChecked.value,
        permanent: deleteFileChecked.value,
      })
      const d = res.data || {}
      const failCount = (d.errors || []).length
      showToast(`已处理 ${d.success || 0}/${selectedIds.value.length} 条` + (failCount ? `，${failCount} 条失败` : ''))
    } catch (err) {
      showToast(err.response?.data?.detail || '批量删除失败')
    }
    clearSelection()
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

function buildXlsxRows(items) {
  return items.map(e => [
    e.student_name, e.grade, e.essay_title, e.corrected_title || '', e.essay_number ? `第${e.essay_number}次` : '',
    e.teaching_mode, statusLabel(e.status), e.collector_name,
    e.collector_note || '', e.reviewer_note || '',
    e.created_at ? formatDateTime(e.created_at) : '', e.corrected_at ? formatDateTime(e.corrected_at) : '',
  ])
}

async function exportXlsx() {
  if (!list.value.length) { showToast('当前页没有数据可导出'); return }
  showLoadingToast({ message: '正在生成 Excel...', forbidClick: true, duration: 0 })
  try {
    const headers = ['学生','年级','作文','修改后标题','第几次','提交方式','状态','收集者','收集者备注','批改者备注','收集时间','修改时间']
    const rows = buildXlsxRows(list.value)
    const ts = new Date().toISOString().slice(0, 10)
    await exportXlsxFile(`作文列表_${ts}.xlsx`, '作文列表', headers, rows)
    closeToast()
    showSuccessToast(`已导出当前页 ${rows.length} 条`)
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '导出失败')
  }
}

async function downloadXlsxFromItems(items) {
  const headers = ['学生','年级','作文','修改后标题','第几次','提交方式','状态','收集者','收集者备注','批改者备注','收集时间','修改时间']
  const rows = buildXlsxRows(items)
  const ts = new Date().toISOString().slice(0, 10)
  await exportXlsxFile(`作文已选_${ts}.xlsx`, '作文列表', headers, rows)
  return rows
}

async function exportXlsxSelected() {
  if (!selectedIds.value.length) return
  const items = selectedPreviewList()
  const confirmed = await showDialog({
    title: '确认导出已选',
    message: `将导出已选的 ${items.length} 篇作文为 Excel：\n\n${previewText()}`,
    showCancelButton: true,
  }).catch(() => false)
  if (!confirmed) return
  showLoadingToast({ message: '正在生成 Excel...', forbidClick: true, duration: 0 })
  try {
    const rows = await downloadXlsxFromItems(items)
    closeToast()
    showSuccessToast(`已导出 ${rows.length} 条`)
  } catch (err) {
    closeToast()
    showFailToast(err.response?.data?.detail || '导出失败')
  }
}

onMounted(async () => {
  loadColumnSettings()
  await loadTasks()
  loadReviewers()
  loadCourseList()
  window.addEventListener('resize', updateTopScrollWidth)
  // 从URL参数读取task_id（优先：重置筛选后再按任务筛选）
  const taskIdFromQuery = Number(route.query.task_id)
  const courseIdFromQuery = Number(route.query.course_id)
  const dayFromQuery = route.query.day
  if (courseIdFromQuery) {
    // 重置筛选后按课程筛选（课程管理跳转）
    Object.keys(filters.value).forEach(k => { filters.value[k] = '' })
    filters.value.collectedBy = defaultCollectedBy.value
    filters.value.courseId = courseIdFromQuery
  } else if (taskIdFromQuery) {
    // 重置所有筛选
    Object.keys(filters.value).forEach(k => { filters.value[k] = '' })
    filters.value.collectedBy = defaultCollectedBy.value
    filters.value.taskId = taskIdFromQuery
    const t = taskList.value.find(x => x.id === taskIdFromQuery)
    if (t) filterTaskSearch.value = t.name
  } else if (dayFromQuery) {
    // 重置筛选后按指定日期筛选（数据统计热力图跳转）
    Object.keys(filters.value).forEach(k => { filters.value[k] = '' })
    filters.value.collectedBy = defaultCollectedBy.value
    filters.value.dateFrom = dayFromQuery
    filters.value.dateTo = dayFromQuery
  } else {
    // 恢复之前保存的筛选，如果没有则设置默认值
    const hasSaved = loadFilters()
    if (!hasSaved) {
      filters.value.collectedBy = defaultCollectedBy.value
    }
    // 同步任务搜索框文字
    if (filters.value.taskId === 0) {
      filterTaskSearch.value = '无任务'
    } else if (filters.value.taskId && taskList.value.length) {
      const t = taskList.value.find(x => x.id == filters.value.taskId)
      if (t) filterTaskSearch.value = t.name
    }
  }
  await applyFilter()
})
onUnmounted(() => {
  window.removeEventListener('resize', updateTopScrollWidth)
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

.title-hint {
  display: inline-block;
  margin-left: 12px;
  padding: 4px 10px;
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 6px;
  font-size: 12px;
  color: #d46b08;
  vertical-align: middle;
  line-height: 1.4;
}

/* 批量预览 */
.batch-preview {
  background: #f8f9fb;
  border-radius: 8px;
  padding: 8px 12px;
  margin-top: 6px;
  max-height: 180px;
  overflow-y: auto;
}
.batch-preview-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}
.batch-preview-body {
  font-size: 13px;
  color: #333;
  line-height: 1.8;
  white-space: pre-line;
}

/* 手机端批量工具栏 */
.mobile-batch-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  margin-bottom: 10px;
}
.m-sel-all {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  margin-right: auto;
}
.m-sel-count {
  font-size: 12px;
  color: #666;
}

  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.desktop-table {
  border-collapse: separate;
  border-spacing: 0;
  overflow: visible;
}
.desktop-table th.sticky-col,
.desktop-table td.sticky-col {
  position: sticky;
  right: 0;
  background: #fff;
  box-shadow: -1px 0 0 rgba(0,0,0,0.05);
}
.desktop-table th.sticky-col {
  background: #fafafa;
  z-index: 3;
}
.desktop-table td.sticky-col {
  z-index: 1;
}
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

.desktop-table td.td-note {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-selected { background: #e6f4ff !important; }

.desktop-table.table-dragging { user-select: none; }
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
.tag-rework { background: #fff1f0; color: #ff4d4f; }
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
  height: 10px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  margin-bottom: 2px;
}
.scroll-sync-content {
  height: 9px;
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

/* ===== 手机端卡片列表 ===== */
.mobile-list { display: flex; flex-direction: column; gap: 10px; }
.mobile-card {
  background: #fff;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.mobile-card.row-selected { background: #e6f4ff; }
.mobile-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.mobile-card-name-wrap { display: flex; align-items: center; gap: 8px; min-width: 0; }
.mobile-card-name { font-size: 15px; font-weight: 600; color: #333; }
.mobile-card-title {
  font-size: 13px;
  color: #555;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mobile-card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.m-sep { color: #d9d9d9; }
.mobile-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #aaa;
  padding-top: 8px;
  border-top: 1px dashed #f0f0f0;
}
.mobile-card-actions { display: flex; align-items: center; gap: 6px; }

/* 任务选择器 */
.task-picker-sheet :deep(.van-action-sheet__content) { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
.task-picker-sheet .picker-list { flex: 1; overflow-y: auto; padding-bottom: 16px; }
.task-item-option {
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  transition: background 0.15s;
}
.task-item-option:hover { background: #f5f5f5; }
.task-item-option.active { background: #e6f4ff; }
.task-item-title { display: flex; align-items: center; margin-bottom: 4px; }
.task-item-title span { font-size: 14px; }
.task-item-meta { display: flex; align-items: center; gap: 6px; font-size: 12px; flex-wrap: wrap; }
.task-split { display: flex; gap: 8px; padding: 0 4px; }
.task-col { flex: 1; min-width: 0; }
.task-col-title { font-size: 13px; color: #999; padding: 12px 12px 6px; font-weight: 600; }
.task-select-btn { background: #fff; border: 1px solid #d9d9d9; border-radius: 6px; padding: 6px 12px; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-select-btn:hover { border-color: #1677ff; }
.pagination-row { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 8px 0; }
.page-info { font-size: 12px; color: #666; }
.settings-section-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 10px; }
.batch-ops-list { padding: 8px 0 12px; }
.batch-ops-item { display: flex; align-items: center; gap: 10px; padding: 14px 20px; font-size: 14px; color: #333; cursor: pointer; border-bottom: 1px solid #f5f5f5; }
.batch-ops-item:active { background: #f5f8ff; }
.batch-ops-icon { font-size: 18px; }
.batch-ops-name { flex: 1; }
.batch-ops-cancel { text-align: center; padding: 14px 0 4px; font-size: 14px; color: #999; cursor: pointer; }
</style>
