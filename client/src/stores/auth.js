/**
 * 登录状态管理（Pinia）。
 */

import { defineStore } from 'pinia'
import { api } from '../utils/api'

const TOKEN_KEY = 'enterprise_qa_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: null,
    userLoaded: false,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  actions: {
    /**
     * 登录并保存 token。
     */
    async login(username, password) {
      const res = await api.post('/auth/login', { username, password })
      const token = res?.data?.access_token
      if (!token) throw new Error('登录失败：缺少 token')
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
      this.user = res?.data?.user || null
      this.userLoaded = true
      return this.user
    },

    /**
     * 获取当前用户信息。
     */
    async fetchMe() {
      const res = await api.get('/auth/me')
      this.user = res?.data || null
      this.userLoaded = true
      return this.user
    },

    /**
     * 退出登录。
     */
    logout() {
      this.token = ''
      this.user = null
      this.userLoaded = false
      localStorage.removeItem(TOKEN_KEY)
    },
  },
})

