<template>
  <div class="page notfound-page">
    <div class="empty-state">
      <div class="icon">🧭</div>
      <p>页面不存在或已被移除</p>
      <button class="btn btn-primary" style="margin-top:12px" @click="goHome">返回工作台</button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
function goHome() { router.push('/dashboard') }
</script>
