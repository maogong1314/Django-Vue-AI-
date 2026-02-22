<template>
  <!-- 聊天面板主容器 -->
  <div class="chat-panel">
    <!-- 全局拖拽遮罩层，当文件拖拽到页面时显示 -->
    <div v-if="showDropMask" class="drop-mask" @drop.prevent="handleGlobalDrop" @dragover.prevent>
      <!-- 拖拽提示内容 -->
      <div class="drop-mask-content">
        <!-- 拖拽图标 -->
        <div class="drop-icon">📄<br/>⬆️</div>
        <!-- 拖拽标题 -->
        <div class="drop-title">文件拖动到此处即可上传</div>
        <!-- 拖拽描述 -->
        <div class="drop-desc">支持txt、md、csv、json文件，AI将识别其内容</div>
      </div>
    </div>
    <!-- 消息显示区域 -->
    <div class="messages-area" ref="messagesArea">
      <!-- 加载提示 -->
      <div v-if="isLoading" class="loading-messages">正在加载历史消息...</div>
      <!-- 消息列表，遍历显示每条消息 -->
      <div v-for="(message, idx) in messages" :key="message.id" :class="['message', getMessageRole(message)]">
        <!-- AI助手标签，只在AI消息时显示 -->
        <div class="author-tag" v-if="getMessageRole(message) === 'assistant'">
          <!-- AI图标 -->
          <span class="ai-icon">🤖</span> AI 助手
        </div>
        <!-- 消息内容包装器：用户消息不展示模式 prompt，仅展示用户实际输入 -->
        <div class="message-content-wrapper">
          <div class="message-content" v-html="formatMessage(getDisplayContent(message))"></div>
          <button class="copy-btn" @click="copyToClipboard(getDisplayContent(message))" title="复制内容">📋</button>
        </div>
      </div>
    </div>
    <!-- 输入区域 -->
    <div class="input-area" @dragover.prevent @drop.prevent="handleDrop">
      <!-- 附件预览，当有附件时显示 -->
      <div v-if="attachedFile" class="attachment-preview">
        <!-- 附件信息 -->
        <div class="attachment-info">
          <span>{{ attachedFile.name }}</span>
        </div>
        <!-- 移除附件按钮 -->
        <button @click="removeAttachment" class="remove-attachment-btn" title="移除附件">×</button>
      </div>
      <!-- 输入控制区域 -->
      <div class="input-controls">
      <!-- 文本输入框 -->
      <textarea
        v-model="userInput"
        @keydown.enter.prevent="handleSendMessage"
        placeholder="输入你的问题..."
        :disabled="isSending"
      ></textarea>
        <!-- 隐藏的文件输入框 -->
        <input type="file" ref="fileInput" style="display:none" @change="handleFileChange" accept="image/*,text/*,application/pdf" />
      <!-- 文件上传按钮 -->
      <button class="upload-btn" @click="triggerFileInput" title="上传文件/图片">📎</button>
      <!-- 复制输入内容按钮 -->
      <button class="copy-btn" @click="copyToClipboard(userInput)" :disabled="!userInput" title="复制提问">📋</button>
      <!-- 思考模式：选择后仅显示当前模式，点击展开切换（不常驻显示三个按钮） -->
      <div class="mode-select-wrap" ref="modeSelectWrap">
        <button
          type="button"
          class="mode-current"
          :class="{ open: modeDropdownOpen }"
          @click="modeDropdownOpen = !modeDropdownOpen"
          :title="'当前：' + (MODES.find(m => m.key === mode)?.label || '')"
        >
          <span class="mode-current-label">{{ MODES.find(m => m.key === mode)?.label || '思考模式' }}</span>
          <span class="mode-arrow">▾</span>
        </button>
        <Transition name="mode-drop">
          <div v-if="modeDropdownOpen" class="mode-dropdown" @click.stop>
            <button
              v-for="m in MODES"
              :key="m.key"
              type="button"
              class="mode-option"
              :class="{ active: mode === m.key }"
              @click="mode = m.key; modeDropdownOpen = false"
            >{{ m.label }}</button>
          </div>
        </Transition>
      </div>
        <!-- 发送按钮 -->
        <button @click="handleSendMessage" :disabled="isSending || (!userInput.trim() && !attachedFile)">
        {{ isSending ? '思考中...' : '发送' }}
      </button>
      <!-- 停止生成按钮，仅在生成过程中显示 -->
      <button v-if="isSending && !isStopped" class="stop-btn" @click="stopAnswer">停止</button>
      </div>
    </div>
    <!-- 上传提示信息 -->
    <div v-if="uploadingFileName" class="uploading-tip">已附加：{{ uploadingFileName }}</div>
  </div>
