<template>
  <div class="border rounded p-4 shadow-sm bg-white">
    <h2 class="font-bold mb-2">{{ title }}</h2>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">Error: {{ error }}</div>
    <pre v-else>{{ data }}</pre>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  title: String,
  url: String
})

const data = ref(null)
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const res = await fetch(props.url)
    if (!res.ok) throw new Error(res.statusText)
    data.value = await res.json()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})
</script>
