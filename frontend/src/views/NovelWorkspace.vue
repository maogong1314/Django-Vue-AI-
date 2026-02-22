<template>
  <div class="workspace-page">
    <!-- 顶部操作栏：与爬取小说同一位置 -->
    <div class="workspace-top">
      <router-link to="/novel-spider" class="top-link">
        <span class="top-link-icon">📥</span> 爬取小说
      </router-link>
      <button
        type="button"
        class="top-link top-btn"
        :disabled="!currentChapter || isStreaming"
        @click="showContinueDialog = true"
        title="续写当前选中章节"
      >
        <span class="top-link-icon">✏️</span> 续写本章
      </button>
      <button
        type="button"
        class="top-link top-btn"
        :disabled="!selectedNovelId || isStreaming"
        @click="showNextDialog = true"
        title="在当前小说下新建下一章"
      >
        <span class="top-link-icon">📄</span> 新建下一章
      </button>
    </div>
    <div class="workspace-toggleable">
    <!-- 分类侧边栏，可折叠、可调整宽度 -->
    <div class="sidebar" :class="{collapsed: !showSidebar}" :style="{width: showSidebar ? sidebarWidth + 'px' : '16px'}">
      <button class="toggle-btn" @click="showSidebar = !showSidebar">
        <span v-if="showSidebar">«</span><span v-else>»</span>
      </button>
      <transition name="fade">
        <div v-if="showSidebar" class="sidebar-inner">
          <div class="panel-header">
            <h3>分类管理</h3>
          </div>
          <ul class="category-list">
            <li v-for="cat in categories" :key="cat.id" :class="{active: cat.id === selectedCategoryId}">
              <span class="list-label" @click="selectCategory(cat.id)">{{ cat.name }}</span>
              <span class="list-actions">
                <button @click.stop="editCategory(cat)" class="icon-btn" title="编辑">✏️</button>
                <button @click.stop="deleteCategory(cat.id)" class="icon-btn" title="删除">🗑️</button>
              </span>
            </li>
          </ul>
          <div class="add-bar">
            <input v-model="newCategoryName" placeholder="新分类名" class="add-input" />
            <button @click="addCategory" class="add-btn">添加</button>
          </div>
        </div>
      </transition>
    </div>
    <!-- 小说栏，可折叠、可调整宽度 -->
    <div class="novelbar" :class="{collapsed: !showNovelbar}" :style="{width: showNovelbar ? novelbarWidth + 'px' : '16px'}">
      <button class="toggle-btn" @click="showNovelbar = !showNovelbar">
        <span v-if="showNovelbar">«</span><span v-else>»</span>
      </button>
      <transition name="fade">
        <div v-if="showNovelbar" class="sidebar-inner">
          <div class="panel-header">
            <h3>小说管理</h3>
          </div>
          <ul class="novel-list">
            <li v-for="novel in novels" :key="novel.id" :class="{active: novel.id === selectedNovelId}">
              <span class="list-label" @click="selectNovel(novel.id)">{{ novel.title }}</span>
              <span class="list-actions">
                <button @click.stop="editNovel(novel)" class="icon-btn" title="编辑">✏️</button>
                <button @click.stop="deleteNovel(novel.id)" class="icon-btn" title="删除">🗑️</button>
              </span>
            </li>
          </ul>
          <div class="add-bar">
            <input v-model="newNovelTitle" placeholder="新小说名" class="add-input" />
            <button @click="addNovel" class="add-btn">添加</button>
          </div>
        </div>
      </transition>
    </div>
    <!-- 章节栏，可折叠 -->
    <div class="chapterbar">
      <div class="chapter-list-area" :class="{collapsed: !showChapterList}" :style="{width: showChapterList ? '180px' : '24px'}">
        <button class="toggle-btn" @click="showChapterList = !showChapterList">
          <span v-if="showChapterList">«</span><span v-else>»</span>
        </button>
        <transition name="fade">
          <div v-if="showChapterList" class="sidebar-inner">
            <div class="panel-header">
              <h3>章节目录</h3>
            </div>
            <ul class="chapter-list">
              <li v-for="(chapter, idx) in chapters" :key="chapter.id" :class="{active: chapter.id === selectedChapterId}">
                <span class="list-label" @click="selectChapter(chapter.id)">{{ idx+1 }}. {{ chapter.title }}</span>
                <span class="list-actions">
                  <button @click.stop="editChapter(chapter)" class="icon-btn" title="编辑">✏️</button>
                  <button @click.stop="deleteChapter(chapter.id)" class="icon-btn" title="删除">🗑️</button>
                </span>
              </li>
            </ul>
            <div class="add-bar">
              <input v-model="newChapterTitle" placeholder="新章节标题" class="add-input" />
              <button @click="addChapter" class="add-btn">添加</button>
            </div>
          </div>
        </transition>
      </div>
      <!-- 章节内容区 -->
      <div class="chapter-content-area">
        <div v-if="currentChapter">
          <h2>{{ currentChapter.title }}</h2>
          <!-- AI流式续写时实时渲染 -->
          <div class="chapter-content markdown-body" v-if="(isStreaming && streamingType==='continue')">
            <div v-html="marked.parse((currentChapter.content||'') + streamingContent)"></div>
          </div>
          <!-- 普通渲染 -->
          <div class="chapter-content markdown-body" v-else-if="renderedContent.trim()">
            <div v-html="renderedContent"></div>
          </div>
          <div class="chapter-content" v-else>
            <pre style="white-space: pre-wrap;">{{ currentChapter.content }}</pre>
          </div>
          <!-- 续写本章 / 新建下一章 已移至顶部与爬取小说同一栏 -->
          <!-- 评论区 (已隐藏) -->
          <div class="comments-section" v-if="false">
            <h4>评论</h4>
            <div v-if="comments.length === 0" class="comment-empty">暂无评论</div>
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <b>{{ comment.user_name }}</b>：{{ comment.content }} <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            </div>
            <div v-if="isAuthenticated" class="comment-input">
              <textarea v-model="newComment" placeholder="输入评论..." rows="2"></textarea>
              <button @click="submitComment" :disabled="!newComment.trim() || submittingComment">发表评论</button>
            </div>
            <div v-else class="comment-login-tip">请登录后发表评论</div>
          </div>
        </div>
        <div v-else class="empty-tip">请选择章节</div>
        <div v-if="isStreaming" class="streaming-tip">AI生成中，请稍候...</div>
      </div>
    </div>
    <!-- 续写弹窗 -->
    <div v-if="showContinueDialog" class="modal-mask">
      <div class="modal-dialog">
        <h4>续写本章</h4>
        <textarea v-model="continuePrompt" placeholder="请输入续写提示（可选）"></textarea>
        <div class="modal-actions">
          <button @click="showContinueDialog=false">取消</button>
          <button @click="continueChapter">续写</button>
        </div>
      </div>
    </div>
    <!-- 新建下一章弹窗 -->
    <div v-if="showNextDialog" class="modal-mask">
      <div class="modal-dialog">
        <h4>新建下一章</h4>
        <input v-model="nextChapterTitle" placeholder="下一章标题" />
        <textarea v-model="nextPrompt" placeholder="请输入生成提示（可选）"></textarea>
        <div class="modal-actions">
          <button @click="showNextDialog=false">取消</button>
          <button @click="addNextChapter">生成</button>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue' // 导入 Vue 响应式和生命周期相关方法