</template>

<script setup>
// 导入Vue组合式API相关函数
import { ref, watch, onMounted, nextTick, onBeforeUnmount } from 'vue';
// 导入API客户端
import apiClient from '@/services/api';
// 导入获取Cookie的工具函数
import { getCookie } from '@/services/api';
// 导入Markdown解析库
import { marked } from 'marked';
// 导入数学公式渲染库
import katex from 'katex';
// 导入数学公式样式
import 'katex/dist/katex.min.css';
// 导入OCR文字识别库
import Tesseract from 'tesseract.js';
import { sanitizeText } from '@/utils/inputSanitizer';

// 定义组件属性
const props = defineProps({
  // 对话ID，可以是数字或字符串
  conversationId: {
    type: [Number, String],
    default: null,
  },
});

// 定义组件事件
const emit = defineEmits(['new-conversation-started']);

// 响应式数据定义
const messages = ref([]); // 消息列表
const userInput = ref(''); // 用户输入内容
const isLoading = ref(false); // 是否正在加载
const isSending = ref(false); // 是否正在发送
const currentConversationId = ref(props.conversationId); // 当前对话ID
const messagesArea = ref(null); // 消息区域DOM引用
const isStopped = ref(false); // 是否已停止生成
const showDropMask = ref(false); // 是否显示拖拽遮罩
const isStreaming = ref(false); // 是否正在流式传输
let readerRef = null; // 流式读取器引用
let controllerRef = null; // 中止控制器引用
let dragCounter = 0; // 拖拽计数器
const attachedFile = ref(null); // 附件文件信息 { name, type, url }
const fileInput = ref(null); // 文件输入框引用

// 思考模式配置
const MODES = [
  {
    key: 'deep', // 深度思考模式
    label: '深度思考',
    prompt: '请以深度思考模式回答，逐步分析问题，提供详尽的推理过程，并给出最终结论。确保回答全面、严谨，避免遗漏关键细节。'
  },
  {
    key: 'search', // 联网思考模式
    label: '联网思考',
    prompt: '请结合联网搜索获取最新信息，综合分析后给出回答。确保引用权威来源，并验证信息的准确性。'
  },
  {
    key: 'fast', // 快速思考模式
    label: '快速思考',
    prompt: '请以快速思考模式回答，直接给出核心要点，避免冗长分析，保持简洁高效。'
  }
]
const mode = ref('deep') // 当前选择的思考模式
const modeDropdownOpen = ref(false) // 思考模式下拉是否展开
const modeSelectWrap = ref(null) // 模式选择容器，用于点击外部关闭

// 获取消息角色（用户或AI助手）
const getMessageRole = (message) => {
  return message.author.username === 'AI_Assistant' ? 'assistant' : 'user';
};

// 去掉内容开头的思考模式 prompt，仅用于前端展示，不把 prompt 词暴露给用户
const stripModePromptFromContent = (content) => {
  if (!content || typeof content !== 'string') return content;
  let text = content.trim();
  for (const m of MODES) {
    const p = (m.prompt || '').trim();
    if (p && text.startsWith(p)) {
      text = text.slice(p.length).trim();
      break;
    }
  }
  return text || content;
};

// 展示用内容：用户消息去掉模式 prompt，AI 消息原样
const getDisplayContent = (message) => {
  return getMessageRole(message) === 'user'
    ? stripModePromptFromContent(message.content)
    : (message.content || '');
};

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesArea.value) {
      messagesArea.value.scrollTop = messagesArea.value.scrollHeight;
    }
  });
};

