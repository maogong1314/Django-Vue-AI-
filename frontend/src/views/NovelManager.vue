<template>
  <div class="novel-manager">
    <!-- 小说 Logo 区域 -->
    <div class="novel-logo">
      <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%23007bff'%3E%3Cpath d='M1 2.828c.885-.37 2.154-.678 3.513-.787 1.428-.114 2.83.002 3.487.273v10.802c-.657-.271-2.06-.387-3.487-.273C3.154 13 1.885 13.308 1 13.678V2.828z'/%3E%3Cpath d='M14.5 15a.5.5 0 0 0 .5-.5V2.424a.5.5 0 0 0-.753-.429C13.451 2.37 11.833 3 10 3c-1.933 0-3.55-.63-4.247-.994a.5.5 0 0 0-.753.429v12.076a.5.5 0 0 0 .753.429C6.45 14.63 8.067 14 10 14c1.833 0 3.451.63 4.247.994A.5.5 0 0 0 14.5 15z'/%3E%3C/svg%3E" alt="小说Logo" class="logo-img" />
      <h2>AI 小说创作与管理</h2>
    </div>
    <!-- 顶部导航按钮 -->
    <div style="margin-bottom: 18px; display:flex; gap:12px;">
      <button @click="goToWorkspace" class="workspace-btn">小说管理界面</button>
      <button @click="goToFront" class="front-btn">小说界面</button>
    </div>

    <!-- 分类选择与管理 -->
    <div class="category-bar">
      <label>分类：</label>
      <select v-model="selectedCategoryId" @change="fetchNovels">
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
      </select>
      <input v-model="newCategoryName" placeholder="新分类名" style="margin-left:8px;" />
      <button @click="addCategory">新建分类</button>
    </div>

    <!-- 小说选择与管理 -->
    <div class="novel-bar">
      <label>小说：</label>
      <select v-model="selectedNovelId" @change="fetchChapters">
        <option v-for="novel in novels" :key="novel.id" :value="novel.id">{{ novel.title }}</option>
      </select>
      <input v-model="newNovelTitle" placeholder="新小说名" style="margin-left:8px;" />
      <button @click="addNovel">新建小说</button>
    </div>

    <!-- 导入章节（AI生成） -->
    <div class="import-section">
      <h3>导入小说章节</h3>
      <input v-model="chapterTitle" placeholder="章节标题" />
      <textarea v-model="chapterPrompt" placeholder="请输入本章节的内容要求或提示（AI将自动生成）"></textarea>
      <button @click="importChapter" :disabled="!canImport">导入章节</button>
      <div v-if="isGenerating">
        <h4>正在生成章节...</h4>
        <pre>{{ generatingContent }}</pre>
      </div>
    </div>

    <!-- 查看小说章节列表及内容 -->
    <div class="view-section">
      <h3>小说章节列表</h3>
      <ul>
        <li v-for="chapter in chapters" :key="chapter.id" @click="selectChapter(chapter)" :class="{active: chapter.id === selectedChapter?.id}">
          {{ chapter.title }}
        </li>
      </ul>
      <div v-if="selectedChapter" class="chapter-content">
        <h4>{{ selectedChapter.title }}</h4>
        <div v-html="renderedChapterContent" class="markdown-body"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue' // 导入 Vue 响应式和生命周期相关方法
import { marked } from 'marked' // 导入 marked 用于 Markdown 渲染
import apiClient from '@/services/api' // 导入 API 客户端
import { useRouter } from 'vue-router' // 导入路由实例
import { getCookie } from '@/services/api' // 导入获取 CSRF Token 的方法
import { sanitizePayload } from '@/utils/inputSanitizer'

// 分类、小说、章节等数据
const categories = ref([]) // 分类列表
const novels = ref([]) // 小说列表
const chapters = ref([]) // 章节列表
const selectedCategoryId = ref(null) // 当前选中的分类ID
const selectedNovelId = ref(null) // 当前选中的小说ID
const selectedChapter = ref(null) // 当前选中的章节
const newCategoryName = ref('') // 新分类名输入
const newNovelTitle = ref('') // 新小说名输入
const chapterTitle = ref('') // 新章节标题输入
const chapterPrompt = ref('') // 新章节AI提示输入
const loading = ref(false) // 加载状态
const router = useRouter() // 获取路由实例

const isGenerating = ref(false) // 是否正在生成章节
const generatingContent = ref('') // 实时生成的章节内容