import apiClient from '@/services/api' // 导入 API 客户端
import { marked } from 'marked' // 导入 marked 用于 Markdown 渲染
import { useAuthStore } from '@/stores/auth' // 导入认证状态管理
import { sanitizePayload, sanitizeText } from '@/utils/inputSanitizer'

/* 更宽的侧栏，视觉更舒展 */
const sidebarWidth = ref(200) // 分类栏宽度
const novelbarWidth = ref(220) // 小说栏宽度
const showSidebar = ref(true) // 是否显示分类栏
const showNovelbar = ref(true) // 是否显示小说栏
const showChapterList = ref(true) // 是否显示章节栏
let resizing = null // 当前正在调整的栏类型
let startX = 0 // 鼠标起始位置
let startSidebarWidth = 0 // 分类栏起始宽度
let startNovelbarWidth = 0 // 小说栏起始宽度
// 开始拖拽调整栏宽度
const startResize = (type) => {
  resizing = type
  startX = event.clientX
  startSidebarWidth = sidebarWidth.value
  startNovelbarWidth = novelbarWidth.value
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
}
// 拖拽调整栏宽度
const handleResize = (event) => {
  if (resizing === 'sidebar') {
    sidebarWidth.value = Math.max(80, Math.min(220, startSidebarWidth + event.clientX - startX))
  } else if (resizing === 'novelbar') {
    novelbarWidth.value = Math.max(100, Math.min(220, startNovelbarWidth + event.clientX - startX))
  }
}
// 停止拖拽
const stopResize = () => {
  resizing = null
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}
// 分类相关逻辑
const categories = ref([]) // 分类列表
const selectedCategoryId = ref(null) // 当前选中的分类ID
const newCategoryName = ref('') // 新分类名输入
const fetchCategories = async () => {
  const res = await apiClient.get('novel/novel-categories/')
  categories.value = res.data
  if (!selectedCategoryId.value && categories.value.length > 0) {
    selectedCategoryId.value = categories.value[0].id
  }
}
const addCategory = async () => {
  if (!newCategoryName.value.trim()) return
  await apiClient.post('novel/novel-categories/', { name: newCategoryName.value })
  newCategoryName.value = ''
  await fetchCategories()
}
const selectCategory = (id) => {
  selectedCategoryId.value = id
  fetchNovels()
}
const editCategory = (cat) => {
  const newName = prompt('重命名分类', cat.name)
  if (newName && newName !== cat.name) {
    apiClient.patch(`novel/novel-categories/${cat.id}/`, { name: newName }).then(fetchCategories)
  }
}
const deleteCategory = (id) => {
  if (confirm('确定删除该分类？')) {
    apiClient.delete(`novel/novel-categories/${id}/`).then(fetchCategories)
  }
}
// 小说相关逻辑
const novels = ref([]) // 小说列表
const selectedNovelId = ref(null) // 当前选中的小说ID
const newNovelTitle = ref('') // 新小说名输入
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
    selectedChapterId.value = null
  }
}
const addNovel = async () => {
  if (!newNovelTitle.value.trim() || !selectedCategoryId.value) return
  await apiClient.post('novel/novels/', { title: newNovelTitle.value, category_id: selectedCategoryId.value })
  newNovelTitle.value = ''
  await fetchNovels()
}
const selectNovel = (id) => {
  selectedNovelId.value = id
  fetchChapters()
}
const editNovel = (novel) => {
  const newTitle = prompt('重命名小说', novel.title)
  if (newTitle && newTitle !== novel.title) {
    apiClient.patch(`novel/novels/${novel.id}/`, { title: newTitle }).then(fetchNovels)
  }
}
const deleteNovel = (id) => {
  if (confirm('确定删除该小说？')) {
    apiClient.delete(`novel/novels/${id}/`).then(fetchNovels)
  }
}
// 章节相关逻辑
const chapters = ref([]) // 章节列表
const selectedChapterId = ref(null) // 当前选中的章节ID
const newChapterTitle = ref('') // 新章节标题输入
const fetchChapters = async () => {
  if (!selectedNovelId.value) return
  const res = await apiClient.get('novel/novel-chapters/?novel=' + selectedNovelId.value)
  chapters.value = res.data
  if (chapters.value.length > 0) {
    selectedChapterId.value = chapters.value[0].id
  } else {
    selectedChapterId.value = null
  }
}
const addChapter = async () => {
  if (!newChapterTitle.value.trim() || !selectedNovelId.value) return
  await apiClient.post('novel/novel-chapters/', { novel: selectedNovelId.value, title: newChapterTitle.value, content: '' })
  newChapterTitle.value = ''
  await fetchChapters()
}
const selectChapter = (id) => {
  selectedChapterId.value = id
}
const editChapter = (chapter) => {
  const newTitle = prompt('重命名章节', chapter.title)
  if (newTitle && newTitle !== chapter.title) {
    apiClient.patch(`novel/novel-chapters/${chapter.id}/`, { title: newTitle }).then(fetchChapters)
  }
}
const deleteChapter = (id) => {
  if (confirm('确定删除该章节？')) {
    apiClient.delete(`novel/novel-chapters/${id}/`).then(fetchChapters)
  }
}
const currentChapter = computed(() => chapters.value.find(c => c.id === selectedChapterId.value) || null)
const renderedContent = computed(() =>
  currentChapter.value ? marked.parse(currentChapter.value.content || '') : ''
)
// 续写与新建下一章相关逻辑
const showContinueDialog = ref(false) // 是否显示续写弹窗
const continuePrompt = ref('') // 续写提示
const streamingContent = ref('') // AI流式生成内容
const isStreaming = ref(false) // 是否正在AI生成
const streamingType = ref('') // 'continue' or 'next'
// 续写本章
const continueChapter = async () => {
  if (!currentChapter.value) return
  showContinueDialog.value = false
  isStreaming.value = true
  streamingType.value = 'continue'
  streamingContent.value = ''
  // 流式请求
  const response = await fetch('/api/novel/generate-chapter-stream/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || ''
    },
    body: JSON.stringify(sanitizePayload({
      prompt: (currentChapter.value.content || '') + '\n' + continuePrompt.value,
      novel_id: selectedNovelId.value,
      chapter_title: currentChapter.value.title + '（续写）'
    }))
  })
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let done = false
  let fullContent = ''
  while (!done) {
    const { value, done: doneReading } = await reader.read()
    done = doneReading
    if (value) {
      const chunk = decoder.decode(value, { stream: true })
      streamingContent.value += chunk
    }
  }
  fullContent = streamingContent.value
  // 追加到当前章节内容
  await apiClient.patch(`novel/novel-chapters/${currentChapter.value.id}/`, {
    content: currentChapter.value.content + '\n' + fullContent
  })
  continuePrompt.value = ''
  isStreaming.value = false
  streamingType.value = ''
  streamingContent.value = ''
  await fetchChapters()
}
// 新建下一章
const showNextDialog = ref(false) // 是否显示新建下一章弹窗
const nextChapterTitle = ref('') // 下一章标题
const nextPrompt = ref('') // 下一章AI提示
const addNextChapter = async () => {
  if (!nextChapterTitle.value.trim() || !selectedNovelId.value) return
  showNextDialog.value = false
  isStreaming.value = true
  streamingType.value = 'next'
  streamingContent.value = ''
  // 流式请求
  const response = await fetch('/api/novel/generate-chapter-stream/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || ''
    },
    body: JSON.stringify(sanitizePayload({
      prompt: nextPrompt.value,
      novel_id: selectedNovelId.value,
      chapter_title: nextChapterTitle.value
    }))
  })
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let done = false
  let fullContent = ''
  while (!done) {
    const { value, done: doneReading } = await reader.read()
    done = doneReading
    if (value) {
      const chunk = decoder.decode(value, { stream: true })
      streamingContent.value += chunk
    }
  }
  fullContent = streamingContent.value
  // 新建章节
  await apiClient.post('novel/novel-chapters/', {
    novel: selectedNovelId.value,
    title: nextChapterTitle.value,
    content: fullContent
  })
  nextChapterTitle.value = ''
  nextPrompt.value = ''
  isStreaming.value = false
  streamingType.value = ''
  streamingContent.value = ''
  await fetchChapters()
}
// 评论相关逻辑（已隐藏）
const comments = ref([])
const newComment = ref('')
const submittingComment = ref(false)
const authStore = useAuthStore()
const isAuthenticated = computed(() => authStore.isAuthenticated)

