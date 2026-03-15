<template>
  <div class="library-selector" v-if="libraries.length > 0 || selectedLibraries.length > 0">
    <div class="selector-header" @click="toggleExpanded">
      <span class="selector-label">文档库</span>
      <span class="selected-count" v-if="selectedLibraries.length > 0">
        已选 {{ selectedLibraries.length }} 个
      </span>
      <span class="expand-icon">{{ expanded ? '▼' : '▶' }}</span>
    </div>
    
    <transition name="slide">
      <div v-if="expanded" class="selector-body">
        <div v-if="deletedWarning" class="deleted-warning">
          <span>⚠️ 部分文档库已被删除，已自动解除绑定</span>
          <button class="dismiss-btn" @click="deletedWarning = false">×</button>
        </div>
        
        <div v-if="loading" class="loading">加载中...</div>
        
        <template v-else>
          <div v-if="libraries.length === 0" class="no-libraries">
            暂无可用文档库
          </div>
          
          <div v-else class="library-checkboxes">
            <label v-for="lib in libraries" :key="lib.id" class="library-checkbox">
              <input 
                type="checkbox" 
                :value="lib.id"
                :checked="isSelected(lib.id)"
                @change="toggleLibrary(lib.id)"
                :disabled="disabled"
              />
              <span class="checkbox-label">
                <span class="lib-name">{{ lib.name }}</span>
                <span class="lib-type">{{ lib.type }}</span>
              </span>
            </label>
          </div>
        </template>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '@/api'

const props = defineProps({
  conversationId: String,
  disabled: Boolean
})

const emit = defineEmits(['change'])

const expanded = ref(false)
const loading = ref(false)
const libraries = ref([])
const selectedLibraries = ref([])
const deletedWarning = ref(false)

function toggleExpanded() {
  expanded.value = !expanded.value
}

function isSelected(id) {
  return selectedLibraries.value.includes(id)
}

async function toggleLibrary(id) {
  if (props.disabled) return
  
  const newSelection = isSelected(id)
    ? selectedLibraries.value.filter(i => i !== id)
    : [...selectedLibraries.value, id]
  
  try {
    await api.setConversationLibraries(props.conversationId, newSelection)
    selectedLibraries.value = newSelection
    emit('change', newSelection)
  } catch (err) {
    console.error('Failed to update libraries:', err)
  }
}

async function loadLibraries() {
  loading.value = true
  try {
    const res = await api.getLibraries()
    libraries.value = res.libraries.filter(l => l.status === 'ready' && l.chunk_count > 0)
  } catch (err) {
    console.error('Failed to load libraries:', err)
  } finally {
    loading.value = false
  }
}

async function loadConversationLibraries() {
  if (!props.conversationId) return
  
  try {
    const res = await api.getConversationLibraries(props.conversationId)
    selectedLibraries.value = res.libraries.map(l => l.id)
    
    if (res.deleted_library_ids && res.deleted_library_ids.length > 0) {
      deletedWarning.value = true
    }
  } catch (err) {
    console.error('Failed to load conversation libraries:', err)
  }
}

watch(() => props.conversationId, async (newId) => {
  if (newId) {
    await Promise.all([loadLibraries(), loadConversationLibraries()])
  } else {
    selectedLibraries.value = []
  }
}, { immediate: true })

defineExpose({
  refresh: () => {
    loadLibraries()
    loadConversationLibraries()
  }
})
</script>

<style lang="scss" scoped>
.library-selector {
  background: var(--bg-tertiary);
  border-radius: 8px;
  overflow: hidden;
  font-size: 0.8125rem;
}

.selector-header {
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  user-select: none;
  
  &:hover {
    background: var(--bg-secondary);
  }
}

.selector-label {
  font-weight: 500;
  flex: 1;
}

.selected-count {
  color: var(--primary-color);
  font-size: 0.75rem;
  margin-right: 0.5rem;
}

.expand-icon {
  font-size: 0.625rem;
  color: var(--text-muted);
}

.selector-body {
  border-top: 1px solid var(--border-color);
  padding: 0.5rem;
}

.deleted-warning {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem;
  background: #fef3c7;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.75rem;
  color: #92400e;
}

.dismiss-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #92400e;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
}

.loading, .no-libraries {
  text-align: center;
  padding: 0.5rem;
  color: var(--text-muted);
}

.library-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.library-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  
  &:hover {
    background: var(--bg-secondary);
  }
  
  input {
    margin: 0;
  }
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.lib-name {
  flex: 1;
}

.lib-type {
  font-size: 0.6875rem;
  color: var(--text-muted);
  background: var(--bg-primary);
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
}

// Slide transition
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.slide-enter-to,
.slide-leave-from {
  max-height: 200px;
}
</style>
