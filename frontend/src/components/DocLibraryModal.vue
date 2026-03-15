<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="handleClose">
      <div class="modal-container doc-library-modal">
        <!-- Library List View -->
        <template v-if="!editingLibrary">
          <div class="modal-header">
            <h3>我的文档库</h3>
            <button class="close-btn" @click="handleClose">×</button>
          </div>
          
          <div class="modal-body">
            <div v-if="loading" class="loading-state">加载中...</div>
            
            <template v-else>
              <div v-if="libraries.length === 0" class="empty-state">
                <p>暂无文档库</p>
                <p class="text-muted">点击下方按钮创建第一个文档库</p>
              </div>
              
              <div v-else class="library-list">
                <div 
                  v-for="lib in libraries" 
                  :key="lib.id"
                  class="library-item"
                  @mouseenter="hoveredLibraryId = lib.id"
                  @mouseleave="hoveredLibraryId = null"
                >
                  <div class="library-info">
                    <div class="library-name">{{ lib.name }}</div>
                    <div class="library-meta">
                      <span class="library-type">{{ lib.type }}</span>
                      <span class="library-stats">
                        {{ lib.doc_count }} 个文档 · {{ formatTokens(lib.total_tokens) }} tokens · {{ lib.chunk_count }} 块
                      </span>
                    </div>
                  </div>
                  <div class="library-actions" :class="{ visible: hoveredLibraryId === lib.id }">
                    <button class="action-btn" @click="openLibraryEditor(lib)" title="编辑">
                      <img :src="iconEdit" class="action-icon" alt="编辑" />
                    </button>
                    <button class="action-btn danger" @click="confirmDeleteLibrary(lib)" title="删除">
                      <img :src="iconDelete" class="action-icon" alt="删除" />
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </div>
          
          <div class="modal-footer">
            <button class="btn btn-primary" @click="showCreateDialog = true">
              <img :src="iconPlus" class="btn-icon" alt="" /> 新建文档库
            </button>
          </div>
        </template>
        
        <!-- Library Editor View -->
        <template v-else>
          <div class="modal-header">
            <button class="back-btn" @click="closeLibraryEditor">←</button>
            <h3>{{ editingLibrary.name }}</h3>
            <button class="close-btn" @click="handleClose">×</button>
          </div>
          
          <div class="modal-body editor-body">
            <div class="upload-zone" 
                 :class="{ dragging: isDragging, disabled: isUploading }"
                 @dragover.prevent="handleDragOver"
                 @dragleave.prevent="handleDragLeave"
                 @drop.prevent="handleDrop">
              <div class="upload-hint">
                <p v-if="!isUploading">将文件拖拽到此处，或点击下方按钮上传</p>
                <p v-else>正在上传和处理文件...</p>
                <p class="upload-note">仅支持 .txt 和 .md 文件</p>
              </div>
              
              <div v-if="isUploading" class="upload-progress">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
                </div>
                <div class="progress-text">{{ uploadStatus }}</div>
                <button class="btn btn-danger btn-sm" @click="cancelUpload">停止上传</button>
              </div>
              
              <div v-else class="upload-actions">
                <input type="file" ref="fileInput" @change="handleFileSelect" 
                       accept=".txt,.md" multiple style="display: none" />
                <button class="btn btn-primary" @click="$refs.fileInput.click()">选择文件</button>
              </div>
            </div>
            
            <div class="documents-section">
              <div class="section-header">
                <h4>文件列表 ({{ documents.length }})</h4>
                <button v-if="hasPendingDocs" 
                        class="btn btn-primary btn-sm"
                        :disabled="isProcessing"
                        @click="startProcessing">
                  {{ isProcessing ? '处理中...' : '开始处理' }}
                </button>
              </div>
              
              <div v-if="documentsLoading" class="loading-state">加载中...</div>
              
              <div v-else-if="documents.length === 0" class="empty-docs">
                <p>暂无文件</p>
              </div>
              
              <div v-else class="document-list">
                <div 
                  v-for="doc in documents" 
                  :key="doc.id"
                  class="document-item"
                  @mouseenter="hoveredDocId = doc.id"
                  @mouseleave="hoveredDocId = null"
                >
                  <div class="doc-info">
                    <div class="doc-name">
                      {{ doc.original_filename }}
                      <span v-if="doc.status === 'pending'" class="doc-status pending">待处理</span>
                      <span v-else-if="doc.status === 'processing'" class="doc-status processing">处理中</span>
                      <span v-else-if="doc.status === 'failed'" class="doc-status failed" :title="doc.error_message">失败</span>
                    </div>
                    <div class="doc-meta" v-if="doc.status === 'completed'">
                      {{ formatTokens(doc.token_count) }} tokens · {{ doc.chunk_count }} 块
                    </div>
                  </div>
                  <button 
                    class="action-btn danger" 
                    :class="{ visible: hoveredDocId === doc.id }"
                    @click="confirmDeleteDocument(doc)"
                    title="删除"
                    :disabled="doc.status === 'processing'"
                  >
                    <img :src="iconDelete" class="action-icon" alt="删除" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
    
    <!-- Create Library Dialog -->
    <div v-if="showCreateDialog" class="modal-overlay" @click.self="showCreateDialog = false">
      <div class="modal-container create-dialog">
        <div class="modal-header">
          <h3>新建文档库</h3>
          <button class="close-btn" @click="showCreateDialog = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>名称</label>
            <input v-model="newLibraryName" class="input" placeholder="输入文档库名称" />
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="newLibraryType" class="input">
              <option v-for="t in libraryTypes" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showCreateDialog = false">取消</button>
          <button class="btn btn-primary" @click="createLibrary" :disabled="!newLibraryName.trim()">创建</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '@/api'