// 获取分类列表
const fetchCategories = async () => {
  const res = await apiClient.get('novel/novel-categories/')
  categories.value = res.data
  if (!selectedCategoryId.value && categories.value.length > 0) {
    selectedCategoryId.value = categories.value[0].id
  }
}
// 新建分类
const addCategory = async () => {
  if (!newCategoryName.value.trim()) return
  await apiClient.post('novel/novel-categories/', { name: newCategoryName.value })
  newCategoryName.value = ''
  await fetchCategories()
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
    selectedChapter.value = null
  }
}
// 新建小说
const addNovel = async () => {
  if (!newNovelTitle.value.trim() || !selectedCategoryId.value) return
  await apiClient.post('novel/novels/', { title: newNovelTitle.value, category_id: selectedCategoryId.value })
  newNovelTitle.value = ''
  await fetchNovels()
}
// 获取章节列表
const fetchChapters = async () => {
  if (!selectedNovelId.value) return
  const res = await apiClient.get('novel/novel-chapters/?novel=' + selectedNovelId.value)
  chapters.value = res.data
  selectedChapter.value = null
}
// 导入章节（AI生成，流式输出）
const importChapter = async () => {
  if (!chapterTitle.value.trim() || !chapterPrompt.value.trim() || !selectedNovelId.value) return
  loading.value = true
  isGenerating.value = true
  generatingContent.value = ''
  try {
    const response = await fetch(`${apiClient.defaults.baseURL}/novel/generate-chapter-stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(sanitizePayload({
      prompt: chapterPrompt.value,
      novel_id: selectedNovelId.value,
      chapter_title: chapterTitle.value
    }))
    })

    if (!response.ok) throw new Error('Stream request failed')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      generatingContent.value += chunk
    }

    chapterTitle.value = ''
    chapterPrompt.value = ''
    await fetchChapters()
    if (chapters.value.length > 0) {
      selectedChapter.value = chapters.value[chapters.value.length - 1]
    }
    alert('章节导入成功！')
  } catch (e) {
    alert('章节导入失败: ' + e.message)
  } finally {
    loading.value = false
    isGenerating.value = false
  }
}
// 渲染选中章节为 HTML（Markdown 转换）
const renderedChapterContent = computed(() =>
  selectedChapter.value ? marked.parse(selectedChapter.value.content || '') : ''
)

// 选中章节
const selectChapter = (chapter) => {
  selectedChapter.value = chapter
}
// 跳转到小说工作区
const goToWorkspace = () => {
  router.push('/novel-workspace')
}
// 跳转到小说前台界面
const goToFront = () => {
  router.push('/novel-home')
}
// 是否允许导入章节
const canImport = computed(() =>
  chapterTitle.value.trim() && chapterPrompt.value.trim() && selectedNovelId.value && !loading.value
)

// 生命周期钩子：页面挂载时加载分类和小说
onMounted(async () => {
  await fetchCategories()
  await fetchNovels()
})
// 监听分类变化，自动刷新小说
watch(selectedCategoryId, async () => {
  await fetchNovels()
})
// 监听小说变化，自动刷新章节
watch(selectedNovelId, async () => {
  await fetchChapters()
})
</script>

<!-- 样式部分已省略，如需详细注释可补充 -->

<style scoped>
.novel-manager {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 16px #eee;
}
.novel-logo {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 24px;
}
.novel-logo img {
  width: 60px;
  height: 60px;
}
.category-bar, .novel-bar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 8px;
}
.import-section, .view-section {
  margin-top: 24px;
  padding: 16px;
  border: 1px solid #eee;
  border-radius: 8px;
}
.import-section input, .import-section textarea {
  display: block;
  width: 100%;
  margin: 8px 0;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
}
.import-section button {
  margin-top: 8px;
}
.view-section ul {
  list-style: none;
  padding: 0;
  margin: 0 0 12px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.view-section li {
  padding: 6px 12px;
  border-radius: 4px;
  background: #f5f5f5;
  cursor: pointer;
  transition: background 0.2s;
}
.view-section li.active, .view-section li:hover {
  background: #007bff;
  color: #fff;
}
.chapter-content {
  margin-top: 16px;
  background: #fafbfc;
  border-radius: 6px;
  padding: 12px;
  white-space: pre-wrap;
}
.workspace-btn {
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 6px 16px;
  cursor: pointer;
}
.front-btn {
  background: #ff4d4f;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 6px 16px;
  cursor: pointer;
}
.workspace-btn:hover {
  background: #0056b3;
}
.front-btn:hover {
  background: #d9363e;
}
.logo-img {
  width: 60px;
  height: 60px;
}

.chapter-content {
  overflow-x: auto;
}

.chapter-content pre {
  white-space: pre-wrap;
  word-break: break-word;
}

</style> 