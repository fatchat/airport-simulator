<template>
  <main class="p-6 flex gap-4">
    <Sky title="Sky" url="http://localhost:5004/state" />
    <Runway title="Runway" url="http://localhost:5003/state" />
    <Gate title="Gate" url="http://localhost:5001/state" />
    <Gate title="Gate" url="http://localhost:5002/state" />
  </main>
</template>

<script setup>
import Runway from './components/Runway.vue'
import Sky from './components/Sky.vue'
import Gate from './components/Gate.vue'
</script>

<style>
body {
  font-family: system-ui, sans-serif;
  margin: 0;
}
</style>
