<script setup>
/**
 * 对话历史：当前用户在本系统的问答记录。
 */

import { onMounted, ref } from 'vue'
import { api } from '../utils/api'

const rows = ref([])
const errorMsg = ref('')
const loading = ref(false)

async function load() {
  errorMsg.value = ''
  loading.value = true
  try {
    const res = await api.get('/chat/history', { params: { limit: 100 } })
    rows.value = res?.data || []
  } catch (e) {
    errorMsg.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="head">
      <p class="page-lead">仅展示当前账号的问答记录</p>
      <button class="btn" type="button" :disabled="loading" @click="load">刷新</button>
    </div>
    <div v-if="errorMsg" class="err">{{ errorMsg }}</div>
    <div class="list">
      <div v-for="r in rows" :key="r.id" class="card">
        <div class="meta">
          <span class="id">#{{ r.id }}</span>
          <span class="time">{{ r.created_at || '-' }}</span>
        </div>
        <div class="q">
          <span class="label">问</span>
          <div class="text">{{ r.question }}</div>
        </div>
        <div class="a">
          <span class="label">答</span>
          <div class="text">{{ r.answer }}</div>
        </div>
      </div>
      <div v-if="!loading && !rows.length" class="empty">暂无记录，去「智能问答」提问后会出现在这里</div>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: grid;
  gap: 14px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}
.page-lead {
  margin: 0;
  flex: 1;
  min-width: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
  max-width: 52rem;
}
.head .btn {
  flex-shrink: 0;
  margin-top: 1px;
}
.btn {
  height: 36px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  color: var(--text-h);
  cursor: pointer;
  padding: 0 12px;
}
.err {
  font-size: 13px;
  color: #ef4444;
}
.list {
  display: grid;
  gap: 12px;
}
.card {
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 14px 16px;
  background: color-mix(in oklab, var(--bg) 92%, transparent);
}
.meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text);
  margin-bottom: 10px;
}
.id {
  font-weight: 700;
  color: var(--text-h);
}
.q,
.a {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: 8px;
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.55;
}
.q {
  margin-top: 0;
}
.label {
  font-weight: 800;
  color: var(--accent);
  font-size: 12px;
  padding-top: 2px;
}
.text {
  color: var(--text-h);
  white-space: pre-wrap;
}
.empty {
  text-align: center;
  padding: 40px 16px;
  color: var(--text);
  font-size: 14px;
  border: 1px dashed var(--border);
  border-radius: 16px;
}
</style>
