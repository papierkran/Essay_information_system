import axios from 'axios'

function getBaseUrl() {
  const saved = localStorage.getItem('apiBaseUrl')
  if (saved) {
    return saved.replace(/\/+$/, '') + '/api'
  }
  return '/api'
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

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      clearAuth()
      if (err.config?.url && !err.config.url.includes('/file/')) {
        window.location.hash = '#/login'
      }
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

export default api
