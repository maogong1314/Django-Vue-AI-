<template>
  <div class="novel-home">
    <!-- 搜索栏：支持分类筛选和关键字搜索 -->
    <div class="search-bar">
      <select v-model="selectedCategoryId" @change="fetchNovels">
        <option value="">全部分类</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
      </select>
      <input v-model="keyword" placeholder="输入小说名称关键字" />
      <button @click="doFilter">搜索</button>
    </div>

    <h2 class="section-title">本期强推</h2>
    <!-- 小说展示区：网格布局，点击可进入阅读页 -->
    <div class="book-grid">
      <router-link
        v-for="novel in displayedNovels"
        :key="novel.id"
        :to="{ name: 'novel-reader', query: { novel: novel.id } }"
        class="book-item"
      >
        <img
          :src="coverUrl(novel)"
          :alt="novel.title"
          class="cover"
          referrerpolicy="no-referrer"
          @error="($event) => ($event.target.src = fallbackCoverUrl(novel))"
        />
        <div class="book-title">{{ novel.title }}</div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue' // 导入 ref/onMounted/computed 用于响应式和生命周期
import apiClient from '@/services/api' // 导入 API 客户端

const novels = ref([]) // 所有小说列表
const displayedNovels = computed(() => {
  if (!keyword.value.trim()) return novels.value
  const kw = keyword.value.trim().toLowerCase()
  return novels.value.filter((n) => n.title.toLowerCase().includes(kw))
}) // 根据关键字过滤后的小说列表

const categories = ref([]) // 分类列表
const selectedCategoryId = ref('') // 当前选中的分类ID
const keyword = ref('') // 搜索关键字

// 页面挂载时加载分类和小说列表
onMounted(async () => {
  await fetchCategories()
  const res = await apiClient.get('novel/novels/')
  novels.value = res.data
})

// 爬不到封面时使用的随机占位图（与封面加载失败时一致）
const fallbackCoverUrl = (novel) => `https://picsum.photos/seed/novel_${novel.id}/200/280`

// 获取小说封面图片地址，支持防盗链代理；爬不到则用随机占位图
const coverUrl = (novel) => {
  if (novel.cover_url) {
    const noProto = novel.cover_url.replace(/^https?:\/\//, '')
    return `https://images.weserv.nl/?url=${encodeURIComponent(noProto)}&w=220`
  }
  return fallbackCoverUrl(novel)
}

// 获取分类列表
const fetchCategories = async () => {
  const res = await apiClient.get('novel/novel-categories/')
  categories.value = res.data
}

// 根据分类筛选小说
const fetchNovels = async () => {
  const url = selectedCategoryId.value
    ? `novel/novels/?category=${selectedCategoryId.value}`
    : 'novel/novels/'
  const res = await apiClient.get(url)
  novels.value = res.data
}

// 搜索按钮点击（实际由 computed 自动响应）
const doFilter = () => {
  /* computed displayedNovels already reacts to keyword */
}
</script>

<style scoped>
.novel-home {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 12px;
}
.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.search-bar select,
.search-bar input {
  padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}
.search-bar button {
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 6px 14px;
  cursor: pointer;
}
.section-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  border-left: 4px solid #ff5a5f;
  padding-left: 8px;
}
.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 24px 18px;
}
.book-item {
  text-align: center;
  color: inherit;
  text-decoration: none;
  transition: transform 0.2s;
}
.book-item:hover {
  transform: translateY(-6px);
}
.cover {
  width: 100%;
  height: 220px;
  object-fit: cover;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
.book-title {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.3;
  font-weight: 500;
}
</style> 