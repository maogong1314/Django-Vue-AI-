<template>
  <div class="spider-page">
    <h2>小说爬取导入</h2>
    <!-- 爬虫表单：输入目录页URL，点击开始爬取 -->
    <div class="spider-form">
      <input v-model="catalogUrl" placeholder="请输入小说目录页URL" class="spider-input" />
      <button @click="startSpider" :disabled="loading">开始爬取</button>
      <button v-if="loading" @click="stopSpider" class="stop-btn">停止</button>
    </div>
    <!-- 爬取进度显示 -->
    <div v-if="loading" class="spider-loading">
      <div v-if="progress">
        <div>爬取进度：{{ progress.current }}/{{ progress.total }}
          <span v-if="progress.current_title">（{{ progress.current_title }}）</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar" :style="{width: progressPercent + '%'}"></div>
        </div>
      </div>
      <div v-else>爬取中，请稍候...</div>
    </div>
    <!-- 爬取结果显示 -->
    <div v-if="result" class="spider-result">
      <div v-if="result.success">✅ 已导入《{{ result.novel_title }}》，共 {{ result.chapter_count }} 章</div>
      <div v-else style="color:red">❌ {{ result.error }}</div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue' // 导入 ref/computed 用于响应式变量
import apiClient from '@/services/api' // 导入 API 客户端
let timer = null // 定时器句柄
const catalogUrl = ref('') // 小说目录页URL输入
const loading = ref(false) // 是否正在爬取
const result = ref(null) // 爬取结果
const progress = ref(null) // 爬取进度信息
const taskId = ref(null) // 后端返回的任务ID
const progressPercent = computed(() => {
  if (!progress.value || !progress.value.total) return 0
  return Math.round((progress.value.current / progress.value.total) * 100)
}) // 进度百分比

// 停止爬虫任务
const stopSpider = async () => {
  if (!taskId.value) return
  try {
    await apiClient.post('novel/novel-spider/', { action: 'stop', task_id: taskId.value })
  } catch (e) {
    console.error('停止爬取失败', e)
  }
}
// 轮询后端获取爬取进度
const pollProgress = async () => {
  if (!taskId.value) return
  try {
    const res = await apiClient.get('novel/novel-spider/', { params: { task_id: taskId.value } })
    progress.value = res.data.progress
    if (progress.value.done || progress.value.error) {
      clearInterval(timer)
      loading.value = false
      if (progress.value.error) {
        result.value = { success: false, error: progress.value.error }
      } else {
        result.value = { success: true, novel_title: progress.value.novel_title, chapter_count: progress.value.total }
      }
    }
  } catch (e) {
    clearInterval(timer)
    loading.value = false
    result.value = { success: false, error: e?.response?.data?.error || '进度获取失败' }
  }
}
// 启动爬虫任务
const startSpider = async () => {
  if (!catalogUrl.value.trim()) return
  loading.value = true
  result.value = null
  progress.value = null
  taskId.value = null
  try {
    const res = await apiClient.post('novel/novel-spider/', { catalog_url: catalogUrl.value })
    if (res.data.task_id) {
      taskId.value = res.data.task_id
      timer = setInterval(pollProgress, 3500) // 每3.5秒轮询进度
    } else {
      loading.value = false
      result.value = { success: false, error: '未获取到任务ID' }
    }
  } catch (e) {
    loading.value = false
    result.value = { success: false, error: e?.response?.data?.error || '爬取失败' }
  }
}
</script>
<style scoped>
.spider-page { max-width: 500px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 12px #eee; padding: 32px; }
.spider-form { display: flex; gap: 8px; margin-bottom: 18px; }
.spider-input { flex: 1; padding: 6px 10px; border-radius: 4px; border: 1px solid #ccc; }
.spider-loading { color: #888; margin-bottom: 10px; }
.spider-result { font-size: 1.1em; margin-top: 10px; }
.progress-bar-bg { width: 100%; height: 12px; background: #eee; border-radius: 6px; margin: 8px 0; }
.progress-bar { height: 100%; background: #4caf50; border-radius: 6px; transition: width 0.3s; }
</style> 