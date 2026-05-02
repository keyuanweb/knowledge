/**
 * 前端路由配置。
 *
 * 说明：
 * - 登录：/login
 * - 主应用：左侧菜单 + 顶栏，子路由为各功能页
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import LoginPage from '../views/LoginPage.vue'
import AppLayout from '../views/AppLayout.vue'
import ChatPage from '../views/ChatPage.vue'
import AdminHome from '../views/admin/AdminHome.vue'
import AdminDocs from '../views/admin/AdminDocs.vue'
import KnowledgeManage from '../views/KnowledgeManage.vue'
import UserManage from '../views/UserManage.vue'
import ChatHistory from '../views/ChatHistory.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginPage },
    {
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/chat' },
        {
          path: 'overview',
          component: AdminHome,
          meta: { requiresAdmin: true, title: '数据概览' },
        },
        {
          path: 'knowledge',
          component: KnowledgeManage,
          meta: { requiresAdmin: true, title: '知识库管理' },
        },
        {
          path: 'docs',
          component: AdminDocs,
          meta: { requiresAdmin: true, title: '文档管理' },
        },
        {
          path: 'users',
          component: UserManage,
          meta: { requiresAdmin: true, title: '用户管理' },
        },
        { path: 'chat', component: ChatPage, meta: { title: '智能问答' } },
        { path: 'history', component: ChatHistory, meta: { title: '对话历史' } },
      ],
    },
    { path: '/admin', redirect: '/overview' },
    { path: '/admin/:pathMatch(.*)*', redirect: '/overview' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.token && !auth.userLoaded) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
    }
  }

  const needAuth = to.matched.some((r) => r.meta.requiresAuth)
  if (needAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const needAdmin = to.matched.some((r) => r.meta.requiresAdmin)
  if (needAdmin && auth.user?.role !== 'admin') {
    return { path: '/chat' }
  }

  return true
})

export default router
