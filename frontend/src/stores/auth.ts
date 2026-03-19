/**
 * Auth Store - User authentication state management
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import service, { API_URL } from '@/api'

interface User {
  id: string
  username: string
  email: string
  nickname?: string
  avatar?: string
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('token') || null)
  const userInfo = ref<User | null>(null)
  const loading = ref(false)

  // Computed
  const isLoggedIn = computed(() => !!token.value)

  // Actions
  const login = async (username: string, password: string) => {
    loading.value = true
    try {
      const data = await service.post(API_URL.USER.LOGIN, { username, password })
      token.value = data.token
      userInfo.value = data.user
      localStorage.setItem('token', data.token)
      return data
    } finally {
      loading.value = false
    }
  }

  const register = async (username: string, email: string, password: string) => {
    loading.value = true
    try {
      const data = await service.post(API_URL.USER.REGISTER, { username, email, password })
      return data
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    token.value = null
    userInfo.value = null
    localStorage.removeItem('token')
  }

  const fetchUserInfo = async () => {
    if (!token.value) return null
    try {
      const data = await service.get(API_URL.USER.PROFILE)
      userInfo.value = data
      return data
    } catch (error) {
      logout()
      return null
    }
  }

  const updateProfile = async (profile: Partial<User>) => {
    const data = await service.put(API_URL.USER.PROFILE, profile)
    userInfo.value = { ...userInfo.value, ...profile }
    return data
  }

  const changePassword = async (oldPassword: string, newPassword: string) => {
    return await service.post(API_URL.USER.CHANGE_PASSWORD, { old_password: oldPassword, new_password: newPassword })
  }

  return {
    token,
    userInfo,
    loading,
    isLoggedIn,
    login,
    register,
    logout,
    fetchUserInfo,
    updateProfile,
    changePassword
  }
})
