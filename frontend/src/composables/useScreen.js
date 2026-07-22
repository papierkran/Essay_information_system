import { ref, computed, onMounted, onUnmounted } from 'vue'

const BREAKPOINT = 768
const width = ref(window.innerWidth)
const isDesktop = computed(() => width.value >= BREAKPOINT)
const isMobile = computed(() => width.value < BREAKPOINT)

function onResize() { width.value = window.innerWidth }

export function useScreen() {
  onMounted(() => window.addEventListener('resize', onResize))
  onUnmounted(() => window.removeEventListener('resize', onResize))
  return { width, isDesktop, isMobile }
}
