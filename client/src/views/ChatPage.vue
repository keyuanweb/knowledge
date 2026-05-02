<script setup>
/**
 * 智能问答：左侧可展开/收起的知识库选择，右侧对话。
 */

import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { api } from '../utils/api'
import { streamChatAsk } from '../utils/chatAskStream'

const msgsEl = ref(null)
let scrollRaf = 0
function scrollMsgsToBottom() {
  if (scrollRaf) return
  scrollRaf = requestAnimationFrame(() => {
    scrollRaf = 0
    const el = msgsEl.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

const knowledgeBases = ref([])
const knowledgeBaseId = ref(null)
const kbPanelOpen = ref(true)

const state = reactive({
  question: '',
  loading: false,
  errorMsg: '',
})

const messages = ref([
  {
    role: 'assistant',
    content:
      '你好，我是企业知识库问答助手。在左侧选择一个知识库后即可提问，答案将基于该库中的文档。',
    sources: [],
  },
])

const canAsk = computed(
  () => !!state.question.trim() && !state.loading && knowledgeBaseId.value != null,
)

const currentKb = computed(() => knowledgeBases.value.find((k) => k.id === knowledgeBaseId.value))

const currentKbTitle = computed(() => currentKb.value?.name || '未选择')

async function loadKnowledgeBases() {
  try {
    const res = await api.get('/chat/knowledge-bases')
    knowledgeBases.value = res?.data || []
    if (knowledgeBaseId.value == null && knowledgeBases.value.length) {
      knowledgeBaseId.value = knowledgeBases.value[0].id
    }
  } catch {
    knowledgeBases.value = []
  }
}

function selectKb(id) {
  knowledgeBaseId.value = id
}

onMounted(loadKnowledgeBases)

async function ask() {
  const q = state.question.trim()
  if (!q || state.loading) return
  state.errorMsg = ''
  state.loading = true

  messages.value.push({ role: 'user', content: q })
  state.question = ''
  await nextTick()
  scrollMsgsToBottom()

  const assistantMsg = reactive({
    role: 'assistant',
    content: '',
    sources: [],
    streaming: true,
  })
  messages.value.push(assistantMsg)
  await nextTick()
  scrollMsgsToBottom()

  try {
    await streamChatAsk({
      question: q,
      knowledgeBaseId: knowledgeBaseId.value,
      onMeta(sources) {
        assistantMsg.sources = sources || []
        scrollMsgsToBottom()
      },
      onToken(text) {
        assistantMsg.content += text
        scrollMsgsToBottom()
      },
      onDone() {},
    })
  } catch (e) {
    state.errorMsg = e?.message || '请求失败'
    assistantMsg.content = `抱歉，本次请求失败：${state.errorMsg}`
    assistantMsg.sources = []
  } finally {
    assistantMsg.streaming = false
    state.loading = false
    await nextTick()
    scrollMsgsToBottom()
  }
}
</script>

<template>
  <div class="wrap">
    <div class="layout" :class="{ 'kb-collapsed': !kbPanelOpen }">
      <aside class="kb-side" aria-label="知识库选择">
        <div class="kb-toolbar" :class="{ 'toolbar-collapsed': !kbPanelOpen }">
          <span v-show="kbPanelOpen" class="kb-heading">知识库</span>
          <button
            type="button"
            class="kb-fold"
            :title="kbPanelOpen ? '收起侧边栏' : '展开知识库'"
            :aria-expanded="kbPanelOpen"
            @click="kbPanelOpen = !kbPanelOpen"
          >
            <span class="chev" aria-hidden="true">{{ kbPanelOpen ? '⟨' : '⟩' }}</span>
          </button>
        </div>

        <div v-show="kbPanelOpen" class="kb-list">
          <p v-if="!knowledgeBases.length" class="kb-empty">暂无知识库，请联系管理员配置。</p>
          <button
            v-for="k in knowledgeBases"
            :key="k.id"
            type="button"
            class="kb-card"
            :class="{ active: knowledgeBaseId === k.id }"
            @click="selectKb(k.id)"
          >
            <span class="kb-name">{{ k.name }}</span>
            <span class="kb-meta">{{ k.doc_count }} 个文档</span>
            <span v-if="k.description" class="kb-desc">{{ k.description }}</span>
          </button>
        </div>

        <div v-show="!kbPanelOpen" class="kb-rail">
          <span class="rail-label" :title="currentKbTitle">{{ currentKbTitle }}</span>
        </div>
      </aside>

      <div class="chat">
        <div v-if="currentKb && kbPanelOpen" class="chat-hint">
          当前：<strong>{{ currentKb.name }}</strong>
        </div>
        <div ref="msgsEl" class="msgs">
          <div v-for="(m, idx) in messages" :key="idx" class="msg" :class="m.role">
            <div class="bubble" :class="{ 'bubble-stream': m.role === 'assistant' && m.streaming }">
              <template v-if="m.role === 'assistant'">
                <div class="msg-row">
                  <template v-if="m.streaming && !m.content">
                    <div class="wait-block" aria-live="polite">
                      <span class="wait-label">正在生成回答</span>
                      <span class="wait-dots" aria-hidden="true">
                        <i></i><i></i><i></i>
                      </span>
                    </div>
                  </template>
                  <template v-else>
                    <span class="msg-text">{{ m.content }}</span><span v-if="m.streaming" class="caret" aria-hidden="true"></span>
                  </template>
                </div>
                <details v-if="(m.sources?.length || 0) > 0 && !m.streaming" class="sources">
                  <summary>查看引用来源（{{ m.sources.length }}）</summary>
                  <div class="source" v-for="(s, i) in m.sources" :key="i">
                    <div class="st">{{ s.title }} · chunk#{{ s.chunk_index }}</div>
                    <div class="ss">{{ s.snippet }}</div>
                  </div>
                </details>
              </template>
              <template v-else>
                <div class="msg-text">{{ m.content }}</div>
              </template>
            </div>
          </div>
        </div>

        <div class="composer">
          <input
            v-model="state.question"
            class="input"
            placeholder="请输入你的问题，例如：报销流程怎么走？"
            :disabled="!knowledgeBases.length"
            @keydown.enter.prevent="ask"
          />
          <button class="btn" :disabled="!canAsk" @click="ask">{{ state.loading ? '生成中…' : '发送' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wrap {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(200px, 248px) minmax(0, 1fr);
  gap: 0;
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  background: color-mix(in oklab, var(--bg) 94%, transparent);
}
.layout.kb-collapsed {
  grid-template-columns: 44px minmax(0, 1fr);
}
.kb-side {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid var(--border);
  background: color-mix(in oklab, var(--bg) 92%, transparent);
}
.kb-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 10px 8px;
  border-bottom: 1px solid var(--border);
}
.kb-toolbar.toolbar-collapsed {
  justify-content: center;
  padding: 8px 4px;
}
.kb-heading {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-h);
  padding-left: 4px;
}
.kb-fold {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  color: var(--text-h);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.kb-fold:hover {
  border-color: color-mix(in oklab, var(--accent) 45%, var(--border));
}
.kb-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.kb-empty {
  margin: 8px 4px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
}
.kb-card {
  text-align: left;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  cursor: pointer;
  display: grid;
  gap: 4px;
  transition:
    border-color 0.15s,
    background 0.15s;
}
.kb-card:hover {
  border-color: color-mix(in oklab, var(--accent) 40%, var(--border));
}
.kb-card.active {
  border-color: color-mix(in oklab, var(--accent) 55%, var(--border));
  background: color-mix(in oklab, var(--accent) 12%, var(--code-bg));
  box-shadow: 0 0 0 1px color-mix(in oklab, var(--accent) 25%, transparent);
}
.kb-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-h);
}
.kb-meta {
  font-size: 12px;
  color: var(--text);
}
.kb-desc {
  font-size: 11px;
  color: var(--text);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.kb-rail {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 12px 4px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
}
.rail-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-h);
  max-height: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.06em;
}
.chat {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chat-hint {
  flex-shrink: 0;
  padding: 8px 14px;
  font-size: 12px;
  color: var(--text);
  border-bottom: 1px solid var(--border);
  background: color-mix(in oklab, var(--bg) 96%, transparent);
}
.chat-hint strong {
  color: var(--text-h);
}
.msgs {
  flex: 1;
  overflow: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.msg {
  display: flex;
}
.msg.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 78%;
  border: 1px solid var(--border);
  background: var(--code-bg);
  border-radius: 14px;
  padding: 12px 12px;
  color: var(--text-h);
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.06);
}
.msg.user .bubble {
  background: color-mix(in oklab, var(--accent) 16%, var(--code-bg));
}
.msg-row {
  display: block;
  font-size: 14px;
  line-height: 1.55;
}
.msg-text {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.55;
}
.bubble-stream {
  border-color: color-mix(in oklab, var(--accent) 35%, var(--border));
  box-shadow: 0 0 0 1px color-mix(in oklab, var(--accent) 12%, transparent);
  animation: bubble-pulse 1.4s ease-in-out infinite;
}
@keyframes bubble-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 1px color-mix(in oklab, var(--accent) 10%, transparent);
  }
  50% {
    box-shadow: 0 0 0 3px color-mix(in oklab, var(--accent) 18%, transparent);
  }
}
.wait-block {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text);
  font-size: 13px;
}
.wait-label {
  font-weight: 600;
  color: var(--text-h);
}
.wait-dots {
  display: inline-flex;
  gap: 4px;
  align-items: center;
}
.wait-dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0.35;
  animation: dot-bounce 1s ease-in-out infinite;
}
.wait-dots i:nth-child(2) {
  animation-delay: 0.15s;
}
.wait-dots i:nth-child(3) {
  animation-delay: 0.3s;
}
@keyframes dot-bounce {
  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}
