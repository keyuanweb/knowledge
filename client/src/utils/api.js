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
    const ct = String(resp.headers?.['content-type'] || '')
    const url = String(resp.config?.url || '')
    // Prometheus 指标为 text/plain，不走 JSON 包装
    if (url.includes('/metrics') && ct.includes('text/plain')) {
      return resp
    }

    // 健康检查为 { ok, checks }，无 data 字段
    if (url.includes('health') && ct.includes('application/json')) {
      return { ...resp, data: resp.data }
    }

    // 后端统一返回：{ ok, data, message }
    const payload = resp?.data
    if (payload && payload.ok === false) {
      const msg = payload.message || '请求失败'
      return Promise.reject(new Error(msg))
    }
    // 非 JSON 或缺少 ok:true 时勿静默当成空 data（否则列表会「空白无报错」）
    if (typeof payload !== 'object' || payload === null || payload.ok !== true) {
      const msg =
        typeof payload === 'string'
          ? '服务器返回了非 JSON 响应，请检查是否未登录或接口地址错误'
          : '接口响应格式异常'
      return Promise.reject(new Error(msg))
    }
    return { ...resp, data: payload.data }
  },
  (err) => {
    const msg = err?.response?.data?.message || err?.message || '网络错误'
    return Promise.reject(new Error(msg))
  },
)

