import axios from 'axios'

function getBaseUrl() {
  const saved = localStorage.getItem('apiBaseUrl')
  if (saved) {
    return saved.replace(/\/+$/, '') + '/api'
  }
  return '/api'
}

const api = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
})

// 当前使用哪个账号
let _activeKey = `auth_${localStorage.getItem('activeAuth') || 'default'}`

export function setActiveAuth(name) {
  _activeKey = `auth_${name}`
  localStorage.setItem('activeAuth', name)
}

export function getActiveAuth() {
  return localStorage.getItem('activeAuth') || 'default'
}

// 获取当前账号的 token 和 user
function getAuth() {
  try {
    const raw = localStorage.getItem(_activeKey)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

function saveAuth(data) {
  localStorage.setItem(_activeKey, JSON.stringify(data))
}

function clearAuth() {
  localStorage.removeItem(_activeKey)
}

// 请求拦截器：自动带 token
api.interceptors.request.use(config => {
  const auth = getAuth()
  if (auth?.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截器：401 跳登录（只在主页面导航时触发）
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      // 只对实际 API 接口返回 401 做处理，图片等静态文件跳过
      clearAuth()
      // 不在文件请求时跳转
      if (err.config?.url && !err.config.url.includes('/file/')) {
        window.location.hash = '#/login'
      }
    }
    return Promise.reject(err)
  }
)

// 暴露给组件使用
export function useAuth() {
  return {
    getAuth,
    saveAuth(data) {
      saveAuth(data)
    },
    clearAuth,
    setActiveAuth,
    getActiveAuth,
  }
}

export default api
