<template>
  <div 
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm selection:bg-indigo-500 selection:text-white"
    @click.self="$emit('close')"
    @keydown.esc="$emit('close')"
  >
    <div 
      class="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] transition-all transform animate-in fade-in zoom-in-95 duration-200"
    >
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
            <Upload class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-base font-bold text-white leading-tight">Add to Library</h2>
            <p class="text-xs text-slate-400">Upload PDF documents, manga folders, or archives</p>
          </div>
        </div>
        <button
          @click="$emit('close')"
          :disabled="isUploading"
          class="p-2 text-slate-400 hover:text-white hover:bg-slate-800/80 rounded-xl transition cursor-pointer disabled:opacity-50"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body / Form -->
      <div class="p-6 overflow-y-auto space-y-5">
        
        <!-- Upload Mode Tabs -->
        <div class="grid grid-cols-3 gap-1.5 p-1 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <button
            type="button"
            @click="switchMode('pdf')"
            class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg text-xs font-medium transition cursor-pointer"
            :class="uploadMode === 'pdf' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
          >
            <FileText class="w-3.5 h-3.5" />
            <span>PDF File</span>
          </button>

          <button
            type="button"
            @click="switchMode('folder')"
            class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg text-xs font-medium transition cursor-pointer"
            :class="uploadMode === 'folder' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
          >
            <FolderUp class="w-3.5 h-3.5" />
            <span>Folder</span>
          </button>

          <button
            type="button"
            @click="switchMode('archive')"
            class="flex items-center justify-center gap-1.5 py-2 px-2.5 rounded-lg text-xs font-medium transition cursor-pointer"
            :class="uploadMode === 'archive' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
          >
            <Archive class="w-3.5 h-3.5" />
            <span>ZIP / CBZ</span>
          </button>
        </div>

        <!-- Category Selector -->
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">
            Category / Folder
          </label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <select
              v-model="selectedCategory"
              class="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition capitalize cursor-pointer"
            >
              <option v-for="cat in categories" :key="cat" :value="cat">
                📁 {{ cat }}
              </option>
              <option value="__NEW__">+ New Category...</option>
            </select>

            <!-- Custom category input if __NEW__ chosen -->
            <input
              v-if="selectedCategory === '__NEW__'"
              v-model="customCategory"
              type="text"
              placeholder="e.g. comics, novels"
              class="w-full bg-slate-950/80 border border-indigo-500/50 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
        </div>

        <!-- Optional Book Title Override -->
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">
            Book Title <span class="text-slate-500 font-normal">(Optional)</span>
          </label>
          <input
            v-model="bookTitle"
            type="text"
            placeholder="Leave empty to use original filename/folder name"
            class="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
          />
        </div>

        <!-- Dropzone / File Picker Area -->
        <div>
          <!-- Hidden inputs for each mode -->
          <input
            ref="pdfInputRef"
            type="file"
            accept=".pdf"
            multiple
            class="hidden"
            @change="handleFileInput"
          />
          <input
            ref="folderInputRef"
            type="file"
            webkitdirectory
            directory
            multiple
            class="hidden"
            @change="handleFileInput"
          />
          <input
            ref="archiveInputRef"
            type="file"
            accept=".zip,.cbz"
            multiple
            class="hidden"
            @change="handleFileInput"
          />

          <!-- Drop Area -->
          <div
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="openPicker"
            class="border-2 border-dashed rounded-2xl p-6 text-center transition cursor-pointer flex flex-col items-center justify-center gap-2"
            :class="isDragging ? 'border-indigo-500 bg-indigo-500/10' : 'border-slate-800 hover:border-slate-700 bg-slate-950/40 hover:bg-slate-950/80'"
          >
            <div class="p-3 bg-slate-800/60 rounded-full text-indigo-400 mb-1">
              <FolderUp v-if="uploadMode === 'folder'" class="w-6 h-6" />
              <Archive v-else-if="uploadMode === 'archive'" class="w-6 h-6" />
              <FileUp v-else class="w-6 h-6" />
            </div>

            <p class="text-sm font-semibold text-slate-200">
              <span v-if="uploadMode === 'folder'">Choose a manga/comic folder</span>
              <span v-else-if="uploadMode === 'archive'">Click or drag .zip or .cbz file</span>
              <span v-else>Click or drag PDF document(s)</span>
            </p>
            <p class="text-xs text-slate-400">
              <span v-if="uploadMode === 'folder'">Contains images (.jpg, .png, .webp)</span>
              <span v-else-if="uploadMode === 'archive'">Unpacks automatically into a new book</span>
              <span v-else>Supports Thai and Unicode filenames</span>
            </p>
          </div>
        </div>

        <!-- Selected Files List -->
        <div v-if="selectedFiles.length > 0" class="p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-300 font-semibold border-b border-slate-800/60 pb-1.5">
            <span>Selected Files ({{ selectedFiles.length }})</span>
            <div class="flex items-center gap-2">
              <span class="text-slate-400 font-normal">{{ totalSizeFormatted }}</span>
              <button 
                type="button" 
                @click="clearFiles" 
                class="text-rose-400 hover:text-rose-300 transition"
              >
                Clear
              </button>
            </div>
          </div>
          <div class="max-h-28 overflow-y-auto space-y-1 text-xs text-slate-400 pr-1">
            <div 
              v-for="(f, idx) in selectedFiles.slice(0, 10)" 
              :key="idx" 
              class="flex items-center justify-between truncate py-0.5"
            >
              <span class="truncate pr-2">{{ f.webkitRelativePath || f.name }}</span>
              <span class="text-[10px] text-slate-500 whitespace-nowrap">{{ formatBytes(f.size) }}</span>
            </div>
            <div v-if="selectedFiles.length > 10" class="text-[10px] text-slate-500 text-center pt-1">
              + {{ selectedFiles.length - 10 }} more files
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="p-3 bg-rose-950/40 border border-rose-800/50 rounded-xl flex items-center gap-2.5 text-xs text-rose-300">
          <AlertCircle class="w-4 h-4 shrink-0 text-rose-400" />
          <span>{{ errorMessage }}</span>
        </div>

        <!-- Uploading / Processing State -->
        <div v-if="isUploading" class="space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-300">
            <span class="flex items-center gap-2">
              <Loader2 class="w-3.5 h-3.5 animate-spin text-indigo-400" />
              <span>{{ uploadStatusMessage }}</span>
            </span>
            <span class="font-medium text-indigo-400">{{ uploadProgress }}%</span>
          </div>
          <div class="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
            <div 
              class="bg-indigo-600 h-full rounded-full transition-all duration-300"
              :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
        </div>

      </div>

      <!-- Footer Actions -->
      <div class="px-6 py-4 border-t border-slate-800/80 bg-slate-900/50 flex items-center justify-end gap-3">
        <button
          type="button"
          @click="$emit('close')"
          :disabled="isUploading"
          class="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800/80 rounded-xl transition cursor-pointer disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="button"
          @click="submitUpload"
          :disabled="selectedFiles.length === 0 || isUploading"
          class="flex items-center gap-2 px-5 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-950 disabled:text-indigo-400/50 text-white rounded-xl transition shadow-lg shadow-indigo-500/20 cursor-pointer disabled:cursor-not-allowed"
        >
          <Loader2 v-if="isUploading" class="w-3.5 h-3.5 animate-spin" />
          <Upload v-else class="w-3.5 h-3.5" />
          <span>{{ isUploading ? 'Uploading & Indexing...' : 'Upload & Add to Library' }}</span>
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  Upload,
  FileUp,
  FolderUp,
  Archive,
  FileText,
  X,
  Loader2,
  AlertCircle
} from 'lucide-vue-next'

