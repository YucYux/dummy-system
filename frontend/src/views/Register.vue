<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h1>Dummy System</h1>
          <p>创建新账户</p>
        </div>
        
        <form @submit.prevent="handleRegister" class="auth-form">
          <div class="input-group">
            <label for="username">用户名</label>
            <input 
              id="username"
              v-model="username"
              type="text"
              class="input"
              placeholder="设置用户名"
              minlength="3"
              required
            />
          </div>
          
          <div class="input-group">
            <label for="password">密码</label>
            <input 
              id="password"
              v-model="password"
              type="password"
              class="input"
              placeholder="设置密码"
              minlength="6"
              required
            />
          </div>
          
          <div class="input-group">
            <label for="confirmPassword">确认密码</label>
            <input 
              id="confirmPassword"
              v-model="confirmPassword"
              type="password"
              class="input"
              placeholder="再次输入密码"
              required
            />
          </div>
          
          <div v-if="error" class="error-message">
            {{ error }}
          </div>
          
          <button 
            type="submit" 
            class="btn btn-primary btn-lg"
            :disabled="loading"
          >
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>
        
        <div class="auth-footer">
          <p>
            已有账号？
            <router-link to="/login">立即登录</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    await authStore.register(username.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = err.error || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.auth-container {
  width: 100%;
  max-width: 400px;
}

.auth-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.auth-header {
  padding: 2rem 2rem 1.5rem;
  text-align: center;
  
  h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }
  
  p {
    color: var(--text-secondary);
    font-size: 0.9375rem;
  }
}

.auth-form {
  padding: 0 2rem 2rem;
  
  .btn {
    width: 100%;
    margin-top: 0.5rem;
  }
}

.error-message {
  padding: 0.75rem;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--border-radius);
  color: var(--danger-color);
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.auth-footer {
  padding: 1.5rem 2rem;
  background-color: var(--bg-secondary);
  text-align: center;
  font-size: 0.875rem;
  
  a {
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 500;
    
    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