import iconEdit from '../../assets/edit.svg'
import iconDelete from '../../assets/delete.svg'
import iconPlus from '../../assets/plus.svg'

const props = defineProps({
  visible: Boolean
})

const emit = defineEmits(['close', 'libraries-changed'])

// State
const loading = ref(false)
const libraries = ref([])
const libraryTypes = ref([])
const hoveredLibraryId = ref(null)
const editingLibrary = ref(null)
const documents = ref([])
const documentsLoading = ref(false)
const hoveredDocId = ref(null)

// Upload state
const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const uploadCancelled = ref(false)

// Processing state
const isProcessing = ref(false)
const processingInterval = ref(null)

// Create dialog state
const showCreateDialog = ref(false)
const newLibraryName = ref('')
const newLibraryType = ref('')

const hasPendingDocs = computed(() => {
  return documents.value.some(d => d.status === 'pending')
})

function formatTokens(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n
}

async function loadLibraries() {
  loading.value = true
  try {
    const [libRes, typesRes] = await Promise.all([
      api.getLibraries(),
      api.getLibraryTypes()
    ])
    libraries.value = libRes.libraries
    libraryTypes.value = typesRes.types
    if (!newLibraryType.value && typesRes.types.length > 0) {
      newLibraryType.value = typesRes.types[0]
    }
  } catch (err) {
    console.error('Failed to load libraries:', err)
  } finally {
    loading.value = false
  }
}

async function loadDocuments() {
  if (!editingLibrary.value) return
  documentsLoading.value = true
  try {
    const res = await api.getLibraryDocuments(editingLibrary.value.id)
    documents.value = res.documents
  } catch (err) {
    console.error('Failed to load documents:', err)
  } finally {
    documentsLoading.value = false
  }
}

function openLibraryEditor(lib) {
  editingLibrary.value = lib
  loadDocuments()
}

function closeLibraryEditor() {
  editingLibrary.value = null
  documents.value = []
  loadLibraries()
}

async function createLibrary() {
  if (!newLibraryName.value.trim()) return
  try {
    await api.createLibrary({
      name: newLibraryName.value.trim(),
      type: newLibraryType.value
    })
    showCreateDialog.value = false
    newLibraryName.value = ''
    loadLibraries()
    emit('libraries-changed')
  } catch (err) {
    alert('创建失败: ' + (err.error || err.message || '未知错误'))
  }
}

async function confirmDeleteLibrary(lib) {
  if (!confirm(`确定要删除文档库"${lib.name}"吗？所有文档和数据将被永久删除。`)) return
  try {
    await api.deleteLibrary(lib.id)
    loadLibraries()
    emit('libraries-changed')
  } catch (err) {
    alert('删除失败: ' + (err.error || err.message || '未知错误'))
  }
}

async function confirmDeleteDocument(doc) {
  if (!confirm(`确定要删除文件"${doc.original_filename}"吗？`)) return
  try {
    await api.deleteDocument(editingLibrary.value.id, doc.id)
    loadDocuments()
    emit('libraries-changed')
  } catch (err) {
    alert('删除失败: ' + (err.error || err.message || '未知错误'))
  }
}

// File upload handling
function handleDragOver(e) {
  if (isUploading.value) return
  isDragging.value = true
}

function handleDragLeave(e) {
  isDragging.value = false
}

async function handleDrop(e) {
  isDragging.value = false
  if (isUploading.value) return
  
  const files = Array.from(e.dataTransfer.files)
  await uploadFiles(files)
}

async function handleFileSelect(e) {
  const files = Array.from(e.target.files)
  await uploadFiles(files)
  e.target.value = ''
}

