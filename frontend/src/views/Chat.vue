<template>
  <div class="chat-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>Dummy System</h2>
        <button @click="goToHome" class="btn btn-primary btn-sm">
          <span>+</span> 新对话
        </button>
      </div>
      
      <div class="conversation-list">
        <TransitionGroup name="list" tag="div">
          <div
            v-for="conv in chatStore.conversations"
            :key="conv.id"
            :class="['conversation-item', { active: currentConversationId === conv.id }]"
            @click="selectConversation(conv.id)"
          >
            <span class="conversation-title">{{ conv.title }}</span>
            <span v-if="isConversationStreaming(conv.id)" class="conversation-status">生成中</span>
            <button 
              class="delete-btn"
              :disabled="isConversationStreaming(conv.id)"
              @click.stop="deleteConversation(conv.id)"
              :title="isConversationStreaming(conv.id) ? '该对话正在生成，暂时不能删除' : '删除对话'"
            >
              ×
            </button>
          </div>
        </TransitionGroup>
        
        <div v-if="chatStore.conversations.length === 0" class="empty-state">
          <p>暂无对话</p>
          <p class="text-muted">输入消息开始新对话</p>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <div class="user-info">
          <span>{{ authStore.user?.username }}</span>
          <span v-if="authStore.isAdmin" class="admin-badge">管理员</span>
        </div>
        <div class="sidebar-actions">
          <router-link v-if="authStore.isAdmin" to="/admin" class="btn btn-ghost btn-sm">
            设置
          </router-link>
          <button @click="handleLogout" class="btn btn-ghost btn-sm">
            退出
          </button>
        </div>
      </div>
    </aside>
    
    <main class="chat-main">
      <!-- 起始页 -->
      <div v-if="!currentConversationId" class="welcome-screen">
        <div class="welcome-content">
          <h1 class="welcome-title">
            <span class="greeting">{{ authStore.user?.username }}，你好</span>
          </h1>
          <p class="welcome-subtitle">需要我为你做些什么？</p>
        </div>
        
        <!-- 起始页的模型选择和输入区域 -->
        <div class="welcome-input-section">
          <div 
            v-if="isModelDropdownOpen || isReasoningDropdownOpen" 
            class="dropdown-overlay" 
            @click="closeAllDropdowns"
          ></div>
          
          <div class="welcome-controls">
            <div class="custom-dropdown">
              <button 
                class="dropdown-trigger" 
                :class="{ active: isModelDropdownOpen }"
                @click="toggleModelDropdown"
              >
                <span class="dropdown-label">模型：</span>
                <span class="model-name">{{ currentModelName }}</span>
                <span class="chevron">▼</span>
              </button>
              
              <transition name="dropdown-fade">
                <div v-show="isModelDropdownOpen" class="dropdown-menu model-menu welcome-dropdown">
                  <div class="dropdown-header">选择大模型</div>
                  <div 
                    v-for="model in chatStore.models" 
                    :key="model.id"
                    class="dropdown-item"
                    :class="{ selected: selectedModelId === model.id }"
                    @click="selectModel(model.id)"
                  >
                    <span class="item-title">{{ model.name }}</span>
                    <span v-if="selectedModelId === model.id" class="check-icon">✓</span>
                  </div>
                </div>
              </transition>
            </div>

            <div v-if="showReasoningSelector" class="custom-dropdown">
              <button 
                class="dropdown-trigger reasoning-trigger" 
                :class="{ active: isReasoningDropdownOpen }"
                @click="toggleReasoningDropdown"
              >
                <span class="dropdown-label">思考强度：</span>
                <span class="reasoning-label">{{ currentReasoningLabel }}</span>
                <span class="chevron">▼</span>
              </button>
              
              <transition name="dropdown-fade">
                <div v-show="isReasoningDropdownOpen" class="dropdown-menu reasoning-menu welcome-dropdown">
                  <div class="dropdown-header">思考强度</div>
                  <div 
                    v-for="option in reasoningOptions" 
                    :key="option.value"
                    class="dropdown-item"
                    :class="{ selected: chatStore.reasoningEffort === option.value }"
                    @click="selectReasoning(option.value)"
                  >
                    <span class="item-title">{{ option.label }}</span>
                    <span v-if="chatStore.reasoningEffort === option.value" class="check-icon">✓</span>
                  </div>
                </div>
              </transition>
            </div>
          </div>
          
          <form @submit.prevent="hasAnyStreamingConversation ? handleStop() : sendFirstMessage()" class="welcome-input-form">
            <textarea
              v-model="inputMessage"
              class="input welcome-input"
              placeholder="在此处输入消息开始新对话..."
              @keydown.enter.exact.prevent="hasAnyStreamingConversation ? handleStop() : sendFirstMessage()"
              :disabled="hasAnyStreamingConversation"
              rows="1"
            ></textarea>
            <button 
              v-if="hasAnyStreamingConversation"
              type="button"
              class="btn btn-danger send-btn"
              @click="handleStop"
            >
              {{ stopButtonLabel }}
            </button>
            <button 
              v-else
              type="submit"
              class="btn btn-primary send-btn"
              :disabled="!canSendFirstMessage"
            >
              发送
            </button>
          </form>
        </div>
      </div>
      
      <!-- 对话页 -->
      <template v-else>
        <header class="chat-header">
          <h3>{{ chatStore.currentConversation?.title || '新对话' }}</h3>
          
          <div 
            v-if="isModelDropdownOpen || isReasoningDropdownOpen" 
            class="dropdown-overlay" 
            @click="closeAllDropdowns"
          ></div>

          <div class="header-controls">
            <div class="custom-dropdown">
              <button 
                class="dropdown-trigger" 
                :class="{ active: isModelDropdownOpen }"
                @click="toggleModelDropdown"
              >
                <span class="dropdown-label">模型：</span>
                <span class="model-name">{{ currentModelName }}</span>
                <span class="chevron">▼</span>
              </button>
              
              <transition name="dropdown-fade">
                <div v-show="isModelDropdownOpen" class="dropdown-menu model-menu">
                  <div class="dropdown-header">选择大模型</div>
                  <div 
                    v-for="model in chatStore.models" 
                    :key="model.id"
                    class="dropdown-item"
                    :class="{ selected: selectedModelId === model.id }"
                    @click="selectModel(model.id)"
                  >
                    <span class="item-title">{{ model.name }}</span>
                    <span v-if="selectedModelId === model.id" class="check-icon">✓</span>
                  </div>
                </div>
              </transition>
            </div>

            <div v-if="showReasoningSelector" class="custom-dropdown">
              <button 
                class="dropdown-trigger reasoning-trigger" 
                :class="{ active: isReasoningDropdownOpen }"
                @click="toggleReasoningDropdown"
              >
                <span class="dropdown-label">思考强度：</span>
                <span class="reasoning-label">{{ currentReasoningLabel }}</span>
                <span class="chevron">▼</span>
              </button>
              
              <transition name="dropdown-fade">
                <div v-show="isReasoningDropdownOpen" class="dropdown-menu reasoning-menu">
                  <div class="dropdown-header">思考强度</div>
                  <div 
                    v-for="option in reasoningOptions" 
                    :key="option.value"
                    class="dropdown-item"
                    :class="{ selected: chatStore.reasoningEffort === option.value }"
                    @click="selectReasoning(option.value)"
                  >
                    <span class="item-title">{{ option.label }}</span>
                    <span v-if="chatStore.reasoningEffort === option.value" class="check-icon">✓</span>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </header>
        
        <div class="messages-container" ref="messagesContainer">
          <div class="messages-center-wrapper">
            <TransitionGroup name="message" tag="div" class="message-list-wrapper">
              <div 
                v-for="message in chatStore.messages" 
                :key="message._clientId || message.id"
                :class="['message', message.role]"
                @mouseenter="hoveredMessageId = message.id"
                @mouseleave="hoveredMessageId = null"
              >
                <!-- 用户消息 -->
                <template v-if="message.role === 'user'">
                  <div class="user-message-wrapper">
                    <div class="message-bubble">{{ message.content }}</div>
                    <div class="user-message-actions" :class="{ visible: hoveredMessageId === message.id }">
                      <button class="action-btn" @click="copyMessageContent(message.content)" title="复制">
                        <img :src="iconCopy" class="action-icon-img" alt="" />
                      </button>
                      <button 
                        v-if="isLatestUserMessage(message.id)"
                        class="action-btn" 
                        @click="handleRevertToMessage(message)"
                        title="返回"
                      >
                        <img :src="iconReturn" class="action-icon-img" alt="" />
                      </button>
                    </div>
                  </div>
                </template>
                
                <!-- 助手消息：按顺序渲染 parts -->
                <template v-else-if="message.role === 'assistant'">
                  <div class="assistant-message-content">
                    <template v-for="(part, idx) in getMessageParts(message)" :key="idx">
                      <div v-if="part.type === 'content'" v-html="renderMarkdown(part.text)"></div>
                      <div v-else-if="part.type === 'tool_call'" class="tool-calls completed">
                        <div class="tool-call" :class="{ collapsed: part.collapsed }" @click="part.collapsed = !part.collapsed">
                          <span class="tool-icon">✓</span>
                          <span class="tool-name">已调用: {{ part.name }}</span>
                          <span class="collapse-hint">{{ part.collapsed ? '展开' : '收起' }}</span>
                        </div>
                      </div>
                    </template>
                  </div>
                  <div class="assistant-message-actions" :class="{ visible: hoveredMessageId === message.id }">
                    <button class="action-btn" @click="copyMessageMarkdown(message)" title="复制">
                      <img :src="iconCopy" class="action-icon-img" alt="" />
                    </button>
                    <button 
                      v-if="isLatestAssistantMessage(message.id)"
                      class="action-btn" 
                      @click="handleRegenerate(message.id)"
                      :disabled="hasAnyStreamingConversation"
                      title="重新生成"
                    >
                      <img :src="iconRedo" class="action-icon-img" alt="" />
                    </button>
                  </div>
                </template>
              </div>
              
              <div v-if="isStreaming" :key="streamingMessageId" class="message assistant streaming-message">
                <div class="assistant-message-content">
                  <!-- 思考状态提示 -->
                  <div v-if="streamingParts.length === 0" class="thinking-indicator">
                    <span class="thinking-dots">
                      <span></span><span></span><span></span>
                    </span>
                    <span class="thinking-text">正在思考...</span>
                  </div>
                  
                  <!-- 按时间顺序渲染内容和工具调用 -->
                  <template v-for="(part, index) in streamingParts" :key="index">
                    <!-- 文字内容 -->
                    <div v-if="part.type === 'content'" class="streaming-text-part">
                      <div v-html="renderMarkdown(part.text)"></div>
                    </div>
                    
                    <!-- 工具调用 -->
                    <div v-else-if="part.type === 'tool_call'" class="tool-calls" :class="{ active: !part.toolCall.result, completed: part.toolCall.result }">
                      <div class="tool-call">
                        <span v-if="!part.toolCall.result" class="tool-icon spinning">⚙️</span>
                        <span v-else class="tool-icon">✓</span>
                        <span class="tool-name">{{ part.toolCall.result ? '已调用' : '正在调用' }}: {{ part.toolCall.name }}</span>
                      </div>
                    </div>
                  </template>
                  
                  <!-- 流式光标 -->
                  <span v-if="streamingParts.length > 0" class="typing-cursor"></span>
                </div>
              </div>
            </TransitionGroup>
          </div>
        </div>
        
        <div class="input-area">
          <form @submit.prevent="handleSubmit" class="input-form">
            <textarea
              v-model="inputMessage"
              class="input message-input"
              placeholder="在此处输入消息。回车键发送；Shift+回车键换行。"
              @keydown.enter.exact.prevent="handleSubmit"
              :disabled="hasAnyStreamingConversation"
              rows="1"
            ></textarea>
            <button 
              v-if="hasAnyStreamingConversation"
              type="button" 
              class="btn btn-danger send-btn"
              @click="handleStop"
            >
              {{ stopButtonLabel }}
            </button>
            <button 
              v-else
              type="submit" 
              class="btn btn-primary send-btn"
              :disabled="!inputMessage.trim()"
            >
              发送
            </button>
          </form>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import api from '@/api'
