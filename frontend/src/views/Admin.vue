<template>
  <div class="admin-layout">
    <header class="admin-header">
      <h1>管理面板</h1>
      <router-link to="/" class="btn btn-secondary">返回对话</router-link>
    </header>
    
    <main class="admin-main">
      <div class="admin-grid">
        <!-- Models Management -->
        <section class="admin-section">
          <div class="section-header">
            <h2>模型配置</h2>
            <button @click="showModelModal = true" class="btn btn-primary btn-sm">
              + 添加模型
            </button>
          </div>
          
          <div class="card">
            <div class="card-body">
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>名称</th>
                    <th>类型</th>
                    <th>提供商</th>
                    <th>模型ID</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="model in models" :key="model.id">
                    <td>
                      {{ model.name }}
                      <span v-if="model.is_default" class="default-badge">默认</span>
                    </td>
                    <td>
                      <span :class="['reasoning-badge', model.is_reasoning ? 'reasoning' : 'standard']">
                        {{ model.is_reasoning ? '推理模型' : '普通模型' }}
                      </span>
                    </td>
                    <td>{{ model.provider }}</td>
                    <td>{{ model.model_id }}</td>
                    <td>
                      <span :class="['status-badge', model.enabled ? 'enabled' : 'disabled']">
                        {{ model.enabled ? '已启用' : '已禁用' }}
                      </span>
                    </td>
                    <td>
                      <button @click="editModel(model)" class="btn btn-ghost btn-sm">编辑</button>
                      <button @click="deleteModel(model.id)" class="btn btn-ghost btn-sm text-danger">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              
              <div v-if="isModelsLoading" class="empty-state">
                <p>模型配置加载中...</p>
              </div>

              <div v-else-if="modelsError" class="empty-state">
                <p>{{ modelsError }}</p>
              </div>

              <div v-else-if="models.length === 0" class="empty-state">
                <p>暂无模型配置</p>
              </div>
            </div>
          </div>
        </section>
        
        <!-- Embedding Model Configuration -->
        <section class="admin-section">
          <div class="section-header">
            <h2>Embedding 模型配置</h2>
          </div>
          
          <div class="card">
            <div class="card-body">
              <p class="section-desc">配置用于文档向量化的 Embedding 模型。该模型将用于 RAG 系统的文档处理。</p>
              
              <form @submit.prevent="saveEmbeddingConfig" class="embedding-form">
                <div class="form-row">
                  <div class="input-group">
                    <label>提供商</label>
                    <select v-model="embeddingForm.provider" class="input">
                      <option value="OpenRouter">OpenRouter</option>
                      <option value="custom">自定义</option>
                    </select>
                  </div>
                  
                  <div class="input-group">
                    <label>模型 ID</label>
                    <input v-model="embeddingForm.model_id" type="text" class="input" placeholder="qwen/qwen3-embedding-4b" />
                  </div>
                </div>
                
                <div class="form-row">
                  <div class="input-group">
                    <label>API URL</label>
                    <input v-model="embeddingForm.api_url" type="text" class="input" placeholder="https://openrouter.ai/api/v1" />
                  </div>
                  
                  <div class="input-group">
                    <label>向量维度</label>
                    <input v-model.number="embeddingForm.dimension" type="number" class="input" placeholder="2560" />
                  </div>
                </div>
                
                <div class="input-group full-width">
                  <label>API Key</label>
                  <input v-model="embeddingForm.api_key" type="password" class="input" placeholder="sk-..." />
                </div>
                
                <div class="checkbox-group">
                  <label>
                    <input type="checkbox" v-model="embeddingForm.enabled" />
                    启用 Embedding 模型
                  </label>
                </div>
                
                <div class="form-actions">
                  <button type="submit" class="btn btn-primary" :disabled="embeddingSaving">
                    {{ embeddingSaving ? '保存中...' : '保存配置' }}
                  </button>
                  <span v-if="embeddingSaved" class="save-success">✓ 已保存</span>
                </div>
              </form>
            </div>
          </div>
        </section>
        
        <!-- Users Management -->
        <section class="admin-section">
          <div class="section-header">
            <h2>用户管理</h2>
            <button @click="showUserModal = true" class="btn btn-primary btn-sm">
              + 添加用户
            </button>
          </div>
          
          <div class="card">
            <div class="card-body">
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>用户名</th>
                    <th>角色</th>
                    <th>创建时间</th>
                    <th>最后登录</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in users" :key="user.id">
                    <td>{{ user.username }}</td>
                    <td>
                      <span :class="['role-badge', user.is_admin ? 'admin' : 'user']">
                        {{ user.is_admin ? '管理员' : '用户' }}
                      </span>
                    </td>
                    <td>{{ formatDate(user.created_at) }}</td>
                    <td>{{ user.last_login ? formatDate(user.last_login) : '从未登录' }}</td>
                    <td>
                      <button 
                        @click="deleteUser(user.id)" 
                        class="btn btn-ghost btn-sm text-danger"
                        :disabled="user.id === authStore.user?.id"
                      >
                        删除
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
    <div v-if="showModelModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingModel ? '编辑模型' : '添加模型' }}</h3>
          <button @click="closeModelModal" class="close-btn">×</button>
        </div>
        
        <form @submit.prevent="saveModel" class="modal-body">
          <div class="input-group">
            <label>显示名称</label>
            <input v-model="modelForm.name" type="text" class="input" required />
          </div>
          
          <div class="input-group">
            <label>提供商</label>
            <select v-model="modelForm.provider" class="input">
              <option value="OpenRouter">OpenRouter</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>
          
          <div class="input-group">
            <label>模型 ID</label>
            <input v-model="modelForm.model_id" type="text" class="input" placeholder="例如: openai/gpt-4o 或 minimax/minimax-m2.5" required />
            <p v-if="isMinimaxModel" class="field-hint minimax-hint">
              检测到 MiniMax 模型，建议开启「MiniMax 交错思维链」以提升 Agent 多轮工具调用表现。
            </p>
          </div>
          
          <div class="input-group">
            <label>API URL</label>
            <input v-model="modelForm.api_url" type="text" class="input" placeholder="https://openrouter.ai/api/v1" required />
          </div>
          
          <div class="input-group">
            <label>API Key</label>
            <input v-model="modelForm.api_key" type="password" class="input" placeholder="sk-..." />
          </div>
          
          <div class="checkbox-group">
            <label>
              <input type="checkbox" v-model="modelForm.enabled" />
              启用
            </label>
            <label>
              <input type="checkbox" v-model="modelForm.is_default" />
              设为默认
            </label>
            <label>
              <input type="checkbox" v-model="modelForm.is_reasoning" />
              推理模型
            </label>
            <label :class="['checkbox-with-tooltip', { disabled: !canEnableMinimaxCot }]">
              <input
                type="checkbox"
                v-model="modelForm.minimax_interleaved_cot"
                :disabled="!canEnableMinimaxCot"
              />
              MiniMax 交错思维链
              <span class="tooltip-trigger" :title="minimaxCotTooltip">?</span>
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="closeModelModal" class="btn btn-secondary">取消</button>
            <button type="submit" class="btn btn-primary">{{ editingModel ? '更新' : '创建' }}</button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- User Modal -->
    <div v-if="showUserModal" class="modal-overlay" @click.self="closeUserModal">
      <div class="modal">
        <div class="modal-header">
          <h3>添加用户</h3>
          <button @click="closeUserModal" class="close-btn">×</button>
        </div>
        
        <form @submit.prevent="createUser" class="modal-body">
          <div class="input-group">
            <label>用户名</label>
            <input v-model="userForm.username" type="text" class="input" minlength="3" required />
          </div>
          
          <div class="input-group">
            <label>密码</label>
            <input v-model="userForm.password" type="password" class="input" minlength="6" required />
          </div>
          
          <div class="checkbox-group">
            <label>
              <input type="checkbox" v-model="userForm.is_admin" />
              管理员权限
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="closeUserModal" class="btn btn-secondary">取消</button>
            <button type="submit" class="btn btn-primary">创建</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const authStore = useAuthStore()