const fetchComments = async () => {
  if (!currentChapter.value) { comments.value = []; return }
  const res = await apiClient.get('novel/novel-chapter-comments/?chapter=' + currentChapter.value.id)
  comments.value = res.data
}
const submitComment = async () => {
  if (!newComment.value.trim() || !currentChapter.value) return
  submittingComment.value = true
  try {
    await apiClient.post('novel/novel-chapter-comments/', {
      chapter: currentChapter.value.id,
      content: sanitizeText(newComment.value)
    })
    newComment.value = ''
    await fetchComments()
  } catch (e) {
    // 弹窗显示后端返回的详细错误
    alert(e.response?.data ? JSON.stringify(e.response.data) : e.message)
  } finally {
    submittingComment.value = false
  }
}
const formatTime = (t) => t ? t.replace('T', ' ').slice(0, 16) : ''

// 章节变化时刷新评论
watch(currentChapter, async (val) => { if (val) await fetchComments() })
onMounted(async () => {
  await fetchCategories()
  await fetchNovels()
  await fetchComments()
})
</script>

<style scoped>
.workspace-page {
  display: flex;
  flex-direction: column;
  height: 90vh;
  background: #f0f2f5;
}
.workspace-top {
  flex-shrink: 0;
  padding: 12px 16px;
  border-bottom: 1px solid #e8eaed;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.top-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #28a745;
  color: #fff;
  text-decoration: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s, box-shadow 0.2s;
}
.top-link:hover {
  background: #218838;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}
.top-link.top-btn {
  background: #1a73e8;
  border: none;
  cursor: pointer;
  font-family: inherit;
}
.top-link.top-btn:hover:not(:disabled) {
  background: #1557b0;
  box-shadow: 0 2px 8px rgba(26, 115, 232, 0.3);
}
.top-link.top-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  box-shadow: none;
}
.top-link-icon {
  font-size: 1rem;
}
.workspace-toggleable {
  display: flex;
  flex: 1;
  min-height: 0;
  font-size: 14px;
  column-gap: 16px;
  padding: 16px;
}
.sidebar, .novelbar, .chapterbar {
  background: #fff;
  border: 1px solid #e8eaed;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border-radius: 10px;
  padding: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.2s, box-shadow 0.2s;
}
.sidebar-inner {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  padding: 12px 10px;
}
.panel-header {
  padding: 10px 8px 8px;
  border-bottom: 1px solid #eee;
  margin-bottom: 8px;
}
.panel-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
}
.sidebar.collapsed, .novelbar.collapsed, .chapter-list-area.collapsed {
  min-width: 24px !important;
  max-width: 24px !important;
  width: 24px !important;
  padding: 0;
  overflow: visible;
}

