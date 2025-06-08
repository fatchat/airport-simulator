<template>
  <main class="p-6 flex gap-4">
    <Sky title="Sky" url="http://localhost:5001/state/sky" />
    <Airport title="Airport" url="http://localhost:5001/state/airport" name="BIAL" />
    <Runway title="Runway" url="http://localhost:5001/state/runway" airport="BIAL" runway_number="R1" />
    <Gate title="Gate" url="http://localhost:5001/state/gate" airport="BIAL" gate_number="A1" />
    <Airport title="Airport" url="http://localhost:5001/state/airport" name="LHR" />
  </main>
</template>

<script setup>
import Airport from './components/Airport.vue'
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
