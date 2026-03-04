import { io } from 'socket.io-client'
import api from './index'

let socket = null
let eventHandlers = {}

export const socketService = {
  connect() {
    if (socket?.connected) return
    
    socket = io('/', {
      transports: ['websocket', 'polling'],
      autoConnect: true
    })
    
    socket.on('connect', () => {
      console.log('Socket connected')
      const token = api.getToken()
      if (token) {
        socket.emit('authenticate', { token })
      }
    })
    
    socket.on('disconnect', () => {
      console.log('Socket disconnected')
    })
    
    socket.on('authenticated', (data) => {
      console.log('Socket authenticated:', data)
      this.trigger('authenticated', data)
    })
    
    socket.on('auth_error', (data) => {
      console.error('Socket auth error:', data)
      this.trigger('auth_error', data)
    })
    
    socket.on('error', (data) => {
      console.error('Socket error:', data)
      this.trigger('error', data)
    })
    
    // Chat events
    socket.on('joined', (data) => this.trigger('joined', data))
    socket.on('message_saved', (data) => this.trigger('message_saved', data))
    socket.on('conversation_updated', (data) => this.trigger('conversation_updated', data))
    socket.on('stream_start', (data) => this.trigger('stream_start', data))
    socket.on('stream_content', (data) => this.trigger('stream_content', data))
    socket.on('stream_end', (data) => this.trigger('stream_end', data))
    socket.on('stream_error', (data) => this.trigger('stream_error', data))
    socket.on('tool_call_start', (data) => this.trigger('tool_call_start', data))
    socket.on('tool_call_args', (data) => this.trigger('tool_call_args', data))
    socket.on('tool_call_end', (data) => this.trigger('tool_call_end', data))
  },
  
  disconnect() {
    if (socket) {
      socket.disconnect()
      socket = null
    }
  },
  
  authenticate(token) {
    if (socket?.connected) {
      socket.emit('authenticate', { token })
    }
  },
  
  joinConversation(conversationId) {
    if (socket?.connected) {
      socket.emit('join_conversation', { conversation_id: conversationId })
    }
  },
  
  leaveConversation(conversationId) {
    if (socket?.connected) {
      socket.emit('leave_conversation', { conversation_id: conversationId })
    }
  },
  
  sendMessage(conversationId, content, modelId = null, reasoningEffort = 'auto') {
    if (socket?.connected) {
      socket.emit('send_message', {
        conversation_id: conversationId,
        content,
        model_id: modelId,
        reasoning_effort: reasoningEffort
      })
    }
  },
  
  stopGeneration() {
    if (socket?.connected) {
      socket.emit('stop_generation', {})
    }
  },
  
  on(event, handler) {
    if (!eventHandlers[event]) {
      eventHandlers[event] = []
    }
    eventHandlers[event].push(handler)
  },
  
  off(event, handler) {
    if (eventHandlers[event]) {
      eventHandlers[event] = eventHandlers[event].filter(h => h !== handler)
    }
  },
  
  trigger(event, data) {
    if (eventHandlers[event]) {
      eventHandlers[event].forEach(handler => handler(data))
    }
  },
  
  isConnected() {
    return socket?.connected || false
  }
}

export default socketService
