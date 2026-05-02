<script setup>
/**
 * 登录后主框架：左侧菜单 + 右侧顶栏（用户与退出）+ 内容区。
 */

import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const appTitle = import.meta.env.VITE_APP_TITLE || '企业知识库'
const appSub = import.meta.env.VITE_APP_SUBTITLE || 'RAG · Ollama · Chroma'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const isAdmin = computed(() => auth.user?.role === 'admin')

function logout() {
  auth.logout()
  router.replace('/login')
}

const title = computed(() => route.meta?.title || '')

onMounted(() => {
  const t = import.meta.env.VITE_APP_TITLE
  if (t) document.title = t
})
</script>

<template>
  <div class="shell">
    <aside class="side">
      <div class="brand">
        <div class="logo">QA</div>
        <div>
          <div class="brand-title">{{ appTitle }}</div>
          <div class="brand-sub">{{ appSub }}</div>
        </div>
      </div>

      <nav class="nav">
        <template v-if="isAdmin">
          <router-link to="/overview" class="item" active-class="active">数据概览</router-link>
          <router-link to="/knowledge" class="item" active-class="active">知识库管理</router-link>
          <router-link to="/docs" class="item" active-class="active">文档管理</router-link>
          <router-link to="/users" class="item" active-class="active">用户管理</router-link>
        </template>
        <router-link to="/chat" class="item" active-class="active">智能问答</router-link>
        <router-link to="/history" class="item" active-class="active">对话历史</router-link>
      </nav>
    </aside>

    <div class="right">
      <header class="topbar">
        <div class="topbar-left">
          <span v-if="title" class="page-title">{{ title }}</span>
        </div>
        <div class="user-area">
          <span class="uname">{{ auth.user?.username }}</span>
          <span v-if="auth.user?.role" class="role">（{{ auth.user.role }}）</span>
          <span class="sep">·</span>
          <button type="button" class="link-out" @click="logout">退出</button>
        </div>
      </header>
      <main class="main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  height: 100svh;
  min-height: 100svh;
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  overflow: hidden;
}
.side {
  border-right: 1px solid var(--border);
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: color-mix(in oklab, var(--bg) 92%, transparent);
  min-height: 0;
}
.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--code-bg);
}
.logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: white;
  background: linear-gradient(135deg, #7c3aed, #2563eb);
  flex-shrink: 0;
}
.brand-title {
  color: var(--text-h);
  font-weight: 700;
  font-size: 15px;
}
.brand-sub {
  color: var(--text);
  font-size: 12px;
  margin-top: 2px;
}
.nav {
  display: grid;
  gap: 8px;
  overflow-y: auto;
}
.item {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 11px 14px;
  text-decoration: none;
  color: var(--text-h);
  background: color-mix(in oklab, var(--bg) 86%, transparent);
  font-size: 14px;
}
.item.active {
  border-color: color-mix(in oklab, var(--accent) 55%, var(--border));
  background: color-mix(in oklab, var(--accent) 12%, var(--code-bg));
}
.right {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}
.topbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  background: color-mix(in oklab, var(--bg) 94%, transparent);
}
.topbar-left {
  min-width: 0;
}
.page-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-h);
}
.user-area {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0 4px;
  flex-shrink: 0;
  font-size: 14px;
  line-height: 1.4;
}
.uname {
  font-weight: 600;
  color: var(--text-h);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.role {
  font-size: 13px;
  color: var(--text);
  font-weight: 400;
}
.sep {
  color: var(--text);
  margin: 0 2px;
  user-select: none;
}
.link-out {
  border: none;
  background: none;
  padding: 0;
  margin: 0;
  font: inherit;
  font-size: 14px;
  color: var(--text);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}
.link-out:hover {
  color: #b91c1c;
}
.main {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 16px 20px 24px;
  box-sizing: border-box;
}
@media (max-width: 900px) {
  .shell {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr);
    overflow: auto;
  }
  .side {
    border-right: none;
    border-bottom: 1px solid var(--border);
    max-height: none;
  }
  .nav {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}
</style>
