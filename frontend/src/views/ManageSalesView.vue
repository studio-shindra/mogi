<script setup>
import { computed, onMounted, ref } from 'vue'
import { staffPerformanceSummary } from '../api/reservations.js'

const summaries = ref([])
const loading = ref(false)
const error = ref('')

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    summaries.value = await staffPerformanceSummary()
  } catch (e) {
    error.value = e.response?.data?.detail || 'データの取得に失敗しました。'
  } finally {
    loading.value = false
  }
}

function formatDateTime(iso) {
  const d = new Date(iso)
  const m = d.getMonth() + 1
  const day = d.getDate()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${m}/${day} ${hh}:${mm}`
}

function yen(n) {
  return '¥' + (n ?? 0).toLocaleString()
}

// 並び: starts_at 昇順
const sortedSummaries = computed(() => {
  const arr = [...summaries.value]
  arr.sort((a, b) => new Date(a.starts_at) - new Date(b.starts_at))
  return arr
})

// 全体合計
const totals = computed(() => {
  const base = {
    count: 0,
    quantity: 0,
    revenue_estimate: 0,
    unpaid_count: 0,
    invite_qty: 0,
    advance_qty: 0,
    walk_in_qty: 0,
    checked_in: 0,
    not_checked_in: 0,
    capacity: 0,
    remaining: 0,
  }
  for (const s of summaries.value) {
    base.count += s.count || 0
    base.quantity += s.quantity || 0
    base.revenue_estimate += s.revenue_estimate || 0
    base.unpaid_count += s.unpaid_count || 0
    base.invite_qty += s.invite_qty || 0
    base.advance_qty += s.advance_qty || 0
    base.walk_in_qty += s.walk_in_qty || 0
    base.checked_in += s.checked_in || 0
    base.not_checked_in += s.not_checked_in || 0
    base.capacity += s.capacity || 0
    base.remaining += s.remaining || 0
  }
  return base
})
</script>

<template>
  <div class="container-fluid py-3">
    <!-- ヘッダー -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="h4 mb-0">売上サマリー</h1>
      <div class="d-flex gap-2">
        <RouterLink to="/manage" class="btn btn-sm btn-outline-secondary">受付へ戻る</RouterLink>
        <button class="btn btn-sm btn-outline-dark" :disabled="loading" @click="load">
          {{ loading ? '更新中...' : '再読み込み' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

    <!-- 上段: 全体サマリーカード -->
    <div class="row g-2 mb-4">
      <div class="col-6 col-md-4 col-lg-2">
        <div class="card h-100">
          <div class="card-body p-3">
            <div class="text-muted small">総予約件数</div>
            <div class="fs-4 fw-bold">{{ totals.count.toLocaleString() }}</div>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-4 col-lg-2">
        <div class="card h-100">
          <div class="card-body p-3">
            <div class="text-muted small">総枚数</div>
            <div class="fs-4 fw-bold">{{ totals.quantity.toLocaleString() }}</div>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-4 col-lg-2">
        <div class="card h-100 border-primary">
          <div class="card-body p-3">
            <div class="text-muted small">売上概算</div>
            <div class="fs-4 fw-bold text-primary">{{ yen(totals.revenue_estimate) }}</div>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-4 col-lg-2">
        <div class="card h-100">
          <div class="card-body p-3">
            <div class="text-muted small">当日精算</div>
            <div class="fs-4 fw-bold">{{ totals.unpaid_count.toLocaleString() }}<span class="fs-6 text-muted">件</span></div>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-4 col-lg-2">
        <div class="card h-100">
          <div class="card-body p-3">
            <div class="text-muted small">招待</div>
            <div class="fs-4 fw-bold">{{ totals.invite_qty.toLocaleString() }}<span class="fs-6 text-muted">枚</span></div>
          </div>
        </div>
      </div>
      <div class="col-6 col-md-4 col-lg-2">
        <div class="card h-100">
          <div class="card-body p-3">
            <div class="text-muted small">来場済み</div>
            <div class="fs-4 fw-bold">{{ totals.checked_in.toLocaleString() }}<span class="fs-6 text-muted">枚</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 中段: 公演別サマリー表 -->
    <h2 class="h6 mb-2">公演別サマリー</h2>

    <div v-if="loading && !summaries.length" class="text-center py-4">
      <div class="spinner-border spinner-border-sm" />
    </div>

    <div v-else-if="sortedSummaries.length" class="table-responsive mb-4">
      <table class="table table-sm table-bordered align-middle mb-0">
        <thead class="table-light">
          <tr class="text-center">
            <th rowspan="2" class="align-middle">公演日時</th>
            <th rowspan="2" class="align-middle">件数</th>
            <th rowspan="2" class="align-middle">枚数</th>
            <th colspan="3" class="text-center">販売ルート（枚）</th>
            <th rowspan="2" class="align-middle">売上概算</th>
            <th rowspan="2" class="align-middle">当日精算</th>
            <th colspan="2" class="text-center">入場（枚）</th>
            <th rowspan="2" class="align-middle">残席</th>
          </tr>
          <tr class="text-center small">
            <th>前売</th>
            <th>当日</th>
            <th>招待</th>
            <th>来場</th>
            <th>未入場</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in sortedSummaries" :key="s.performance_id">
            <td>
              <div class="fw-bold small">{{ formatDateTime(s.starts_at) }}</div>
              <div class="text-muted" style="font-size: 0.75rem;">{{ s.label }}</div>
            </td>
            <td class="text-end">{{ (s.count ?? 0).toLocaleString() }}</td>
            <td class="text-end">{{ (s.quantity ?? 0).toLocaleString() }}</td>
            <td class="text-end">{{ (s.advance_qty ?? 0).toLocaleString() }}</td>
            <td class="text-end">{{ (s.walk_in_qty ?? 0).toLocaleString() }}</td>
            <td class="text-end">{{ (s.invite_qty ?? 0).toLocaleString() }}</td>
            <td class="text-end fw-bold text-primary">{{ yen(s.revenue_estimate) }}</td>
            <td class="text-end">
              <span v-if="s.unpaid_count > 0" class="badge bg-warning text-dark">
                {{ s.unpaid_count }}件
              </span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-end">{{ (s.checked_in ?? 0).toLocaleString() }}</td>
            <td class="text-end fw-bold">{{ (s.not_checked_in ?? 0).toLocaleString() }}</td>
            <td class="text-end">{{ (s.remaining ?? 0).toLocaleString() }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="table-light fw-bold">
            <td>合計</td>
            <td class="text-end">{{ totals.count.toLocaleString() }}</td>
            <td class="text-end">{{ totals.quantity.toLocaleString() }}</td>
            <td class="text-end">{{ totals.advance_qty.toLocaleString() }}</td>
            <td class="text-end">{{ totals.walk_in_qty.toLocaleString() }}</td>
            <td class="text-end">{{ totals.invite_qty.toLocaleString() }}</td>
            <td class="text-end text-primary">{{ yen(totals.revenue_estimate) }}</td>
            <td class="text-end">
              <span v-if="totals.unpaid_count > 0">{{ totals.unpaid_count }}件</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-end">{{ totals.checked_in.toLocaleString() }}</td>
            <td class="text-end">{{ totals.not_checked_in.toLocaleString() }}</td>
            <td class="text-end">{{ totals.remaining.toLocaleString() }}</td>
          </tr>
        </tfoot>
      </table>
    </div>

    <div v-else class="text-center text-muted py-4">公演データがありません</div>

    <!-- 注記 -->
    <div class="text-muted small">
      <p class="mb-1">※ 売上概算は「招待=0円 / 当日券=price_cash / その他=price_card」で算出した概算値です。</p>
      <p class="mb-1">※ 集計対象は applied / cancelled を除いた予約です。</p>
      <p class="mb-0">※ 当日精算は `payment_status=unpaid` の件数です。</p>
    </div>
  </div>
</template>
