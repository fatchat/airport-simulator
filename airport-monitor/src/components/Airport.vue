<template>
  <div class="max-w-md mx-auto w-64 border-2 border-white rounded-2xl shadow text-left p-2">
    <template v-if="loading">
      <p class="text-center text-gray-500">Loading...</p>
    </template>

    <template v-else-if="error">
      <p class="text-center text-red-500">Error: {{ error }}</p>
    </template>

    <template v-else>
      <h2 class="text-xl font-semibold mt-2 mb-2">Airport {{ props.name }}</h2>

      <div v-for="(state, runway) in data.runways" v-bind:key="runway">
        <Runway title="Runway" url="http://localhost:5001/state/runway" :airport="name" :runway_number="runway" />
      </div>

      <div v-for="(state, gate) in data.gates" v-bind:key="gate">
        <Gate title="Gate" url="http://localhost:5001/state/gate" :airport="name" :gate_number="gate" />
      </div>
    </template>
  </div>
</template>

<script setup>

import { ref, onMounted, onUnmounted } from 'vue'
import Runway from './Runway.vue'
import Gate from './Gate.vue'

const props = defineProps({
  title: String,
  url: String,
  name: String,
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
    const res = await fetch(props.url + "?airport=" + props.name)
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