// 处理文件选择
const handleFileSelect = async (file) => {
  if (!file) return; // 如果没有文件则直接返回

  // 判断是否为文本文件
  const isTextFile = (
    file.type.startsWith('text') || // 以text开头的MIME类型
    file.name.endsWith('.txt') || // .txt文件
    file.name.endsWith('.md') || // .md文件
    file.name.endsWith('.csv') || // .csv文件
    file.name.endsWith('.json') // .json文件
  );

  if (isTextFile) {
    // 读取文本内容
    const reader = new FileReader();
    reader.onload = () => {
      attachedFile.value = {
        name: file.name,
        type: file.type,
        content: reader.result, // 文本内容
      };
    };
    reader.readAsText(file, 'utf-8'); // 以UTF-8编码读取文件
    return;
  }

  // 判断是否为图片文件
  if (file.type.startsWith('image/')) {
    try {
      // 使用OCR识别图片中的文字
      const { data: { text } } = await Tesseract.recognize(
        URL.createObjectURL(file), // 创建文件URL
        'eng', // 语言，根据需要调整
        { logger: m => console.log(m) } // 日志记录器
      );
      attachedFile.value = {
        name: file.name,
        type: file.type,
        content: text, // OCR 提取的文本
      };
    } catch (error) {
      console.error('OCR failed:', error);
      userInput.value += `\n[图片分析失败: ${file.name}]`;
    }
    return;
  }

  // 非文本/图片文件，走原有上传逻辑
  const formData = new FormData();
  formData.append('file', file);

  try {
    // 上传文件到服务器
    const response = await apiClient.post('/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    attachedFile.value = {
      name: file.name,
      type: file.type,
      url: response.data.url, // 服务器返回的文件URL
    };
  } catch (error) {
    console.error('File upload failed:', error);
    userInput.value += `\n[文件上传失败: ${file.name}]`;
  }
};

// 移除附件
const removeAttachment = () => {
  attachedFile.value = null;
};

// 获取历史消息
const fetchMessages = async (id) => {
  if (!id) {
    messages.value = []; // 如果没有ID则清空消息
    return;
  }
  isLoading.value = true; // 设置加载状态
  try {
    // 从API获取指定问题的所有回答
    const response = await apiClient.get(`/questions/${id}/answers/`);
    messages.value = response.data; // 设置消息列表
    scrollToBottom(); // 滚动到底部
  } catch (error) {
    console.error('获取历史消息失败:', error);
    // 显示错误消息
    messages.value = [{ id: 'error', author: { username: 'AI_Assistant' }, content: '无法加载对话内容。' }];
  } finally {
    isLoading.value = false; // 结束加载状态
  }
};

// 格式化消息内容，支持Markdown和数学公式
const formatMessage = (content) => {
  if (!content) return ''; // 如果没有内容则返回空字符串
  let html = content; // 初始化HTML变量

  // 先处理数学公式（同原有逻辑）
  // 处理 ```math 和 ```latex 代码块
  html = html.replace(/```(?:math|latex)\s*([\s\S]+?)```/g, (match, formula) => {
    try {
      return `<div class="math-block">${katex.renderToString(formula.trim(), { displayMode: true })}</div>`;
    } catch (e) {
      return `<pre class="math-error">${formula}</pre>`;
    }
  });

  // 处理行内数学公式 [formula]
  html = html.replace(/\[([^\[\]\n]+)\]/g, (match, formula) => {
    try {
      return katex.renderToString(formula, { displayMode: false });
    } catch (e) {
      return `<span class="math-error">${formula}</span>`;
    }
  });

  // 处理行内数学公式 \(formula\)
  html = html.replace(/\\\(([^\)]+)\\\)/g, (match, formula) => {
    try {
      return katex.renderToString(formula, { displayMode: false });
    } catch (e) {
      return `<span class="math-error">${formula}</span>`;
    }
  });

  // 处理块级数学公式 \[formula\]
  html = html.replace(/\\\[([\s\S]+?)\\\]/g, (match, formula) => {
    try {
      return `<div class="math-block">${katex.renderToString(formula.trim(), { displayMode: true })}</div>`;
    } catch (e) {
      return `<pre class="math-error">${formula}</pre>`;
    }
  });

  // 处理块级数学公式 $$formula$$
  html = html.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
    try {
      return `<div class="math-block">${katex.renderToString(formula.trim(), { displayMode: true })}</div>`;
    } catch (e) {
      return `<pre class="math-error">${formula}</pre>`;
    }
  });

  // 处理行内数学公式 $formula$
  html = html.replace(/\$(.+?)\$/g, (match, formula) => {
    try {
      return katex.renderToString(formula, { displayMode: false });
    } catch (e) {
      return `<span class="math-error">${formula}</span>`;
    }
  });

  // 使用自定义 Renderer 确保图片正确渲染
  const renderer = new marked.Renderer();
  renderer.image = (href, title, text) => {
    return `<img src="${href}" alt="${text}" style="max-width: 100%; height: auto;" />`;
  };

  // 最后用 marked 渲染 Markdown
  html = marked(html, { renderer });
  return html;
};

