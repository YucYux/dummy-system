<template>
  <div class="admin-layout">
    <header class="admin-header">
      <h1>Admin Dashboard</h1>
      <router-link to="/" class="btn btn-secondary">Back to Chat</router-link>
    </header>
    
    <main class="admin-main">
      <div class="admin-grid">
        <!-- Models Management -->
        <section class="admin-section">
          <div class="section-header">
            <h2>Model Configuration</h2>
            <button @click="showModelModal = true" class="btn btn-primary btn-sm">
              + Add Model
            </button>
          </div>
          
          <div class="card">
            <div class="card-body">
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Provider</th>
                    <th>Model ID</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="model in models" :key="model.id">
                    <td>
                      {{ model.name }}
                      <span v-if="model.is_default" class="default-badge">Default</span>
                    </td>
                    <td>{{ model.provider }}</td>
                    <td>{{ model.model_id }}</td>
                    <td>
                      <span :class="['status-badge', model.enabled ? 'enabled' : 'disabled']">
                        {{ model.enabled ? 'Enabled' : 'Disabled' }}
                      </span>
                    </td>
                    <td>
                      <button @click="editModel(model)" class="btn btn-ghost btn-sm">Edit</button>
                      <button @click="deleteModel(model.id)" class="btn btn-ghost btn-sm text-danger">Delete</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              
              <div v-if="models.length === 0" class="empty-state">
                <p>No models configured</p>
              </div>
            </div>
          </div>
        </section>
        
        <!-- Users Management -->
        <section class="admin-section">
          <div class="section-header">
            <h2>User Management</h2>
            <button @click="showUserModal = true" class="btn btn-primary btn-sm">
              + Add User
            </button>
          </div>
          
          <div class="card">
            <div class="card-body">
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Role</th>
                    <th>Created</th>
                    <th>Last Login</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in users" :key="user.id">
                    <td>{{ user.username }}</td>
                    <td>
                      <span :class="['role-badge', user.is_admin ? 'admin' : 'user']">
                        {{ user.is_admin ? 'Admin' : 'User' }}
                      </span>
                    </td>
                    <td>{{ formatDate(user.created_at) }}</td>
                    <td>{{ user.last_login ? formatDate(user.last_login) : 'Never' }}</td>
                    <td>
                      <button 
                        @click="deleteUser(user.id)" 
                        class="btn btn-ghost btn-sm text-danger"
                        :disabled="user.id === authStore.user?.id"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </main>
    
    <!-- Model Modal -->
    <div v-if="showModelModal" class="modal-overlay" @click.self="closeModelModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingModel ? 'Edit Model' : 'Add Model' }}</h3>
          <button @click="closeModelModal" class="close-btn">×</button>
        </div>
        
        <form @submit.prevent="saveModel" class="modal-body">
          <div class="input-group">
            <label>Display Name</label>
            <input v-model="modelForm.name" type="text" class="input" required />
          </div>
          
          <div class="input-group">
            <label>Provider</label>
            <select v-model="modelForm.provider" class="input">
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          
          <div class="input-group">
            <label>Model ID</label>
            <input v-model="modelForm.model_id" type="text" class="input" placeholder="e.g., gpt-4o" required />
          </div>
          
          <div class="input-group">
            <label>API URL</label>
            <input v-model="modelForm.api_url" type="text" class="input" placeholder="https://api.openai.com/v1" required />
          </div>
          
          <div class="input-group">
            <label>API Key</label>
            <input v-model="modelForm.api_key" type="password" class="input" placeholder="sk-..." />
          </div>
          
          <div class="checkbox-group">
            <label>
              <input type="checkbox" v-model="modelForm.enabled" />
              Enabled
            </label>
            <label>
              <input type="checkbox" v-model="modelForm.is_default" />
              Set as Default
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="closeModelModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary">{{ editingModel ? 'Update' : 'Create' }}</button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- User Modal -->
    <div v-if="showUserModal" class="modal-overlay" @click.self="closeUserModal">
      <div class="modal">
        <div class="modal-header">
          <h3>Add User</h3>
          <button @click="closeUserModal" class="close-btn">×</button>
        </div>
        
        <form @submit.prevent="createUser" class="modal-body">
          <div class="input-group">
            <label>Username</label>
            <input v-model="userForm.username" type="text" class="input" minlength="3" required />
          </div>
          
          <div class="input-group">
            <label>Password</label>
            <input v-model="userForm.password" type="password" class="input" minlength="6" required />
          </div>
          
          <div class="checkbox-group">
            <label>
              <input type="checkbox" v-model="userForm.is_admin" />
              Admin privileges
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="closeUserModal" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary">Create</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const authStore = useAuthStore()

