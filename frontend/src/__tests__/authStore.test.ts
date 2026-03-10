import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '@/store/authStore'

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ user: null, token: null })
  })

  it('setAuth updates user and token and persists to localStorage', () => {
    const user = { id: '1', username: 'testuser' }
    const token = 'new_token'

    useAuthStore.getState().setAuth(user, token)

    expect(useAuthStore.getState().user).toEqual(user)
    expect(useAuthStore.getState().token).toBe(token)
    expect(localStorage.getItem('access_token')).toBe(token)
  })

  it('logout clears state and localStorage', () => {
    useAuthStore.setState({ user: { id: '1', username: 'u' }, token: 't' })
    localStorage.setItem('access_token', 't')

    useAuthStore.getState().logout()

    expect(useAuthStore.getState().user).toBeNull()
    expect(useAuthStore.getState().token).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('isAuthenticated returns true when token exists', () => {
    useAuthStore.setState({ token: 'exists' })
    expect(useAuthStore.getState().isAuthenticated()).toBe(true)
  })

  it('isAuthenticated returns false when token is null', () => {
    useAuthStore.setState({ token: null })
    expect(useAuthStore.getState().isAuthenticated()).toBe(false)
  })
})
