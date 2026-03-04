import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConversation = ref(null)
  const messages = ref([])
  const models = ref([])
  const selectedModel = ref(null)
  const isLoading = ref(false)
  const reasoningEffort = ref('auto')
  
  async function loadConversations() {
    const response = await api.getConversations()
    conversations.value = response.conversations
  }
  
  async function loadConversation(conversationId) {
    const response = await api.getConversation(conversationId)
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
    const defaultModel = models.value.find(m => m.is_default) || models.value[0]
    const initialReasoningEffort = (defaultModel?.is_reasoning) ? 'auto' : 'auto' // 默认都是 auto，但逻辑上明确一下

    const response = await api.createConversation({
      model_id: defaultModel?.id,
      reasoning_effort: initialReasoningEffort
    })
    conversations.value.unshift(response.conversation)
    currentConversation.value = response.conversation
    messages.value = []
    
    // 设置当前选择为新对话的配置
    if (defaultModel) {
      selectedModel.value = defaultModel
    }
    reasoningEffort.value = initialReasoningEffort
    
    return response.conversation
  }
  
  async function deleteConversation(conversationId) {
    await api.deleteConversation(conversationId)
    conversations.value = conversations.value.filter(c => c.id !== conversationId)
    
    if (currentConversation.value?.id === conversationId) {
      currentConversation.value = null
      messages.value = []
    }
  }
  
  async function loadModels() {
    const response = await api.getModels()
    models.value = response.models
    
    if (models.value.length > 0 && !selectedModel.value) {
      selectedModel.value = models.value.find(m => m.is_default) || models.value[0]
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
  
  function updateConversationTitle(title) {
    if (currentConversation.value) {
      currentConversation.value.title = title
      const conv = conversations.value.find(c => c.id === currentConversation.value.id)
      if (conv) {
        conv.title = title
      }
    }
  }
  
  function clearCurrent() {
    currentConversation.value = null
    messages.value = []
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
    currentConversation,
    messages,
    models,
    selectedModel,
    isLoading,
    loadConversations,
    loadConversation,
    createConversation,
    deleteConversation,
    loadModels,
    addMessage,
    updateLastMessage,
    updateConversationTitle,
    clearCurrent,
    reasoningEffort,
    setReasoningEffort,
    resetReasoningEffort
  }
})
