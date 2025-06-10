<template>
  <div class="airport-card">
    <template v-if="loading">
      <p class="text-center text-gray-500">Loading...</p>
    </template>

    <template v-else-if="error">
      <p class="text-center text-red-500">Error: {{ error }}</p>
    </template>

    <template v-else>
      <h3>Airport {{ props.name }}</h3>

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

<style scoped>
.airport-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  /* Or use gap with grid/flex in parent */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
}

.airport-card h3 {
  color: #2c3e50;
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1.2em;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 8px;
}

.details p {
  margin-bottom: 6px;
  line-height: 1.4;
  color: #2c3e50;
}

.label {
  font-weight: bold;
  color: #555;
  margin-right: 5px;
}
</style>