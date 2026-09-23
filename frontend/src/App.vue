<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
    <!-- Initial Auth Checking State -->
    <div 
      v-if="isCheckingAuth" 
      class="min-h-screen flex flex-col items-center justify-center gap-3 text-slate-400 bg-slate-950"
    >
      <Loader2 class="w-10 h-10 animate-spin text-indigo-500" />
      <p class="text-sm">Checking session...</p>
    </div>

    <!-- Login Page (shown before library) -->
    <LoginView
      v-else-if="!isAuthenticated"
      @login-success="handleLoginSuccess"
    />

    <!-- Direct URL Loading State -->
    <div 
      v-else-if="isResolvingUrl" 
      class="min-h-screen flex flex-col items-center justify-center gap-3 text-slate-400 bg-slate-950"
    >
      <Loader2 class="w-10 h-10 animate-spin text-indigo-500" />
      <p class="text-sm">Loading book details...</p>
    </div>

    <!-- Main Library View -->
    <LibraryView
      v-else-if="!activeBook"
      @open-reader="openBookReader"
      @logout="handleLogout"
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
import LoginView from './components/LoginView.vue'
import LibraryView from './components/LibraryView.vue'
import ReaderView from './components/ReaderView.vue'

const isAuthenticated = ref(false)
const isCheckingAuth = ref(true)
const activeBook = ref(null)
const isResolvingUrl = ref(false)

const checkAuth = async () => {
  const token = localStorage.getItem('manga_reader_token')
  if (!token) {
    isAuthenticated.value = false
    isCheckingAuth.value = false
    return
  }

  try {
    const res = await fetch('/api/auth/verify', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    if (res.ok) {
      isAuthenticated.value = true
    } else {
      localStorage.removeItem('manga_reader_token')
      localStorage.removeItem('manga_reader_user')
      isAuthenticated.value = false
    }
  } catch (err) {
    console.error('Auth verification error:', err)
    // If backend temporarily unavailable, accept existing token
    isAuthenticated.value = !!token
  } finally {
    isCheckingAuth.value = false
  }
}

const handleLoginSuccess = () => {
  isAuthenticated.value = true
  loadBookFromUrl()
}

const handleLogout = () => {
  localStorage.removeItem('manga_reader_token')
  localStorage.removeItem('manga_reader_user')
  isAuthenticated.value = false
  activeBook.value = null
  if (window.location.pathname !== '/') {
    window.history.replaceState({}, '', '/')
  }
}

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
  if (isAuthenticated.value) {
    loadBookFromUrl()
  }
}

onMounted(async () => {
  await checkAuth()
  if (isAuthenticated.value) {
    loadBookFromUrl()
  }
  window.addEventListener('popstate', handlePopState)
})

onUnmounted(() => {
  window.removeEventListener('popstate', handlePopState)
})
</script>
