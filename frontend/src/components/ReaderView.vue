<template>
  <div 
    class="relative min-h-screen bg-slate-950 text-slate-100 flex flex-col select-none overflow-x-hidden"
    @click="handleContainerClick"
  >
    <!-- Floating Top Bar -->
    <transition
      enter-active-class="transform transition ease-out duration-200"
      enter-from-class="-translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transform transition ease-in duration-150"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="-translate-y-full opacity-0"
    >
      <header
        v-if="showControls"
        class="fixed top-0 left-0 right-0 z-50 bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80 px-4 py-2.5 flex items-center justify-between shadow-xl"
        @click.stop
      >
        <!-- Left: Back Button & Title -->
        <div class="flex items-center gap-3 min-w-0 flex-1 mr-4">
          <button
            @click="$emit('close')"
            class="p-2 hover:bg-slate-800/80 text-slate-400 hover:text-white rounded-xl transition cursor-pointer"
            title="Back to Library (Esc)"
          >
            <ArrowLeft class="w-5 h-5" />
          </button>
          <div class="min-w-0">
            <h2 class="text-sm sm:text-base font-bold text-white truncate">
              {{ book.title }}
            </h2>
            <div class="flex items-center gap-2 text-xs text-slate-400">
              <span class="capitalize">{{ book.type }}</span>
              <span>&bull;</span>
              <span>{{ pages.length }} total pages</span>
            </div>
          </div>
        </div>

        <!-- Right: View Controls -->
        <div class="flex items-center gap-1.5 sm:gap-2">
          <!-- Zero Gap Toggle -->
          <button
            @click="zeroGap = !zeroGap"
            class="px-2.5 py-1.5 text-xs rounded-xl border flex items-center gap-1.5 transition cursor-pointer"
            :class="zeroGap ? 'bg-indigo-600/30 border-indigo-500/50 text-indigo-300' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'"
            title="Toggle zero gap between pages (ideal for webtoons)"
          >
            <SplitSquareVertical class="w-4 h-4" />
            <span class="hidden sm:inline">{{ zeroGap ? 'No Gap' : 'Spaced' }}</span>
          </button>

          <!-- Fit-Width Toggle -->
          <button
            @click="fitWidth = !fitWidth"
            class="px-2.5 py-1.5 text-xs rounded-xl border flex items-center gap-1.5 transition cursor-pointer"
            :class="fitWidth ? 'bg-indigo-600/30 border-indigo-500/50 text-indigo-300' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'"
            title="Toggle Fit Width vs Constrained Column"
          >
            <Scaling class="w-4 h-4" />
            <span class="hidden sm:inline">{{ fitWidth ? 'Fit Width' : 'Constrained' }}</span>
          </button>

          <!-- Fullscreen Toggle -->
          <button
            @click="toggleFullscreen"
            class="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white rounded-xl transition cursor-pointer"
            title="Toggle Fullscreen (F)"
          >
            <Maximize2 v-if="!isFullscreen" class="w-4 h-4" />
            <Minimize2 v-else class="w-4 h-4" />
          </button>
        </div>
      </header>
    </transition>

    <!-- Reading Canvas (Vertical Continuous Scroll) -->
    <main 
      ref="canvasRef"
      class="flex-1 w-full flex flex-col items-center justify-start bg-slate-950 py-2 sm:py-4 transition-all"
    >
      <!-- Loading Initial Pages Spinner -->
      <div v-if="isLoadingPages" class="flex flex-col items-center justify-center min-h-[70vh] gap-3 text-slate-400">
        <Loader2 class="w-10 h-10 animate-spin text-indigo-500" />
        <p class="text-sm">Rendering & loading manga pages...</p>
      </div>

      <!-- Error message -->
      <div v-else-if="errorMessage" class="my-auto p-8 max-w-md bg-slate-900 border border-rose-800/80 rounded-2xl text-center">
        <p class="text-rose-400 font-semibold mb-2">Error Loading Book</p>
        <p class="text-xs text-slate-400 mb-6">{{ errorMessage }}</p>
        <button
          @click="fetchPages"
          class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs rounded-xl text-white transition"
        >
          Retry
        </button>
      </div>

      <!-- Continuous Image Stream -->
      <div
        v-else
        class="w-full flex flex-col items-center transition-all duration-200"
        :class="[
          fitWidth ? 'max-w-full' : 'max-w-3xl sm:max-w-4xl px-2 sm:px-0',
          zeroGap ? 'gap-0' : 'gap-3 sm:gap-4'
        ]"
      >
        <div
          v-for="(pageUrl, index) in pages"
          :key="index"
          :id="'page-container-' + index"
          :data-page-index="index"
          ref="pageRefs"
          class="relative w-full flex justify-center items-center bg-slate-950 transition-all duration-200"
        >
          <!-- Skeleton Placeholder until image enters viewport & finishes loading -->
          <div
            v-if="!imageLoadedMap[index]"
            class="w-full aspect-[2/3] max-h-[85vh] skeleton-placeholder rounded flex flex-col items-center justify-center text-slate-600"
          >
            <div class="flex items-center gap-2 text-xs text-slate-500 bg-slate-950/60 px-3 py-1.5 rounded-full backdrop-blur-sm">
              <Loader2 class="w-3.5 h-3.5 animate-spin text-indigo-400" />
              <span>Page {{ index + 1 }}</span>
            </div>
          </div>

          <!-- Lazy Loaded Image -->
          <img
            v-if="visiblePages[index]"
            :src="pageUrl"
            :alt="'Page ' + (index + 1)"
            class="w-full h-auto object-contain select-none transition-opacity duration-300"
            :class="imageLoadedMap[index] ? 'opacity-100' : 'opacity-0 absolute inset-0'"
            loading="lazy"
            @load="onImageLoad(index)"
            @error="onImageError(index)"
          />
        </div>
      </div>
    </main>

    <!-- Floating Bottom Bar -->
    <transition
      enter-active-class="transform transition ease-out duration-200"
      enter-from-class="translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transform transition ease-in duration-150"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-full opacity-0"
    >
      <footer
        v-if="showControls && pages.length > 0"
        class="fixed bottom-0 left-0 right-0 z-50 bg-slate-950/90 backdrop-blur-md border-t border-slate-800/80 px-4 py-3 shadow-2xl"
        @click.stop
      >
        <div class="max-w-3xl mx-auto flex flex-col gap-2">
          
          <!-- Slider & Quick Navigation -->
          <div class="flex items-center gap-4">
            <button
              @click="jumpPage(currentPage - 1)"
              :disabled="currentPage <= 1"
              class="p-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-30 rounded-lg text-slate-300 transition"
              title="Previous Page"
            >
              <ChevronUp class="w-4 h-4" />
            </button>

            <!-- Range input for quick scrub -->
            <div class="flex-1 relative flex items-center">
              <input
                type="range"
                min="1"
                :max="pages.length"
                :value="currentPage"
                @input="jumpPage(parseInt($event.target.value, 10))"
                class="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none"
              />
            </div>

            <button
              @click="jumpPage(currentPage + 1)"
              :disabled="currentPage >= pages.length"
              class="p-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-30 rounded-lg text-slate-300 transition"
              title="Next Page"
            >
              <ChevronDown class="w-4 h-4" />
            </button>
          </div>

          <!-- Status Indicator: '14 / 85' and Percentage -->
          <div class="flex items-center justify-between text-xs text-slate-400 px-1">
            <span class="font-mono text-slate-300 font-semibold">
              Page {{ currentPage }} / {{ pages.length }}
            </span>
            
            <div class="flex items-center gap-3">
              <span class="text-indigo-400 font-medium">
                {{ Math.round((currentPage / (pages.length || 1)) * 100) }}%
              </span>
              <span class="text-[11px] text-slate-400 hidden sm:inline">
                Tap anywhere to toggle UI
              </span>
            </div>
          </div>

        </div>
      </footer>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import {
  ArrowLeft,
  Maximize2,
  Minimize2,
  ChevronUp,
  ChevronDown,
  Loader2,
  Scaling,
  SplitSquareVertical
} from 'lucide-vue-next'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'progress-updated'])