import socketService from '@/api/socket'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import iconCopy from '../../assets/copy.svg'
import iconRedo from '../../assets/redo.svg'
import iconReturn from '../../assets/return.svg'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const inputMessage = ref('')
const messagesContainer = ref(null)
const hoveredMessageId = ref(null)

// Custom Dropdown States
const selectedModelId = ref(null)
const isModelDropdownOpen = ref(false)
const isReasoningDropdownOpen = ref(false)

const reasoningOptions = [
  { value: 'auto', label: '自动' },
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' }
]
const showReasoningSelector = computed(() => {
  const model = chatStore.models.find(m => m.id === selectedModelId.value)
  return model?.is_reasoning
})

const currentModelName = computed(() => {
  const model = chatStore.models.find(m => m.id === selectedModelId.value)
  if (model) {
    return model.name
  }
  return chatStore.models.length > 0 ? '选择模型' : '暂无可用模型'
})

const currentReasoningLabel = computed(() => {
  const opt = reasoningOptions.find(o => o.value === chatStore.reasoningEffort)
  return opt ? opt.label : '自动'
})

const canSendFirstMessage = computed(() => {
  return Boolean(inputMessage.value.trim() && selectedModelId.value && !hasAnyStreamingConversation.value)
})

const currentConversationId = computed(() => chatStore.currentConversationId)
const currentStreamingState = computed(() => chatStore.getStreamingState(currentConversationId.value))
const isStreaming = computed(() => currentStreamingState.value.isStreaming)
const streamingParts = computed(() => currentStreamingState.value.streamingParts)
const streamingMessageId = computed(() => currentStreamingState.value.streamingMessageId)
const hasAnyStreamingConversation = computed(() => chatStore.hasAnyStreamingConversation)
const activeStreamingConversationId = computed(() => chatStore.activeStreamingConversationId)
const stopButtonLabel = computed(() => {
  return isStreaming.value ? '停止' : '停止后台回答'
})

