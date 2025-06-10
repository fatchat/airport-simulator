<template>
  <div class="max-w-md mx-auto w-64  shadow">
    <template v-if="loading">
      <p class="text-center text-gray-500">Loading...</p>
    </template>

    <template v-else-if="error">
      <p class="text-center text-red-500">Error: {{ error }}</p>
    </template>

    <template v-else>
      <h2 class="text-xl font-semibold mt-2 mb-2">Gate {{ props.gate_number }} / {{ props.airport }}</h2>
      <p>{{ data.state }}</p>
      <template v-if="data.current_plane">
        <p class="font-medium">{{ data.current_plane.plane_id }} is at the gate</p>
        <p>Leaving in: {{ data.current_plane.time_at_gate }} ticks</p>
      </template>
    </template>
  </div>
</template>

<script setup>

import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  title: String,
  url: String,
  airport: String,
  gate_number: String,
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
    const res = await fetch(props.url + "?airport=" + props.airport + "&gate_number=" + props.gate_number)
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