const models = ref([])
const users = ref([])
const isModelsLoading = ref(false)
const modelsError = ref('')
const showModelModal = ref(false)
const showUserModal = ref(false)
const editingModel = ref(null)

// Embedding config
const embeddingForm = ref({
  provider: 'OpenRouter',
  model_id: '',
  api_url: 'https://openrouter.ai/api/v1',
  api_key: '',
  dimension: 2560,
  enabled: false
})
const embeddingSaving = ref(false)
const embeddingSaved = ref(false)

const modelForm = ref({
  name: '',
  provider: 'OpenRouter',
  model_id: '',
  api_url: 'https://openrouter.ai/api/v1',
  api_key: '',
  enabled: true,
  is_default: false,
  is_reasoning: false,
  minimax_interleaved_cot: false
})

const minimaxCotTooltip = '交错思维链是 MiniMax 提出的机制：在每轮对话中保留模型的历史思考过程（reasoning），以 <think> 标签拼接到内容中传给下一轮，可显著提升多轮工具调用场景下的任务成功率。目前仅建议在 MiniMax 系列模型上开启。'

const isMinimaxModel = computed(() => {
  const id = (modelForm.value.model_id || '').toLowerCase()
  return id.includes('minimax')
})

const canEnableMinimaxCot = computed(() => modelForm.value.is_reasoning)