// UI & Reading states
const pages = ref([])
const currentPage = ref(1)
const showControls = ref(true)
const fitWidth = ref(true) // Full width vs constrained
const zeroGap = ref(true) // Default to zero gap for clean continuous webtoon reading
const isFullscreen = ref(false)
const isLoadingPages = ref(true)
const errorMessage = ref(null)

// Lazy loading and visibility tracking
const visiblePages = reactive({})
const imageLoadedMap = reactive({})
const pageRefs = ref([])

let lazyObserver = null
let scrollObserver = null
let debounceTimer = null

// 1. Fetch Pages List from Backend
const fetchPages = async () => {
  isLoadingPages.value = true
  errorMessage.value = null
  try {
    const res = await fetch(`/api/books/${props.book.id}/pages`)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Server returned code ${res.status}`)
    }
    const data = await res.json()
    pages.value = data.pages || []

    // Determine initial last read page (1-indexed)
    let initialPage = 1
    const localSaved = localStorage.getItem(`manga_progress_${props.book.id}`)
    if (localSaved) {
      initialPage = parseInt(localSaved, 10) || 1
    } else if (props.book.last_page && props.book.last_page > 0) {
      initialPage = props.book.last_page
    }

    currentPage.value = Math.max(1, Math.min(initialPage, pages.value.length))

    // Pre-mark pages around initial page as visible so Page 1 renders immediately without observer delay
    const startIdx = Math.max(0, currentPage.value - 2)
    const endIdx = Math.min(pages.value.length - 1, currentPage.value + 2)
    for (let i = startIdx; i <= endIdx; i++) {
      visiblePages[i] = true
    }

    // Set loading false FIRST so Vue renders the continuous pages list in the DOM
    isLoadingPages.value = false

    // Once DOM updates with the page containers, attach IntersectionObservers and scroll to position
    await nextTick()
    setupObservers()
    scrollToPage(currentPage.value, false)

    // Auto-hide controls after 3.5s of initial open
    setTimeout(() => {
      showControls.value = false
    }, 3500)

  } catch (err) {
    errorMessage.value = err.message
    isLoadingPages.value = false
  }
}

// 2. Setup IntersectionObservers for Lazy Loading & Page Tracking
const setupObservers = () => {
  if (lazyObserver) lazyObserver.disconnect()
  if (scrollObserver) scrollObserver.disconnect()

  // (a) Lazy load images as they approach viewport (margin 800px)
  lazyObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const idx = parseInt(entry.target.dataset.pageIndex, 10)
        if (!isNaN(idx)) {
          visiblePages[idx] = true
        }
      }
    })
  }, {
    root: null,
    rootMargin: '800px 0px 800px 0px',
    threshold: 0.01
  })

  // (b) Active page tracker: detects which page is centered in viewport
  scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const idx = parseInt(entry.target.dataset.pageIndex, 10)
        if (!isNaN(idx)) {
          const pageNum = idx + 1
          if (currentPage.value !== pageNum) {
            currentPage.value = pageNum
            onPageScrolled(pageNum)
          }
        }
      }
    })
  }, {
    root: null,
    rootMargin: '-40% 0px -40% 0px', // Page intersecting center 20% of screen
    threshold: 0
  })

  // Attach observers to every page container
  const elements = document.querySelectorAll('[data-page-index]')
  elements.forEach(el => {
    lazyObserver.observe(el)
    scrollObserver.observe(el)
  })
}

// 3. Image Loading State Handler
const onImageLoad = (index) => {
  imageLoadedMap[index] = true
}

const onImageError = (index) => {
  console.warn(`Failed to load page image ${index}`)
  imageLoadedMap[index] = true
}

// 4. Auto-save reading progress to localStorage and debounce sync to API
const onPageScrolled = (pageNum) => {
  // Save immediately to localStorage
  try {
    localStorage.setItem(`manga_progress_${props.book.id}`, pageNum.toString())
  } catch (e) {
    console.error('LocalStorage error:', e)
  }

  // Debounced sync with POST /api/books/{book_id}/progress
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    syncProgressWithBackend(pageNum)
  }, 600)
}

const syncProgressWithBackend = async (pageNum) => {
  try {
    await fetch(`/api/books/${props.book.id}/progress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page: pageNum })
    })
    emit('progress-updated', { bookId: props.book.id, page: pageNum })
  } catch (e) {
    console.error('Failed to sync progress with backend:', e)
  }
}

