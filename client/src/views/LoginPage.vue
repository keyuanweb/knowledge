<script setup>
/**
 * 登录页。
 */

import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({
  username: '',
  password: '',
})

const loading = ref(false)
const errorMsg = ref('')

async function onSubmit() {
  errorMsg.value = ''
  loading.value = true
  try {
    const user = await auth.login(form.username, form.password)
    const redirect = route.query.redirect?.toString() || ''
    if (redirect) return router.replace(redirect)
    if (user?.role === 'admin') return router.replace('/overview')
    return router.replace('/chat')
  } catch (e) {
    errorMsg.value = e?.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="bg" aria-hidden="true" />
    <div class="panel">
      <header class="head">
        <div class="mark">QA</div>
        <div class="titles">
          <h1 class="name">企业知识库问答</h1>
          <p class="tagline">基于企业文档的智能检索与问答</p>
        </div>
      </header>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="lbl">用户名</span>
          <input
            v-model.trim="form.username"
            class="inp"
            type="text"
            name="username"
            autocomplete="username"
            placeholder="请输入用户名"
          />
        </label>

        <label class="field">
          <span class="lbl">密码</span>
          <input
            v-model="form.password"
            class="inp"
            type="password"
            name="password"
            autocomplete="current-password"
            placeholder="请输入密码"
          />
        </label>

        <div v-if="errorMsg" class="error" role="alert">{{ errorMsg }}</div>

        <button class="submit" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '进入系统' }}
        </button>
      </form>

      <p class="foot">账号由管理员分配；如遇问题请联系管理员</p>
    </div>
  </div>
</template>

<style scoped>
.page {
  position: relative;
  min-height: 100svh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  box-sizing: border-box;
}

.bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(ellipse 120% 80% at 10% -20%, color-mix(in oklab, var(--accent) 22%, transparent), transparent 55%),
    radial-gradient(ellipse 90% 70% at 100% 10%, color-mix(in oklab, #2563eb 18%, transparent), transparent 50%),
    linear-gradient(165deg, var(--bg) 0%, color-mix(in oklab, var(--code-bg) 55%, var(--bg)) 100%);
}

@media (prefers-color-scheme: dark) {
  .bg {
    background:
      radial-gradient(ellipse 120% 80% at 10% -20%, color-mix(in oklab, var(--accent) 28%, transparent), transparent 55%),
      radial-gradient(ellipse 90% 70% at 100% 10%, color-mix(in oklab, #60a5fa 14%, transparent), transparent 50%),
      linear-gradient(165deg, var(--bg) 0%, color-mix(in oklab, #1a1b22 80%, var(--bg)) 100%);
  }
}

.panel {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 36px 32px 28px;
  border-radius: 20px;
  border: 1px solid color-mix(in oklab, var(--border) 70%, transparent);
  background: color-mix(in oklab, var(--bg) 88%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow:
    0 1px 0 color-mix(in oklab, white 40%, transparent) inset,
    0 24px 48px -12px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(0, 0, 0, 0.03);
}

@media (prefers-color-scheme: dark) {
  .panel {
    background: color-mix(in oklab, var(--bg) 82%, transparent);
    box-shadow:
      0 1px 0 color-mix(in oklab, white 6%, transparent) inset,
      0 24px 48px -12px rgba(0, 0, 0, 0.45);
  }
}

.head {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 28px;
}

.mark {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: white;
  background: linear-gradient(145deg, #7c3aed 0%, #4f46e5 48%, #2563eb 100%);
  box-shadow: 0 8px 24px color-mix(in oklab, var(--accent) 35%, transparent);
  flex-shrink: 0;
}

.titles {
  min-width: 0;
}

.name {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.25;
  color: var(--text-h);
}

.tagline {
  margin: 6px 0 0;
  font-size: 0.8125rem;
  line-height: 1.45;
  color: var(--text);
}

.form {
  display: grid;
  gap: 18px;
}

.field {
  display: grid;
  gap: 8px;
}

.lbl {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-h);
}

.inp {
  width: 100%;
  box-sizing: border-box;
  height: 46px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  color: var(--text-h);
  font-size: 0.9375rem;
  outline: none;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.inp::placeholder {
  color: color-mix(in oklab, var(--text) 65%, var(--bg));
}

.inp:hover {
  border-color: color-mix(in oklab, var(--text) 25%, var(--border));
}

.inp:focus {
  border-color: color-mix(in oklab, var(--accent) 55%, var(--border));
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--accent) 18%, transparent);
}

.error {
  margin: -4px 0 0;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 0.8125rem;
  line-height: 1.4;
  color: #b91c1c;
  background: color-mix(in oklab, #ef4444 10%, var(--code-bg));
  border: 1px solid color-mix(in oklab, #ef4444 22%, var(--border));
}

.submit {
  margin-top: 4px;
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, color-mix(in oklab, var(--accent) 92%, #000) 0%, var(--accent) 100%);
  color: white;
  font-size: 0.9375rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  cursor: pointer;
  box-shadow: 0 4px 14px color-mix(in oklab, var(--accent) 35%, transparent);
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    opacity 0.12s ease;
}

.submit:hover:not(:disabled) {
  box-shadow: 0 6px 20px color-mix(in oklab, var(--accent) 42%, transparent);
  transform: translateY(-1px);
}

.submit:active:not(:disabled) {
  transform: translateY(0);
}

.submit:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
}

.foot {
  margin: 24px 0 0;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--text);
  text-align: center;
}
</style>
