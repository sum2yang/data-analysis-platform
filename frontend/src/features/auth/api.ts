import { apiClient } from '@/api/client'
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '@/api/types'

export async function loginApi(data: LoginRequest): Promise<AuthResponse> {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)
  const res = await apiClient.post<AuthResponse>('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export async function registerApi(data: RegisterRequest): Promise<User> {
  const res = await apiClient.post<User>('/auth/register', data)
  return res.data
}

export async function fetchCurrentUser(): Promise<User> {
  const res = await apiClient.get<User>('/auth/me')
  return res.data
}
