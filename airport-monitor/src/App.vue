<template>
  <main class="p-6 gap-4">
    <Sky title="Sky" url="http://localhost:5001/state/sky" />

    <!-- Airport input form -->
    <div class="p-4 border rounded mb-4">
      <div class="flex gap-2">
        <input v-model="newAirport" type="text" placeholder="Enter airport code (e.g., BIAL, LHR)"
          class="border p-2 flex-grow" />
        <button @click="addAirport" class="bg-blue-500 text-white px-4 py-2 rounded">
          Add Airport
        </button>
      </div>
    </div>

    <!-- Dynamic airport list -->
    <div class="p-6 flex flex-wrap gap-4">
      <div v-for="(airport, index) in airports" :key="airport" class="relative">
        <button @click="removeAirport(index)"
          class="absolute top-2 right-2 bg-red-500 text-white w-6 h-6 rounded-full flex items-center justify-center"
          title="Remove airport">
          ×
        </button>
        <Airport title="Airport" url="http://localhost:5001/state/airport" :name="airport" />
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import Airport from './components/Airport.vue'
import Sky from './components/Sky.vue'

// Local state
const airports = ref([])
const newAirport = ref('')

// Add airport function
const addAirport = () => {
  const airportCode = newAirport.value.trim()
  if (airportCode && !airports.value.includes(airportCode)) {
    airports.value.push(airportCode)
    newAirport.value = '' // Clear input after adding
  }
}

// Remove airport function
const removeAirport = (index) => {
  airports.value.splice(index, 1)
}
</script>

<style>
body {
  font-family: system-ui, sans-serif;
  margin: 0;
}
</style>
