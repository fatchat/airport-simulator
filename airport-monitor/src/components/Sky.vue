<template>
  <div class="max-w-md mx-auto w-64 border-2 border-white rounded-2xl shadow">
    <template v-if="loading">
      <p class="text-center text-gray-500">Loading...</p>
    </template>

    <template v-else-if="error">
      <p class="text-center text-red-500">Error: {{ error }}</p>
    </template>

    <template v-else>
      <h2 class="text-xl font-semibold mt-2 mb-2">In the air</h2>
      <p>{{ data.plane_queue.length }} planes in the air</p>
      <p v-if="data.plane_queue.length > 0">{{ data.plane_queue[0].plane_id }} is next </p>
    </template>
  </div>
</template>

<script setup>

import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  title: String,
  url: String,
  interval: {
    type: Number,
    default: 1000 // Default to 5 seconds
  }
})

const data = ref(null)
const loading = ref(true)
const error = ref(null)

let intervalId = null

const fetchData = async () => {
  try {
    const res = await fetch(props.url)
    if (!res.ok) throw new Error(res.statusText)
    data.value = await res.json()
    error.value = null
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  intervalId = setInterval(fetchData, props.interval)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})

</script>