// 复制到剪贴板
const copyToClipboard = async (text) => {
  if (!text) return; // 如果没有文本则直接返回
  try {
    // 尝试使用现代剪贴板API
    await navigator.clipboard.writeText(text);
  } catch (e) {
    // 降级方案：使用传统方法
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
};

// 停止AI回答生成
const stopAnswer = () => {
  isStopped.value = true; // 设置停止标志
  if (controllerRef) controllerRef.abort(); // 中止请求
};

// 处理发送消息
const handleSendMessage = async () => {
  const hasText = !!userInput.value.trim(); // 是否有文本内容
  const hasAttachment = !!attachedFile.value; // 是否有附件

  // 如果没有文本和附件，或者正在发送，则直接返回
  if ((!hasText && !hasAttachment) || isSending.value) return;

  let displayedMessage = sanitizeText(userInput.value); // 显示给用户的消息内容

  // 只拼接文件名提示，避免展开内容
  if (hasAttachment) {
    const EOL = displayedMessage ? '\n\n' : ''; // 换行符
    displayedMessage += `${EOL}【已附加文件：${attachedFile.value.name}】`;
  }

  // 拼接模式前缀和完整内容（发送给后端）
  const modePrompt = MODES.find(m => m.key === mode.value)?.prompt || ''; // 获取当前模式的提示词
  let userMessageContent = sanitizeText(userInput.value); // 发送给后端的完整内容
  if (hasAttachment && attachedFile.value.content) {
    // 如果有附件内容，则拼接附件内容
    const EOL = userMessageContent ? '\n\n' : '';
    userMessageContent += `${EOL}【附加文件内容：${attachedFile.value.name}】\n${attachedFile.value.content}`;
  } else if (hasAttachment && attachedFile.value.url) {
    // 如果有附件URL，则拼接附件链接
    const EOL = userMessageContent ? '\n\n' : '';
    userMessageContent += `${EOL}![${attachedFile.value.name}](${attachedFile.value.url})`;
  }
  // 如果消息不是以模式提示开头，则添加模式提示
  if (!userMessageContent.startsWith(modePrompt)) {
    userMessageContent = `${sanitizeText(modePrompt)}\n${userMessageContent}`;
  }

  // 对话列表标题：仅用户输入，不含模式 prompt（在清空输入前保存）
  const displayTitle = sanitizeText(userInput.value).trim().slice(0, 50) || undefined;

  userInput.value = ''; // 清空输入框
  removeAttachment(); // 移除附件

  isSending.value = true; // 设置发送状态
  isStreaming.value = true; // 设置流式传输状态
  isStopped.value = false; // 重置停止标志
  
  // 创建临时用户消息
  let tempUserMsg = {
    id: Date.now(),
    content: displayedMessage,
    author: { username: 'currentUser' },
  };
  // 创建临时AI消息
  let tempAIMessage = {
    id: Date.now() + 1,
    content: '',
    author: { username: 'AI_Assistant' },
  };
  // 将临时消息添加到消息列表
  messages.value = [...messages.value, tempUserMsg, tempAIMessage];
  scrollToBottom(); // 滚动到底部
  
  try {
    const csrfToken = getCookie('csrftoken'); // 获取CSRF令牌
    controllerRef = new AbortController(); // 创建中止控制器
    // 必须用相对路径，走 Vite 代理，这样和登录同源，浏览器才会带 session cookie
    const response = await fetch('/api/chat/stream/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        question: userMessageContent,
        conversation_id: currentConversationId.value,
        title: displayTitle, // 对话列表标题只用用户输入，不含模式 prompt
      }),
      signal: controllerRef.signal, // 绑定中止信号
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`服务器错误: ${response.status} ${errorText}`);
    } // 检查响应状态
    
    const reader = response.body.getReader(); // 获取流式读取器
    readerRef = reader;
    const decoder = new TextDecoder('utf-8'); // 创建文本解码器
    let firstChunk = true; // 是否是第一个数据块
    
    // 循环读取流式数据
    while (true) {
      if (isStopped.value) break; // 如果已停止则跳出循环
      const { done, value } = await reader.read(); // 读取数据块
      if (done) break; // 如果读取完成则跳出循环
      
      let chunk = decoder.decode(value, { stream: true }); // 解码数据块
      
      if (firstChunk) {
        firstChunk = false;
        // 检查是否包含对话ID信息
        const idMatch = chunk.match(/^CONVERSATION_ID:(\d+)\n/);
        if (idMatch) {
          const newId = parseInt(idMatch[1], 10);
          if (!currentConversationId.value) {
            currentConversationId.value = newId;
            // 延迟发送新对话开始事件
            setTimeout(() => emit('new-conversation-started', newId), 800);
          }
          chunk = chunk.substring(idMatch[0].length); // 移除对话ID部分
        }
      }
      
      tempAIMessage.content += chunk; // 将数据块添加到AI消息内容
      messages.value = [...messages.value]; // 更新消息列表以触发响应式更新
      scrollToBottom(); // 滚动到底部
    }
  } catch (error) {
    // 如果出错，在AI消息末尾添加错误提示
    tempAIMessage.content += '\n[AI回答失败]';
    messages.value = [...messages.value];
    console.error('Streaming error:', error);
  } finally {
    isSending.value = false; // 重置发送状态
    isStreaming.value = false; // 重置流式传输状态
    readerRef = null; // 清空读取器引用
    controllerRef = null; // 清空中止控制器引用
    scrollToBottom(); // 滚动到底部
  }
};