async function uploadFiles(files) {
  if (!files.length || isUploading.value) return
  
  const validFiles = []
  const invalidFiles = []
  
  for (const file of files) {
    const ext = file.name.split('.').pop().toLowerCase()
    if (['txt', 'md'].includes(ext)) {
      validFiles.push(file)
    } else {
      invalidFiles.push(file.name)
    }
  }
  
  if (invalidFiles.length > 0) {
    alert(`以下文件类型不支持，已跳过：\n${invalidFiles.join('\n')}`)
  }
  
  if (validFiles.length === 0) return
  
  isUploading.value = true
  uploadCancelled.value = false
  uploadProgress.value = 0
  
  let uploaded = 0
  for (const file of validFiles) {
    if (uploadCancelled.value) break
    
    uploadStatus.value = `上传中: ${file.name} (${uploaded + 1}/${validFiles.length})`
    
    try {
      await api.uploadDocument(editingLibrary.value.id, file)
      uploaded++
      uploadProgress.value = (uploaded / validFiles.length) * 100
    } catch (err) {
      const msg = err.error || err.message || '上传失败'
      alert(`文件 ${file.name} 上传失败: ${msg}`)
    }
  }
  
  isUploading.value = false
  uploadStatus.value = ''
  loadDocuments()
  emit('libraries-changed')
}

function cancelUpload() {
  uploadCancelled.value = true
}

async function startProcessing() {
  if (isProcessing.value) return
  
  try {
    await api.startEmbedding(editingLibrary.value.id)
    isProcessing.value = true
    startPolling()
  } catch (err) {
    alert('启动处理失败: ' + (err.error || err.message || '未知错误'))
  }
}

function startPolling() {
  if (processingInterval.value) return
  
  processingInterval.value = setInterval(async () => {
    try {
      const res = await api.getEmbeddingProgress()
      if (!res.status.is_embedding) {
        stopPolling()
        isProcessing.value = false
        loadDocuments()
        loadLibraries()
        emit('libraries-changed')
      } else {
        loadDocuments()
      }
    } catch (err) {
      console.error('Polling error:', err)
    }
  }, 2000)
}

function stopPolling() {
  if (processingInterval.value) {
    clearInterval(processingInterval.value)
    processingInterval.value = null
  }
}

function handleClose() {
  if (isUploading.value) {
    if (!confirm('正在上传文件，确定要关闭吗？已上传的文件会保留。')) return
    uploadCancelled.value = true
  }
  stopPolling()
  editingLibrary.value = null
  emit('close')
}

watch(() => props.visible, (val) => {
  if (val) {
    loadLibraries()
    checkProcessingStatus()
  } else {
    stopPolling()
  }
})

async function checkProcessingStatus() {
  try {
    const res = await api.getEmbeddingProgress()
    if (res.status.is_embedding) {
      isProcessing.value = true
      startPolling()
    }
  } catch (err) {
    console.error('Failed to check processing status:', err)
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style lang="scss" scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: var(--bg-primary);
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-library-modal {
  width: 600px;
  min-height: 400px;
}

.create-dialog {
  width: 400px;
}

.modal-header {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  
  h3 {
    flex: 1;
    margin: 0;
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
  padding: 0;
  line-height: 1;
  
  &:hover {
    color: var(--text-primary);
  }
}

.back-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  margin-right: 0.5rem;
  border-radius: 4px;
  
  &:hover {
    background: var(--bg-tertiary);
  }
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.editor-body {
  padding: 0;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.loading-state, .empty-state, .empty-docs {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
}

.library-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.library-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  transition: background-color 0.2s;
  
  &:hover {
    background: var(--bg-tertiary);
  }
}

.library-info {
  flex: 1;
  min-width: 0;
}

.library-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.library-meta {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.library-type {
  background: var(--bg-tertiary);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  margin-right: 0.5rem;
}

.library-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
  
  &.visible {
    opacity: 1;
  }
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: var(--bg-tertiary);
  }
  
  &.danger:hover {
    background: #fee2e2;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.action-icon {
  width: 16px;
  height: 16px;
  filter: saturate(0) brightness(0.5);
}

.btn-icon {
  width: 14px;
  height: 14px;
  margin-right: 0.5rem;
  filter: brightness(100);
}

// Upload Zone
.upload-zone {
  padding: 2rem;
  border-bottom: 1px solid var(--border-color);
  text-align: center;
  transition: background-color 0.2s;
  
  &.dragging {
    background: var(--primary-light, #eef2ff);
  }
  
  &.disabled {
    opacity: 0.7;
    pointer-events: none;
  }
}

.upload-hint {
  margin-bottom: 1rem;
  
  p {
    margin: 0.25rem 0;
  }
  
  .upload-note {
    font-size: 0.8125rem;
    color: var(--text-muted);
  }
}

.upload-progress {
  margin-top: 1rem;
}

.progress-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.3s;
}

.progress-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

// Documents Section
.documents-section {
  padding: 1rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  
  h4 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
  }
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.document-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  
  &:hover {
    background: var(--bg-tertiary);
  }
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.doc-status {
  font-size: 0.75rem;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  
  &.pending {
    background: #fef3c7;
    color: #92400e;
  }
  
  &.processing {
    background: #dbeafe;
    color: #1e40af;
  }
  
  &.failed {
    background: #fee2e2;
    color: #b91c1c;
    cursor: help;
  }
}

.doc-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.125rem;
}

// Form
.form-group {
  margin-bottom: 1rem;
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    font-size: 0.875rem;
  }
}
</style>
