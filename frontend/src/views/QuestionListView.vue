<template>
  <div class="question-layout">
    <!-- 左侧面板：问题列表及操作 -->
    <div class="question-list-panel">
      <div class="new-chat-button-container">
        <button @click="startNewChat" class="new-chat-button">
          + 新的对话
        </button>
      </div>
      <div class="novel-button-container">
        <button @click="goToNovel" class="novel-button">
          📖 写小说
        </button>
        <router-link to="/novel-workspace" class="novel-sub-btn workspace">📖 小说管理界面</router-link>
        <router-link to="/novel-home" class="novel-sub-btn front">📖 小说界面</router-link>
      </div>
      <div v-if="isLoading" class="loading">正在加载...</div>
      <div v-else-if="questions.length === 0" class="no-questions">
        没有找到问题。
      </div>
      <ul v-else class="question-list">
        <li
          v-for="question in sortedQuestions"
          :key="question.id"
          @click="selectQuestion(question)"
          :class="{ active: selectedQuestion && selectedQuestion.id === question.id }"
        >
          <div class="question-title-row">
            <div class="question-title">{{ question.title }}</div>
            <div class="menu-btn" @click.stop="openMenu(question, $event)">⋮</div>
          </div>
          <div class="question-date">{{ formatDate(question.created_at) }}</div>
          <div v-if="menuOpenId === question.id" class="menu-popup" :style="menuStyle">
            <div class="menu-item" @click.stop="showRenameDialog(question)">重命名</div>
            <div class="menu-item" @click.stop="togglePin(question)">{{ question.is_pinned ? '取消置顶' : '置顶' }}</div>
            <div class="menu-item delete" @click.stop="confirmDelete(question)">删除</div>
          </div>
        </li>
      </ul>
    </div>

    <!-- 右侧面板：聊天面板 -->
    <div class="question-detail-panel">
       <ChatPanel 
        :conversation-id="selectedQuestion ? selectedQuestion.id : null"
        @new-conversation-started="handleNewConversation"
      />
    </div>
  </div>

  <!-- 重命名弹窗 -->
  <div v-if="renameDialogVisible" class="modal-mask">
    <div class="modal-dialog">
      <div class="modal-title">重命名对话</div>
      <input v-model="renameInput" class="modal-input" maxlength="50" />
      <div class="modal-actions">
        <button @click="renameDialogVisible=false">取消</button>
        <button @click="doRename">确定</button>
      </div>
    </div>
  </div>
  <!-- 删除确认弹窗 -->
  <div v-if="deleteDialogVisible" class="modal-mask">
    <div class="modal-dialog">
      <div class="modal-title">确认删除</div>
      <div class="modal-content">确定要删除该对话吗？此操作不可恢复。</div>
      <div class="modal-actions">
        <button @click="deleteDialogVisible=false">取消</button>
        <button class="delete" @click="doDelete">删除</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'; // 导入 Vue 响应式和生命周期相关方法
import { useRouter } from 'vue-router'; // 导入路由实例
import { getQuestions, patchQuestion, deleteQuestion } from '@/services/api'; // 导入 API 方法
import ChatPanel from '@/components/ChatPanel.vue'; // 导入聊天面板组件

const questions = ref([]); // 问题列表
const selectedQuestion = ref(null); // 当前选中的问题
const isLoading = ref(true); // 加载状态

// 菜单相关
const menuOpenId = ref(null); // 当前打开菜单的问题ID
const menuStyle = ref({}); // 菜单弹窗样式
const openMenu = (question, event) => {
  menuOpenId.value = question.id;
  // 让菜单靠近按钮
  menuStyle.value = { top: event.target.offsetTop + 24 + 'px', left: event.target.offsetLeft + 'px' };
  document.addEventListener('click', closeMenuOnClickOutside);
};
const closeMenuOnClickOutside = (e) => {
  menuOpenId.value = null;
  document.removeEventListener('click', closeMenuOnClickOutside);
};

// 排序：置顶的在最上面
const sortedQuestions = computed(() => {
  return [...questions.value].sort((a, b) => {
    if (a.is_pinned && !b.is_pinned) return -1;
    if (!a.is_pinned && b.is_pinned) return 1;
    return new Date(b.created_at) - new Date(a.created_at);
  });
});

// 获取问题列表
const fetchQuestions = async () => {
  isLoading.value = true;
  try {
    const response = await getQuestions();
    questions.value = response.data;
    if (questions.value.length > 0 && !selectedQuestion.value) {
      selectQuestion(questions.value[0]);
    }
  } catch (error) {
    console.error('获取问题列表失败:', error);
  } finally {
    isLoading.value = false;
  }
};

// 选中问题
const selectQuestion = (question) => {
  selectedQuestion.value = question;
};

// 新建对话
const startNewChat = () => {
  selectedQuestion.value = null;
};

// 聊天面板新对话回调
const handleNewConversation = async (newId) => {
  await fetchQuestions();
  const newQuestion = questions.value.find(q => q.id === newId);
  if (newQuestion) {
    selectQuestion(newQuestion);
  }
};