// 处理全局拖拽进入事件
const handleGlobalDragEnter = (e) => {
  if (e.dataTransfer && e.dataTransfer.types && e.dataTransfer.types.includes('Files')) {
    dragCounter++; // 增加拖拽计数器
    showDropMask.value = true; // 显示拖拽遮罩
  }
};

// 处理全局拖拽离开事件
const handleGlobalDragLeave = (e) => {
  dragCounter--; // 减少拖拽计数器
  if (dragCounter <= 0) {
    showDropMask.value = false; // 隐藏拖拽遮罩
    dragCounter = 0; // 重置计数器
  }
};

// 处理全局拖拽放置事件
const handleGlobalDrop = (e) => {
  showDropMask.value = false; // 隐藏拖拽遮罩
  dragCounter = 0; // 重置计数器
  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    handleFileSelect(e.dataTransfer.files[0]); // 处理拖拽的文件
  }
};

// 处理输入区域的拖拽放置事件
const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]; // 获取拖拽的文件
  if (file) {
    handleFileSelect(file); // 处理文件
  }
};

// 处理文件选择变化事件
const handleFileChange = (e) => {
  const file = e.target.files[0]; // 获取选择的文件
  if (file) {
    handleFileSelect(file); // 处理文件
  }
  // 重置输入值以允许选择相同文件
  e.target.value = '';
};

// 触发文件输入框点击
const triggerFileInput = () => {
  fileInput.value.click(); // 模拟点击文件输入框
};

// 监听对话ID变化
watch(() => props.conversationId, (newId) => {
  currentConversationId.value = newId; // 更新当前对话ID
  if (!isStreaming.value) {
    fetchMessages(newId); // 如果不是流式传输状态，则获取消息
  }
}, { immediate: true }); // 立即执行一次

// 点击页面其他区域关闭思考模式下拉
const closeModeDropdown = (e) => {
  if (modeSelectWrap.value && !modeSelectWrap.value.contains(e.target)) {
    modeDropdownOpen.value = false;
  }
};

// 组件挂载时的生命周期钩子
onMounted(() => {
  // 添加全局拖拽事件监听器
  window.addEventListener('dragenter', handleGlobalDragEnter);
  window.addEventListener('dragleave', handleGlobalDragLeave);
  window.addEventListener('drop', handleGlobalDrop);
  document.addEventListener('click', closeModeDropdown);
});

// 组件卸载前的生命周期钩子
onBeforeUnmount(() => {
  window.removeEventListener('dragenter', handleGlobalDragEnter);
  window.removeEventListener('dragleave', handleGlobalDragLeave);
  window.removeEventListener('drop', handleGlobalDrop);
  document.removeEventListener('click', closeModeDropdown);
});

</script>

<style scoped>
/* 导入数学公式样式 */
@import 'katex/dist/katex.min.css';

/* 聊天面板主容器样式 */
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 消息区域样式 */
.messages-area {
  flex-grow: 1; /* 占据剩余空间 */
  overflow-y: auto; /* 垂直滚动 */
  padding: 1rem;
}

/* 消息样式 */
.message {
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
}

/* 用户消息样式 */
.message.user {
  align-items: flex-end; /* 右对齐 */
}

/* AI助手消息样式 */
.message.assistant {
  align-items: flex-start; /* 左对齐 */
}

/* 消息内容样式 */
.message-content {
  max-width: 80%; /* 最大宽度80% */
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background-color: #f0f0f0;
  line-height: 1.6;
}

