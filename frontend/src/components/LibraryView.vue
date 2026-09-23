<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
    <!-- Header with Admin Scan & Search -->
    <header class="sticky top-0 z-30 bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 lg:px-8 py-3.5">
      <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-6">
        
        <!-- Brand & Title -->
        <div class="flex items-center justify-between w-full sm:w-auto">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400 shadow-sm">
              <BookOpen class="w-6 h-6" />
            </div>
            <div>
              <h1 class="text-base sm:text-lg font-bold text-white tracking-tight leading-tight">
                Local Manga Reader
              </h1>
              <p class="text-xs text-slate-400 font-normal">
                Self-hosted Document & Manga Reader
              </p>
            </div>
          </div>

          <!-- Mobile Actions -->
          <div class="sm:hidden flex items-center gap-1.5">
            <button
              @click="showUploadModal = true"
              class="flex items-center gap-1 px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition"
              title="Add ebook or folder"
            >
              <Plus class="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
            <button
              @click="triggerScan"
              :disabled="isScanning"
              class="p-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg transition"
              title="Scan data/library"
            >
              <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isScanning }" />
            </button>
          </div>
        </div>

        <!-- Search Bar -->
        <div class="relative w-full sm:max-w-md">
          <Search class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search titles, authors, or files..."
            class="w-full bg-slate-900/90 border border-slate-800 rounded-xl pl-10 pr-9 py-2 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
          />
          <button 
            v-if="searchQuery" 
            @click="searchQuery = ''" 
            class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Desktop Action Buttons -->
        <div class="hidden sm:flex items-center gap-2.5">
          <button
            @click="showUploadModal = true"
            class="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition cursor-pointer shadow-md shadow-indigo-500/20"
          >
            <Plus class="w-4 h-4" />
            <span>Add Book</span>
          </button>

          <button
            @click="triggerScan"
            :disabled="isScanning"
            class="flex items-center gap-2 px-3.5 py-2 text-sm font-medium bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white rounded-xl transition cursor-pointer disabled:cursor-not-allowed"
          >
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isScanning }" />
            <span>{{ isScanning ? 'Scanning...' : 'Scan Library' }}</span>
          </button>
        </div>

      </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      
      <!-- Sub-bar: Filters & Count -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div class="flex items-center gap-2.5">
          <h2 class="text-xl font-bold text-white tracking-tight">Your Books</h2>
          <span class="text-xs px-2 py-0.5 bg-slate-900 border border-slate-800 rounded-full text-slate-400">
            {{ filteredBooks.length }}
          </span>
          <button
            @click="showUploadModal = true"
            class="flex items-center gap-1 px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-medium transition cursor-pointer shadow-sm ml-1"
            title="Add ebook or folder"
          >
            <Plus class="w-3.5 h-3.5 text-indigo-400" />
            <span>Add</span>
          </button>
        </div>

        <!-- Dynamic Category Pills & Subdirectory Navigation -->
        <div class="flex items-center gap-1.5 overflow-x-auto max-w-full pb-1 scrollbar-none self-start sm:self-auto">
          <button
            v-for="cat in availableCategories"
            :key="cat.name"
            @click="selectedCategory = cat.name"
            :class="selectedCategory === cat.name ? 'bg-indigo-600 text-white font-medium shadow-sm' : 'bg-slate-900/90 text-slate-400 hover:text-slate-200 border border-slate-800/80'"
            class="px-3 py-1.5 rounded-xl text-xs transition cursor-pointer whitespace-nowrap capitalize flex items-center gap-1.5"
          >
            <Folder class="w-3.5 h-3.5 opacity-70" />
            <span>{{ cat.name }}</span>
            <span class="text-[10px] opacity-75">({{ cat.count }})</span>
          </button>
        </div>
      </div>

      <!-- Toast Feedback Message -->
      <transition
        enter-active-class="transform ease-out duration-300 transition"
        enter-from-class="translate-y-2 opacity-0"
        enter-to-class="translate-y-0 opacity-100"
        leave-active-class="transition ease-in duration-200"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div 
          v-if="toastMessage" 
          class="mb-6 p-4 rounded-xl border text-sm flex items-center justify-between backdrop-blur-sm"
          :class="toastType === 'error' ? 'bg-rose-950/50 border-rose-800/80 text-rose-300' : 'bg-emerald-950/50 border-emerald-800/80 text-emerald-300'"
        >
          <div class="flex items-center gap-2">
            <CheckCircle2 v-if="toastType !== 'error'" class="w-4 h-4 text-emerald-400" />
            <AlertCircle v-else class="w-4 h-4 text-rose-400" />
            <span>{{ toastMessage }}</span>
          </div>
          <button @click="toastMessage = ''" class="text-slate-400 hover:text-white">&times;</button>
        </div>
      </transition>

      <!-- Loading State -->
      <div v-if="isLoading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3.5 sm:gap-5">
        <div 
          v-for="n in 12" 
          :key="n" 
          class="rounded-xl bg-slate-900 border border-slate-800/80 overflow-hidden flex flex-col"
        >
          <div class="w-full aspect-[2/3] skeleton-placeholder"></div>
          <div class="p-3 space-y-2">
            <div class="h-3.5 bg-slate-800 rounded w-3/4 skeleton-placeholder"></div>
            <div class="h-3 bg-slate-800 rounded w-1/2 skeleton-placeholder"></div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div 
        v-else-if="filteredBooks.length === 0" 
        class="bg-slate-900/60 border border-dashed border-slate-800 rounded-2xl p-10 sm:p-14 text-center max-w-md mx-auto my-12"
      >
        <div class="w-14 h-14 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <BookX class="w-7 h-7" />
        </div>
        <h3 class="text-base sm:text-lg font-semibold text-slate-200">No books found</h3>
        <p class="text-xs sm:text-sm text-slate-400 mt-2 mb-6 leading-relaxed">
          <span v-if="searchQuery">No items match your search for "{{ searchQuery }}".</span>
          <span v-else>Put manga folders or PDF documents inside <code class="text-indigo-400 px-1 py-0.5 bg-slate-800 rounded">data/library/</code> and run a scan.</span>
        </p>
        <div class="flex flex-wrap items-center justify-center gap-3">
          <button
            @click="showUploadModal = true"
            class="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition cursor-pointer shadow-md shadow-indigo-500/20"
          >
            <Plus class="w-4 h-4" />
            <span>Add Book</span>
          </button>
          <button
            @click="triggerScan"
            :disabled="isScanning"
            class="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl text-sm font-medium transition cursor-pointer"
          >
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isScanning }" />
            <span>Scan data/library/</span>
          </button>
        </div>
      </div>

      <!-- Book Grid -->
      <div 
        v-else 
        class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3.5 sm:gap-5"
      >
        <a
          v-for="book in filteredBooks"
          :key="book.id"
          :href="'/read/' + encodeURIComponent(book.id)"
          @click="handleCardClick(book, $event)"
          @auxclick="handleCardAuxClick(book, $event)"
          class="group relative bg-slate-900/80 hover:bg-slate-900 border border-slate-800/80 hover:border-indigo-500/50 rounded-xl overflow-hidden shadow-lg transition-all duration-200 hover:-translate-y-1 cursor-pointer flex flex-col no-underline text-inherit select-none"
        >
          <!-- Cover Image Container -->
          <div class="relative w-full aspect-[2/3] bg-slate-950 overflow-hidden">
            <img
              v-if="book.cover_url"
              :src="book.cover_url"
              :alt="book.title"
              loading="lazy"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              @error="handleImageError($event, book)"
            />
            <div v-else class="w-full h-full flex flex-col items-center justify-center p-3 text-center bg-slate-950 text-slate-500">
              <component :is="book.type === 'pdf' ? FileText : Folder" class="w-10 h-10 mb-1 text-slate-600" />
              <span class="text-[11px] text-slate-400">No Cover</span>
            </div>

            <!-- Open in New Tab Quick Action Button -->
            <button
              type="button"
              @click.stop.prevent="openInNewTab(book)"
              class="absolute top-2 left-2 p-1.5 bg-slate-950/80 hover:bg-indigo-600 text-slate-300 hover:text-white rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 backdrop-blur-md shadow-md z-10 cursor-pointer"
              title="Open in new tab"
            >
              <ExternalLink class="w-3.5 h-3.5" />
            </button>

            <!-- Format & Subdirectory Category Badges -->
            <div class="absolute top-2 right-2 flex items-center gap-1.5 z-10">
              <span 
                v-if="book.category && book.category !== 'General'"
                class="px-1.5 py-0.5 text-[9px] font-semibold tracking-wide uppercase rounded-md shadow-md backdrop-blur-md bg-slate-900/90 text-indigo-300 border border-indigo-500/30"
              >
                {{ book.category }}
              </span>
              <span 
                class="px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded-md shadow-md backdrop-blur-md"
                :class="book.type === 'pdf' ? 'bg-rose-500/90 text-white' : 'bg-indigo-600/90 text-white'"
              >
                {{ book.type }}
              </span>
            </div>

            <!-- Progress Overlay Bar -->
            <div v-if="book.total_pages > 0" class="absolute bottom-0 left-0 right-0 h-1 bg-slate-950/80">
              <div 
                class="h-full bg-indigo-500 transition-all duration-300"
                :style="{ width: getProgressPercent(book) + '%' }"
              ></div>
            </div>
          </div>

          <!-- Metadata & Progress Badge -->
          <div class="p-3 flex flex-col flex-1 justify-between gap-2.5">
            <div>
              <h3 
                class="text-xs sm:text-sm font-semibold text-slate-100 group-hover:text-indigo-400 transition-colors line-clamp-2 leading-snug"
                :title="book.title"
              >
                {{ book.title }}
              </h3>
            </div>

            <div class="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
              <!-- Progress Badge e.g. 'Page 12/45' -->
              <span 
                class="font-medium inline-flex items-center px-2 py-0.5 rounded text-[11px]"
                :class="getProgressBadgeClass(book)"
              >
                {{ getProgressText(book) }}
              </span>

              <span class="text-slate-400 font-mono text-[10px]">
                {{ book.total_pages }}p
              </span>
            </div>
          </div>
        </a>
      </div>

    </main>

    <!-- Upload Modal -->
    <UploadModal
      v-if="showUploadModal"
      :categories="rawCategoriesList"
      @close="showUploadModal = false"
      @uploaded="onBookUploaded"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  BookOpen,
  Search,
  RefreshCw,
  Folder,
  FileText,
  X,
  BookX,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Upload,
  Plus
} from 'lucide-vue-next'
import UploadModal from './UploadModal.vue'

