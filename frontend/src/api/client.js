import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// CSRF トークンを cookie から取得して送る
client.interceptors.request.use((config) => {
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrftoken='))
    ?.split('=')[1]
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

// 401/403 レスポンス時にログイン画面へリダイレクト（/manage 配下のみ、ログイン画面自体は除外）
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const path = window.location.pathname
    if (
      (error.response?.status === 401 || error.response?.status === 403) &&
      path.startsWith('/manage') &&
      path !== '/manage/login'
    ) {
      window.location.href = '/manage/login?next=' + encodeURIComponent(path)
    }
    return Promise.reject(error)
  },
)

export default client
