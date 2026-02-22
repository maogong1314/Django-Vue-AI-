<template>
  <div class="login-container">
    <div class="login-form">
      <h2>登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" id="username" v-model="username" required>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <p v-if="registered" class="success">注册成功，请登录！</p>
        <p v-if="error" class="error">{{ error }}</p>
        <BaseButton type="submit">登录</BaseButton>
      </form>
      <p class="register-link">
        没有账号？ <router-link to="/register">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue' // 导入 ref/computed 用于响应式变量
import { useRouter, useRoute } from 'vue-router' // 导入路由实例和当前路由
import { useAuthStore } from '@/stores/auth' // 导入认证状态管理
import BaseButton from '@/components/BaseButton.vue' // 导入基础按钮组件

const username = ref('') // 用户名输入框绑定变量
const password = ref('') // 密码输入框绑定变量
const error = ref(null) // 错误提示信息
const authStore = useAuthStore() // 获取认证 store
const router = useRouter() // 获取路由实例
const route = useRoute() // 获取当前路由
const registered = computed(() => route.query.registered === '1') // 判断是否注册成功

// 处理登录表单提交
const handleLogin = async () => {
  error.value = null
  const success = await authStore.login(username.value, password.value) // 调用登录方法
  if (success) {
    router.push('/') // 登录成功，跳转到主页
  } else {
    error.value = '登录失败，请检查您的用户名和密码。'
  }
}
</script>

<style scoped>
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
  box-sizing: border-box; /* Important for padding */
}
.error {
  color: red;
  margin-bottom: 1rem;
}
.success {
  color: green;
  margin-bottom: 1rem;
}
.register-link {
    margin-top: 1.5rem;
    text-align: center;
    font-size: 0.9rem;
}
</style> 