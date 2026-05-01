<script setup>
import { computed } from 'vue';

const props = defineProps(['time']);

const progress = computed(() => {
  return (props.time / 60) * 100;
});

const isWarning = computed(() => props.time <= 30);
const isCritical = computed(() => props.time <= 10);
</script>

<template>
  <div class="timer-container glass-card" :class="{ 'warning': isWarning, 'critical': isCritical }">
    <div class="timer-icon">🕒</div>
    
    <div class="timer-content">
      <div class="timer-text">
        <span class="seconds">{{ time }}</span>
      </div>
      
      <div class="progress-bar-bg">
        <div 
          class="progress-bar-fill" 
          :style="{ width: `${progress}%` }"
        ></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timer-container {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding: 0.75rem 1.5rem;
  min-width: 180px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border-glass);
  transition: all 0.3s ease;
}

.timer-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.2));
}

.timer-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.timer-text {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.seconds {
  font-size: 1.75rem;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: var(--text-main);
}

.label {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-muted);
}

.progress-bar-bg {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 3px;
  transition: width 1s linear;
}

/* Warning States */
.warning .seconds {
  color: #fbbf24;
}

.warning .progress-bar-fill {
  background: #fbbf24;
}

.critical {
  border-color: rgba(239, 68, 68, 0.5);
  background: rgba(239, 68, 68, 0.1);
  animation: shake 0.5s infinite;
}

.critical .seconds {
  color: #ef4444;
}

.critical .progress-bar-fill {
  background: #ef4444;
}

@keyframes shake {
  0% { transform: translateX(0); }
  25% { transform: translateX(-2px); }
  75% { transform: translateX(2px); }
  100% { transform: translateX(0); }
}

@media (max-width: 768px) {
  .timer-container {
    min-width: 0;
    padding: 0.4rem 0.8rem;
    gap: 0.6rem;
    border-radius: 0.75rem;
  }
  
  .timer-icon {
    font-size: 1rem;
  }
  
  .seconds {
    font-size: 1.25rem;
  }
  
  .progress-bar-bg {
    height: 4px;
  }
  
  .timer-content {
    gap: 0.25rem;
  }
}
</style>
