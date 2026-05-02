<script setup>
/**
 * 用户管理（管理员）：列表、编辑、删除。
 */

import { onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { api } from '../utils/api'

const auth = useAuthStore()

const users = ref([])
const errorMsg = ref('')

const showEdit = ref(false)
const editTarget = ref(null)
const editForm = reactive({ username: '', role: 'user', password: '' })
const editErr = ref('')
const editLoading = ref(false)

const showDelete = ref(false)
const deleteTarget = ref(null)
const deleteErr = ref('')
const deleteLoading = ref(false)

async function load() {
  errorMsg.value = ''
  try {
    const res = await api.get('/admin/users')
    users.value = res?.data || []
  } catch (e) {
    errorMsg.value = e?.message || '加载失败'
  }
}

function openEdit(u) {
  editTarget.value = u
  editForm.username = u.username
  editForm.role = u.role
  editForm.password = ''
  editErr.value = ''
  showEdit.value = true
}

function closeEdit() {
  if (editLoading.value) return
  showEdit.value = false
  editTarget.value = null
}

async function submitEdit() {
  if (!editTarget.value) return
  editErr.value = ''
  const un = editForm.username.trim()
  if (!un) {
    editErr.value = '用户名不能为空'
    return
  }
  editLoading.value = true
  try {
    const body = { username: un, role: editForm.role }
    if (editForm.password.trim()) body.password = editForm.password
    await api.patch(`/admin/users/${editTarget.value.id}`, body)
    closeEdit()
    await load()
  } catch (e) {
    editErr.value = e?.message || '保存失败'
  } finally {
    editLoading.value = false
  }
}

function openDelete(u) {
  deleteTarget.value = u
  deleteErr.value = ''
  showDelete.value = true
}

function closeDelete() {
  if (deleteLoading.value) return
  showDelete.value = false
  deleteTarget.value = null
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleteErr.value = ''
  deleteLoading.value = true
  try {
    await api.delete(`/admin/users/${deleteTarget.value.id}`)
    closeDelete()
    await load()
  } catch (e) {
    deleteErr.value = e?.message || '删除失败'
  } finally {
    deleteLoading.value = false
  }
}

function canDelete(u) {
  if (auth.user?.id === u.id) return false
  if (u.role === 'admin') {
    const admins = users.value.filter((x) => x.role === 'admin')
    if (admins.length <= 1) return false
  }
  return true
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="head">
      <p class="page-lead">系统登录账号与角色；不能删除自己或唯一管理员</p>
      <button class="btn" type="button" @click="load">刷新</button>
    </div>
    <div v-if="errorMsg" class="err">{{ errorMsg }}</div>
    <div class="panel">
      <div class="table">
        <div class="tr th">
          <div>ID</div>
          <div>用户名</div>
          <div>角色</div>
          <div>创建时间</div>
          <div class="col-act">操作</div>
        </div>
        <div v-for="u in users" :key="u.id" class="tr">
          <div>{{ u.id }}</div>
          <div class="strong">{{ u.username }}</div>
          <div>
            <span class="badge">{{ u.role }}</span>
          </div>
          <div class="muted">{{ u.created_at || '-' }}</div>
          <div class="col-act">
            <button type="button" class="btn-sm" @click="openEdit(u)">修改</button>
            <button
              v-if="canDelete(u)"
              type="button"
              class="btn-sm danger"
              @click="openDelete(u)"
            >
              删除
            </button>
            <span v-else class="muted tiny" :title="auth.user?.id === u.id ? '不可删除当前登录账号' : '不可删除唯一管理员'">
              —
            </span>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showEdit" class="modal-mask" @click.self="closeEdit">
        <div class="modal" role="dialog" aria-modal="true">
          <div class="modal-h">
            <h2 class="modal-title">修改用户</h2>
            <button type="button" class="icon-close" aria-label="关闭" :disabled="editLoading" @click="closeEdit">×</button>
          </div>
          <div class="modal-b">
            <label class="fld">
              <span>用户名</span>
              <input v-model.trim="editForm.username" maxlength="64" autocomplete="off" />
            </label>
            <label class="fld">
              <span>角色</span>
              <select v-model="editForm.role" class="sel">
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </label>
            <label class="fld">
              <span>新密码</span>
              <input v-model="editForm.password" type="password" autocomplete="new-password" placeholder="不修改请留空" />
            </label>
            <p v-if="editErr" class="cerr">{{ editErr }}</p>
          </div>
          <div class="modal-f">
            <button type="button" class="btn" :disabled="editLoading" @click="closeEdit">取消</button>
            <button type="button" class="primary" :disabled="editLoading" @click="submitEdit">
              {{ editLoading ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showDelete" class="modal-mask" @click.self="closeDelete">
        <div class="modal modal-sm" role="dialog" aria-modal="true">
          <div class="modal-h">
            <h2 class="modal-title">确认删除用户</h2>
            <button type="button" class="icon-close" aria-label="关闭" :disabled="deleteLoading" @click="closeDelete">×</button>
          </div>
          <div class="modal-b">
            <p class="tip">
              确定删除用户「<strong>{{ deleteTarget?.username }}</strong>」？此操作<strong>不可恢复</strong>。
            </p>
            <p v-if="deleteErr" class="cerr">{{ deleteErr }}</p>
          </div>
          <div class="modal-f">
            <button type="button" class="btn" :disabled="deleteLoading" @click="closeDelete">取消</button>
            <button type="button" class="btn-del-solid" :disabled="deleteLoading" @click="confirmDelete">
              {{ deleteLoading ? '删除中…' : '确定删除' }}
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
.panel {
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 12px;
  background: color-mix(in oklab, var(--bg) 90%, transparent);
}
.table {
  display: grid;
  gap: 8px;
}
.tr {
  display: grid;
  grid-template-columns: 72px 1fr 120px 1fr 140px;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--code-bg);
  font-size: 13px;
}
.tr.th {
  background: color-mix(in oklab, var(--bg) 85%, transparent);
  color: var(--text);
  font-weight: 700;
}
.strong {
  color: var(--text-h);
  font-weight: 700;
}
.muted {
  color: var(--text);
  font-size: 12px;
}
.tiny {
  font-size: 12px;
}
.badge {
  display: inline-flex;
  padding: 2px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  font-size: 12px;
}
.col-act {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}
.btn-sm {
  height: 30px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--code-bg);
  color: var(--text-h);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.btn-sm.danger {
  border-color: color-mix(in oklab, #ef4444 35%, var(--border));
  color: #b91c1c;
  background: color-mix(in oklab, #ef4444 8%, var(--code-bg));
}
.btn-sm.danger:hover {
  background: color-mix(in oklab, #ef4444 16%, var(--code-bg));
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
  max-width: 420px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--bg);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  max-height: min(90vh, 560px);
}
.modal-sm {
  max-width: 400px;
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
.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.cerr {
  margin: 0;
  font-size: 13px;
  color: #ef4444;
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
@media (max-width: 720px) {
  .tr {
    grid-template-columns: 56px 1fr;
  }
  .tr.th {
    display: none;
  }
}
</style>
