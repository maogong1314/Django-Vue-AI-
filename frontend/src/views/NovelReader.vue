<template>
  <div class="novel-reader">
    <!-- 侧边栏：分类、小说、章节目录选择 -->
    <div class="sidebar">
      <h3>小说目录</h3>
      <div class="category-select">
        <label>分类：</label>
        <select v-model="selectedCategoryId" @change="fetchNovels">
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>
      </div>
      <div class="novel-select">
        <label>小说：</label>
        <select v-model="selectedNovelId" @change="fetchChapters">
          <option v-for="novel in novels" :key="novel.id" :value="novel.id">{{ novel.title }}</option>
        </select>
      </div>
      <ul class="chapter-list">
        <li v-for="(chapter, idx) in chapters" :key="chapter.id" :class="{active: idx === currentChapterIndex}" @click="goToChapter(idx)">
          {{ idx+1 }}. {{ chapter.title }}
        </li>
      </ul>
    </div>
    <!-- 主内容区：章节内容、章导航、评论 -->
    <div class="content-area">
      <div class="chapter-content" v-if="currentChapter">
        <h2>{{ currentChapter.title }}</h2>
        <pre>{{ currentChapter.content }}</pre>

        <!-- 上一章/下一章/章信息：放在正文下方、评论上方 -->
        <div class="toolbar">
          <button @click="toggleFullscreen">{{ isFullscreen ? '退出全屏' : '全屏' }}</button>
          <button @click="prevChapter" :disabled="currentChapterIndex <= 0">上一章</button>
          <button @click="nextChapter" :disabled="currentChapterIndex >= chapters.length-1">下一章</button>
          <span>第{{ currentChapterIndex+1 }}章 / 共{{ chapters.length }}章</span>
        </div>

        <!-- 评论区 -->
        <div class="comments-section">
          <h4>评论</h4>
          <div v-if="comments.length === 0" class="comment-empty">暂无评论</div>
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <b>{{ comment.user_name }}</b>：{{ comment.content }}
            <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            <button v-if="canDelete(comment)" class="delete-btn" @click="deleteComment(comment.id)">删除</button>
          </div>
          <div v-if="isAuthenticated" class="comment-input">
            <textarea v-model="newComment" placeholder="输入评论..." rows="2"></textarea>
            <button @click="submitComment" :disabled="!newComment.trim() || submittingComment">发表评论</button>
          </div>
          <div v-else class="comment-login-tip">请登录后发表评论</div>
        </div>
      </div>
      <div v-else class="empty-tip">请选择章节</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue' // 导入 Vue 响应式和生命周期相关方法
import { useRoute, useRouter } from 'vue-router' // 导入路由实例和当前路由
import apiClient from '@/services/api' // 导入 API 客户端
import { useAuthStore } from '@/stores/auth' // 导入认证状态管理

const authStore = useAuthStore() // 获取认证 store
const isAuthenticated = computed(() => authStore.isAuthenticated) // 是否已登录

const categories = ref([]) // 分类列表
const novels = ref([]) // 小说列表
const chapters = ref([]) // 章节列表
const selectedCategoryId = ref(null) // 当前选中的分类ID
const selectedNovelId = ref(null) // 当前选中的小说ID
const currentChapterIndex = ref(0) // 当前章节索引
const isFullscreen = ref(false) // 是否全屏

// 获取分类列表
const fetchCategories = async () => {
  const res = await apiClient.get('novel/novel-categories/')
  categories.value = res.data
  if (!selectedCategoryId.value && categories.value.length > 0) {
    selectedCategoryId.value = categories.value[0].id
  }
}
// 获取小说列表
const fetchNovels = async () => {
  if (!selectedCategoryId.value) return
  const res = await apiClient.get('novel/novels/?category=' + selectedCategoryId.value)
  novels.value = res.data
  if (novels.value.length > 0) {
    selectedNovelId.value = novels.value[0].id
    await fetchChapters()
  } else {
    selectedNovelId.value = null
    chapters.value = []
    currentChapterIndex.value = 0
  }
}
// 获取章节列表
const fetchChapters = async () => {
  if (!selectedNovelId.value) return
  const res = await apiClient.get('novel/novel-chapters/?novel=' + selectedNovelId.value)
  chapters.value = res.data
  currentChapterIndex.value = 0
}
// 跳转到指定章节
const goToChapter = (idx) => {
  currentChapterIndex.value = idx
}
// 上一章
const prevChapter = () => {
  if (currentChapterIndex.value > 0) currentChapterIndex.value--
}
// 下一章
const nextChapter = () => {
  if (currentChapterIndex.value < chapters.value.length-1) currentChapterIndex.value++
}
// 切换全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  const el = document.documentElement
  if (isFullscreen.value) {
    if (el.requestFullscreen) el.requestFullscreen()
  } else {
    if (document.exitFullscreen) document.exitFullscreen()
  }
}
// 当前章节对象
const currentChapter = computed(() => chapters.value[currentChapterIndex.value] || null)

