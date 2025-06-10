<template>
  <div class="max-w-md mx-auto w-64  shadow">
    <template v-if="loading">
      <p class="text-center text-gray-500">Loading...</p>
    </template>

    <template v-else-if="error">
      <p class="text-center text-red-500">Error: {{ error }}</p>
    </template>

    <template v-else>
      <h2 class="text-xl font-semibold mt-2 mb-2">Runway {{ props.runway_number }} / {{ props.airport }}</h2>
      <p>{{ data.state }}</p>
      <div class="space-y-1" v-if="data.current_plane">
        <p>{{ data.current_plane.plane_id }} -> {{ data.current_plane.destination_gate }}</p>
        <p><span class="font-medium">Arriving in...</span> {{ data.ticks_till_exit }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>

import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  title: String,
  url: String,
  airport: String,
  runway_number: String,
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
    const res = await fetch(props.url + "?airport=" + props.airport + "&runway_number=" + props.runway_number)
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
