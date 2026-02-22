<template>
  <div class="login-container">
    <div class="login-form">
      <h2>管理员登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" id="username" v-model="username" required>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <BaseButton type="submit">登录</BaseButton>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue' // 导入 ref 用于响应式变量
import { useRouter } from 'vue-router' // 导入路由实例
import { useAuthStore } from '@/stores/auth' // 导入认证状态管理
import BaseButton from '@/components/BaseButton.vue' // 导入基础按钮组件

const username = ref('') // 用户名输入框绑定变量
const password = ref('') // 密码输入框绑定变量
const error = ref(null) // 错误提示信息
const authStore = useAuthStore() // 获取认证 store
const router = useRouter() // 获取路由实例

// 处理登录表单提交
const handleLogin = async () => {
  error.value = null
  const success = await authStore.login(username.value, password.value) // 调用登录方法
  if (success && (authStore.user.is_staff || authStore.user.is_superuser)) {
    router.push('/admin') // 登录成功且为管理员，跳转后台
  } else if (success) {
    error.value = '您不是管理员，无法进入后台'
    await authStore.logout() // 非管理员自动登出
  } else {
    error.value = '登录失败，请检查您的用户名和密码。'
  }
}
</script>

<style scoped>
/* 可复用普通登录页样式 */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
}
.login-form {
  width: 350px;
  padding: 2rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
h2 {
  text-align: center;
  margin-bottom: 1.5rem;
}
.form-group {
  margin-bottom: 1rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
}
.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.error {
  color: red;
  margin-bottom: 1rem;
}
</style> 