// 路由相关
const route = useRoute()
const router = useRouter()

// 辅助：通过小说ID加载小说及其章节
const loadNovelById = async (novelId) => {
  try {
    const res = await apiClient.get(`novel/novels/${novelId}/`)
    const novel = res.data
    // 先设置分类，确保 fetchNovels 拉取正确列表
    selectedCategoryId.value = novel.category ? novel.category.id : null
    await fetchNovels()
    selectedNovelId.value = novelId
    await fetchChapters()
  } catch (e) {
    console.error('加载指定小说失败', e)
  }
}

// 页面挂载时初始化数据
onMounted(async () => {
  // 确认会话状态
  await authStore.checkAuth()
  await fetchCategories()
  const initialNovelId = route.query.novel ? parseInt(route.query.novel) : null
  if (initialNovelId) {
    await loadNovelById(initialNovelId)
  } else {
    await fetchNovels()
  }
})

// 监听小说ID变化，更新路由
watch(selectedNovelId, (newId) => {
  if (newId) {
    router.replace({ name: 'novel-reader', query: { novel: newId } })
  }
})
// 监听路由参数变化（如用户点击不同小说）
watch(() => route.query.novel, (newVal) => {
  if (newVal) {
    const id = parseInt(newVal)
    if (id !== selectedNovelId.value) {
      loadNovelById(id)
    }
  }
})
// 选中小说时加载章节
const selectNovel = async (id) => {
  selectedNovelId.value = id
  await fetchChapters()
}

// 评论相关逻辑
const comments = ref([]) // 当前章节评论列表
const newComment = ref('') // 新评论内容
const submittingComment = ref(false) // 评论提交状态

// 获取评论（仅拉取当前章节的评论，由后端按 chapter 过滤）
const fetchComments = async () => {
  if (!currentChapter.value) {
    comments.value = []
    return
  }
  const res = await apiClient.get(`novel/novel-chapter-comments/?chapter=${currentChapter.value.id}`)
  comments.value = res.data || []
}
// 提交评论
const submitComment = async () => {
  if (!newComment.value.trim()) return
  submittingComment.value = true
  try {
    await apiClient.post('novel/novel-chapter-comments/', {
      chapter: currentChapter.value.id,
      content: newComment.value.trim()
    })
    newComment.value = ''
    await fetchComments()
  } finally {
    submittingComment.value = false
  }
}
// 删除评论
const deleteComment = async (id) => {
  if (!confirm('确认删除该评论？')) return
  await apiClient.delete(`novel/novel-chapter-comments/${id}/`)
  await fetchComments()
}
// 判断是否有权限删除评论
const canDelete = (comment) => {
  return authStore.user && (authStore.user.id === comment.user || authStore.user.is_staff)
}
// 格式化时间
const formatTime = (ts) => new Date(ts).toLocaleString()

// 章节或小说切换时刷新评论（确保只显示当前章节的评论）
watch(currentChapter, (val, old) => {
  if (!val) {
    comments.value = []
    return
  }
  fetchComments()
}, { immediate: true })
</script>

<!-- 样式部分已省略，如需详细注释可补充 -->

<style scoped>
.novel-reader {
  display: flex;
  height: 90vh;
  background: #f7f7fa;
}
.sidebar {
  width: 320px;
  background: #fff;
  border-right: 1px solid #eee;
  padding: 24px 12px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.chapter-list {
  flex: 1;
  overflow-y: auto;
  margin: 0;
  padding: 0;
  list-style: none;
}
.chapter-list li {
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}
.chapter-list li.active, .chapter-list li:hover {
  background: #007bff;
  color: #fff;
}
.content-area {
  flex: 1;
  padding: 32px 40px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.toolbar {
  margin-top: 24px;
  margin-bottom: 18px;
  padding-top: 16px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 12px;
  align-items: center;
}
.chapter-content {
  background: #fff;            /* 统一底色 */
  border-radius: 8px;
  padding: 32px 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  color: #333;
  line-height: 1.8;
  font-size: 1.1rem;
}
.chapter-content pre {
  background: none;            /* 移除 pre 默认灰底 */
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  text-indent: 2em;
}
.chapter-content p {
  margin: 0 0 1em 0;
  text-indent: 2em;           /* 首行缩进两字 */
}
.empty-tip {
  color: #888;
  text-align: center;
  margin-top: 80px;
  font-size: 1.2rem;
}
.comments-section {
  margin-top: 24px;
  border-top: 1px solid #eee;
  padding-top: 16px;
}
.comment-item {
  margin-bottom: 8px;
}
.comment-time {
  color: #888;
  margin-left: 6px;
  font-size: 12px;
}
.delete-btn {
  background: none;
  border: none;
  color: #d9534f;
  cursor: pointer;
  margin-left: 8px;
}
.comment-input textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.comment-input button {
  margin-top: 6px;
  background: #007bff;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
}
.comment-login-tip {
  color: #888;
}
</style> 