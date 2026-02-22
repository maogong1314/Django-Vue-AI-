<template>
  <!-- 导航栏主容器 -->
  <nav class="navbar">
    <!-- 导航栏品牌区域（左侧） -->
    <div class="navbar-brand">
      <!-- 品牌链接，点击跳转到首页 -->
      <router-link to="/" class="navbar-item brand-text">AI问答社区</router-link>
    </div>
    <!-- 导航栏菜单区域（右侧） -->
    <div class="navbar-menu">
      <!-- 导航栏右侧菜单项 -->
      <div class="navbar-end">
        <!-- 写小说页面链接 -->
        <router-link to="/novel" class="navbar-item">写小说</router-link>
        <!-- 已认证用户显示的内容 -->
        <template v-if="authStore.isAuthenticated">
          <!-- 欢迎信息，显示用户名 -->
          <span class="navbar-item">欢迎, {{ authStore.user.username }}</span>
          <!-- 退出登录按钮 -->
          <BaseButton @click="handleLogout" class="logout-button">退出登录</BaseButton>
        </template>
        <!-- 未认证用户显示的内容 -->
        <template v-else>
          <!-- 管理员登录链接 -->
          <router-link to="/admin-login" class="navbar-item">管理员登录</router-link>
          <!-- 普通用户登录链接 -->
          <router-link to="/login" class="navbar-item">登录</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
// 导入认证状态管理store
import { useAuthStore } from '@/stores/auth'
// 导入Vue Router的useRouter组合式函数
import { useRouter } from 'vue-router'
// 导入基础按钮组件
import BaseButton from './BaseButton.vue'

// 获取认证状态管理store实例
const authStore = useAuthStore()
// 获取路由实例
const router = useRouter()

// 处理退出登录的函数
const handleLogout = async () => {
  await authStore.logout() // 调用store的退出登录方法
  router.push('/login') // 退出后跳转到登录页面
}
</script>

<style scoped>
/* 导航栏主容器样式 */
.navbar {
  background-color: #fff; /* 白色背景 */
  padding: 0 2rem; /* 左右内边距2rem，上下为0 */
  display: flex; /* 使用弹性布局 */
  justify-content: space-between; /* 主轴对齐方式：两端对齐 */
  align-items: center; /* 交叉轴对齐方式：居中对齐 */
  border-bottom: 1px solid #dbdbdb; /* 底部边框：1px实线，浅灰色 */
  height: 5rem; /* 固定高度5rem */
}

/* 导航栏品牌区域样式 */
.navbar-brand {
  font-weight: bold; /* 字体粗细为粗体 */
}

/* 品牌文字样式 */
.brand-text {
  font-size: 1.5rem; /* 字体大小1.5倍根元素字体大小 */
}

/* 导航栏项目样式 */
.navbar-item {
  color: #4a4a4a; /* 深灰色文字 */
  text-decoration: none; /* 无下划线 */
  padding: 0.5rem 0.75rem; /* 内边距：上下0.5rem，左右0.75rem */
}

/* 导航栏项目悬停效果 */
.navbar-item:hover {
  background-color: #f5f5f5; /* 悬停时背景色变为浅灰色 */
}

/* 导航栏菜单样式 */
.navbar-menu {
  display: flex; /* 使用弹性布局 */
}

/* 导航栏右侧菜单样式 */
.navbar-end {
  display: flex; /* 使用弹性布局 */
  align-items: center; /* 交叉轴对齐方式：居中对齐 */
}

/* 退出登录按钮样式 */
.logout-button {
    margin-left: 1rem; /* 左侧外边距1rem */
    padding: 8px 15px; /* 内边距：上下8px，左右15px */
    font-size: 0.9rem; /* 字体大小0.9倍根元素字体大小 */
}
</style> 