/**
 * Axios 封装。
 *
 * 说明：
 * - baseURL 默认指向 Flask 后端：http://localhost:5000/api
 * - 自动附带 Authorization: Bearer <token>
 */

import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('enterprise_qa_token') || ''
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (resp) => {
    // 后端统一返回：{ ok, data, message }
    const payload = resp?.data
    if (payload && payload.ok === false) {
      const msg = payload.message || '请求失败'
      return Promise.reject(new Error(msg))
    }
    return { ...resp, data: payload?.data }
  },
  (err) => {
    const msg = err?.response?.data?.message || err?.message || '网络错误'
    return Promise.reject(new Error(msg))
  },
)