/* 折叠后将箭头外移一些，确保可见 */
.sidebar.collapsed .toggle-btn,
.novelbar.collapsed .toggle-btn,
.chapter-list-area.collapsed .toggle-btn {
  right: -6px;
  box-shadow: 0 0 4px rgba(0,0,0,0.1);
}
/* 调整 toggle-btn 风格 */
.toggle-btn {
  position: absolute;
  top: 10px;
  right: 4px;
  width: 18px;
  height: 26px;
  background: #f1f3f5;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  z-index: 20;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background 0.2s;
}
.toggle-btn:hover {
  background: #d0e2ff;
}
.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  padding: 0 2px;
  border-radius: 2px;
  transition: background 0.2s;
}
.icon-btn:hover {
  background: #e9ecef;
}
.add-btn {
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 3px;
  padding: 2px 10px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  min-width: 36px;
  box-sizing: border-box;
}
.add-btn:hover {
  background: #0056b3;
}
.category-list, .novel-list, .chapter-list {
  flex: 1;
  overflow-y: auto;
  margin: 0;
  padding: 0;
  list-style: none;
}
.category-list li, .novel-list li, .chapter-list li {
  padding: 8px 8px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s, color 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 14px;
}
.list-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.list-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0.85;
}
.category-list li:hover .list-actions,
.novel-list li:hover .list-actions,
.chapter-list li:hover .list-actions {
  opacity: 1;
}
.category-list li.active, .novel-list li.active, .chapter-list li.active {
  background: #1a73e8;
  color: #fff;
}
.category-list li:hover:not(.active), .novel-list li:hover:not(.active), .chapter-list li:hover:not(.active) {
  background: #e8f0fe;
  color: #1a1a2e;
}
.add-bar {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #eee;
  min-width: 0;
}
.add-input {
  min-width: 0;
  flex: 1;
  font-size: 13px;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #dadce0;
  box-sizing: border-box;
  transition: border-color 0.2s;
}
.add-input:focus {
  outline: none;
  border-color: #1a73e8;
}
.add-bar .add-btn {
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 6px;
  flex-shrink: 0;
}
.chapter-list-area {
  width: 180px;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.2s;
}
.chapter-content-area {
  flex: 1;
  padding: 10px 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.chapter-content {
  background: #fff;
  border-radius: 6px;
  padding: 12px 8px;
  box-shadow: 0 2px 8px #eee;
  min-height: 120px;
  max-height: 60vh;
  overflow-y: auto;
  font-size: 15px;
  line-height: 1.8;
  word-break: break-all;
  white-space: normal;
}
.chapter-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}
.action-btn {
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 3px;
  padding: 2px 10px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}
