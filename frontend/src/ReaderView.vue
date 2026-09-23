<template>
  <ReaderView 
    :book="book" 
    @close="$emit('close')" 
    @progress-updated="$emit('progress-updated', $event)" 
  />
</template>

<script setup>
import ReaderView from './components/ReaderView.vue'

defineProps({
  book: {
    type: Object,
    required: true
  }
})

defineEmits(['close', 'progress-updated'])
</script>
