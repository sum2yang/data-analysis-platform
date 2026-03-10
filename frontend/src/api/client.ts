import axios from 'axios'
import type { AxiosError } from 'axios'
import { API_BASE } from '@/config/constants'
import type { ApiError } from './types'

const errorMessages: Record<number, string> = {
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '没有操作权限',
  404: '请求的资源不存在',
  409: '数据冲突',
  413: '文件过大',
  422: '数据验证失败',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误',
  502: '服务不可用',
  503: '服务暂时不可用',
}

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status ?? 0
    const serverMessage = error.response?.data?.detail

    if (status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }

    const apiError: ApiError = {
      detail: serverMessage ?? errorMessages[status] ?? '网络错误，请检查连接',
      status,
    }
    return Promise.reject(apiError)
  },
)