const props = defineProps({
  categories: {
    type: Array,
    default: () => ['document', 'manga']
  }
})

const emit = defineEmits(['close', 'uploaded'])

// Form State
const uploadMode = ref('pdf') // 'pdf' | 'folder' | 'archive'
const selectedCategory = ref('document')
const customCategory = ref('')
const bookTitle = ref('')
const selectedFiles = ref([])
const isDragging = ref(false)

// Upload Progress & Status
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatusMessage = ref('Preparing files...')
const errorMessage = ref(null)

// Template Refs
const pdfInputRef = ref(null)
const folderInputRef = ref(null)
const archiveInputRef = ref(null)

// Mode Switcher
const switchMode = (mode) => {
  uploadMode.value = mode
  clearFiles()
  if (mode === 'pdf') {
    selectedCategory.value = 'document'
  } else {
    selectedCategory.value = 'manga'
  }
}

const openPicker = () => {
  if (uploadMode.value === 'folder' && folderInputRef.value) {
    folderInputRef.value.click()
  } else if (uploadMode.value === 'archive' && archiveInputRef.value) {
    archiveInputRef.value.click()
  } else if (pdfInputRef.value) {
    pdfInputRef.value.click()
  }
}

const handleFileInput = (e) => {
  const files = Array.from(e.target.files || [])
  if (files.length > 0) {
    selectedFiles.value = files
    // If single file or folder, pre-fill title if empty
    if (!bookTitle.value) {
      if (uploadMode.value === 'folder' && files[0].webkitRelativePath) {
        const rootFolder = files[0].webkitRelativePath.split('/')[0]
        bookTitle.value = rootFolder
      } else if (files.length === 1) {
        const nameWithoutExt = files[0].name.replace(/\.[^/.]+$/, '')
        bookTitle.value = nameWithoutExt
      }
    }
  }
}