.action-btn:hover {
  background: #0056b3;
}
.empty-tip {
  color: #888;
  text-align: center;
  margin-top: 40px;
  font-size: 1.1rem;
}
.modal-mask {
  position: fixed;
  left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.2);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-dialog {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  min-width: 220px;
  box-shadow: 0 2px 16px #aaa;
}
.modal-dialog textarea, .modal-dialog input {
  width: 100%;
  margin: 6px 0;
  padding: 4px;
  border-radius: 3px;
  border: 1px solid #ccc;
  font-size: 13px;
}
.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 8px;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
/* markdown-body 基础美化 */
.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  font-weight: bold;
  margin: 1em 0 0.5em 0;
}
.markdown-body ul, .markdown-body ol {
  margin: 0.5em 0 0.5em 1.5em;
}
.markdown-body p {
  margin: 0.5em 0;
}
.markdown-body code, .markdown-body pre {
  background: #f6f8fa;
  border-radius: 3px;
  padding: 2px 4px;
  font-size: 13px;
}
.markdown-body pre {
  padding: 8px;
  overflow-x: auto;
}
.streaming-tip {
  color: #888;
  text-align: center;
  margin-top: 40px;
  font-size: 1.1rem;
}
.comments-section { margin-top: 32px; background: #f9f9f9; border-radius: 6px; padding: 16px 12px; }
.comment-item { margin-bottom: 8px; font-size: 15px; }
.comment-time { color: #888; font-size: 12px; margin-left: 8px; }
.comment-input { margin-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.comment-input textarea { resize: vertical; border-radius: 4px; border: 1px solid #ccc; padding: 6px; font-size: 14px; }
.comment-input button { align-self: flex-end; background: #007bff; color: #fff; border: none; border-radius: 3px; padding: 4px 16px; cursor: pointer; }
.comment-input button:disabled { background: #aaa; }
.comment-login-tip { color: #888; margin-top: 8px; }
.comment-empty { color: #aaa; margin-bottom: 8px; }
</style> 