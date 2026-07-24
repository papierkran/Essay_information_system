import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/', redirect: '/dashboard' },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/essay/upload',
    name: 'EssayUpload',
    component: () => import('../views/EssayUpload.vue'),
    meta: { requiresAuth: true, roles: ['collector', 'admin', 'guest'] },
  },
  {
    path: '/essay/batch-upload',
    name: 'EssayBatchUpload',
    component: () => import('../views/EssayBatchUpload.vue'),
    meta: { requiresAuth: true, roles: ['collector', 'admin', 'guest'] },
  },
  {
    path: '/essay/list',
    name: 'EssayList',
    component: () => import('../views/EssayList.vue'),
    meta: { requiresAuth: true, roles: ['collector', 'admin', 'guest'] },
  },
  {
    path: '/review/pending',
    name: 'ReviewPending',
    component: () => import('../views/ReviewPending.vue'),
    meta: { requiresAuth: true, roles: ['reviewer', 'admin', 'guest'] },
  },
  {
    path: '/review/detail/:id',
    name: 'ReviewDetail',
    component: () => import('../views/ReviewDetail.vue'),
    meta: { requiresAuth: true, roles: ['reviewer', 'collector', 'admin', 'guest'] },
  },
  {
    path: '/review/history',
    name: 'ReviewHistory',
    component: () => import('../views/ReviewHistory.vue'),
    meta: { requiresAuth: true, roles: ['reviewer', 'admin', 'guest'] },
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('../views/AdminUsers.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/classes',
    name: 'AdminClasses',
    component: () => import('../views/AdminClasses.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/settings',
    name: 'AdminSettings',
    component: () => import('../views/AdminSettings.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  let token = null
  let userRole = ''
  try {
    const raw = localStorage.getItem(`auth_${localStorage.getItem('activeAuth') || 'default'}`)
    if (raw) {
      const auth = JSON.parse(raw)
      token = auth.token
      userRole = auth.user?.role || ''
    }
  } catch {}

  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  if (to.meta.roles && userRole) {
    const roles = userRole.split(',')
    const hasRole = to.meta.roles.some(r => roles.includes(r))
    if (!hasRole) {
      next('/dashboard')
      return
    }
  }

  next()
})

export default router
