<template>
  <div class="fixed inset-0 z-50 bg-black/95 flex flex-col select-none">
    
    <!-- Top Bar Controls -->
    <header class="bg-[#12141c]/90 border-b border-slate-800/80 px-4 py-2.5 flex items-center justify-between text-slate-200">
      <div class="flex items-center gap-3 min-w-0">
        <button 
          @click="$emit('close')" 
          class="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition cursor-pointer"
          title="Close Reader (Esc)"
        >
          <ArrowLeft class="w-5 h-5" />
        </button>
        <div class="min-w-0">
          <h2 class="text-sm font-semibold truncate text-slate-100">{{ book.title }}</h2>
          <p class="text-[11px] text-slate-400">
            Page {{ currentPage + 1 }} of {{ pages.length || book.total_pages }}
          </p>
        </div>
      </div>

      <!-- Center: Reading Mode Switcher -->
      <div class="flex items-center bg-[#1c202d] p-1 rounded-lg border border-slate-800 text-xs">
        <button
          @click="mode = 'single'"
          :class="mode === 'single' ? 'bg-indigo-600 text-white font-medium shadow' : 'text-slate-400 hover:text-white'"
          class="px-2.5 py-1 rounded transition flex items-center gap-1 cursor-pointer"
        >
          <FileText class="w-3.5 h-3.5" />
          <span>Single</span>
        </button>
        <button
          @click="mode = 'continuous'"
          :class="mode === 'continuous' ? 'bg-indigo-600 text-white font-medium shadow' : 'text-slate-400 hover:text-white'"
          class="px-2.5 py-1 rounded transition flex items-center gap-1 cursor-pointer"
        >
          <Rows class="w-3.5 h-3.5" />
          <span>Webtoon</span>
        </button>
      </div>

      <!-- Right: Fullscreen & Close -->
      <div class="flex items-center gap-2">
        <button
          @click="toggleFullscreen"
          class="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition cursor-pointer"
          title="Toggle Fullscreen"
        >
          <Maximize2 v-if="!isFullscreen" class="w-4 h-4" />
          <Minimize2 v-else class="w-4 h-4" />
        </button>
        <button
          @click="$emit('close')"
          class="p-1.5 hover:bg-rose-500/20 hover:text-rose-400 rounded-lg text-slate-400 transition cursor-pointer"
          title="Close (Esc)"
        >
          <X class="w-5 h-5" />
        </button>
      </div>
    </header>

    <!-- Viewer Body -->
    <div class="relative flex-1 overflow-hidden flex items-center justify-center bg-black">
      
      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center gap-3 text-slate-400">
        <Loader2 class="w-8 h-8 animate-spin text-indigo-500" />
        <span class="text-sm">Loading book pages...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-6 max-w-md text-center bg-slate-900 border border-red-500/30 rounded-xl text-slate-200">
        <p class="text-red-400 font-semibold mb-2">Failed to load pages</p>
        <p class="text-xs text-slate-400 mb-4">{{ error }}</p>
        <button
          @click="fetchPages"
          class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg transition"
        >
          Retry
        </button>
      </div>

      <!-- 1. Single Page Mode -->
      <div 
        v-else-if="mode === 'single'" 
        class="relative w-full h-full flex items-center justify-center p-2"
      >
        <!-- Previous Page Click Area / Button -->
        <button
          @click="prevPage"
          :disabled="currentPage <= 0"
          class="absolute left-4 top-1/2 -translate-y-1/2 z-20 p-3 bg-black/60 hover:bg-black/90 text-white rounded-full backdrop-blur-md opacity-40 hover:opacity-100 disabled:opacity-0 transition cursor-pointer"
          title="Previous Page (Left Arrow)"
        >
          <ChevronLeft class="w-6 h-6" />
        </button>

        <div class="w-full h-full flex items-center justify-center max-w-5xl">
          <img
            v-if="pages[currentPage]"
            :src="pages[currentPage]"
            :alt="'Page ' + (currentPage + 1)"
            class="max-h-full max-w-full object-contain select-none shadow-2xl rounded"
          />
        </div>

        <!-- Next Page Click Area / Button -->
        <button
          @click="nextPage"
          :disabled="currentPage >= pages.length - 1"
          class="absolute right-4 top-1/2 -translate-y-1/2 z-20 p-3 bg-black/60 hover:bg-black/90 text-white rounded-full backdrop-blur-md opacity-40 hover:opacity-100 disabled:opacity-0 transition cursor-pointer"
          title="Next Page (Right Arrow)"
        >
          <ChevronRight class="w-6 h-6" />
        </button>
      </div>

      <!-- 2. Continuous Webtoon Mode -->
      <div 
        v-else-if="mode === 'continuous'" 
        ref="scrollContainer"
        @scroll="onContinuousScroll"
        class="w-full h-full overflow-y-auto flex flex-col items-center py-6 px-2 gap-2"
      >
        <div 
          v-for="(pageUrl, idx) in pages" 
          :key="idx" 
          :id="'page-view-' + idx"
          class="max-w-3xl w-full flex justify-center bg-black/40"
        >
          <img
            :src="pageUrl"
            :alt="'Page ' + (idx + 1)"
            class="w-full object-contain shadow-md rounded"
            loading="lazy"
          />
        </div>
      </div>

    </div>

    <!-- Bottom Navigation Bar (Single Page Mode) -->
    <footer 
      v-if="mode === 'single' && pages.length > 0"
      class="bg-[#12141c]/90 border-t border-slate-800/80 px-4 py-2 flex items-center justify-between text-xs text-slate-300"
    >
      <button 
        @click="prevPage" 
        :disabled="currentPage <= 0"
        class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-30 rounded-lg flex items-center gap-1 transition"
      >
        <ChevronLeft class="w-4 h-4" />
        <span>Prev</span>
      </button>

      <!-- Slider Jump Control -->
      <div class="flex items-center gap-3 flex-1 max-w-md mx-4">
        <span>1</span>
        <input
          type="range"
          min="0"
          :max="pages.length - 1"
          :value="currentPage"
          @input="goToPage(parseInt($event.target.value))"
          class="w-full accent-indigo-500 cursor-pointer"
        />
        <span>{{ pages.length }}</span>
      </div>

      <button 
        @click="nextPage" 
        :disabled="currentPage >= pages.length - 1"
        class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-30 rounded-lg flex items-center gap-1 transition"
      >
        <span>Next</span>
        <ChevronRight class="w-4 h-4" />
      </button>
    </footer>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import {
  ArrowLeft,
  X,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  FileText,
  Rows,
  Loader2
} from 'lucide-vue-next'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'progress-updated'])

