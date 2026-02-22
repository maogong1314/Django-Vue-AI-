<template>
  <div class="register-container">
    <div class="register-form">
      <h2>注册新账号</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" id="username" v-model="username" required>
        </div>
        <div class="form-group">
          <label for="email">邮箱 (可选)</label>
          <input type="email" id="email" v-model="email">
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <BaseButton type="submit">注册</BaseButton>
      </form>
      <p class="login-link">
        已经有账号了？ <router-link to="/login">立即登录</router-link>
      </p>
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
const email = ref('') // 邮箱输入框绑定变量
const error = ref(null) // 错误提示信息
const authStore = useAuthStore() // 获取认证 store
const router = useRouter() // 获取路由实例

// 处理注册表单提交
const handleRegister = async () => {
  error.value = null
  const result = await authStore.register(username.value, password.value, email.value) // 调用注册方法
  if (result.success) {
    router.push({ name: 'login', query: { registered: '1' } }) // 注册成功，跳转到登录页
  } else {
    error.value = result.error
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
}
.register-form {
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
.login-link {
    margin-top: 1.5rem;
    text-align: center;
    font-size: 0.9rem;
}
</style> 