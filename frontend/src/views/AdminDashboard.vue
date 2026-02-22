<template>
  <div class="admin-dashboard">
    <h2>管理员后台</h2>
    <BaseButton style="margin-bottom: 1.5rem;" @click="openDeepSeekUsage">DeepSeek用量信息</BaseButton>
    <div class="admin-actions">
      <form @submit.prevent="handleRegisterAdmin" class="register-form">
        <h3>注册新管理员</h3>
        <input v-model="newAdmin.username" placeholder="用户名" required>
        <input v-model="newAdmin.password" type="password" placeholder="密码" required>
        <input v-model="newAdmin.email" placeholder="邮箱（可选）">
        <BaseButton type="submit">注册</BaseButton>
        <span v-if="registerError" class="error">{{ registerError }}</span>
        <span v-if="registerSuccess" class="success">{{ registerSuccess }}</span>
      </form>
    </div>
    <div class="user-list">
      <h3>用户列表</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>是否管理员</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.is_staff ? '是' : '否' }}</td>
            <td>
              <BaseButton v-if="user.id !== authStore.user.id" @click="deleteUser(user.id)" class="delete-btn">删除</BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
      <span v-if="userError" class="error">{{ userError }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue' // 导入 ref 用于响应式变量，onMounted 用于生命周期钩子
import { useAuthStore } from '@/stores/auth' // 导入认证状态管理
import BaseButton from '@/components/BaseButton.vue' // 导入基础按钮组件
import apiClient from '@/services/api' // 导入 API 客户端
import { useRouter } from 'vue-router' // 导入路由实例

const users = ref([]) // 用户列表
const userError = ref('') // 用户相关错误信息
const registerError = ref('') // 注册相关错误信息
const registerSuccess = ref('') // 注册成功提示
const newAdmin = ref({ username: '', password: '', email: '' }) // 新管理员表单数据
const authStore = useAuthStore() // 获取认证 store
const router = useRouter() // 获取路由实例

// 获取用户列表
const fetchUsers = async () => {
  userError.value = ''
  try {
    const res = await apiClient.get('/admin/users/') // 请求后端获取用户列表
    users.value = res.data
  } catch (e) {
    users.value = []
    userError.value = '获取用户列表失败，或无权限。'
    if (e.response && e.response.status === 403) {
      router.push('/admin-login') // 无权限时跳转到管理员登录页
    }
  }
}

// 删除用户
const deleteUser = async (id) => {
  if (!confirm('确定要删除该用户吗？')) return
  try {
    await apiClient.delete(`/admin/delete_user/${id}/`) // 请求后端删除用户
    await fetchUsers() // 刷新用户列表
  } catch (e) {
    userError.value = '删除失败：' + (e.response?.data?.error || '未知错误')
  }
}

// 处理注册新管理员表单提交
const handleRegisterAdmin = async () => {
  registerError.value = ''
  registerSuccess.value = ''
  try {
    const res = await apiClient.post('/admin/register/', newAdmin.value) // 请求后端注册新管理员
    registerSuccess.value = '新管理员注册成功！'
    newAdmin.value = { username: '', password: '', email: '' } // 重置表单
    fetchUsers() // 刷新用户列表
  } catch (e) {
    registerError.value = e.response?.data?.error || '注册失败'
  }
}

// 打开 DeepSeek 用量信息页面
const openDeepSeekUsage = () => {
  window.open('https://platform.deepseek.com/usage', '_blank')
}

// 组件挂载时检查权限并加载用户列表
onMounted(() => {
  if (!authStore.user?.is_staff) {
    router.push('/admin-login') // 非管理员跳转到登录页
  } else {
    fetchUsers() // 管理员加载用户列表
  }
})
</script>

<style scoped>
.admin-dashboard {
  max-width: 900px;
  margin: 2rem auto;
  background: #fff;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.admin-actions {
  margin-bottom: 2rem;
}
.register-form {
  display: flex;
  gap: 1rem;
  align-items: center;
}
.register-form input {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.user-list table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
.user-list th, .user-list td {
  border: 1px solid #eee;
  padding: 0.75rem;
  text-align: center;
}
.delete-btn {
  background: #e74c3c;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.4rem 1rem;
  cursor: pointer;
}
.error {
  color: red;
  margin-left: 1rem;
}
.success {
  color: green;
  margin-left: 1rem;
}
</style> 