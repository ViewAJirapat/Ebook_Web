<template>
  <div class="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 selection:bg-indigo-500 selection:text-white relative overflow-hidden">
    <!-- Subtle Ambient Background Glow -->
    <div class="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

    <div class="w-full max-w-md relative z-10">
      <!-- Card Container -->
      <div class="bg-slate-900/90 border border-slate-800/90 backdrop-blur-xl rounded-2xl p-6 sm:p-8 shadow-2xl shadow-indigo-950/20">
        
        <!-- Brand Header -->
        <div class="text-center mb-7">
          <div class="inline-flex p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl shadow-inner mb-3">
            <BookOpen class="w-8 h-8" />
          </div>
          <h1 class="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Local Manga Reader
          </h1>
          <p class="text-xs sm:text-sm text-slate-400 mt-1 font-normal">
            Sign in to access your manga & document library
          </p>
        </div>

        <!-- Error Alert -->
        <div
          v-if="errorMessage"
          class="mb-5 p-3.5 bg-rose-950/50 border border-rose-800/80 rounded-xl text-rose-300 text-xs flex items-center gap-2.5 animate-shake"
        >
          <AlertCircle class="w-4 h-4 text-rose-400 shrink-0" />
          <span>{{ errorMessage }}</span>
        </div>

        <!-- Login Form -->
        <form @submit.prevent="handleLogin" class="space-y-4">
          <!-- Username Field -->
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Username
            </label>
            <div class="relative">
              <User class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                v-model="username"
                type="text"
                required
                autocomplete="username"
                placeholder="Enter username"
                class="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
              />
            </div>
          </div>

          <!-- Password Field -->
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Password
            </label>
            <div class="relative">
              <Lock class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="Enter password"
                class="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-0.5 cursor-pointer"
                title="Toggle password visibility"
              >
                <EyeOff v-if="showPassword" class="w-4 h-4" />
                <Eye v-else class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="pt-2">
            <button
              type="submit"
              :disabled="isLoading"
              class="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900/60 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/25 transition cursor-pointer disabled:cursor-not-allowed"
            >
              <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin text-white" />
              <ArrowRight v-else class="w-4 h-4" />
              <span>{{ isLoading ? 'Signing In...' : 'Sign In' }}</span>
            </button>
          </div>
        </form>

        <!-- Credentials Hint / Notice -->
        <div class="mt-6 pt-4 border-t border-slate-800/80 text-center text-slate-500 text-[11px] leading-relaxed">
          Default access: <code class="text-indigo-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 font-mono">admin</code> / <code class="text-indigo-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 font-mono">123456</code>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import {
  BookOpen,
  User,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  ArrowRight
} from 'lucide-vue-next'

const emit = defineEmits(['login-success'])

const username = ref('admin')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = 'Please provide both username and password.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value.trim(),
        password: password.value
      })
    })

    const data = await res.json().catch(() => ({}))

    if (res.ok && data.success) {
      localStorage.setItem('manga_reader_token', data.token)
      localStorage.setItem('manga_reader_user', data.user || username.value)
      emit('login-success', data)
    } else {
      errorMessage.value = data.detail || 'Invalid username or password.'
    }
  } catch (err) {
    errorMessage.value = `Network error: ${err.message}`
  } finally {
    isLoading.value = false
  }
}
</script>
