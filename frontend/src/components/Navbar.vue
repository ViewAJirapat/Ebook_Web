<template>
  <header class="sticky top-0 z-30 bg-[#161822]/90 backdrop-blur-md border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
      
      <!-- Brand Logo -->
      <div class="flex items-center gap-3">
        <div class="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-lg text-indigo-400">
          <BookOpen class="w-6 h-6" />
        </div>
        <div>
          <h1 class="text-lg font-bold text-slate-100 tracking-tight leading-tight">Local Manga Reader</h1>
          <p class="text-xs text-slate-400">Self-hosted Manga & Document Reader</p>
        </div>
      </div>

      <!-- Search & Filters -->
      <div class="flex-1 max-w-md hidden md:block">
        <div class="relative">
          <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            :value="searchQuery"
            @input="$emit('update:searchQuery', $event.target.value)"
            type="text"
            placeholder="Search manga or document..."
            class="w-full bg-[#1e2230] border border-slate-700/60 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition"
          />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-3">
        <button
          @click="$emit('scan')"
          :disabled="isScanning"
          class="flex items-center gap-2 px-3.5 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900/50 text-white rounded-lg transition shadow-sm shadow-indigo-600/30 cursor-pointer disabled:cursor-not-allowed"
          title="Scan data/library folder for new items"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isScanning }" />
          <span>{{ isScanning ? 'Scanning...' : 'Scan Library' }}</span>
        </button>
      </div>

    </div>
  </header>
</template>

<script setup>
import { BookOpen, RefreshCw, Search } from 'lucide-vue-next'

defineProps({
  searchQuery: {
    type: String,
    default: ''
  },
  isScanning: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:searchQuery', 'scan'])
</script>