const emit = defineEmits(['open-reader'])

const books = ref([])
const isLoading = ref(true)
const isScanning = ref(false)
const showUploadModal = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('All')

const toastMessage = ref('')
const toastType = ref('success')

const rawCategoriesList = computed(() => {
  const cats = new Set(['document', 'manga'])
  books.value.forEach(b => {
    if (b.category && b.category !== 'General') {
      cats.add(b.category)
    }
  })
  return Array.from(cats).sort((a, b) => a.localeCompare(b))
})

const onBookUploaded = async ({ category, result }) => {
  await fetchBooks()
  if (category) {
    selectedCategory.value = category
  }
  showToast(result?.message || `Successfully added book to "${category}"!`, 'success')
}

const showToast = (msg, type = 'success') => {
  toastMessage.value = msg
  toastType.value = type
  setTimeout(() => {
    if (toastMessage.value === msg) {
      toastMessage.value = ''
    }
  }, 4000)
}

const fetchBooks = async () => {
  try {
    const res = await fetch('/api/books')
    if (res.ok) {
      const data = await res.json()
      // Merge with localStorage progress if local is more recent
      books.value = data.map(b => {
        const localProgress = localStorage.getItem(`manga_progress_${b.id}`)
        if (localProgress) {
          const parsed = parseInt(localProgress, 10)
          if (!isNaN(parsed) && parsed > (b.last_page || 0)) {
            b.last_page = parsed
          }
        }
        return b
      })
    }
  } catch (err) {
    console.error('Failed to load books:', err)
  } finally {
    isLoading.value = false
  }
}

