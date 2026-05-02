<script setup>
/**
 * 知识库管理：列表、新建（独立 Chroma collection）。
 */

import { onMounted, reactive, ref } from 'vue'
import { api } from '../utils/api'

const rows = ref([])
const loading = ref(false)
const err = ref('')
const showCreate = ref(false)
const createForm = reactive({ name: '', description: '' })
const createErr = ref('')
const creating = ref(false)

const deleteTarget = ref(null)
const showKbBlock = ref(false)
const kbBlockMsg = ref('')
const showKbConfirm = ref(false)
const delKbLoading = ref(false)
const kbDeleteErr = ref('')

async function load() {
  err.value = ''
  loading.value = true
  try {
    const res = await api.get('/admin/knowledge-bases')
    rows.value = res?.data || []
  } catch (e) {
    err.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  createForm.name = ''
  createForm.description = ''
  createErr.value = ''
  showCreate.value = true
}

function closeCreate() {
  if (creating.value) return
  showCreate.value = false
}

async function submitCreate() {
  createErr.value = ''
  const name = createForm.name.trim()
  if (!name) {
    createErr.value = '请填写知识库名称'
    return
  }
  creating.value = true
  try {
    await api.post('/admin/knowledge-bases', {
      name,
      description: createForm.description.trim(),
    })
    creating.value = false
    closeCreate()
    await load()
  } catch (e) {
    createErr.value = e?.message || '创建失败'
  } finally {
    creating.value = false
  }
}

function clickDeleteKb(row) {
  if (row.id === 1) return
  deleteTarget.value = row
  if (row.doc_count > 0) {
    kbBlockMsg.value = `该知识库下仍有 ${row.doc_count} 个文档，请先在「文档管理」中删除全部文档后再删除知识库。`
    showKbBlock.value = true
    return
  }
  kbDeleteErr.value = ''
  showKbConfirm.value = true
}

function closeKbBlock() {
  showKbBlock.value = false
  deleteTarget.value = null
}

function closeKbConfirm() {
  if (delKbLoading.value) return
  showKbConfirm.value = false
  deleteTarget.value = null
}

async function confirmDeleteKb() {
  if (!deleteTarget.value) return
  kbDeleteErr.value = ''
  delKbLoading.value = true
  try {
    await api.delete(`/admin/knowledge-bases/${deleteTarget.value.id}`)
    delKbLoading.value = false
    showKbConfirm.value = false
    deleteTarget.value = null
    await load()
  } catch (e) {
    kbDeleteErr.value = e?.message || '删除失败'
  } finally {
    delKbLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="head">
      <p class="page-lead">每个知识库对应独立向量集合；文档上传时须指定归属知识库</p>
      <div class="actions">
        <button type="button" class="btn" :disabled="loading" @click="load">刷新</button>
        <button type="button" class="primary" @click="openCreate">新建知识库</button>
      </div>
    </div>

    <div v-if="err" class="err">{{ err }}</div>

    <div class="panel">
      <div class="ph">
        <div class="pt">知识库列表</div>
        <div class="ps">collection 名用于 Chroma；默认库与历史配置 enterprise_qa 一致</div>
      </div>
      <div class="table-wrap">
        <table class="tb">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>说明</th>
              <th>向量集合</th>
              <th>文档数</th>
              <th>创建时间</th>
              <th class="col-act">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rows" :key="r.id">
              <td>{{ r.id }}</td>
              <td class="strong">{{ r.name }}</td>
              <td class="desc">{{ r.description || '—' }}</td>
              <td><code class="code">{{ r.collection_name }}</code></td>
              <td>{{ r.doc_count }}</td>
              <td class="muted">{{ r.created_at || '—' }}</td>
              <td class="col-act">
                <button
                  v-if="r.id !== 1"
                  type="button"
                  class="btn-del"
                  @click="clickDeleteKb(r)"
                >
                  删除
                </button>
                <span v-else class="muted tiny">—</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!loading && !rows.length" class="empty">暂无知识库，请先执行数据库迁移或点击「新建知识库」</div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showCreate" class="modal-mask" @click.self="closeCreate">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="kb-create-title">
          <div class="modal-h">
            <h2 id="kb-create-title" class="modal-title">新建知识库</h2>
            <button type="button" class="icon-close" aria-label="关闭" :disabled="creating" @click="closeCreate">×</button>
          </div>
          <div class="modal-b">
            <label class="fld">
              <span>名称 <em class="req">*</em></span>
              <input v-model.trim="createForm.name" placeholder="例如：人事制度库" maxlength="128" />
            </label>
            <label class="fld">
              <span>说明</span>
              <textarea v-model.trim="createForm.description" rows="3" placeholder="可选，简要描述用途" maxlength="512" />
            </label>
            <p v-if="createErr" class="cerr">{{ createErr }}</p>
          </div>
          <div class="modal-f">
            <button type="button" class="btn" :disabled="creating" @click="closeCreate">取消</button>
            <button type="button" class="primary" :disabled="creating" @click="submitCreate">
              {{ creating ? '提交中…' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showKbBlock" class="modal-mask" @click.self="closeKbBlock">
        <div class="modal modal-sm" role="dialog" aria-modal="true">
          <div class="modal-h">
            <h2 class="modal-title">无法删除</h2>
            <button type="button" class="icon-close" aria-label="关闭" @click="closeKbBlock">×</button>
          </div>
          <div class="modal-b">
            <p class="tip">{{ kbBlockMsg }}</p>
          </div>
          <div class="modal-f">
            <button type="button" class="primary" @click="closeKbBlock">知道了</button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showKbConfirm" class="modal-mask" @click.self="closeKbConfirm">
        <div class="modal modal-sm" role="dialog" aria-modal="true">
          <div class="modal-h">
            <h2 class="modal-title">确认删除知识库</h2>
            <button type="button" class="icon-close" aria-label="关闭" :disabled="delKbLoading" @click="closeKbConfirm">
              ×
            </button>
          </div>
          <div class="modal-b">
            <p class="tip">
              确定删除知识库「<strong>{{ deleteTarget?.name }}</strong>」？将删除对应的向量集合，且<strong>不可恢复</strong>。
            </p>
            <p v-if="kbDeleteErr" class="cerr">{{ kbDeleteErr }}</p>
          </div>
          <div class="modal-f">
            <button type="button" class="btn" :disabled="delKbLoading" @click="closeKbConfirm">取消</button>
            <button type="button" class="btn-del-solid" :disabled="delKbLoading" @click="confirmDeleteKb">
              {{ delKbLoading ? '删除中…' : '确定删除' }}
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
  flex-shrink: 0;
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
.table-wrap {
  overflow-x: auto;
}
.tb {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.tb th,
.tb td {
  padding: 12px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.tb th {
  color: var(--text);
  font-weight: 700;
  background: color-mix(in oklab, var(--bg) 88%, transparent);
}
.tb tbody tr:hover td {
  background: color-mix(in oklab, var(--accent) 6%, transparent);
}
.strong {
  font-weight: 700;
  color: var(--text-h);
}
.desc {
  color: var(--text);
  max-width: 280px;
}
.code {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 6px;
  background: var(--code-bg);
  color: var(--text-h);
}
.muted {
  color: var(--text);
  font-size: 12px;
}
.empty {
  padding: 28px 16px;
  text-align: center;
  color: var(--text);
  font-size: 14px;
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
  max-width: 440px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  max-height: min(90vh, 560px);
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
.icon-close:hover {
  background: var(--code-bg);
  color: var(--text-h);
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
.fld textarea {
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  color: var(--text-h);
  padding: 10px 12px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
}
.fld textarea {
  resize: vertical;
  min-height: 72px;
}
.cerr {
  margin: 0;
  font-size: 13px;
  color: #ef4444;
}
.col-act {
  width: 88px;
  white-space: nowrap;
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
.tiny {
  font-size: 12px;
}
.modal-sm {
  max-width: 400px;
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
</style>