const models = ref([])
const users = ref([])
const showModelModal = ref(false)
const showUserModal = ref(false)
const editingModel = ref(null)

const modelForm = ref({
  name: '',
  provider: 'openai',
  model_id: '',
  api_url: 'https://api.openai.com/v1',
  api_key: '',
  enabled: true,
  is_default: false
})

const userForm = ref({
  username: '',
  password: '',
  is_admin: false
})

async function loadModels() {
  const response = await api.getAdminModels()
  models.value = response.models
}

async function loadUsers() {
  const response = await api.getUsers()
  users.value = response.users
}

function editModel(model) {
  editingModel.value = model
  modelForm.value = { ...model }
  showModelModal.value = true
}

async function saveModel() {
  try {
    if (editingModel.value) {
      await api.updateModel(editingModel.value.id, modelForm.value)
    } else {
      await api.createModel(modelForm.value)
    }
    await loadModels()
    closeModelModal()
  } catch (err) {
    alert(err.error || 'Failed to save model')
  }
}

async function deleteModel(modelId) {
  if (!confirm('Are you sure you want to delete this model?')) return
  
  try {
    await api.deleteModel(modelId)
    await loadModels()
  } catch (err) {
    alert(err.error || 'Failed to delete model')
  }
}

function closeModelModal() {
  showModelModal.value = false
  editingModel.value = null
  modelForm.value = {
    name: '',
    provider: 'openai',
    model_id: '',
    api_url: 'https://api.openai.com/v1',
    api_key: '',
    enabled: true,
    is_default: false
  }
}

async function createUser() {
  try {
    await api.createUser(userForm.value)
    await loadUsers()
    closeUserModal()
  } catch (err) {
    alert(err.error || 'Failed to create user')
  }
}

async function deleteUser(userId) {
  if (!confirm('Are you sure you want to delete this user?')) return
  
  try {
    await api.deleteUser(userId)
    await loadUsers()
  } catch (err) {
    alert(err.error || 'Failed to delete user')
  }
}

function closeUserModal() {
  showUserModal.value = false
  userForm.value = {
    username: '',
    password: '',
    is_admin: false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

onMounted(() => {
  loadModels()
  loadUsers()
})
</script>

<style lang="scss" scoped>
.admin-layout {
  min-height: 100vh;
  background-color: var(--bg-secondary);
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  
  h1 {
    font-size: 1.5rem;
    font-weight: 600;
  }
}

.admin-main {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.admin-grid {
  display: grid;
  gap: 2rem;
}

.admin-section {
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    
    h2 {
      font-size: 1.25rem;
      font-weight: 600;
    }
  }
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  
  th, td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
  }
  
  th {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: 0.8125rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  tbody tr:hover {
    background-color: var(--bg-tertiary);
  }
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  
  &.enabled {
    background-color: #dcfce7;
    color: #166534;
  }
  
  &.disabled {
    background-color: #f3f4f6;
    color: #6b7280;
  }
}

.role-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  
  &.admin {
    background-color: #dbeafe;
    color: #1e40af;
  }
  
  &.user {
    background-color: #f3f4f6;
    color: #6b7280;
  }
}

.default-badge {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.125rem 0.375rem;
  background-color: var(--primary-color);
  color: white;
  border-radius: 4px;
  font-size: 0.6875rem;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
}

// Modal
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: var(--bg-primary);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  
  h3 {
    font-size: 1.125rem;
    font-weight: 600;
  }
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-muted);
  cursor: pointer;
  
  &:hover {
    color: var(--text-primary);
  }
}

.modal-body {
  padding: 1.5rem;
}

.checkbox-group {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
  
  label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    cursor: pointer;
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}
</style>