// 5. Scroll-to-page navigation
const scrollToPage = (pageNum, smooth = true) => {
  const index = pageNum - 1
  const targetEl = document.getElementById(`page-container-${index}`)
  if (targetEl) {
    targetEl.scrollIntoView({
      behavior: smooth ? 'smooth' : 'auto',
      block: 'start'
    })
  }
}

const jumpPage = (targetNum) => {
  const bounded = Math.max(1, Math.min(targetNum, pages.value.length))
  currentPage.value = bounded
  scrollToPage(bounded, true)
  onPageScrolled(bounded)
}

// 6. UI Interactions
const handleContainerClick = (e) => {
  // Toggle controls when tapping canvas (not buttons or links)
  if (!e.target.closest('button') && !e.target.closest('input')) {
    showControls.value = !showControls.value
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
  } else if (e.key === 'f' || e.key === 'F') {
    toggleFullscreen()
  } else if (e.key === 'w' || e.key === 'W') {
    fitWidth.value = !fitWidth.value
  } else if (e.key === 'g' || e.key === 'G') {
    zeroGap.value = !zeroGap.value
  }
}

onMounted(() => {
  fetchPages()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (lazyObserver) lazyObserver.disconnect()
  if (scrollObserver) scrollObserver.disconnect()
  clearTimeout(debounceTimer)
})
</script>