function isConversationStreaming(conversationId) {
  return chatStore.isConversationStreaming(conversationId)
}

// Configure marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true
})

function renderMarkdown(content) {
  if (!content) return ''
  const html = marked.parse(content)
  return DOMPurify.sanitize(html)
}

function getMessageParts(message) {
  // 如果消息已经有 parts（从数据库或流式输出保存的），直接使用
  if (message.parts && message.parts.length > 0) {
    return message.parts
  }
  
  // 否则，从 content 和 tool_calls 生成 parts（兼容旧消息）
  const parts = []
  
  if (message.content) {
    parts.push({ type: 'content', text: message.content })
  }
  
  if (message.tool_calls && message.tool_calls.length > 0) {
    for (const tc of message.tool_calls) {
      parts.push({
        type: 'tool_call',
        name: tc.function?.name || tc.name || 'unknown',
        collapsed: true
      })
    }
  }
  
  return parts
}

let scrollRafId = null
function scrollToBottom() {
  if (scrollRafId) return
  scrollRafId = requestAnimationFrame(() => {
    scrollRafId = null
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Dropdown Actions
function toggleModelDropdown() {
  isModelDropdownOpen.value = !isModelDropdownOpen.value
  isReasoningDropdownOpen.value = false
}

function toggleReasoningDropdown() {
  isReasoningDropdownOpen.value = !isReasoningDropdownOpen.value
  isModelDropdownOpen.value = false
}

function closeAllDropdowns() {
  isModelDropdownOpen.value = false
  isReasoningDropdownOpen.value = false
}

function selectModel(id) {
  const model = chatStore.models.find(m => m.id === id)
  if (model) {
    chatStore.setSelectedModel(model)
    selectedModelId.value = id
    handleModelChange()
  }
  closeAllDropdowns()
}

function selectReasoning(value) {
  chatStore.setReasoningEffort(value)
  closeAllDropdowns()
}

function syncHomeModelSelection() {
  const defaultModel = chatStore.models.find(m => m.is_default) || chatStore.models[0] || null

  if (defaultModel) {
    selectedModelId.value = defaultModel.id
    chatStore.setSelectedModel(defaultModel)
  } else {
    selectedModelId.value = null
  }

  if (!defaultModel || !defaultModel.is_reasoning) {
    chatStore.resetReasoningEffort()
  }
}

// 回到起始页
function goToHome() {
  if (currentConversationId.value) {
    socketService.leaveConversation(currentConversationId.value)
  }
  chatStore.clearCurrent()
  syncHomeModelSelection()
}

// 从起始页发送第一条消息（创建对话并发送）
async function sendFirstMessage() {
  if (!inputMessage.value.trim()) return
  if (!selectedModelId.value) {
    alert('暂无可用模型，请先在管理面板配置并启用模型')
    return
  }
  
  const message = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 先创建对话
  const conv = await chatStore.createConversationWithModel(selectedModelId.value, chatStore.reasoningEffort)
  socketService.joinConversation(conv.id)
  
  // 添加用户消息占位
  const clientId = `pending-${Date.now()}`
  const placeholder = {
    id: clientId,
    _clientId: clientId,
    conversation_id: conv.id,
    role: 'user',
    content: message,
    created_at: new Date().toISOString(),
    pending: true
  }
  chatStore.addMessage(placeholder)
  
  await nextTick()
  scrollToBottom()
  
  // 发送消息
  socketService.sendMessage(
    conv.id,
    message,
    selectedModelId.value,
    chatStore.reasoningEffort
  )
}

async function selectConversation(conversationId) {
  if (currentConversationId.value === conversationId) return

  if (currentConversationId.value) {
    socketService.leaveConversation(currentConversationId.value)
  }

  await chatStore.loadConversation(conversationId)
  
  // 同步模型选择
  if (chatStore.selectedModel) {
    selectedModelId.value = chatStore.selectedModel.id
  }
  
  socketService.joinConversation(conversationId)
  scrollToBottom()
}

async function deleteConversation(conversationId) {
  if (isConversationStreaming(conversationId)) {
    showToast('对话正在生成，暂时不能删除')
    return
  }

  if (confirm('确定要删除这个对话吗？')) {
    const wasCurrentConversation = currentConversationId.value === conversationId
    
    if (wasCurrentConversation) {
      socketService.leaveConversation(conversationId)
    }
    
    await chatStore.deleteConversation(conversationId)
    
    // 如果删除的是当前对话，回到起始页
    if (wasCurrentConversation) {
      chatStore.clearCurrent()
      syncHomeModelSelection()
    }
  }
}

function sendMessage() {
  if (!inputMessage.value.trim() || hasAnyStreamingConversation.value) return
  
  const message = inputMessage.value.trim()
  inputMessage.value = ''
  
  const clientId = `pending-${Date.now()}`
  const placeholder = {
    id: clientId,
    _clientId: clientId, 
    conversation_id: currentConversationId.value,
    role: 'user',
    content: message,
    created_at: new Date().toISOString(),
    pending: true
  }
  chatStore.addMessage(placeholder)
  scrollToBottom()

  socketService.sendMessage(
    currentConversationId.value, 
    message,
    selectedModelId.value,
    chatStore.reasoningEffort
  )
}

function handleSubmit() {
  if (isStreaming.value) {
    handleStop()
  } else {
    sendMessage()
  }
}

function handleStop() {
  if (!activeStreamingConversationId.value) return
  socketService.stopGeneration(activeStreamingConversationId.value)
}

function handleModelChange() {
  const model = chatStore.models.find(m => m.id === selectedModelId.value)
  if (model && !model.is_reasoning) {
    chatStore.resetReasoningEffort()
  }
}

// 检查是否是最新的用户消息
function isLatestUserMessage(messageId) {
  const userMessages = chatStore.messages.filter(m => m.role === 'user')
  if (userMessages.length === 0) return false
  return userMessages[userMessages.length - 1].id === messageId
}

// 检查是否是最新的助手消息（仅最新一条允许重新生成）
function isLatestAssistantMessage(messageId) {
  const assistantMessages = chatStore.messages.filter(m => m.role === 'assistant')
  if (assistantMessages.length === 0) return false
  return assistantMessages[assistantMessages.length - 1].id === messageId
}

// 复制消息内容（纯文本）
async function copyMessageContent(content) {
  try {
    await navigator.clipboard.writeText(content)
    showToast('已复制到剪贴板')
  } catch (err) {
    console.error('复制失败:', err)
    showToast('复制失败')
  }
}

// 复制助手消息（保留markdown格式）
async function copyMessageMarkdown(message) {
  try {
    const content = message.content || ''
    await navigator.clipboard.writeText(content)
    showToast('已复制到剪贴板')
  } catch (err) {
    console.error('复制失败:', err)
    showToast('复制失败')
  }
}

// 简单的提示函数
function showToast(message) {
  const toast = document.createElement('div')
  toast.className = 'toast-notification'
  toast.textContent = message
  document.body.appendChild(toast)
  setTimeout(() => {
    toast.classList.add('fade-out')
    setTimeout(() => toast.remove(), 300)
  }, 2000)
}

// 重新生成消息
async function handleRegenerate(messageId) {
  if (hasAnyStreamingConversation.value) return
  
  try {
    // 调用后端API删除该消息
    const response = await api.regenerateMessage(currentConversationId.value, messageId)
    
    if (response.success) {
      // 从本地状态中移除该助手消息
      const msgIndex = chatStore.messages.findIndex(m => m.id === messageId)
      if (msgIndex !== -1) {
        chatStore.messages.splice(msgIndex, 1)
      }
      
      // 获取最后一条用户消息内容
      const lastUserMessage = chatStore.messages.filter(m => m.role === 'user').pop()
      if (lastUserMessage) {
        // 发送重新生成请求（标记为regenerate，后端不会再次保存用户消息）
        socketService.sendMessage(
          currentConversationId.value,
          lastUserMessage.content,
          selectedModelId.value,
          chatStore.reasoningEffort,
          true  // isRegenerate = true
        )
      }
    }
  } catch (err) {
    console.error('重新生成失败:', err)
    showToast('重新生成失败: ' + (err.message || '未知错误'))
  }
}

// 返回到指定用户消息状态
async function handleRevertToMessage(message) {
  if (hasAnyStreamingConversation.value) {
    showToast('有对话正在生成，请先停止')
    return
  }

  if (!confirm('确定要返回到这条消息发送之前的状态吗？该消息及其后的所有回复都将被删除。')) {
    return
  }
  
  try {
    // 调用后端API删除该消息及其后续所有消息
    const response = await api.revertToMessage(currentConversationId.value, message.id)
    
    if (response.success) {
      // 将消息内容填充到输入框
      inputMessage.value = message.content
      
      // 从本地状态中移除该消息及其后续所有消息
      const msgIndex = chatStore.messages.findIndex(m => m.id === message.id)
      if (msgIndex !== -1) {
        chatStore.messages.splice(msgIndex)
      }
    }
  } catch (err) {
    console.error('返回失败:', err)
    alert('返回失败: ' + (err.message || '未知错误'))
  }
}

function handleLogout() {
  socketService.disconnect()
  chatStore.clearAllStreamingStates()
  chatStore.clearCurrent()
  authStore.logout()
  router.push('/login')
}

async function initializeChatView() {
  chatStore.initializeSocket()

  await Promise.all([
    chatStore.loadConversations(),
    chatStore.loadModels()
  ])

  if (!currentConversationId.value) {
    syncHomeModelSelection()
  } else {
    socketService.joinConversation(currentConversationId.value)
  }
}

function handlePageUnload() {
  if (!activeStreamingConversationId.value) return
  socketService.stopGeneration(activeStreamingConversationId.value)
  socketService.disconnect()
}

let streamingScrollInterval = null

function startStreamingScroll() {
  if (streamingScrollInterval) return
  streamingScrollInterval = setInterval(() => {
    if (isStreaming.value) {
      scrollToBottom()
    }
  }, 100)
}

function stopStreamingScroll() {
  if (streamingScrollInterval) {
    clearInterval(streamingScrollInterval)
    streamingScrollInterval = null
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', handlePageUnload)
  window.addEventListener('pagehide', handlePageUnload)

  initializeChatView()
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handlePageUnload)
  window.removeEventListener('pagehide', handlePageUnload)
  stopStreamingScroll()
  if (scrollRafId) {
    cancelAnimationFrame(scrollRafId)
    scrollRafId = null
  }
})

watch(() => chatStore.selectedModel, (model) => {
  if (model) {
    selectedModelId.value = model.id
  }
})

watch(() => chatStore.messages.length, () => {
  if (currentConversationId.value) {
    scrollToBottom()
  }
})

watch(isStreaming, (streaming) => {
  if (streaming) {
    startStreamingScroll()
  } else {
    stopStreamingScroll()
    scrollToBottom()
  }
})
</script>

<style lang="scss" scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

// Sidebar
.sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  h2 {
    font-size: 1.125rem;
    font-weight: 600;
  }
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  overflow-x: hidden;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: var(--border-radius);
  cursor: pointer;
  margin-bottom: 0.25rem;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: var(--bg-tertiary);
  }
  
  &.active {
    background-color: var(--primary-color);
    color: white;
    
    .delete-btn {
      color: rgba(255, 255, 255, 0.7);
      
      &:hover {
        color: white;
      }
    }
  }
}

