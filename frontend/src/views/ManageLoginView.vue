<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '../api/client.js'

const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  // CSRF クッキーを発行させる。既にログイン済みならダッシュボードへ飛ばす。
  try {
    const res = await client.get('/auth/me/')
    if (res.data?.is_staff) {
      const next = typeof route.query.next === 'string' ? route.query.next : '/manage'
      router.replace(next)
    }
  } catch {
    // noop
  }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await client.post('/auth/login/', {
      username: username.value,
      password: password.value,
    })
    const next = typeof route.query.next === 'string' ? route.query.next : '/manage'
    router.replace(next)
  } catch (e) {
    error.value = e.response?.data?.detail || 'ログインに失敗しました。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 420px;">
    <h1 class="h5 mb-4 text-center">管理画面ログイン</h1>
    <form @submit.prevent="submit">
      <div class="mb-3">
        <label class="form-label small">ユーザー名</label>
        <input
          v-model="username"
          type="text"
          class="form-control"
          autocomplete="username"
          autocapitalize="off"
          autocorrect="off"
          required
        />
      </div>
      <div class="mb-3">
        <label class="form-label small">パスワード</label>
        <input
          v-model="password"
          type="password"
          class="form-control"
          autocomplete="current-password"
          required
        />
      </div>
      <div v-if="error" class="alert alert-danger py-2 small">{{ error }}</div>
      <button type="submit" class="btn btn-dark w-100" :disabled="loading">
        {{ loading ? 'ログイン中...' : 'ログイン' }}
      </button>
    </form>
  </div>
</template>