const pages = ref([])
const currentPage = ref(0)
const mode = ref('single') // 'single' | 'continuous'
const loading = ref(true)
const error = ref(null)
const isFullscreen = ref(false)
const scrollContainer = ref(null)

const fetchPages = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/books/${props.book.id}/pages`)
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || `Server returned ${res.status}`)
    }
    const data = await res.json()
    pages.value = data.pages || []

    // Resume from saved reading progress (0-indexed)
    if (props.book.last_page && props.book.last_page > 0) {
      currentPage.value = Math.min(props.book.last_page - 1, Math.max(0, pages.value.length - 1))
    } else {
      currentPage.value = 0
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const saveProgress = async (pageIdx) => {
  try {
    const pageNum = pageIdx + 1
    await fetch(`/api/books/${props.book.id}/progress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page: pageNum })
    })
    emit('progress-updated', { bookId: props.book.id, page: pageNum })
  } catch (e) {
    console.error('Failed to save progress:', e)
  }
}

const goToPage = (pageIdx) => {
  if (pageIdx < 0 || pageIdx >= pages.value.length) return
  currentPage.value = pageIdx
  saveProgress(pageIdx)
}

const nextPage = () => {
  if (currentPage.value < pages.value.length - 1) {
    goToPage(currentPage.value + 1)
  }
}

const prevPage = () => {
  if (currentPage.value > 0) {
    goToPage(currentPage.value - 1)
  }
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().then(() => {
      isFullscreen.value = true
    }).catch(() => {})
  } else {
    document.exitFullscreen().then(() => {
      isFullscreen.value = false
    }).catch(() => {})
  }
}

const handleKeydown = (e) => {
  if (e.key === 'Escape') {
    emit('close')
  } else if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
    if (mode.value === 'single') nextPage()
  } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
    if (mode.value === 'single') prevPage()
  }
}

const onContinuousScroll = () => {
  if (!scrollContainer.value || pages.value.length === 0) return
  const container = scrollContainer.value
  const scrollMiddle = container.scrollTop + container.clientHeight / 2

  for (let i = 0; i < pages.value.length; i++) {
    const el = document.getElementById(`page-view-${i}`)
    if (el) {
      const top = el.offsetTop
      const bottom = top + el.clientHeight
      if (scrollMiddle >= top && scrollMiddle <= bottom) {
        if (currentPage.value !== i) {
          currentPage.value = i
          saveProgress(i)
        }
        break
      }
    }
  }
}

onMounted(() => {
  fetchPages()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>
