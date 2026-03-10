import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient } from '@/api/client'

describe('apiClient interceptors', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('location', { href: '' })
  })

  it('request interceptor adds Authorization header when token exists', () => {
    localStorage.setItem('access_token', 'test_token')
    const config = { headers: {} as any }

    const handler = (apiClient.interceptors.request as any).handlers[0].fulfilled
    const result = handler(config)

    expect(result.headers.Authorization).toBe('Bearer test_token')
  })

  it('request interceptor skips header when no token', () => {
    const config = { headers: {} as any }
    const handler = (apiClient.interceptors.request as any).handlers[0].fulfilled
    const result = handler(config)

    expect(result.headers.Authorization).toBeUndefined()
  })

  it('response error interceptor maps 404 to Chinese message', async () => {
    const handler = (apiClient.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 404, data: {} } }

    await expect(handler(error)).rejects.toEqual({
      detail: '请求的资源不存在',
      status: 404,
    })
  })

  it('response error interceptor maps 500 to Chinese message', async () => {
    const handler = (apiClient.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 500, data: {} } }

    await expect(handler(error)).rejects.toEqual({
      detail: '服务器内部错误',
      status: 500,
    })
  })

  it('401 error clears token and redirects to /login', async () => {
    localStorage.setItem('access_token', 'old_token')
    const handler = (apiClient.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 401, data: {} } }

    try {
      await handler(error)
    } catch {
      // Expected rejection
    }

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(window.location.href).toBe('/login')
  })

  it('uses server message when available', async () => {
    const handler = (apiClient.interceptors.response as any).handlers[0].rejected
    const error = { response: { status: 400, data: { detail: 'Custom error' } } }

    await expect(handler(error)).rejects.toEqual({
      detail: 'Custom error',
      status: 400,
    })
  })

  it('network error returns generic message', async () => {
    const handler = (apiClient.interceptors.response as any).handlers[0].rejected
    const error = { response: undefined }

    await expect(handler(error)).rejects.toEqual({
      detail: '网络错误，请检查连接',
      status: 0,
    })
  })
})
