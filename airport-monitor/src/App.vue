<template>
  <main class="p-6 flex gap-4">
    <Sky title="Sky" url="http://localhost:5001/state/sky" />
    <Runway title="Runway" url="http://localhost:5001/state/runway" />
    <Gate title="Gate" url="http://localhost:5001/state/gate?gate_number=A1" />
    <Gate title="Gate" url="http://localhost:5001/state/gate?gate_number=A2" />
    <Gate title="Gate" url="http://localhost:5001/state/gate?gate_number=B3" />
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
