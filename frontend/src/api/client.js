import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
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

// 401/403 レスポンス時にログイン画面へリダイレクト（staff ページのみ）
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      (error.response?.status === 401 || error.response?.status === 403) &&
      window.location.pathname.startsWith('/staff')
    ) {
      window.location.href = '/admin/login/?next=' + encodeURIComponent(window.location.pathname)
    }
    return Promise.reject(error)
  },
)

export default client
