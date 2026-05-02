/**
 * 智能问答流式请求（POST /chat/ask，响应为 NDJSON 行）。
 */

function apiBase() {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'
}

function bearer() {
  const token = localStorage.getItem('enterprise_qa_token') || ''
  return token ? `Bearer ${token}` : ''
}

/**
 * @param {object} opts
 * @param {string} opts.question
 * @param {number} opts.knowledgeBaseId
 * @param {(sources: object[]) => void} [opts.onMeta]
 * @param {(text: string) => void} [opts.onToken]
 * @param {() => void} [opts.onDone]
 */
export async function streamChatAsk({ question, knowledgeBaseId, onMeta, onToken, onDone }) {
  const res = await fetch(`${apiBase()}/chat/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/x-ndjson',
      Authorization: bearer(),
    },
    body: JSON.stringify({
      question,
      knowledge_base_id: knowledgeBaseId,
    }),
  })

  if (!res.ok) {
    let msg = `请求失败 (${res.status})`
    try {
      const j = await res.json()
      if (j?.message) msg = j.message
    } catch {
      try {
        msg = await res.text()
      } catch {
        /* ignore */
      }
    }
    throw new Error(msg)
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('无法读取响应流')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      const s = line.trim()
      if (!s) continue
      let obj
      try {
        obj = JSON.parse(s)
      } catch {
        throw new Error('流数据解析失败')
      }
      if (obj.type === 'meta') {
        onMeta?.(obj.sources || [])
      } else if (obj.type === 'token') {
        const t = obj.text ?? ''
        if (t) onToken?.(t)
      } else if (obj.type === 'done') {
        onDone?.()
        return
      } else if (obj.type === 'error') {
        throw new Error(obj.message || '问答失败')
      }
    }
  }

  for (const line of buffer.split('\n')) {
    const s = line.trim()
    if (!s) continue
    const obj = JSON.parse(s)
    if (obj.type === 'error') throw new Error(obj.message || '问答失败')
    if (obj.type === 'done') {
      onDone?.()
      return
    }
    if (obj.type === 'meta') onMeta?.(obj.sources || [])
    if (obj.type === 'token') {
      const t = obj.text ?? ''
      if (t) onToken?.(t)
    }
  }
}
