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
  }
}

// Response interceptor for error handling
client.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error.response?.data || error)
  }
)

export default api
