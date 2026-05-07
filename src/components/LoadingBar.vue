<template>
  <div class="loading-container">
    <div class="loading-bar">
      <div 
        class="loading-fill" 
        :class="{ 'indeterminate': indeterminate }"
        :style="indeterminate ? {} : { width: `${progress}%` }"
      ></div>
    </div>
    <div class="loading-label" v-if="label">{{ label }}</div>
  </div>
</template>

<script setup>
defineProps({
  progress: { type: Number, default: 0 },
  indeterminate: { type: Boolean, default: false },
  label: { type: String, default: '' }
});
</script>

<style scoped>
.loading-container {
  width: 100%;
  max-width: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.loading-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
}

.loading-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f46e5, #06b6d4);
  box-shadow: 0 0 10px rgba(79, 70, 229, 0.5);
  transition: width 0.3s ease-out;
}

.loading-fill.indeterminate {
  width: 40%;
  position: absolute;
  animation: indeterminate-flow 1.5s infinite ease-in-out;
}

@keyframes indeterminate-flow {
  0% { left: -40%; }
  100% { left: 100%; }
}

.loading-label {
  font-size: 0.65rem;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.2em;
  text-transform: uppercase;
}
</style>
