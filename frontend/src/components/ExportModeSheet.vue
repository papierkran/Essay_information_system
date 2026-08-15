<template>
  <van-action-sheet v-model:show="visible" :title="title" :close-on-click-action="true">
    <div class="export-mode-options">
      <div v-for="opt in options" :key="opt.value" class="export-mode-option" @click="choose(opt.value)">
        <span class="export-mode-icon">{{ opt.icon }}</span>
        <span class="export-mode-name">{{ opt.name }}</span>
      </div>
      <div class="export-mode-cancel" @click="visible = false">取消</div>
    </div>
  </van-action-sheet>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '选择导出方式' },
})
const emit = defineEmits(['update:show', 'confirm'])

const visible = ref(false)
watch(() => props.show, v => { visible.value = v })
watch(visible, v => emit('update:show', v))

const options = [
  { value: 'zip', icon: '📦', name: '修改前后 · 单独docx（ZIP 打包）' },
  { value: 'merged', icon: '📄', name: '修改前后 · 合并为一个docx' },
  { value: 'corrected', icon: '✂️', name: '仅修改后 · 合并为一个docx' },
  { value: 'original', icon: '📝', name: '仅修改前 · 合并为一个docx' },
]

function choose(value) {
  visible.value = false
  emit('confirm', value)
}
</script>

<style scoped>
.export-mode-options {
  padding: 8px 0 12px;
}
.export-mode-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
}
.export-mode-option:active { background: #f5f8ff; }
.export-mode-icon { font-size: 18px; }
.export-mode-name { flex: 1; }
.export-mode-cancel {
  text-align: center;
  padding: 14px 0 4px;
  font-size: 14px;
  color: #999;
  cursor: pointer;
}
</style>
