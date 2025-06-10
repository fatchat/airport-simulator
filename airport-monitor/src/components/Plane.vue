<template>
  <div class="plane-card">
    <h3>Plane {{ plane.plane_id }}</h3>
    <div class="details">
      <p><span class="label">Flight:</span> {{ plane.flight_id }}</p>
      <p>{{ plane.start_airport }} &rarr; {{ plane.end_airport }}</p>
      <p v-if="Number(plane.ticks_in_sky) > 0"><span class="label">Ticks in sky:</span> {{ plane.ticks_in_sky }}</p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    plane: {
      type: Object,
      required: true
    }
  }
};
</script>

<style scoped>
.plane-card {
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

.plane-card h3 {
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