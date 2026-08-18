import axios from 'axios'
import { showToast } from 'vant'

/* global __API_BASE_URL__ */
const DEFAULT_BASE = (typeof __API_BASE_URL__ !== 'undefined' ? __API_BASE_URL__ : '').replace(/\/+$/, '')

function getBaseUrl() {
  const saved = localStorage.getItem('apiBaseUrl')
  if (saved && saved.trim()) {
    return saved.trim().replace(/\/+$/, '') + '/api'
  }
  return DEFAULT_BASE ? DEFAULT_BASE + '/api' : '/api'
}

const api = axios.create({
  timeout: 30000,
})

let _activeKey = `auth_${localStorage.getItem('activeAuth') || 'default'}`

export function setActiveAuth(name) {
  _activeKey = `auth_${name}`
  localStorage.setItem('activeAuth', name)
}

export function getActiveAuth() {
  return localStorage.getItem('activeAuth') || 'default'
}

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

api.interceptors.request.use(config => {
  config.baseURL = getBaseUrl()
  const auth = getAuth()
  if (auth?.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

const COMMON_ERRORS = {
  400: '请求参数有误',
  401: '登录已过期，请重新登录',
  403: '没有权限执行该操作',
  404: '请求的资源不存在',
  409: '数据冲突，请检查后重试',
  422: '提交的数据有误',
  429: '请求过于频繁，请稍后重试',
  500: '服务器内部错误，请稍后重试',
  502: '服务器繁忙，请稍后重试',
  503: '服务暂不可用，请稍后重试',
}

export function getApiErrorMessage(err, fallback = '请求失败') {
  if (!err) return fallback
  if (err.response) {
    // 拦截器已把 detail 统一为带状态码的消息，此处直接使用
    const detail = err.response.data?.detail
    if (typeof detail === 'string' && detail.trim()) return detail
    return `[${err.response.status}] ${COMMON_ERRORS[err.response.status] || '请求失败'}`
  }
  if (err.code === 'ECONNABORTED') return '[ECONNABORTED] 请求超时，请重试'
  if (err.code) return `[${err.code}] 网络连接失败，请检查服务器地址或网络`
  return '网络连接失败，请检查服务器地址或网络'
}

api.interceptors.response.use(
  res => res,
  err => {
    const resp = err.response
    // 统一为响应错误附加带状态码的消息（页面读取 err.response.data.detail 处自动生效）
    let hadDetail = false
    if (resp) {
      const status = resp.status
      const rawDetail = resp.data?.detail
      hadDetail = typeof rawDetail === 'string' && rawDetail.trim()
      const msg = hadDetail
        ? `[${status}] ${rawDetail}`
        : `[${status}] ${COMMON_ERRORS[status] || '请求失败'}`
      if (resp.data && typeof resp.data === 'object') {
        resp.data.detail = msg
      }
    }
    if (resp?.status === 401) {
      clearAuth()
      // 会话过期登出：不应触发登录后的回跳
      sessionStorage.removeItem('loginRedirect')
      if (err.config?.url && !err.config.url.includes('/file/')) {
        window.location.hash = '#/login'
      }
    } else if (err.config && err.config.__toastError !== false && !hadDetail) {
      // 后端未返回 detail 时才由拦截器兜底提示（避免与页面 catch 重复提示）
      showToast(getApiErrorMessage(err))
    }
    return Promise.reject(err)
  }
)

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

export { getBaseUrl }
export default api
