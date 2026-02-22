<template>
  <div class="chat-container">
    <!-- 消息显示区域 -->
    <div class="messages-area">
      <div v-for="(message, index) in messages" :key="index" :class="['message', message.role]">
        <div class="message-content" v-html="formatMessage(message.content)"></div>
      </div>
    </div>
    <!-- 输入区域 -->
    <div class="input-area">
      <textarea
        v-model="userInput"
        @keydown.enter.prevent="handleSendMessage"
        placeholder="输入你的问题..."
        :disabled="isLoading"
      ></textarea>
      <button @click="handleSendMessage" :disabled="isLoading">
        {{ isLoading ? '思考中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'; // 导入 ref 用于响应式变量
import { useRouter } from 'vue-router'; // 导入路由实例
import { getCookie } from '@/services/api'; // 导入获取 CSRF Token 的方法
import { marked } from 'marked'; // 导入 marked 用于 Markdown 渲染
import { sanitizeText } from '@/utils/inputSanitizer';

const router = useRouter(); // 获取路由实例

const messages = ref([
  { role: 'assistant', content: '你好！有什么可以帮助你的吗？' }
]); // 聊天消息列表，初始有一条 AI 问候
const userInput = ref(''); // 用户输入内容
const isLoading = ref(false); // 是否正在等待 AI 回复

// 格式化消息内容为 HTML（支持 Markdown）
const formatMessage = (content) => {
  return marked(content || '');
};

// 发送消息处理函数
const handleSendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  const userMessage = sanitizeText(userInput.value);
  messages.value.push({ role: 'user', content: userMessage }); // 添加用户消息
  userInput.value = '';
  isLoading.value = true;

  // 添加 AI 回复占位
  const assistantMessage = { role: 'assistant', content: '' };
  messages.value.push(assistantMessage);

  try {
    const csrfToken = getCookie('csrftoken'); // 获取 CSRF Token
    // 必须用相对路径，走 Vite 代理，这样和登录同源，浏览器才会带 session cookie
    const response = await fetch('/api/chat/stream/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ question: userMessage }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`服务器错误: ${response.status} ${errorText}`);
    }

    const reader = response.body.getReader(); // 获取流式响应 reader
    const decoder = new TextDecoder('utf-8'); // 用于解码字节流

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      const chunk = decoder.decode(value, { stream: true });
      assistantMessage.content += chunk; // 实时追加 AI 回复内容
    }
  } catch (error) {
    assistantMessage.content = '抱歉，请求出错了。请检查网络或联系管理员。';
    console.error('Streaming error:', error);
  } finally {
    isLoading.value = false;
    // Redirect to the question list view after the stream is complete
    router.push('/'); // 流式回复结束后跳转到首页
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 8rem); 
  max-width: 800px;
  margin: 1rem auto;
  border: 1px solid #ccc;
  border-radius: 8px;
}
.messages-area {
  flex-grow: 1;
  overflow-y: auto;
  padding: 1rem;
}
.message {
  margin-bottom: 1rem;
  display: flex;
}
.message.user {
  justify-content: flex-end;
}
.message-content {
  max-width: 80%;
  padding: 0.75rem;
  border-radius: 10px;
  background-color: #f0f0f0;
}
.message.user .message-content {
  background-color: #007bff;
  color: white;
}
.input-area {
  display: flex;
  padding: 1rem;
  border-top: 1px solid #ccc;
}
textarea {
  flex-grow: 1;
  padding: 0.5rem;
  border-radius: 5px;
  border: 1px solid #ccc;
  resize: none;
  height: 50px;
}
button {
  margin-left: 1rem;
  padding: 0 1.5rem;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}
button:disabled {
  background-color: #aaa;
}
</style> 