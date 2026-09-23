<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
    <!-- Direct URL Loading State -->
    <div 
      v-if="isResolvingUrl" 
      class="min-h-screen flex flex-col items-center justify-center gap-3 text-slate-400 bg-slate-950"
    >
      <Loader2 class="w-10 h-10 animate-spin text-indigo-500" />
      <p class="text-sm">Loading book details...</p>
    </div>

    <!-- Main Library View -->
    <LibraryView
      v-else-if="!activeBook"
      @open-reader="openBookReader"
    />

    <!-- Webtoon / Document Reader View -->
    <ReaderView
      v-else
      :book="activeBook"
      @close="closeBookReader"
      @progress-updated="handleProgressUpdated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import LibraryView from './components/LibraryView.vue'
import ReaderView from './components/ReaderView.vue'

const activeBook = ref(null)
const isResolvingUrl = ref(false)

const getBookIdFromUrl = () => {
  // Check HTML5 pathname: /read/:bookId
  const pathMatch = window.location.pathname.match(/^\/read\/(.+)/)
  if (pathMatch && pathMatch[1]) {
    return decodeURIComponent(pathMatch[1])
  }
  // Check Hash fallback: #/read/:bookId
  const hashMatch = window.location.hash.match(/^#\/read\/(.+)/)
  if (hashMatch && hashMatch[1]) {
    return decodeURIComponent(hashMatch[1])
  }
  return null
}

const loadBookFromUrl = async () => {
  const targetId = getBookIdFromUrl()
  if (!targetId) {
    activeBook.value = null
    document.title = 'Local Manga & Document Reader'
    return
  }

  isResolvingUrl.value = true
  try {
    const res = await fetch(`/api/books/${encodeURIComponent(targetId)}`)
    if (res.ok) {
      const bookData = await res.json()
      activeBook.value = bookData
      document.title = `${bookData.title} - Local Manga Reader`
    } else {
      // If single book lookup returns 404, fallback to /api/books
      const allRes = await fetch('/api/books')
      if (allRes.ok) {
        const books = await allRes.json()
        const matched = books.find(b => b.id === targetId)
        if (matched) {
          activeBook.value = matched
          document.title = `${matched.title} - Local Manga Reader`
        } else {
          // Not found -> reset to library
          window.history.replaceState({}, '', '/')
          activeBook.value = null
        }
      }
    }
  } catch (err) {
    console.error('Failed to load book from URL:', err)
    activeBook.value = null
  } finally {
    isResolvingUrl.value = false
  }
}

const openBookReader = (book) => {
  activeBook.value = book
  document.title = `${book.title} - Local Manga Reader`
  const targetUrl = `/read/${encodeURIComponent(book.id)}`
  if (window.location.pathname !== targetUrl) {
    window.history.pushState({ bookId: book.id }, '', targetUrl)
  }
}

const closeBookReader = () => {
  activeBook.value = null
  document.title = 'Local Manga & Document Reader'
  if (window.location.pathname !== '/') {
    window.history.pushState({}, '', '/')
  }
}

const handleProgressUpdated = ({ bookId, page }) => {
  if (activeBook.value && activeBook.value.id === bookId) {
    activeBook.value.last_page = page
  }
}

const handlePopState = () => {
  loadBookFromUrl()
}

onMounted(() => {
  loadBookFromUrl()
  window.addEventListener('popstate', handlePopState)
})

onUnmounted(() => {
  window.removeEventListener('popstate', handlePopState)
})
</script>
