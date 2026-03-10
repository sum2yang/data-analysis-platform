import { useMutation, useQuery } from '@tanstack/react-query'
import { message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { loginApi, registerApi, fetchCurrentUser } from '../api'
import type { LoginRequest, RegisterRequest, ApiError } from '@/api/types'

export function useLogin() {
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: LoginRequest) => loginApi(data),
    onSuccess: async (res) => {
      const token = res.access_token
      localStorage.setItem('access_token', token)
      const user = await fetchCurrentUser()
      setAuth(user, token)
      message.success('登录成功')
      navigate('/')
    },
    onError: (err: ApiError) => {
      message.error(err.detail ?? '登录失败')
    },
  })
}

export function useRegister() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: RegisterRequest) => registerApi(data),
    onSuccess: () => {
      message.success('注册成功，请登录')
      navigate('/login')
    },
    onError: (err: ApiError) => {
      message.error(err.detail ?? '注册失败')
    },
  })
}

export function useCurrentUser() {
  const { token, setAuth, logout } = useAuthStore()

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const user = await fetchCurrentUser()
      setAuth(user, token!)
      return user
    },
    enabled: !!token,
    retry: false,
    meta: {
      onError: () => logout(),
    },
  })
}