/* 用户消息内容样式 */
.message.user .message-content {
  background-color: #007bff;
  color: white;
}

/* 消息内容中的图片样式 */
.message-content img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0.5rem 0;
}

/* 作者标签样式 */
.author-tag {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
}

/* AI图标样式 */
.ai-icon {
  margin-right: 6px;
}

/* 输入区域样式 */
.input-area {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  border-top: 1px solid #ccc;
  background-color: #f8f9fa;
}

/* 输入控制区域样式 */
.input-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.input-controls > button,
.input-controls > .mode-select-wrap {
  margin-left: 0;
}

/* 文本输入框样式 */
textarea {
  flex-grow: 1; /* 占据剩余空间 */
  padding: 0.75rem;
  border-radius: 5px;
  border: 1px solid #ccc;
  resize: none; /* 禁止调整大小 */
  height: 60px;
  font-size: 1rem;
  line-height: 1.5;
}

/* 按钮通用样式 */
button {
  margin-left: 1rem;
  padding: 0 1.5rem;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
}

/* 禁用状态按钮样式 */
button:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

/* 加载消息提示样式 */
.loading-messages {
  text-align: center;
  color: #6c757d;
  padding: 2rem;
}

/* 附件预览样式 */
.attachment-preview {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: #e9ecef;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 附件信息样式 */
.attachment-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}

/* 附件缩略图样式 */
.attachment-thumbnail {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 3px;
}

/* 移除附件按钮样式 */
.remove-attachment-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #888;
  padding: 0 0.5rem;
}

/* 移除附件按钮悬停样式 */
.remove-attachment-btn:hover {
  color: #e74c3c;
}

/* 数学公式块样式 */
.math-block {
  margin: 1em 0;
  text-align: left;
}

/* 数学公式错误样式 */
.math-error {
  color: red;
  background: #fff0f0;
  padding: 2px 4px;
  border-radius: 3px;
}

/* 消息内容包装器样式 */
.message-content-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 4px;
}

/* 复制按钮样式 */
.copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #888;
  margin-left: 2px;
  padding: 2px 4px;
  border-radius: 3px;
  transition: background 0.2s;
}

/* 复制按钮悬停样式 */
.copy-btn:hover {
  background: #e9ecef;
  color: #007bff;
}

/* 停止按钮样式 */
.stop-btn {
  margin-left: 8px;
  background: #e74c3c;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0 14px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}

/* 停止按钮悬停样式 */
.stop-btn:hover {
  background: #c0392b;
}

/* 拖拽遮罩样式 */
.drop-mask {
  position: fixed; /* 固定定位 */
  left: 0; top: 0; right: 0; bottom: 0; /* 覆盖整个屏幕 */
  background: rgba(255,255,255,0.95);
  z-index: 2000; /* 高层级 */
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 拖拽提示内容样式 */
.drop-mask-content {
  text-align: center;
}

/* 拖拽图标样式 */
.drop-icon {
  font-size: 64px;
  margin-bottom: 18px;
}

/* 拖拽标题样式 */
.drop-title {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 10px;
}

/* 拖拽描述样式 */
.drop-desc {
  font-size: 15px;
  color: #888;
}

/* 上传提示样式 */
.uploading-tip {
  text-align: center;
  color: #6c757d;
  padding: 1rem;
}

/* 思考模式：选择后仅显示当前模式，不常驻三个按钮 */
.mode-select-wrap {
  position: relative;
  margin-left: 0.5rem;
}
.mode-current {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #e8f0fe;
  color: #1967d2;
  border: 1px solid #aecbfa;
  border-radius: 6px;
  padding: 0.35rem 0.6rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}
.mode-current:hover {
  background: #d2e3fc;
}
.mode-current.open {
  background: #d2e3fc;
  border-color: #1967d2;
}
.mode-current-label {
  white-space: nowrap;
}
.mode-arrow {
  font-size: 0.75rem;
  opacity: 0.8;
  transition: transform 0.2s;
}
.mode-current.open .mode-arrow {
  transform: rotate(180deg);
}
.mode-dropdown {
  position: absolute;
  bottom: 100%;
  right: 0;
  margin-bottom: 4px;
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 4px;
  min-width: 120px;
  z-index: 50;
}
.mode-option {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #333;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}
.mode-option:hover {
  background: #f0f0f0;
}
.mode-option.active {
  background: #e8f0fe;
  color: #1967d2;
}
.mode-drop-enter-active,
.mode-drop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.mode-drop-enter-from,
.mode-drop-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style> 