.conversation-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.875rem;
}

.conversation-status {
  flex-shrink: 0;
  margin-left: 0.5rem;
  font-size: 0.75rem;
  color: var(--primary-color);
}

.delete-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
  
  .conversation-item:hover & {
    opacity: 1;
  }
  
  &:hover {
    color: var(--danger-color);
  }

  &:disabled {
    opacity: 0.35;
    cursor: not-allowed;
    color: var(--text-muted);
  }
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--text-muted);
  
  p:first-child {
    font-weight: 500;
    color: var(--text-secondary);
  }
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.admin-badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  background-color: var(--primary-color);
  color: white;
  border-radius: 999px;
}

.sidebar-actions {
  display: flex;
  gap: 0.5rem;
}

// Main Chat Area
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-secondary);
  overflow: hidden;
}

// Welcome Screen (Gemini Style)
.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 2rem;
}

.welcome-content {
  text-align: center;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.welcome-title {
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  background: linear-gradient(135deg, var(--primary-color) 0%, #8b5cf6 50%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle {
  font-size: 1.25rem;
  color: var(--text-secondary);
}

.welcome-input-section {
  width: 100%;
  max-width: 700px;
  animation: fadeInUp 0.6s ease-out 0.1s both;
}

.welcome-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  position: relative;
}

.welcome-dropdown {
  bottom: auto;
  top: calc(100% + 0.5rem);
}

.welcome-input-form {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  background: var(--bg-primary);
  padding: 1rem;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color);
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
  
  &:focus-within {
    box-shadow: 0 4px 25px rgba(99, 102, 241, 0.15);
    border-color: var(--primary-color);
  }
}