// 格式化日期
const formatDate = (dateString) => {
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString('zh-CN', options);
};

// 重命名弹窗相关
const renameDialogVisible = ref(false); // 是否显示重命名弹窗
const renameInput = ref(''); // 重命名输入内容
let renameTarget = null; // 当前重命名目标
const showRenameDialog = (question) => {
  renameTarget = question;
  renameInput.value = question.title;
  renameDialogVisible.value = true;
  menuOpenId.value = null;
  nextTick(() => {
    document.querySelector('.modal-input')?.focus();
  });
};
const doRename = async () => {
  if (!renameInput.value.trim()) return;
  await patchQuestion(renameTarget.id, { title: renameInput.value.trim() });
  renameDialogVisible.value = false;
  await fetchQuestions();
};

// 置顶/取消置顶
const togglePin = async (question) => {
  await patchQuestion(question.id, { is_pinned: !question.is_pinned });
  menuOpenId.value = null;
  await fetchQuestions();
};

// 删除弹窗相关
const deleteDialogVisible = ref(false); // 是否显示删除弹窗
let deleteTarget = null; // 当前删除目标
const confirmDelete = (question) => {
  deleteTarget = question;
  deleteDialogVisible.value = true;
  menuOpenId.value = null;
};
const doDelete = async () => {
  await deleteQuestion(deleteTarget.id);
  deleteDialogVisible.value = false;
  await fetchQuestions();
  if (selectedQuestion.value && selectedQuestion.value.id === deleteTarget.id) {
    selectedQuestion.value = null;
  }
};

const router = useRouter(); // 获取路由实例
const goToNovel = () => {
  router.push('/novel');
};

onMounted(() => {
  fetchQuestions();
});
</script>

<!-- 样式部分已省略，如需详细注释可补充 -->

<style scoped>
.question-layout {
  display: flex;
  height: calc(100vh - 60px); /* Adjust based on your header's height */
}

.question-list-panel {
  width: 320px;
  background-color: #f8f9fa;
  border-right: 1px solid #dee2e6;
  display: flex;
  flex-direction: column;
}

.new-chat-button-container {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.new-chat-button {
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
}
.new-chat-button:hover {
  background-color: #0056b3;
}

.novel-button-container {
  padding: 0 1rem 1rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.novel-button {
  width: 100%;
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0.75rem 0;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.novel-button:hover {
  background: #0056b3;
}

/* 与写小说按钮对齐、同款样式 */
.novel-sub-btn {
  display: block;
  width: 100%;
  padding: 0.75rem 0;
  border: none;
  border-radius: 6px;
  font-size: 1.1rem;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  box-sizing: border-box;
}
.novel-sub-btn.workspace {
  background: #007bff;
  color: #fff;
}
.novel-sub-btn.workspace:hover {
  background: #0056b3;
}
.novel-sub-btn.front {
  background: #ff4d4f;
  color: #fff;
}
.novel-sub-btn.front:hover {
  background: #d9363e;
}

.question-list {
  list-style: none;
  padding: 0;
  margin: 0;
  overflow-y: auto;
  flex-grow: 1;
}

.question-list li {
  padding: 1rem;
  cursor: pointer;
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.2s;
}

.question-list li:hover {
  background-color: #e9ecef;
}

.question-list li.active {
  background-color: #ddeaff;
  border-left: 4px solid #007bff;
  padding-left: calc(1rem - 4px);
}

.question-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.question-title {
  font-weight: 500;
  color: #343a40;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-date {
  font-size: 0.8rem;
  color: #6c757d;
  margin-top: 4px;
}

.question-detail-panel {
  flex-grow: 1;
  overflow-y: auto;
  /* The ChatPanel component will manage its own padding */
}

.loading, .no-questions {
  padding: 1rem;
  text-align: center;
  color: #6c757d;
}

.menu-btn {
  cursor: pointer;
  padding: 0 6px;
  font-size: 18px;
  color: #888;
  border-radius: 3px;
  transition: background 0.2s;
}
.menu-btn:hover {
  background: #e9ecef;
}
.menu-popup {
  position: absolute;
  z-index: 10;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  min-width: 72px;
  width: max-content;   /* 宽度由内容决定，不再被 left+right 撑满 */
  padding: 4px 0;
  /* 不设 right，避免与内联 left 同时存在时把整条拉长 */
}
.menu-item {
  padding: 4px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #333;
  transition: background 0.15s;
  white-space: nowrap;
}
.menu-item:hover {
  background: #f0f0f0;
}
.menu-item.delete {
  color: #e74c3c;
}
.modal-mask {
  position: fixed;
  left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.15);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-dialog {
  background: #fff;
  border-radius: 8px;
  padding: 24px 28px 18px 28px;
  min-width: 320px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.10);
}
.modal-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 12px;
}
.modal-input {
  width: 100%;
  padding: 8px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  margin-bottom: 16px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
.modal-actions button {
  padding: 6px 18px;
  border: none;
  border-radius: 4px;
  background: #eee;
  color: #333;
  font-size: 15px;
  cursor: pointer;
}
.modal-actions button.delete {
  background: #e74c3c;
  color: #fff;
}
</style> 