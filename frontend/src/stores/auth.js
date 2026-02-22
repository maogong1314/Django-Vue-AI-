import { defineStore } from 'pinia' // 导入 Pinia 的 defineStore，用于定义全局状态
import { ref } from 'vue' // 导入 ref，用于声明响应式变量
import apiClient from '@/services/api' // 导入封装的 API 客户端
import { fetchCsrfToken } from '@/services/api' // 导入获取 CSRF Token 的方法

// defineStore的第一个参数是这个store的唯一ID
export const useAuthStore = defineStore('auth', () => {
    // state
    const isAuthenticated = ref(false) // 是否已认证（登录）
    const user = ref(null) // 当前用户信息

    // actions
    // 注册新用户
    async function register(username, password, email) {
        try {
            const response = await apiClient.post('/auth/register/', { username, password, email }); // 调用注册接口
            user.value = response.data; // 保存用户信息
            isAuthenticated.value = true; // 设置为已登录
            return { success: true };
        } catch (error) {
            console.error('Registration failed:', error);
            const errorMessage = error.response?.data?.error || '注册失败，请稍后再试。'; // 获取后端返回的错误信息
            return { success: false, error: errorMessage };
        }
    }

    // 用户登录
    async function login(username, password) {
        try {
            // 登录前主动获取CSRF Token，确保Django认证
            await fetchCsrfToken();
            const response = await apiClient.post('/auth/login/', { username, password }, { withCredentials: true }) // 调用登录接口
            user.value = response.data // 保存用户信息
            isAuthenticated.value = true // 设置为已登录
            return true
        } catch (error) {
            console.error('Login failed:', error)
            return false
        }
    }

    // 用户登出
    async function logout() {
        try {
            // 我们也将在下一步创建这个后端登出接口
            await apiClient.post('/auth/logout/') // 调用登出接口
        } finally {
            // 无论后端是否成功，前端都清除状态
            user.value = null
            isAuthenticated.value = false
        }
    }

    // 检查当前用户认证状态
    async function checkAuth() {
        try {
            // 以及一个检查当前会话是否有效的接口
            const response = await apiClient.get('/auth/check/') // 调用检查接口
            user.value = response.data // 保存用户信息
            isAuthenticated.value = true
        } catch (error) {
            user.value = null
            isAuthenticated.value = false
        }
    }

    // return a "public interface" for the store
    // 返回 store 的“公开接口”，供组件调用
    return { isAuthenticated, user, login, logout, checkAuth, register }
}) 