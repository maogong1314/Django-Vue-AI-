<template>
  <!-- 基础按钮组件模板 -->
  <button class="base-button" @click="$emit('click')">
    <!-- 插槽：允许父组件传入按钮内容 -->
    <slot></slot>
  </button>
</template>

<script setup>
// 定义组件可触发的事件
defineEmits(['click'])  // 声明组件会触发'click'事件
</script>

<style scoped>
/* 基础按钮样式 (scoped表示只作用于当前组件) */
.base-button {
  background-color: #007bff;  /* 默认背景色（蓝色） */
  color: white;               /* 文字颜色 */
  border: none;               /* 去除边框 */
  padding: 10px 20px;         /* 内边距 */
  border-radius: 5px;         /* 圆角 */
  cursor: pointer;            /* 鼠标悬停时显示手型指针 */
  font-size: 1rem;            /* 字体大小 */
  transition: background-color 0.3s;  /* 背景色过渡动画 */
}

/* 悬停状态样式 */
.base-button:hover {
  background-color: #0056b3;  /* 悬停时更深的蓝色 */
}
</style>