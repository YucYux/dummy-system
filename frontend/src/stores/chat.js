import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/api'
import socketService from '@/api/socket'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConversationId = ref(null)
  const currentConversation = ref(null)
  const messages = ref([])
  const models = ref([])
  const selectedModel = ref(null)
  const isLoading = ref(false)
  const reasoningEffort = ref('auto')
  const streamingStates = ref({})
  const socketInitialized = ref(false)

  const emptyStreamingState = Object.freeze({
    isStreaming: false,
    streamingContent: '',
    activeToolCalls: [],
    streamingParts: [],
    streamingMessageId: null
  })

  const hasAnyStreamingConversation = computed(() => {
    return Object.values(streamingStates.value).some(state => state.isStreaming)
  })

  const activeStreamingConversationId = computed(() => {
    const activeEntry = Object.entries(streamingStates.value).find(([, state]) => state.isStreaming)
    return activeEntry ? activeEntry[0] : null
  })

  function getDefaultOrFirstModel() {
    return models.value.find(m => m.is_default) || models.value[0] || null
  }
  
  async function loadConversations() {
    const response = await api.getConversations()
    conversations.value = response.conversations
  }
  
  async function loadConversation(conversationId) {
    const response = await api.getConversation(conversationId)
    currentConversationId.value = conversationId
    currentConversation.value = response.conversation
    messages.value = response.messages
    
    // 加载对话特定的模型和思考强度
    if (response.conversation?.model_id) {
      const model = models.value.find(m => m.id === response.conversation.model_id)
      if (model) {
        selectedModel.value = model
      }
    }
    reasoningEffort.value = response.conversation?.reasoning_effort || 'auto'
    
    return response
  }
  
  async function createConversation() {
    // 使用默认模型
    const defaultModel = getDefaultOrFirstModel()
    const initialReasoningEffort = 'auto'

    if (!defaultModel) {
      throw new Error('暂无可用模型，请先在管理面板配置并启用模型')
    }

    const response = await api.createConversation({
      model_id: defaultModel.id,
      reasoning_effort: initialReasoningEffort
    })
    conversations.value.unshift(response.conversation)
    currentConversationId.value = response.conversation.id
    currentConversation.value = response.conversation
    messages.value = []
    
    // 设置当前选择为新对话的配置
    if (defaultModel) {
      selectedModel.value = defaultModel
    }
    reasoningEffort.value = initialReasoningEffort
    
    return response.conversation
  }
  
  // 使用指定模型创建对话（用于起始页发送首条消息时）
  async function createConversationWithModel(modelId, reasoning) {
    const model = models.value.find(m => m.id === modelId) || getDefaultOrFirstModel()
    const initialReasoningEffort = reasoning || 'auto'

    if (!model) {
      throw new Error('暂无可用模型，请先在管理面板配置并启用模型')
    }

    const response = await api.createConversation({
      model_id: model.id,
      reasoning_effort: initialReasoningEffort
    })
    conversations.value.unshift(response.conversation)
    currentConversationId.value = response.conversation.id
    currentConversation.value = response.conversation
    messages.value = []
    
    if (model) {
      selectedModel.value = model
    }
    reasoningEffort.value = initialReasoningEffort
    
    return response.conversation
  }
  
  async function deleteConversation(conversationId) {
    await api.deleteConversation(conversationId)
    conversations.value = conversations.value.filter(c => c.id !== conversationId)
    clearStreamingState(conversationId)
    
    if (currentConversationId.value === conversationId) {
      clearCurrent()
    }
  }
  
  async function loadModels() {
    const response = await api.getModels()
    models.value = response.models

    const nextSelectedModel = selectedModel.value
      ? models.value.find(m => m.id === selectedModel.value.id)
      : null

    selectedModel.value = nextSelectedModel || getDefaultOrFirstModel()

    if (!selectedModel.value || !selectedModel.value.is_reasoning) {
      reasoningEffort.value = 'auto'
    }
  }
  
  function addMessage(message) {
    messages.value.push(message)
  }
  
  function updateLastMessage(content) {
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1]
      lastMsg.content = content
    }
  }
  
  function updateConversationTitle(conversationId, title) {
    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) {
      conv.title = title
    }

    if (currentConversation.value?.id === conversationId) {
      currentConversation.value.title = title
    }
  }
  
  function clearCurrent() {
    currentConversationId.value = null
    currentConversation.value = null
    messages.value = []
  }

  function setCurrentConversationId(conversationId) {
    currentConversationId.value = conversationId
  }

  function createStreamingState() {
    return {
      isStreaming: false,
      streamingContent: '',
      activeToolCalls: [],
      streamingParts: [],
      streamingMessageId: null
    }
  }

  function ensureStreamingState(conversationId) {
    if (!conversationId) return null
    if (!streamingStates.value[conversationId]) {
      streamingStates.value[conversationId] = createStreamingState()
    }
    return streamingStates.value[conversationId]
  }

  function getStreamingState(conversationId) {
    if (!conversationId) return emptyStreamingState
    return streamingStates.value[conversationId] || emptyStreamingState
  }

  function isConversationStreaming(conversationId) {
    return Boolean(streamingStates.value[conversationId]?.isStreaming)
  }

  function clearStreamingState(conversationId) {
    if (!conversationId || !streamingStates.value[conversationId]) return
    delete streamingStates.value[conversationId]
  }

  function clearAllStreamingStates() {
    streamingStates.value = {}
  }

  function updateStreamingMessage(conversationId, updater) {
    const state = ensureStreamingState(conversationId)
    if (!state) return
    updater(state)
  }

  function initializeSocket() {
    socketService.connect()

    if (socketInitialized.value) return

    socketInitialized.value = true

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
    socketService.on('generation_stopped', onGenerationStopped)
    socketService.on('disconnected', onDisconnected)
  }

  function onAuthenticated() {
    loadConversations()
    loadModels()
  }

  function onMessageSaved(data) {
    const conversationId = data.conversation_id || data.message?.conversation_id
    if (!conversationId || currentConversationId.value !== conversationId) {
      return
    }

    const existingIndex = messages.value.findIndex(
      (msg) => msg.pending && msg.role === 'user' && msg.content === data.message.content
    )

    if (existingIndex !== -1) {
      const oldMsg = messages.value[existingIndex]
      messages.value.splice(existingIndex, 1, {
        ...data.message,
        _clientId: oldMsg._clientId || oldMsg.id
      })
      return
    }

    messages.value.push(data.message)
  }

  function onConversationUpdated(data) {
    if (!data.conversation_id) return
    updateConversationTitle(data.conversation_id, data.title)
  }

  function onStreamStart(data) {
    if (!data.conversation_id) return

    updateStreamingMessage(data.conversation_id, (state) => {
      state.isStreaming = true
      state.streamingContent = ''
      state.activeToolCalls = []
      state.streamingParts = []
      state.streamingMessageId = `streaming-${data.conversation_id}-${Date.now()}`
    })
  }

  function onStreamContent(data) {
    if (!data.conversation_id) return

    updateStreamingMessage(data.conversation_id, (state) => {
      state.isStreaming = true
      state.streamingContent += data.content

      const lastPart = state.streamingParts[state.streamingParts.length - 1]
      if (lastPart && lastPart.type === 'content') {
        lastPart.text += data.content
      } else {
        state.streamingParts.push({ type: 'content', text: data.content })
      }
    })
  }

  function onStreamEnd(data) {
    const conversationId = data.conversation_id || data.message?.conversation_id
    if (!conversationId) return

    const state = getStreamingState(conversationId)
    const messageWithClientId = {
      ...data.message,
      _clientId: state.streamingMessageId || `message-${data.message.id}`
    }

    if (currentConversationId.value === conversationId) {
      messages.value.push(messageWithClientId)
    }

    clearStreamingState(conversationId)
  }

  function onStreamError(data) {
    if (data.conversation_id) {
      clearStreamingState(data.conversation_id)
    }
  }

  function onToolCallStart(data) {
    if (!data.conversation_id) return

    updateStreamingMessage(data.conversation_id, (state) => {
      const toolCall = {
        id: data.id,
        name: data.tool,
        args: '',
        result: null
      }

      state.activeToolCalls.push(toolCall)
      state.streamingParts.push({
        type: 'tool_call',
        toolCall
      })
    })
  }

  function onToolCallArgs(data) {
    if (!data.conversation_id) return

    updateStreamingMessage(data.conversation_id, (state) => {
      const tc = state.activeToolCalls.find(t => t.id === data.id)
      if (tc) {
        tc.args += data.args
      }
    })
  }

  function onToolCallEnd(data) {
    if (!data.conversation_id) return

    updateStreamingMessage(data.conversation_id, (state) => {
      const tc = state.activeToolCalls.find(t => t.id === data.id)
      if (tc) {
        tc.result = data.result || data.error
      }
    })
  }

  function onGenerationStopped(data) {
    if (data.conversation_id) {
      clearStreamingState(data.conversation_id)
    }
  }

  function onDisconnected() {
    clearAllStreamingStates()
  }

  function setReasoningEffort(value) {
    reasoningEffort.value = value
    if (currentConversation.value) {
      api.updateConversation(currentConversation.value.id, {
        reasoning_effort: value
      })
    }
  }

  function setSelectedModel(model) {
    selectedModel.value = model
    if (currentConversation.value) {
      api.updateConversation(currentConversation.value.id, {
        model_id: model.id
      })
    }
  }

  function resetReasoningEffort() {
    reasoningEffort.value = 'auto'
  }
  
  return {
    conversations,
    currentConversationId,
    currentConversation,
    messages,
    models,
    selectedModel,
    isLoading,
    streamingStates,
    hasAnyStreamingConversation,
    activeStreamingConversationId,
    loadConversations,
    loadConversation,
    createConversation,
    createConversationWithModel,
    deleteConversation,
    loadModels,
    addMessage,
    updateLastMessage,
    updateConversationTitle,
    clearCurrent,
    setCurrentConversationId,
    getStreamingState,
    isConversationStreaming,
    clearStreamingState,
    clearAllStreamingStates,
    initializeSocket,
    reasoningEffort,
    setReasoningEffort,
    setSelectedModel,
    resetReasoningEffort
  }
})