watch(
  () => modelForm.value.is_reasoning,
  (isReasoning) => {
    if (!isReasoning) {
      modelForm.value.minimax_interleaved_cot = false
    }
  }
)

const userForm = ref({
  username: '',
  password: '',
  is_admin: false
})

async function loadModels() {
  isModelsLoading.value = true
  modelsError.value = ''

  try {
    const response = await api.getAdminModels()
    models.value = response.models
  } catch (err) {
    modelsError.value = err.error || '加载模型配置失败'
    models.value = []
  } finally {
    isModelsLoading.value = false
  }
}

async function loadUsers() {
  const response = await api.getUsers()
  users.value = response.users
}

async function loadEmbeddingConfig() {
  try {
    const response = await api.getEmbeddingConfig()
    if (response.embedding) {
      embeddingForm.value = {
        provider: response.embedding.provider || 'OpenRouter',
        model_id: response.embedding.model_id || '',
        api_url: response.embedding.api_url || 'https://openrouter.ai/api/v1',
        api_key: response.embedding.api_key || '',
        dimension: response.embedding.dimension || 2560,
        enabled: response.embedding.enabled || false
      }
    }
  } catch (err) {
    console.error('Failed to load embedding config:', err)
  }
}

async function saveEmbeddingConfig() {
  embeddingSaving.value = true
  embeddingSaved.value = false
  
  try {
    await api.updateEmbeddingConfig(embeddingForm.value)
    embeddingSaved.value = true
    setTimeout(() => {
      embeddingSaved.value = false
    }, 3000)
  } catch (err) {
    alert('保存失败: ' + (err.error || err.message || '未知错误'))
  } finally {
    embeddingSaving.value = false
  }
}

function editModel(model) {
  editingModel.value = model
  modelForm.value = {
    ...model,
    minimax_interleaved_cot: model.minimax_interleaved_cot === true
  }
  showModelModal.value = true
}

async function saveModel() {
  try {
    const payload = {
      ...modelForm.value,
      minimax_interleaved_cot: modelForm.value.is_reasoning
        ? modelForm.value.minimax_interleaved_cot
        : false
    }

    if (editingModel.value) {
      await api.updateModel(editingModel.value.id, payload)
    } else {
      await api.createModel(payload)
    }
    await loadModels()
    closeModelModal()
  } catch (err) {
    alert(err.error || '保存模型失败')
  }
}

async function deleteModel(modelId) {
  if (!confirm('确定要删除这个模型吗？')) return
  
  try {
    await api.deleteModel(modelId)
    await loadModels()
  } catch (err) {
    alert(err.error || '删除模型失败')
  }
}

function closeModelModal() {
  showModelModal.value = false
  editingModel.value = null
  modelForm.value = {
    name: '',
    provider: 'OpenRouter',
    model_id: '',
    api_url: 'https://openrouter.ai/api/v1',
    api_key: '',
    enabled: true,
    is_default: false,
    is_reasoning: false,
    minimax_interleaved_cot: false
  }
}

async function createUser() {
  try {
    await api.createUser(userForm.value)
    await loadUsers()
    closeUserModal()
  } catch (err) {
    alert(err.error || '创建用户失败')
  }
}

async function deleteUser(userId) {
  if (!confirm('确定要删除这个用户吗？')) return
  
  try {
    await api.deleteUser(userId)
    await loadUsers()
  } catch (err) {
    alert(err.error || '删除用户失败')
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
  loadEmbeddingConfig()
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
  border-radius: var(--border-radius-sm);
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

.reasoning-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;

  &.reasoning {
    background-color: #ede9fe;
    color: #7c3aed;
  }

  &.standard {
    background-color: #f3f4f6;
    color: #475569;
  }
}

.role-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: var(--border-radius-sm);
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
  border-radius: var(--border-radius-sm);
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
  border-radius: var(--border-radius-lg);
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
  flex-wrap: wrap;
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

.checkbox-with-tooltip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;

  &.disabled {
    color: var(--text-muted);
    cursor: not-allowed;
    opacity: 0.6;
  }
}

.tooltip-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.1rem;
  height: 1.1rem;
  border-radius: 50%;
  background: var(--border-color);
  color: var(--bg-primary);
  font-size: 0.7rem;
  font-weight: 600;
  cursor: help;
  flex-shrink: 0;
  
  &:hover {
    background: var(--text-muted);
  }
}

.field-hint {
  margin: 0.5rem 0 0;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.minimax-hint {
  color: var(--primary-color, #6366f1);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

// Embedding Config
.section-desc {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

.embedding-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  
  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.input-group.full-width {
  grid-column: 1 / -1;
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
}

.save-success {
  color: #16a34a;
  font-size: 0.875rem;
  font-weight: 500;
}
</style>
