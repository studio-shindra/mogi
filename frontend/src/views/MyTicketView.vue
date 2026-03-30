<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { IconTicket, IconSearch } from '@tabler/icons-vue'

const router = useRouter()
const tokenInput = ref('')
const error = ref('')

function handleLookup() {
  const token = tokenInput.value.trim()
  if (!token) {
    error.value = '予約番号を入力してください'
    return
  }
  error.value = ''
  router.push({ name: 'reservation-confirm', params: { token } })
}
</script>

<template>
  <div class="container py-5" style="max-width: 640px; padding-top: 56px">
    <h1 class="fs-4 fw-bold mb-2">マイチケット</h1>
    <p class="text-muted small mb-4">
      予約完了時に届いたメールのリンク、または予約番号から確認できます。
    </p>

    <!-- 予約番号で検索 -->
    <div class="card mb-4">
      <div class="card-body">
        <label class="form-label small text-muted">予約番号で確認</label>
        <form @submit.prevent="handleLookup" class="d-flex gap-2">
          <div class="input-group">
            <span class="input-group-text bg-white">
              <IconSearch :size="18" class="text-muted" />
            </span>
            <input
              type="text"
              class="form-control"
              placeholder="予約番号を入力"
              v-model="tokenInput"
            />
          </div>
          <button type="submit" class="btn btn-primary flex-shrink-0">確認</button>
        </form>
        <div v-if="error" class="text-danger small mt-2">{{ error }}</div>
      </div>
    </div>

    <!-- 案内 -->
    <div class="text-center py-4">
      <IconTicket :size="48" class="text-muted mb-3" stroke-width="1" />
      <p class="text-muted small">
        予約完了メールに記載のURLから<br>直接チケットを確認できます。
      </p>
    </div>
  </div>
</template>
