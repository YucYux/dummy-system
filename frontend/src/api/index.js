import axios from 'axios'

const API_BASE = '/api'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

let authToken = null

const api = {
  setToken(token) {
    authToken = token
    if (token) {
      client.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete client.defaults.headers.common['Authorization']
    }
  },
  
  getToken() {
    return authToken
  },
  
  // Auth
  async login(username, password) {
    const response = await client.post('/auth/login', { username, password })
    return response.data
  },
  
  async register(username, password) {
    const response = await client.post('/auth/register', { username, password })
    return response.data
  },
  
  async getCurrentUser() {
    const response = await client.get('/auth/me')
    return response.data
  },
  
  async changePassword(oldPassword, newPassword) {
    const response = await client.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
    return response.data
  },
  
  // Conversations
  async getConversations() {
    const response = await client.get('/chat/conversations')
    return response.data
  },
  
  async getConversation(conversationId) {
    const response = await client.get(`/chat/conversations/${conversationId}`)
    return response.data
  },
  
  async createConversation(data = {}) {
    const response = await client.post('/chat/conversations', data)
    return response.data
  },
  
  async updateConversation(conversationId, data) {
    const response = await client.put(`/chat/conversations/${conversationId}`, data)
    return response.data
  },
  
  async deleteConversation(conversationId) {
    const response = await client.delete(`/chat/conversations/${conversationId}`)
    return response.data
  },
  
  // Models
  async getModels() {
    const response = await client.get('/models/')
    return response.data
  },
  
  // Tools
  async getTools() {
    const response = await client.get('/chat/tools')
    return response.data
  },
  
  // Message operations
  async regenerateMessage(conversationId, messageId) {
    const response = await client.post(`/chat/conversations/${conversationId}/messages/${messageId}/regenerate`)
    return response.data
  },
  
  async revertToMessage(conversationId, messageId) {
    const response = await client.post(`/chat/conversations/${conversationId}/messages/${messageId}/revert`)
    return response.data
  },
  
  // Admin - Users
  async getUsers() {
    const response = await client.get('/admin/users')
    return response.data
  },
  
  async createUser(data) {
    const response = await client.post('/admin/users', data)
    return response.data
  },
  
  async deleteUser(userId) {
    const response = await client.delete(`/admin/users/${userId}`)
    return response.data
  },
  
  // Admin - Models
  async getAdminModels() {
    const response = await client.get('/models/admin')
    return response.data
  },
  
  async createModel(data) {
    const response = await client.post('/models/admin', data)
    return response.data
  },
  
  async updateModel(modelId, data) {
    const response = await client.put(`/models/admin/${modelId}`, data)
    return response.data
  },
  
  async deleteModel(modelId) {
    const response = await client.delete(`/models/admin/${modelId}`)
    return response.data
  },

  // Admin - Embedding Model
  async getEmbeddingConfig() {
    const response = await client.get('/models/embedding/admin')
    return response.data
  },

  async updateEmbeddingConfig(data) {
    const response = await client.put('/models/embedding/admin', data)
    return response.data
  },

  async getEmbeddingStatus() {
    const response = await client.get('/models/embedding/status')
    return response.data
  },

  // Document Libraries
  async getLibraryTypes() {
    const response = await client.get('/doc-library/types')
    return response.data
  },

  async getLibraries() {
    const response = await client.get('/doc-library/')
    return response.data
  },

  async createLibrary(data) {
    const response = await client.post('/doc-library/', data)
    return response.data
  },

  async getLibrary(libraryId) {
    const response = await client.get(`/doc-library/${libraryId}`)
    return response.data
  },

  async updateLibrary(libraryId, data) {
    const response = await client.put(`/doc-library/${libraryId}`, data)
    return response.data
  },

  async deleteLibrary(libraryId) {
    const response = await client.delete(`/doc-library/${libraryId}`)
    return response.data
  },

  // Documents
  async getLibraryDocuments(libraryId) {
    const response = await client.get(`/doc-library/${libraryId}/documents`)
    return response.data
  },

  async uploadDocument(libraryId, file) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await client.post(`/doc-library/${libraryId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    })
    return response.data
  },

  async deleteDocument(libraryId, docId) {
    const response = await client.delete(`/doc-library/${libraryId}/documents/${docId}`)
    return response.data
  },

  // Embedding
  async startEmbedding(libraryId) {
    const response = await client.post(`/doc-library/${libraryId}/start-embedding`)
    return response.data
  },

  async getEmbeddingProgress() {
    const response = await client.get('/doc-library/embedding-status')
    return response.data
  },

  async stopEmbedding() {
    const response = await client.post('/doc-library/stop-embedding')
    return response.data
  },

  // Conversation Libraries
  async getConversationLibraries(conversationId) {
    const response = await client.get(`/doc-library/conversation/${conversationId}/libraries`)
    return response.data
  },

  async setConversationLibraries(conversationId, libraryIds) {
    const response = await client.put(`/doc-library/conversation/${conversationId}/libraries`, {
      library_ids: libraryIds
    })
    return response.data
  },

  // Search
  async searchDocuments(query, libraryIds, topK = 5) {
    const response = await client.post('/doc-library/search', {
      query,
      library_ids: libraryIds,
      top_k: topK
    })
    return response.data
  }
}

// Response interceptor for error handling
client.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const errorData = error.response?.data
      // Check if session expired due to login on another device
      if (errorData?.code === 'SESSION_EXPIRED') {
        alert('您的账号已在其他设备登录，当前会话已失效')
      }
      // Token expired or invalid
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error.response?.data || error)
  }
)

export default api
