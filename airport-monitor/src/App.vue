<template>
  <main class="p-6 flex gap-4">
    <Airport title="Airport" url="http://localhost:5001/state/airport" name="BIAL" />
    <Sky title="Sky" url="http://localhost:5001/state/sky" />
    <Airport title="Airport" url="http://localhost:5001/state/airport" name="LHR" />
  </main>
</template>

<script setup>
import Airport from './components/Airport.vue'
import Sky from './components/Sky.vue'
</script>

<style>
body {
  font-family: system-ui, sans-serif;
  margin: 0;
}
</style>
