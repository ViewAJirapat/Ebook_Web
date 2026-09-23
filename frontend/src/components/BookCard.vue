<template>
  <a 
    :href="'/read/' + encodeURIComponent(book.id)"
    @click="handleClick"
    class="group relative bg-[#181b26] border border-slate-800/80 hover:border-indigo-500/50 rounded-xl overflow-hidden shadow-lg transition-all duration-300 hover:-translate-y-1 hover:shadow-indigo-500/10 cursor-pointer flex flex-col no-underline text-inherit select-none"
  >
    <!-- Cover Thumbnail -->
    <div class="relative w-full aspect-[2/3] bg-[#12141c] overflow-hidden">
      <img
        v-if="book.cover_url && !imageError"
        :src="book.cover_url"
        :alt="book.title"
        @error="imageError = true"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-slate-900/80 text-slate-500">
        <component :is="book.type === 'pdf' ? FileText : Folder" class="w-12 h-12 mb-2 text-slate-600" />
        <span class="text-xs font-medium text-slate-400">No Cover Available</span>
      </div>

      <!-- Open in New Tab Quick Action Button -->
      <button
        type="button"
        @click.stop.prevent="openInNewTab"
        class="absolute top-2 left-2 p-1.5 bg-slate-950/80 hover:bg-indigo-600 text-slate-300 hover:text-white rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 backdrop-blur-md shadow-md z-10 cursor-pointer"
        title="Open in new tab"
      >
        <ExternalLink class="w-3.5 h-3.5" />
      </button>

      <!-- Format & Category Badges -->
      <div class="absolute top-2.5 right-2.5 flex items-center gap-1.5 z-10">
        <span 
          v-if="book.category && book.category !== 'General'"
          class="px-1.5 py-0.5 text-[9px] font-semibold tracking-wide uppercase rounded-md shadow-md backdrop-blur-md bg-slate-900/90 text-indigo-300 border border-indigo-500/30"
        >
          {{ book.category }}
        </span>
        <span 
          class="px-2 py-0.5 text-[11px] font-semibold tracking-wider uppercase rounded-md backdrop-blur-md shadow-sm"
          :class="book.type === 'pdf' ? 'bg-rose-500/80 text-white' : 'bg-indigo-600/80 text-white'"
        >
          {{ book.type }}
        </span>
      </div>

      <!-- Progress Overlay Bar -->
      <div v-if="book.total_pages > 0" class="absolute bottom-0 left-0 right-0 h-1.5 bg-black/50">
        <div 
          class="h-full bg-indigo-500 transition-all duration-300"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>
    </div>

    <!-- Metadata Content -->
    <div class="p-3.5 flex flex-col flex-1 justify-between gap-2">
      <div>
        <h3 class="text-sm font-semibold text-slate-100 group-hover:text-indigo-400 transition-colors line-clamp-2" :title="book.title">
          {{ book.title }}
        </h3>
      </div>

      <div class="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800">
        <span class="flex items-center gap-1">
          <BookOpen class="w-3.5 h-3.5" />
          {{ book.total_pages }} {{ book.total_pages === 1 ? 'page' : 'pages' }}
        </span>

        <div class="flex items-center gap-2">
          <span v-if="book.last_page > 0" class="text-indigo-400 font-medium">
            p. {{ book.last_page }} ({{ progressPercent }}%)
          </span>
          <span v-else class="text-slate-400">
            Unread
          </span>

          <button
            type="button"
            @click.stop.prevent="$emit('delete', book)"
            class="p-1 text-slate-400 hover:text-rose-400 hover:bg-rose-500/20 rounded-md transition cursor-pointer"
            title="Delete ebook"
          >
            <Trash2 class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  </a>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Folder, FileText, BookOpen, ExternalLink, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['select', 'delete'])

const imageError = ref(false)

const progressPercent = computed(() => {
  if (!props.book.total_pages || props.book.total_pages <= 0) return 0
  const current = props.book.last_page || 0
  return Math.min(100, Math.round((current / props.book.total_pages) * 100))
})

const handleClick = (e) => {
  // If standard left click without modifier keys, emit select for SPA transition
  if (e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
    e.preventDefault()
    emit('select', props.book)
  }
  // Otherwise (middle click with button 1 or ctrl+click), browser default action opens in new tab!
}

const openInNewTab = () => {
  window.open(`/read/${encodeURIComponent(props.book.id)}`, '_blank')
}
</script>
