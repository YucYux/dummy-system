<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h1>LBW Agent</h1>
          <p>Create a new account</p>
        </div>
        
        <form @submit.prevent="handleRegister" class="auth-form">
          <div class="input-group">
            <label for="username">Username</label>
            <input 
              id="username"
              v-model="username"
              type="text"
              class="input"
              placeholder="Choose a username"
              minlength="3"
              required
            />
          </div>
          
          <div class="input-group">
            <label for="password">Password</label>
            <input 
              id="password"
              v-model="password"
              type="password"
              class="input"
              placeholder="Choose a password"
              minlength="6"
              required
            />
          </div>
          
          <div class="input-group">
            <label for="confirmPassword">Confirm Password</label>
            <input 
              id="confirmPassword"
              v-model="confirmPassword"
              type="password"
              class="input"
              placeholder="Confirm your password"
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
            {{ loading ? 'Creating account...' : 'Create Account' }}
          </button>
        </form>
        
        <div class="auth-footer">
          <p>
            Already have an account?
            <router-link to="/login">Sign in</router-link>
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
    error.value = 'Passwords do not match'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    await authStore.register(username.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = err.error || 'Registration failed. Please try again.'
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