const handleDrop = (e) => {
  isDragging.value = false
  const items = e.dataTransfer.files
  if (items && items.length > 0) {
    selectedFiles.value = Array.from(items)
    if (!bookTitle.value && selectedFiles.value.length === 1) {
      bookTitle.value = selectedFiles.value[0].name.replace(/\.[^/.]+$/, '')
    }
  }
}

const clearFiles = () => {
  selectedFiles.value = []
  errorMessage.value = null
  if (pdfInputRef.value) pdfInputRef.value.value = ''
  if (folderInputRef.value) folderInputRef.value.value = ''
  if (archiveInputRef.value) archiveInputRef.value.value = ''
}

// Helpers
const totalSizeFormatted = computed(() => {
  const total = selectedFiles.value.reduce((acc, f) => acc + (f.size || 0), 0)
  return formatBytes(total)
})

const formatBytes = (bytes, decimals = 1) => {
  if (!bytes) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

// Upload Submission
const submitUpload = async () => {
  if (selectedFiles.value.length === 0) return

  let finalCategory = selectedCategory.value === '__NEW__'
    ? customCategory.value.trim()
    : selectedCategory.value

  if (!finalCategory) {
    finalCategory = uploadMode.value === 'pdf' ? 'document' : 'manga'
  }

  isUploading.value = true
  uploadProgress.value = 10
  uploadStatusMessage.value = 'Uploading files to library...'
  errorMessage.value = null

  try {
    const formData = new FormData()
    formData.append('category', finalCategory)
    if (bookTitle.value && bookTitle.value.trim()) {
      formData.append('book_name', bookTitle.value.trim())
    }

    // Include relative paths for folder uploads
    const relPaths = []
    let hasRelativePaths = false
    selectedFiles.value.forEach((file) => {
      formData.append('files', file)
      if (file.webkitRelativePath) {
        hasRelativePaths = true
        relPaths.push(file.webkitRelativePath)
      } else {
        relPaths.push(file.name)
      }
    })

    if (hasRelativePaths) {
      formData.append('relative_paths', JSON.stringify(relPaths))
    }

    // Use XMLHttpRequest for progress tracking
    const result = await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/api/upload')

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          // Keep progress up to 90% during upload, remaining 10% for server cover generation
          const percent = Math.round((event.loaded / event.total) * 85)
          uploadProgress.value = percent
          if (percent >= 85) {
            uploadStatusMessage.value = 'Generating covers & updating library index...'
          }
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText))
          } catch (e) {
            resolve({ success: true })
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText)
            reject(new Error(err.detail || `Upload failed with HTTP ${xhr.status}`))
          } catch (e) {
            reject(new Error(`Upload failed with HTTP ${xhr.status}`))
          }
        }
      }

      xhr.onerror = () => reject(new Error('Network error during upload.'))
      xhr.send(formData)
    })

    uploadProgress.value = 100
    uploadStatusMessage.value = 'Success! Book added to library.'

    setTimeout(() => {
      emit('uploaded', { category: finalCategory, result })
      emit('close')
    }, 600)

  } catch (err) {
    errorMessage.value = err.message
  } finally {
    isUploading.value = false
  }
}
</script>