.welcome-input {
  flex: 1;
  resize: none;
  min-height: 48px;
  max-height: 200px;
  border: none;
  background: transparent;
  font-size: 1rem;
  
  &:focus {
    outline: none;
    box-shadow: none;
  }
}

/* ================= Header 与下拉框样式 ================= */
.chat-header {
  position: relative;
  padding: 1rem 1.5rem;
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  h3 {
    font-size: 1rem;
    font-weight: 600;
  }
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  position: relative;
}

.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 10;
  background: transparent;
}

.custom-dropdown {
  position: relative;
  z-index: 20;
}

.dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--bg-secondary, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 8px;
  color: var(--text-primary, #1e293b);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;

  &:hover {
    background: var(--bg-tertiary, #f1f5f9);
  }

  &.active {
    background: white;
    border-color: var(--primary-color, #6366f1);
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
  }

  .chevron {
    font-size: 0.6rem;
    color: var(--text-muted, #94a3b8);
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }

  &.active .chevron {
    transform: rotate(180deg);
  }
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 220px;
  background: var(--bg-primary, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
  
  &.reasoning-menu {
    min-width: 140px;
  }
}

.dropdown-header {
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  color: var(--text-muted, #64748b);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-primary, #1e293b);

  &:hover {
    background: var(--bg-secondary, #f8fafc);
  }

  &.selected {
    background: var(--primary-light, #eef2ff);
    color: var(--primary-color, #4f46e5);
    font-weight: 600;
  }

  .check-icon {
    font-weight: bold;
    font-size: 0.875rem;
  }
}

/* 下拉框动画 */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  transform-origin: top right;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-5px);
}

// Messages
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  scroll-behavior: smooth;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background-color: rgba(0,0,0,0.15);
    border-radius: 4px;
  }
}

.messages-center-wrapper {
  max-width: 50%;
  margin: 0 auto;
  min-width: 600px;
  
  @media (max-width: 1200px) {
    max-width: 70%;
  }
  
  @media (max-width: 900px) {
    max-width: 90%;
    min-width: unset;
  }
}

.message-list-wrapper {
  display: flex;
  flex-direction: column;
  position: relative;
}

.message {
  margin-bottom: 1.5rem;
  position: relative;
  
  &.user {
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
  }
  
  &.assistant {
    display: block;
  }
}

.user-message-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  max-width: 80%;
}

// 用户消息气泡样式
.message-bubble {
  padding: 0.875rem 1.125rem;
  border-radius: 18px 18px 4px 18px;
  background-color: var(--primary-color);
  color: white;
  line-height: 1.6;
  word-wrap: break-word;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

// 用户消息操作按钮
.user-message-actions {
  display: flex;
  gap: 0.25rem;
  align-items: center;
  margin-top: 0.5rem;
  height: 32px; /* 始终占位，避免悬停时上下闪动 */
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;

  &.visible {
    opacity: 1;
    pointer-events: auto;
  }
}

// 助手消息内容样式（无气泡）
.assistant-message-content {
  line-height: 1.7;
  color: var(--text-primary);
  
  :deep(p) {
    margin-bottom: 0.875rem;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  :deep(pre) {
    background-color: #1e293b;
    color: #e2e8f0;
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    margin: 0.875rem 0;
    
    code {
      background: none;
      padding: 0;
    }
  }
  
  :deep(code) {
    background-color: rgba(0,0,0,0.06);
    padding: 0.125rem 0.375rem;
    border-radius: 4px;
    font-size: 0.875em;
  }
  
  :deep(ul), :deep(ol) {
    margin: 0.875rem 0;
    padding-left: 1.5rem;
  }
  
  :deep(li) {
    margin-bottom: 0.375rem;
  }
  
  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 0.875rem 0;
  }
  
  :deep(th), :deep(td) {
    border: 1px solid var(--border-color);
    padding: 0.5rem;
    text-align: left;
  }
  
  :deep(blockquote) {
    border-left: 3px solid var(--primary-color);
    padding-left: 1rem;
    margin: 0.875rem 0;
    color: var(--text-secondary);
  }
  
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin-top: 1.25rem;
    margin-bottom: 0.625rem;
    font-weight: 600;
  }
  
  :deep(hr) {
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 1rem 0;
  }
}

// 助手消息操作按钮
.assistant-message-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  height: 32px; /* 始终占位，避免悬停时上下闪动 */
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;

  &.visible {
    opacity: 1;
    pointer-events: auto;
  }
}

// 通用操作按钮样式
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--border-radius-sm);
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
}

