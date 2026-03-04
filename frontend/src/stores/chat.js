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
  
  async function loadConversations() {
    const response = await api.getConversations()
    conversations.value = response.conversations
  }
  
  async function loadConversation(conversationId) {
    const response = await api.getConversation(conversationId)
    currentConversation.value = response.conversation
    messages.value = response.messages
    return response
  }
  
  async function createConversation() {
    const response = await api.createConversation({
      model_id: selectedModel.value?.id
    })
    conversations.value.unshift(response.conversation)
    currentConversation.value = response.conversation
    messages.value = []
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
    clearCurrent
  }
})