const triggerScan = async () => {
  if (isScanning.value) return
  isScanning.value = true
  try {
    const res = await fetch('/api/admin/scan', { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      showToast(data.message || `Scan completed (${data.count} items).`, 'success')
      await fetchBooks()
    } else {
      showToast('Scan failed. Please verify server logs.', 'error')
    }
  } catch (err) {
    showToast(`Network error scanning library: ${err.message}`, 'error')
  } finally {
    isScanning.value = false
  }
}

const availableCategories = computed(() => {
  const counts = {}
  books.value.forEach(b => {
    const cat = b.category || 'General'
    counts[cat] = (counts[cat] || 0) + 1
  })
  const sortedKeys = Object.keys(counts).sort((a, b) => a.localeCompare(b))
  const list = sortedKeys.map(cat => ({
    name: cat,
    count: counts[cat]
  }))
  return [{ name: 'All', count: books.value.length }, ...list]
})

const filteredBooks = computed(() => {
  return books.value.filter(book => {
    const bookCategory = (book.category || 'General').toLowerCase()
    const matchesCategory = selectedCategory.value === 'All' || bookCategory === selectedCategory.value.toLowerCase()
    const query = searchQuery.value.toLowerCase().trim()
    const matchesQuery = !query || 
      book.title.toLowerCase().includes(query) || 
      bookCategory.includes(query)
    return matchesCategory && matchesQuery
  })
})

const getProgressPercent = (book) => {
  if (!book.total_pages || book.total_pages <= 0) return 0
  const current = book.last_page || 0
  return Math.min(100, Math.round((current / book.total_pages) * 100))
}

const getProgressText = (book) => {
  const current = book.last_page || 0
  if (current <= 0) return 'Unread'
  if (book.total_pages && current >= book.total_pages) return 'Completed'
  return `Page ${current}/${book.total_pages || '?'}`
}

const getProgressBadgeClass = (book) => {
  const current = book.last_page || 0
  if (current <= 0) {
    return 'bg-slate-800 text-slate-400'
  }
  if (book.total_pages && current >= book.total_pages) {
    return 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
  }
  return 'bg-indigo-950/80 text-indigo-300 border border-indigo-800/60'
}

const handleImageError = (event, book) => {
  event.target.style.display = 'none'
  book.cover_url = ''
}

const handleCardClick = (book, event) => {
  // If standard left click without modifier keys, open seamlessly inside current tab
  if (event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
    event.preventDefault()
    emit('open-reader', book)
  }
  // If ctrl/cmd is pressed or middle click, allow browser default behavior (open in new tab)
}

const handleCardAuxClick = (book, event) => {
  // Middle click (event.button === 1): browser naturally navigates to href in new tab
}

const openInNewTab = (book) => {
  window.open(`/read/${encodeURIComponent(book.id)}`, '_blank')
}

const selectBook = (book) => {
  emit('open-reader', book)
}

onMounted(() => {
  fetchBooks()
})
</script>
