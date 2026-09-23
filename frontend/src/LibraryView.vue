<template>
  <LibraryView @open-reader="$emit('open-reader', $event)" />
</template>

<script setup>
import LibraryView from './components/LibraryView.vue'
defineEmits(['open-reader'])
</script>
