<script setup>
/**
 * 管理员首页：统计卡片 + 图表。
 */

import { onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { api } from '../../utils/api'

const stats = ref({
  user_count: 0,
  doc_count: 0,
  chunk_count: 0,
  chat_count: 0,
  kb_count: 0,
})

const chartRef = ref(null)
let chart = null

const audits = ref([])
const auditErr = ref('')

async function loadAudits() {
  auditErr.value = ''
  try {
    const res = await api.get('/admin/audit-logs', { params: { limit: 50 } })
    audits.value = res?.data || []
  } catch (e) {
    auditErr.value = e?.message || '审计记录加载失败（请确认已执行 sql/04_commercial.sql）'
    audits.value = []
  }
}

async function load() {
  const res = await api.get('/admin/stats')
  stats.value = res?.data || stats.value

  // 简单示例图：用当前统计值做一个柱状图（入门学习用）
  const option = {
    tooltip: {},
    xAxis: {
      type: 'category',
      data: ['用户', '知识库', '文档', '切片', '问答'],
      axisLabel: { color: '#9ca3af' },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#9ca3af' },
      splitLine: { lineStyle: { color: 'rgba(156,163,175,0.15)' } },
    },
    series: [
      {
        type: 'bar',
        data: [
          stats.value.user_count,
          stats.value.kb_count,
          stats.value.doc_count,
          stats.value.chunk_count,
          stats.value.chat_count,
        ],
        itemStyle: { borderRadius: [8, 8, 0, 0] },
      },
    ],
  }
  if (chart) chart.setOption(option)
}

onMounted(async () => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
  }
  await load()
  await loadAudits()
  window.addEventListener('resize', () => chart?.resize())
})
</script>

<template>
  <div class="page">
    <div class="head">
      <p class="page-lead">用于展示系统运行与知识库规模</p>
      <button class="btn" type="button" @click="() => load().then(loadAudits)">刷新</button>
    </div>

    <div class="grid">
      <div class="card">
        <div class="k">用户数</div>
        <div class="v">{{ stats.user_count }}</div>
      </div>
      <div class="card">
        <div class="k">知识库</div>
        <div class="v">{{ stats.kb_count }}</div>
      </div>
      <div class="card">
        <div class="k">文档数</div>
        <div class="v">{{ stats.doc_count }}</div>
      </div>
      <div class="card">
        <div class="k">切片数</div>
        <div class="v">{{ stats.chunk_count }}</div>
      </div>
      <div class="card">
        <div class="k">问答数</div>
        <div class="v">{{ stats.chat_count }}</div>
      </div>
    </div>

    <div class="panel">
      <div class="ph">
        <div class="pt">统计图表</div>
        <div class="ps">入门项目中用简单柱状图即可</div>
      </div>
      <div ref="chartRef" class="chart"></div>
    </div>

    <div class="panel audit-panel">
      <div class="ph">
        <div class="pt">最近管理操作</div>
        <div class="ps">上传/删除文档、知识库与用户变更等审计条目</div>
      </div>
      <div v-if="auditErr" class="audit-err">{{ auditErr }}</div>
      <div v-else class="audit-table">
        <div class="ar head">
          <span>时间</span>
          <span>操作者</span>
          <span>动作</span>
          <span class="detail">详情</span>
        </div>
        <div v-for="a in audits" :key="a.id" class="ar">
          <span class="mono">{{ a.created_at || '—' }}</span>
          <span>{{ a.actor_user_id }}</span>
          <span class="act">{{ a.action }}</span>
          <span class="detail mono" :title="a.detail">{{ a.detail }}</span>
        </div>
        <div v-if="!audits.length" class="audit-empty">暂无审计记录</div>
      </div>
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
.grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.card {
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 14px;
  background: color-mix(in oklab, var(--bg) 90%, transparent);
}
.k {
  font-size: 12px;
  color: var(--text);
}
.v {
  margin-top: 8px;
  font-size: 26px;
  color: var(--text-h);
  font-weight: 900;
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
.chart {
  height: 360px;
}
.audit-panel .audit-err {
  padding: 12px 14px;
  font-size: 13px;
  color: #b45309;
}
.audit-table {
  padding: 0 14px 14px;
  font-size: 12px;
}
.ar {
  display: grid;
  grid-template-columns: 160px 72px 140px minmax(0, 1fr);
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  align-items: start;
}
.ar.head {
  font-weight: 700;
  color: var(--text-h);
  border-bottom-width: 2px;
}
.ar .detail {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ar .act {
  color: var(--text-h);
  font-weight: 600;
}
.mono {
  font-family: ui-monospace, monospace;
  color: var(--text);
}
.audit-empty {
  padding: 20px;
  text-align: center;
  color: var(--text);
}
@media (max-width: 960px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 1200px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>

