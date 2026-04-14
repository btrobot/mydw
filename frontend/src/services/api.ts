import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'
export const buildApiUrl = (path: string) => `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default api
