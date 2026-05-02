<script setup>
/**
 * 文档管理：列表 + 弹窗上传（必选知识库）。
 */

import { onMounted, ref } from 'vue'
import { api } from '../../utils/api'

const docs = ref([])
const knowledgeBases = ref([])
const loading = ref(false)
const listErr = ref('')

const showUpload = ref(false)
const uploadKbId = ref(null)
const title = ref('')
const selectedFile = ref(null)
const fileInputRef = ref(null)
const uploadLoading = ref(false)
const uploadErr = ref('')

const docDeleteTarget = ref(null)
const showDocConfirm = ref(false)
const docDeleteLoading = ref(false)
const docDeleteErr = ref('')

const infoMsg = ref('')
const reindexBusy = ref(null)

async function reindexDoc(d) {
  reindexBusy.value = d.id
  listErr.value = ''
  try {
    await api.post(`/admin/docs/${d.id}/reindex`)
    infoMsg.value = '已提交重建索引任务，请稍后刷新查看状态'
    await loadDocs()
  } catch (e) {
    listErr.value = e?.message || '重建失败'
  } finally {
    reindexBusy.value = null
  }
}

async function loadDocs() {
  listErr.value = ''
  loading.value = true
  try {
    const res = await api.get('/admin/docs')
    docs.value = res?.data || []
  } catch (e) {
    listErr.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadKnowledgeBases() {
  try {
    const res = await api.get('/chat/knowledge-bases')
    knowledgeBases.value = res?.data || []
    if (uploadKbId.value == null && knowledgeBases.value.length) {
      uploadKbId.value = knowledgeBases.value[0].id
    }
  } catch {
    knowledgeBases.value = []
  }
}

function openUpload() {
  uploadErr.value = ''
  title.value = ''
  clearFile()
  loadKnowledgeBases().then(() => {
    if (uploadKbId.value == null && knowledgeBases.value.length) {
      uploadKbId.value = knowledgeBases.value[0].id
    }
  })
  showUpload.value = true
}

function closeUpload() {
  if (uploadLoading.value) return
  showUpload.value = false
}

function onFileChange(e) {
  const input = e.target
  selectedFile.value = input.files?.[0] ?? null
}

function pickFile() {
  fileInputRef.value?.click()
}

function clearFile() {
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

async function submitUpload() {
  uploadErr.value = ''
  if (uploadKbId.value == null) {
    uploadErr.value = '请选择知识库'
    return
  }
  if (!selectedFile.value) {
    uploadErr.value = '请选择文件'
    return
  }
  uploadLoading.value = true
  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)
    fd.append('knowledge_base_id', String(uploadKbId.value))
    if (title.value.trim()) fd.append('title', title.value.trim())
    const res = await api.post('/admin/docs/upload', fd)
    infoMsg.value = res?.data?.document?.message || '已提交后台入库'
    title.value = ''
    clearFile()
    closeUpload()
    await loadDocs()
  } catch (e) {
    uploadErr.value = e?.message || '上传失败'
  } finally {
    uploadLoading.value = false
  }
}

function requestDeleteDoc(d) {
  docDeleteTarget.value = d
  docDeleteErr.value = ''
  showDocConfirm.value = true
}

function closeDocConfirm() {
  if (docDeleteLoading.value) return
  showDocConfirm.value = false
  docDeleteTarget.value = null
}

async function confirmDeleteDoc() {
  if (!docDeleteTarget.value) return
  docDeleteErr.value = ''
  docDeleteLoading.value = true
  try {
    await api.delete(`/admin/docs/${docDeleteTarget.value.id}`)
    closeDocConfirm()
    await loadDocs()
    await loadKnowledgeBases()
  } catch (e) {
    docDeleteErr.value = e?.message || '删除失败'
  } finally {
    docDeleteLoading.value = false
  }
}

onMounted(async () => {
  await loadKnowledgeBases()
  await loadDocs()
})
</script>

<template>
  <div class="page">
    <div class="head">
      <p class="page-lead">上传后会解析、切分并写入对应知识库的 Chroma 向量集合</p>
      <div class="actions">
        <button type="button" class="btn" :disabled="loading" @click="loadDocs">刷新</button>
        <button type="button" class="primary" @click="openUpload">上传文档</button>
      </div>
    </div>

    <div v-if="infoMsg" class="info">{{ infoMsg }}</div>
    <div v-if="listErr" class="err">{{ listErr }}</div>

    <div class="panel">
      <div class="ph">
        <div class="pt">文档列表</div>
        <div class="ps">可用于确认入库状态与所属知识库</div>
      </div>
      <div class="table">
        <div class="tr head">
          <div>ID</div>
          <div>知识库</div>
          <div>标题</div>
          <div>类型</div>
          <div>状态</div>
          <div>创建时间</div>
          <div class="col-act">操作</div>
        </div>
        <div class="tr" v-for="d in docs" :key="d.id">
          <div>{{ d.id }}</div>
          <div class="kb">{{ d.knowledge_base_name || '—' }}</div>
          <div class="title">{{ d.title }}</div>
          <div>{{ d.file_type }}</div>
          <div>
            <span
              class="badge"
              :class="d.status"
              :title="d.ingest_error ? `失败原因：${d.ingest_error}` : ''"
            >{{ d.status }}</span>
          </div>
          <div class="time">{{ d.created_at || '-' }}</div>
          <div class="col-act act-btns">
            <button
              v-if="d.can_reindex"
              type="button"
              class="btn-reidx"
              :disabled="reindexBusy === d.id"
              @click="reindexDoc(d)"
            >
              {{ reindexBusy === d.id ? '提交中…' : '重建索引' }}
            </button>
            <button type="button" class="btn-del" @click="requestDeleteDoc(d)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showUpload" class="modal-mask" @click.self="closeUpload">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="upload-title">
          <div class="modal-h">
            <h2 id="upload-title" class="modal-title">上传文档</h2>
            <button type="button" class="icon-close" aria-label="关闭" :disabled="uploadLoading" @click="closeUpload">
              ×
            </button>
          </div>
          <div class="modal-b">
            <label class="fld">
              <span>知识库 <em class="req">*</em></span>
              <select v-model.number="uploadKbId" class="sel">
                <option v-for="k in knowledgeBases" :key="k.id" :value="k.id">
                  {{ k.name }}（{{ k.doc_count }} 个文档）
                </option>
              </select>
            </label>
            <label class="fld">
              <span>标题（可选）</span>
              <input v-model="title" placeholder="不填则使用文件名" />
            </label>
            <div class="fld">
              <span>文件 <em class="req">*</em></span>
              <div class="file-row">
                <input
                  ref="fileInputRef"
                  type="file"
                  class="file-native"
                  accept=".txt,.md,.pdf,.docx"
                  @change="onFileChange"
                />
                <button type="button" class="pick" @click="pickFile">选择文件</button>
                <span class="fname" :class="{ muted: !selectedFile }">
                  {{ selectedFile ? selectedFile.name : '未选择文件' }}
                </span>
                <button v-if="selectedFile" type="button" class="clear-file" @click="clearFile">清除</button>
              </div>
              <div class="hint">支持：txt / md / pdf / docx</div>
            </div>
            <p v-if="uploadErr" class="cerr">{{ uploadErr }}</p>
          </div>
          <div class="modal-f">
            <button type="button" class="btn" :disabled="uploadLoading" @click="closeUpload">取消</button>
            <button type="button" class="primary" :disabled="uploadLoading" @click="submitUpload">
              {{ uploadLoading ? '上传中…' : '上传（后台入库）' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showDocConfirm" class="modal-mask" @click.self="closeDocConfirm">
        <div class="modal modal-sm" role="dialog" aria-modal="true">
          <div class="modal-h">
            <h2 class="modal-title">确认删除文档</h2>
            <button type="button" class="icon-close" aria-label="关闭" :disabled="docDeleteLoading" @click="closeDocConfirm">
              ×
            </button>
          </div>
          <div class="modal-b">
            <p class="tip">
              确定删除「<strong>{{ docDeleteTarget?.title }}</strong>」？将同步移除向量库中的切片与数据库中的切片记录，<strong>不可恢复</strong>。
            </p>
            <p v-if="docDeleteErr" class="cerr">{{ docDeleteErr }}</p>
          </div>
          <div class="modal-f">
            <button type="button" class="btn" :disabled="docDeleteLoading" @click="closeDocConfirm">取消</button>
            <button type="button" class="btn-del-solid" :disabled="docDeleteLoading" @click="confirmDeleteDoc">
              {{ docDeleteLoading ? '删除中…' : '确定删除' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
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
.actions {
  display: flex;
  gap: 10px;
}
.btn {
  height: 36px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  color: var(--text-h);
  cursor: pointer;
  font-size: 13px;
}
.primary {
  height: 36px;
  padding: 0 16px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: var(--accent);
  color: white;
  font-weight: 700;
  cursor: pointer;
  font-size: 13px;
}
.err {
  font-size: 13px;
  color: #ef4444;
}
.panel {
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  background: color-mix(in oklab, var(--bg) 90%, transparent);
}
.ph {
  padding: 14px;
  border-bottom: 1px solid var(--border);
  background: color-mix(in oklab, var(--bg) 92%, transparent);
}
.pt {
  color: var(--text-h);
  font-weight: 800;
}
.ps {
  font-size: 12px;
  color: var(--text);
  margin-top: 4px;
}
.table {
  padding: 12px;
  display: grid;
  gap: 8px;
}
.tr {
  display: grid;
  grid-template-columns: 56px minmax(88px, 0.85fr) 1fr 72px 92px 168px 76px;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--code-bg);
  font-size: 13px;
}
.tr.head {
  background: color-mix(in oklab, var(--bg) 85%, transparent);
  color: var(--text);
  font-weight: 700;
}
.kb {
  color: var(--text-h);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.title {
  color: var(--text-h);
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.time {
  color: var(--text);
  font-size: 12px;
}
.badge {
  display: inline-flex;
  padding: 2px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: color-mix(in oklab, var(--bg) 85%, transparent);
  font-size: 12px;
}
.badge.indexed {
  border-color: rgba(34, 197, 94, 0.35);
}
.badge.failed {
  border-color: rgba(239, 68, 68, 0.4);
}
.badge.pending,
.badge.processing {
  border-color: rgba(234, 179, 8, 0.45);
}
.badge.uploaded {
  border-color: rgba(148, 163, 184, 0.45);
}
.info {
  font-size: 13px;
  color: #15803d;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(34, 197, 94, 0.35);
  background: color-mix(in oklab, #22c55e 8%, var(--code-bg));
}
.act-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
}
.btn-reidx {
  height: 30px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid color-mix(in oklab, var(--accent) 40%, var(--border));
  background: color-mix(in oklab, var(--accent) 10%, var(--code-bg));
  color: var(--text-h);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.btn-reidx:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.45);
  display: grid;
  place-items: center;
  padding: 20px;
  box-sizing: border-box;
}
.modal {
  width: 100%;
  max-width: 480px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  max-height: min(92vh, 620px);
}
.modal-h {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid var(--border);
}
.modal-title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: var(--text-h);
}
.icon-close {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  border-radius: 10px;
}
.icon-close:hover:not(:disabled) {
  background: var(--code-bg);
  color: var(--text-h);
}
.icon-close:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.modal-b {
  padding: 16px 18px;
  display: grid;
  gap: 14px;
  overflow-y: auto;
}
.modal-f {
  padding: 14px 18px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.fld {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--text);
}
.fld .req {
  color: #ef4444;
  font-style: normal;
}
.fld input,
.fld .sel {
  height: 40px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  color: var(--text-h);
  padding: 0 12px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
}
.hint {
  font-size: 12px;
  color: var(--text);
  margin-top: 4px;
}
.file-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  min-height: 40px;
  padding: 6px 10px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  box-sizing: border-box;
}
.file-native {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.pick {
  flex-shrink: 0;
  height: 32px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid color-mix(in oklab, var(--accent) 45%, var(--border));
  background: color-mix(in oklab, var(--accent) 14%, var(--code-bg));
  color: var(--text-h);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.pick:hover {
  background: color-mix(in oklab, var(--accent) 22%, var(--code-bg));
}
.fname {
  flex: 1;
  min-width: 120px;
  font-size: 13px;
  color: var(--text-h);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fname.muted {
  color: var(--text);
}
.clear-file {
  flex-shrink: 0;
  height: 32px;
  padding: 0 10px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: color-mix(in oklab, var(--bg) 88%, transparent);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
}
.clear-file:hover {
  border-color: color-mix(in oklab, #ef4444 30%, var(--border));
  color: var(--text-h);
}
.cerr {
  margin: 0;
  font-size: 13px;
  color: #ef4444;
}
.col-act {
  text-align: right;
}
.btn-del {
  height: 30px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid color-mix(in oklab, #ef4444 35%, var(--border));
  background: color-mix(in oklab, #ef4444 8%, var(--code-bg));
  color: #b91c1c;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.btn-del:hover {
  background: color-mix(in oklab, #ef4444 16%, var(--code-bg));
}
.modal-sm {
  max-width: 420px;
}
.tip {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--text-h);
}
.btn-del-solid {
  height: 36px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: #dc2626;
  color: white;
  font-weight: 700;
  cursor: pointer;
  font-size: 13px;
}
.btn-del-solid:hover:not(:disabled) {
  background: #b91c1c;
}
.btn-del-solid:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
@media (max-width: 960px) {
  .tr {
    grid-template-columns: 56px 1fr;
  }
  .tr.head {
    display: none;
  }
}
</style>
