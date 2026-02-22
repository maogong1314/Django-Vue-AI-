<template>
  <!-- 使用Vue过渡动画，名称为"modal" -->
  <transition name="modal">
    <!-- 模态框遮罩层，当show为true时显示，点击遮罩层本身时触发close事件 -->
    <div v-if="show" class="modal-mask" @click.self="$emit('close')">
      <!-- 模态框容器 -->
      <div class="modal-container">
        <!-- 模态框头部区域 -->
        <div class="modal-header">
          <!-- 头部插槽，如果没有提供则显示默认标题 -->
          <slot name="header">
            默认标题
          </slot>
          <!-- 关闭按钮，点击时触发close事件 -->
          <button class="modal-close-button" @click="$emit('close')">×</button>
        </div>
        <!-- 模态框主体内容区域 -->
        <div class="modal-body">
          <!-- 主体插槽，如果没有提供则显示默认内容 -->
          <slot name="body">
            默认内容
          </slot>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
// 定义组件属性，show为布尔值，控制模态框的显示/隐藏
defineProps({
  show: Boolean
})
// 定义组件事件，close事件用于关闭模态框
defineEmits(['close'])
</script>

<style scoped>
/* 模态框遮罩层样式 */
.modal-mask {
  position: fixed; /* 固定定位，相对于浏览器窗口 */
  z-index: 9998; /* 层级，确保在其他元素之上 */
  top: 0; /* 距离顶部0px */
  left: 0; /* 距离左侧0px */
  width: 100%; /* 宽度占满整个视口 */
  height: 100%; /* 高度占满整个视口 */
  background-color: rgba(0, 0, 0, 0.5); /* 半透明黑色背景 */
  display: flex; /* 使用弹性布局 */
  transition: opacity 0.3s ease; /* 透明度过渡动画，持续0.3秒，缓动效果 */
}

/* 模态框容器样式 */
.modal-container {
  width: 500px; /* 固定宽度500px */
  margin: auto; /* 水平居中 */
  padding: 20px 30px; /* 内边距：上下20px，左右30px */
  background-color: #fff; /* 白色背景 */
  border-radius: 8px; /* 圆角8px */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.33); /* 阴影效果 */
  transition: all 0.3s ease; /* 所有属性过渡动画，持续0.3秒，缓动效果 */
}

/* 模态框头部样式 */
.modal-header {
  margin-top: 0; /* 顶部外边距为0 */
  font-size: 1.5rem; /* 字体大小1.5倍根元素字体大小 */
  font-weight: bold; /* 字体粗细为粗体 */
  border-bottom: 1px solid #eee; /* 底部边框：1px实线，浅灰色 */
  padding-bottom: 1rem; /* 底部内边距1rem */
  margin-bottom: 1rem; /* 底部外边距1rem */
  display: flex; /* 使用弹性布局 */
  justify-content: space-between; /* 主轴对齐方式：两端对齐 */
  align-items: center; /* 交叉轴对齐方式：居中对齐 */
}

/* 模态框关闭按钮样式 */
.modal-close-button {
    background: transparent; /* 透明背景 */
    border: none; /* 无边框 */
    font-size: 2rem; /* 字体大小2倍根元素字体大小 */
    cursor: pointer; /* 鼠标指针样式为手型 */
    color: #aaa; /* 浅灰色文字 */
}

/* 模态框主体样式 */
.modal-body {
  margin: 20px 0; /* 上下外边距20px，左右为0 */
}

/* 模态框进入和离开时的透明度动画 */
.modal-enter-from, .modal-leave-to {
  opacity: 0; /* 透明度为0（完全透明） */
}

/* 模态框进入和离开时容器的缩放动画 */
.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  -webkit-transform: scale(1.1); /* Webkit内核浏览器的缩放变换，放大1.1倍 */
  transform: scale(1.1); /* 标准缩放变换，放大1.1倍 */
}
</style> 