.caret {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  margin-left: 1px;
  vertical-align: text-bottom;
  background: var(--accent);
  border-radius: 1px;
  animation: caret-blink 0.9s step-end infinite;
}
@keyframes caret-blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
.sources {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text);
}
.source {
  border-top: 1px dashed var(--border);
  padding-top: 8px;
  margin-top: 8px;
}
.st {
  color: var(--text-h);
  font-weight: 600;
  margin-bottom: 4px;
}
.ss {
  white-space: pre-wrap;
}
.composer {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-top: 1px solid var(--border);
  background: color-mix(in oklab, var(--bg) 92%, transparent);
}
.input {
  flex: 1;
  height: 40px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  padding: 0 12px;
  color: var(--text-h);
  outline: none;
}
.btn {
  width: 92px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: var(--accent);
  color: white;
  cursor: pointer;
  font-weight: 700;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
@media (max-width: 768px) {
  .layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(200px, 1fr);
  }
  .layout.kb-collapsed {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr);
  }
  .kb-side {
    border-right: none;
    border-bottom: 1px solid var(--border);
    max-height: 42vh;
  }
  .kb-rail {
    writing-mode: horizontal-tb;
    padding: 8px 12px;
    justify-content: flex-start;
  }
  .rail-label {
    max-height: none;
    writing-mode: horizontal-tb;
    text-orientation: mixed;
  }
}
</style>