.action-icon-img {
  width: 16px;
  height: 16px;
  display: block;
  filter: saturate(0) brightness(0.55);
  transition: filter 0.2s ease;
}

.action-btn:hover .action-icon-img {
  filter: saturate(0) brightness(0.25);
}

// Toast通知样式
:global(.toast-notification) {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  z-index: 9999;
  animation: toast-in 0.3s ease;
  
  &.fade-out {
    animation: toast-out 0.3s ease forwards;
  }
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
  to {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
}

.tool-calls {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
  
  &.active {
    border-color: var(--primary-color);
    border-top: none;
    padding-top: 0;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  &.completed {
    border-top: none;
    padding-top: 0;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
}

.streaming-text-part {
  margin-bottom: 0.5rem;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.tool-call {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: var(--bg-tertiary);
  border-radius: 6px;
  font-size: 0.8125rem;
  margin-bottom: 0.5rem;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  .completed & {
    cursor: pointer;
    transition: background-color 0.2s;
    
    &:hover {
      background-color: var(--bg-secondary);
    }
  }
}

.tool-icon {
  flex-shrink: 0;
  
  &.spinning {
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.tool-name {
  font-weight: 500;
  flex: 1;
}

.collapse-hint {
  font-size: 0.75rem;
  color: var(--text-secondary);
  opacity: 0;
  transition: opacity 0.2s;
  
  .tool-call:hover & {
    opacity: 1;
  }
}

// 流式光标
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background-color: var(--text-primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 1s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.tool-result {
  width: 100%;
  margin-top: 0.5rem;
  
  pre {
    font-size: 0.75rem;
    background-color: var(--bg-primary);
    padding: 0.5rem;
    border-radius: 4px;
    overflow-x: auto;
    margin: 0;
  }
}

// Input Area
.input-area {
  padding: 1rem 1.5rem;
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border-color);
}

.input-form {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  max-width: 50%;
  margin: 0 auto;
  min-width: 600px;
  
  @media (max-width: 1200px) {
    max-width: 70%;
  }
  
  @media (max-width: 900px) {
    max-width: 90%;
    min-width: unset;
  }
}

.message-input {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 200px;
}

.send-btn {
  height: 44px;
  min-width: 80px;
}

/* ================= 消息体和列表过渡动画 ================= */

.message-enter-active {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.message-leave-active {
  transition: all 0.3s ease;
  position: absolute; 
  width: calc(100% - 3rem); 
}
.message-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
.message-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
.list-leave-active {
  position: absolute;
}

.streaming-message .message-content {
  min-height: 48px;
  transition: height 0.2s ease;
}

/* 思考指示器 */
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-secondary);
  font-size: 0.9375rem;
}

.thinking-text {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.thinking-dots {
  display: flex;
  gap: 4px;
  
  span {
    width: 8px;
    height: 8px;
    background-color: var(--primary-color);
    border-radius: 50%;
    animation: bounce 1.4s ease-in-out infinite both;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
    &:nth-child(3) { animation-delay: 0s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
