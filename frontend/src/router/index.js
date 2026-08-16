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
    path: '/stats',
    name: 'DashboardStats',
    component: () => import('../views/DashboardStats.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/account/settings',
    name: 'PersonalInfo',
    component: () => import('../views/PersonalInfo.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/essay/upload',
    name: 'EssayUpload',
    component: () => import('../views/EssayUpload.vue'),
    meta: { requiresAuth: true, roles: ['collector', 'admin'] },
  },
  {
    path: '/essay/batch-upload',
    name: 'EssayBatchUpload',
    component: () => import('../views/EssayBatchUpload.vue'),
    meta: { requiresAuth: true, roles: ['collector', 'admin'] },
  },
  {
    path: '/essay/list',
    name: 'EssayList',
    component: () => import('../views/EssayList.vue'),
    meta: { requiresAuth: true, roles: ['collector', 'admin', 'reviewer', 'guest'] },
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
    path: '/review/operations',
    name: 'OperationHistory',
    component: () => import('../views/ReviewHistory.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('../views/AdminUsers.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/course',
    name: 'AdminCourse',
    component: () => import('../views/AdminCourse.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/corrected-upload',
    name: 'AdminCorrectedUpload',
    component: () => import('../views/AdminCorrectedUpload.vue'),
    meta: { requiresAuth: true, roles: ['admin'], superAdmin: true },
  },
  {
    path: '/admin/tasks',
    name: 'AdminTasks',
    component: () => import('../views/AdminTasks.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'collector', 'reviewer', 'guest'] },
  },
  {
    path: '/admin/settings',
    name: 'AdminSettings',
    component: () => import('../views/AdminSettings.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

const PAGE_TITLES = {
  '/dashboard': '工作台',
  '/stats': '数据统计',
  '/account/settings': '个人信息',
  '/essay/upload': '上传作文',
  '/essay/batch-upload': '批量上传',
  '/essay/list': '作文列表',
  '/review/pending': '未改列表',
  '/review/operations': '操作历史',
  '/admin/users': '用户管理',
  '/admin/course': '课程管理',
  '/admin/corrected-upload': '已改作文上传',
  '/admin/tasks': '任务列表',
  '/admin/settings': '系统设置',
  '/login': '登录',
}

router.afterEach((to) => {
  const title = PAGE_TITLES[to.path]
  document.title = title ? `${title} · 作文收集管理系统` : '作文收集管理系统'
})

router.beforeEach((to, from, next) => {
  let token = null
  let userRole = ''
  let username = ''
  try {
    const raw = localStorage.getItem(`auth_${localStorage.getItem('activeAuth') || 'default'}`)
    if (raw) {
      const auth = JSON.parse(raw)
      token = auth.token
      userRole = auth.user?.role || ''
      username = auth.user?.username || ''
    }
  } catch {}

  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  if (to.meta.superAdmin && username !== 'admin') {
    next('/dashboard')
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
