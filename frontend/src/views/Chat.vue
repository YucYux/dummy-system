<template>
  <div class="chat-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>Dummy System</h2>
        <button @click="createNewChat" class="btn btn-primary btn-sm">
          <span>+</span> New Chat
        </button>
      </div>
      
      <div class="conversation-list">
        <div
          v-for="conv in chatStore.conversations"
          :key="conv.id"
          :class="['conversation-item', { active: currentConversationId === conv.id }]"
          @click="selectConversation(conv.id)"
        >
          <span class="conversation-title">{{ conv.title }}</span>
          <button 
            class="delete-btn"
            @click.stop="deleteConversation(conv.id)"
            title="Delete conversation"
          >
            ×
          </button>
        </div>
        
        <div v-if="chatStore.conversations.length === 0" class="empty-state">
          <p>No conversations yet</p>
          <p class="text-muted">Start a new chat</p>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <div class="user-info">
          <span>{{ authStore.user?.username }}</span>
          <span v-if="authStore.isAdmin" class="admin-badge">Admin</span>
        </div>
        <div class="sidebar-actions">
          <router-link v-if="authStore.isAdmin" to="/admin" class="btn btn-ghost btn-sm">
            Settings
          </router-link>
          <button @click="handleLogout" class="btn btn-ghost btn-sm">
            Logout
          </button>
        </div>
      </div>
    </aside>
    
    <!-- Main Chat Area -->
    <main class="chat-main">
      <div v-if="!currentConversationId" class="welcome-screen">
        <h1>Welcome to Dummy System</h1>
        <p>Start a conversation with the AI assistant</p>
        <button @click="createNewChat" class="btn btn-primary btn-lg">
          Start New Chat
        </button>
      </div>
      
      <template v-else>
        <!-- Chat Header -->
        <header class="chat-header">
          <h3>{{ chatStore.currentConversation?.title || 'New Chat' }}</h3>
          <div class="model-selector">
            <select 
              v-model="selectedModelId"
              class="input"
              @change="handleModelChange"
            >
              <option 
                v-for="model in chatStore.models" 
                :key="model.id" 
                :value="model.id"
              >
                {{ model.name }}
              </option>
            </select>
          </div>
        </header>
        
        <!-- Messages -->
        <div class="messages-container" ref="messagesContainer">
          <div 
            v-for="message in chatStore.messages" 
            :key="message.id"
            :class="['message', message.role]"
          >
            <div class="message-avatar">
              {{ message.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-content">
              <div v-if="message.role === 'assistant'" v-html="renderMarkdown(message.content)"></div>
              <div v-else>{{ message.content }}</div>
              
              <!-- Tool calls display -->
              <div v-if="message.tool_calls && message.tool_calls.length" class="tool-calls">
                <div v-for="tc in message.tool_calls" :key="tc.id" class="tool-call">
                  <span class="tool-icon">🔧</span>
                  <span class="tool-name">{{ tc.function?.name }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Streaming message -->
          <div v-if="isStreaming" class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
              <div v-html="renderMarkdown(streamingContent)"></div>
              
              <!-- Active tool calls -->
              <div v-if="activeToolCalls.length" class="tool-calls active">
                <div v-for="tc in activeToolCalls" :key="tc.id" class="tool-call">
                  <span class="tool-icon spinning">⚙️</span>
                  <span class="tool-name">Calling: {{ tc.name }}</span>
                  <div v-if="tc.result" class="tool-result">
                    <pre>{{ JSON.stringify(tc.result, null, 2) }}</pre>
                  </div>
                </div>
              </div>
              
              <span class="typing-indicator">▊</span>
            </div>
          </div>
        </div>
        
        <!-- Input Area -->
        <div class="input-area">
          <form @submit.prevent="sendMessage" class="input-form">
            <textarea
              v-model="inputMessage"
              class="input message-input"
              placeholder="Type your message..."
              @keydown.enter.exact.prevent="sendMessage"
              :disabled="isStreaming"
              rows="1"
            ></textarea>
            <button 
              type="submit" 
              class="btn btn-primary send-btn"
              :disabled="!inputMessage.trim() || isStreaming"
            >
              {{ isStreaming ? 'Stop' : 'Send' }}
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
import socketService from '@/api/socket'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const inputMessage = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const activeToolCalls = ref([])
const messagesContainer = ref(null)
const currentConversationId = ref(null)
const selectedModelId = ref(null)

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

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function createNewChat() {
  const conv = await chatStore.createConversation()
  currentConversationId.value = conv.id
  socketService.joinConversation(conv.id)
}

async function selectConversation(conversationId) {
  if (currentConversationId.value) {
    socketService.leaveConversation(currentConversationId.value)
  }
  
  currentConversationId.value = conversationId
  await chatStore.loadConversation(conversationId)
  socketService.joinConversation(conversationId)
  scrollToBottom()
}

async function deleteConversation(conversationId) {
  if (confirm('Are you sure you want to delete this conversation?')) {
    await chatStore.deleteConversation(conversationId)
  }
}

function sendMessage() {
  if (!inputMessage.value.trim() || isStreaming.value) return
  
  const message = inputMessage.value.trim()
  inputMessage.value = ''
  
  socketService.sendMessage(
    currentConversationId.value, 
    message,
    selectedModelId.value
  )
}

function handleModelChange() {
  chatStore.selectedModel = chatStore.models.find(m => m.id === selectedModelId.value)
}

function handleLogout() {
  socketService.disconnect()
  authStore.logout()
  router.push('/login')
}

// Socket event handlers
function onAuthenticated() {
  chatStore.loadConversations()
  chatStore.loadModels().then(() => {
    if (chatStore.selectedModel) {
      selectedModelId.value = chatStore.selectedModel.id
    }
  })
}

function onMessageSaved(data) {
  chatStore.addMessage(data.message)
  scrollToBottom()
}

function onConversationUpdated(data) {
  chatStore.updateConversationTitle(data.title)
}

function onStreamStart() {
  isStreaming.value = true
  streamingContent.value = ''
  activeToolCalls.value = []
}

function onStreamContent(data) {
  streamingContent.value += data.content
  scrollToBottom()
}

function onStreamEnd(data) {
  isStreaming.value = false
  chatStore.addMessage(data.message)
  streamingContent.value = ''
  activeToolCalls.value = []
  scrollToBottom()
}

function onStreamError(data) {
  isStreaming.value = false
  console.error('Stream error:', data.error)
  alert('Error: ' + data.error)
}

function onToolCallStart(data) {
  activeToolCalls.value.push({
    id: data.id,
    name: data.tool,
    args: '',
    result: null
  })
  scrollToBottom()
}

function onToolCallArgs(data) {
  const tc = activeToolCalls.value.find(t => t.id === data.id)
  if (tc) {
    tc.args += data.args
  }
}

function onToolCallEnd(data) {
  const tc = activeToolCalls.value.find(t => t.id === data.id)
  if (tc) {
    tc.result = data.result || data.error
  }
  scrollToBottom()
}

onMounted(() => {
  socketService.connect()
  
  socketService.on('authenticated', onAuthenticated)
  socketService.on('message_saved', onMessageSaved)
  socketService.on('conversation_updated', onConversationUpdated)
  socketService.on('stream_start', onStreamStart)
  socketService.on('stream_content', onStreamContent)
  socketService.on('stream_end', onStreamEnd)
  socketService.on('stream_error', onStreamError)
  socketService.on('tool_call_start', onToolCallStart)
  socketService.on('tool_call_args', onToolCallArgs)
  socketService.on('tool_call_end', onToolCallEnd)
})

onUnmounted(() => {
  socketService.off('authenticated', onAuthenticated)
  socketService.off('message_saved', onMessageSaved)
  socketService.off('conversation_updated', onConversationUpdated)
  socketService.off('stream_start', onStreamStart)
  socketService.off('stream_content', onStreamContent)
  socketService.off('stream_end', onStreamEnd)
  socketService.off('stream_error', onStreamError)
  socketService.off('tool_call_start', onToolCallStart)
  socketService.off('tool_call_args', onToolCallArgs)
  socketService.off('tool_call_end', onToolCallEnd)
})

watch(() => chatStore.selectedModel, (model) => {
  if (model) {
    selectedModelId.value = model.id
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

.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
  
  h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }
  
  p {
    color: var(--text-secondary);
    margin-bottom: 2rem;
  }
}

.chat-header {
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

.model-selector {
  select {
    min-width: 150px;
  }
}

// Messages
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.message {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  
  &.user {
    .message-content {
      background-color: var(--primary-color);
      color: white;
    }
  }
  
  &.assistant {
    .message-content {
      background-color: var(--bg-primary);
    }
  }
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  padding: 1rem 1.25rem;
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  
  :deep(p) {
    margin-bottom: 0.75rem;
    
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
    margin: 0.75rem 0;
    
    code {
      background: none;
      padding: 0;
    }
  }
  
  :deep(code) {
    background-color: var(--bg-tertiary);
    padding: 0.125rem 0.375rem;
    border-radius: 4px;
    font-size: 0.875em;
  }
  
  :deep(ul), :deep(ol) {
    margin: 0.75rem 0;
    padding-left: 1.5rem;
  }
}

.tool-calls {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
  
  &.active {
    border-color: var(--primary-color);
  }
}

.tool-call {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem;
  background-color: var(--bg-tertiary);
  border-radius: 6px;
  font-size: 0.8125rem;
  margin-bottom: 0.5rem;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.tool-icon {
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

.typing-indicator {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
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
</style>
