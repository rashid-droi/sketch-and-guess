<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useGameStore } from '../stores/gameStore';

const props = defineProps(['isDrawer', 'onDraw']);

const canvasRef = ref(null);
const ctx = ref(null);
const isDrawing = ref(false);

// Local settings
const color = ref('#6366f1');
const brushSize = ref(5);
const lastEmit = ref(0);

// Use store to filter own drawings
const gameStore = useGameStore();

onMounted(() => {
  ctx.value = canvasRef.value.getContext('2d');
  ctx.value.lineCap = 'round';
  ctx.value.lineJoin = 'round';
  
  // Listen for drawing data from other players
  window.addEventListener('remote-draw', handleRemoteDraw);
});

onUnmounted(() => {
  window.removeEventListener('remote-draw', handleRemoteDraw);
});

const handleRemoteDraw = (event) => {
  const data = event.detail;
  
  // DEDUPLICATION: Don't draw your own remote messages back
  if (data.player_id === gameStore.gameState.playerId) return;

  const { x, y, color: rColor, size: rSize, type } = data;
  
  if (type === 'start') {
    ctx.value.beginPath();
    ctx.value.moveTo(x, y);
  } else if (type === 'move') {
    ctx.value.strokeStyle = rColor;
    ctx.value.lineWidth = rSize;
    ctx.value.lineTo(x, y);
    ctx.value.stroke();
  } else if (type === 'clear') {
    localClear();
  }
};

const handleTouchStart = (e) => {
  if (!props.isDrawer) return;
  e.preventDefault();
  startDrawing(e.touches[0]);
};

const handleTouchMove = (e) => {
  if (!props.isDrawer) return;
  e.preventDefault();
  draw(e.touches[0]);
};

const handleTouchEnd = (e) => {
  if (!props.isDrawer) return;
  e.preventDefault();
  stopDrawing();
};

const startDrawing = (e) => {
  if (!props.isDrawer) return;
  isDrawing.value = true;
  
  const rect = canvasRef.value.getBoundingClientRect();
  const scaleX = canvasRef.value.width / rect.width;
  const scaleY = canvasRef.value.height / rect.height;
  
  const x = (e.clientX - rect.left) * scaleX;
  const y = (e.clientY - rect.top) * scaleY;
  
  ctx.value.beginPath();
  ctx.value.moveTo(x, y);
  
  emitDraw('start', x, y);
};

const draw = (e) => {
  if (!isDrawing.value || !props.isDrawer) return;
  
  const rect = canvasRef.value.getBoundingClientRect();
  const scaleX = canvasRef.value.width / rect.width;
  const scaleY = canvasRef.value.height / rect.height;
  
  const x = (e.clientX - rect.left) * scaleX;
  const y = (e.clientY - rect.top) * scaleY;
  
  ctx.value.strokeStyle = color.value;
  ctx.value.lineWidth = brushSize.value;
  ctx.value.lineTo(x, y);
  ctx.value.stroke();
  
  // Throttle emits to every 30ms (~33fps) for performance scaling
  const now = Date.now();
  if (now - lastEmit.value > 30) {
    emitDraw('move', x, y);
    lastEmit.value = now;
  }
};

const stopDrawing = () => {
  isDrawing.value = false;
};

const emitDraw = (type, x, y) => {
  if (props.onDraw) {
    props.onDraw({
      type,
      x: Math.round(x),
      y: Math.round(y),
      color: color.value,
      size: brushSize.value
    });
  }
};

const clearCanvas = () => {
  localClear();
  if (props.isDrawer) {
    emitDraw('clear', 0, 0);
  }
};

const localClear = () => {
  ctx.value.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
};
</script>

<template>
  <div class="canvas-container glass-card">
    <!-- Overlay for when user is not the drawer -->
    <div v-if="!isDrawer" class="canvas-overlay">
      <span class="viewing-hint">👀 Observing the master at work...</span>
    </div>

    <!-- Toolbar: Visible only to the drawer -->
    <div v-if="isDrawer" class="canvas-toolbar">
      <div class="tool-group">
        <label class="hide-mobile">COLOR</label>
        <input v-model="color" type="color" class="color-picker" />
      </div>

      <div class="tool-group flex-1">
        <label class="hide-mobile">BRUSH SIZE: {{ brushSize }}px</label>
        <input v-model="brushSize" type="range" min="1" max="25" class="brush-slider" />
      </div>

      <button @click="clearCanvas" class="btn-clear">
        <span class="hide-mobile">CLEAR CANVAS</span>
        <span class="show-mobile">CLEAR</span>
      </button>
    </div>

    <!-- The Canvas itself -->
    <div class="canvas-viewport">
      <canvas
        ref="canvasRef"
        width="800"
        height="550"
        :class="{ 'drawing-cursor': isDrawer }"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @mouseleave="stopDrawing"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
        @touchcancel="handleTouchEnd"
      ></canvas>
    </div>
  </div>
</template>

<style scoped>
.canvas-container {
  display: flex;
  flex-direction: column;
  background: #111;
  overflow: hidden;
  position: relative;
  height: 100%;
}

.canvas-viewport {
  background: #1a1a1a;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  min-height: 0;
}

canvas {
  display: block;
  max-width: 100%;
  max-height: 100%;
  aspect-ratio: 800 / 550;
  background: #ffffff;
  border-radius: 0.5rem;
  box-shadow: 0 0 20px rgba(0,0,0,0.5);
  touch-action: none;
}

.drawing-cursor {
  cursor: crosshair;
}

.canvas-toolbar {
  display: flex;
  gap: 2rem;
  align-items: center;
  padding: 1rem 1.5rem;
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid var(--border-glass);
}

.tool-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.tool-group label {
  font-size: 0.65rem;
  font-weight: 800;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.color-picker {
  -webkit-appearance: none;
  width: 44px;
  height: 44px;
  padding: 0;
  border: 2px solid var(--border-glass);
  border-radius: 0.5rem;
  background: none;
  cursor: pointer;
  overflow: hidden;
}

.color-picker::-webkit-color-swatch {
  border: none;
  border-radius: 0.25rem;
}

.brush-slider {
  width: 100%;
  cursor: pointer;
}

.btn-clear {
  padding: 0.75rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 0.75rem;
  font-size: 0.75rem;
  font-weight: 800;
  transition: all 0.2s ease;
  cursor: pointer;
}

.btn-clear:hover {
  background: #ef4444;
  color: white;
  transform: translateY(-1px);
}

.canvas-overlay {
  position: absolute;
  top: 1rem;
  right: 1.5rem;
  z-index: 10;
}

.viewing-hint {
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent);
  border: 1px solid var(--border-glass);
}

.show-mobile { display: none; }

@media (max-width: 768px) {
  .canvas-toolbar {
    gap: 1rem;
    padding: 0.75rem 1rem;
  }
  
  .hide-mobile { display: none; }
  .show-mobile { display: inline; }
  
  .btn-clear {
    padding: 0.5rem 0.75rem;
    font-size: 0.65rem;
  }
  
  .color-picker {
    width: 32px;
    height: 32px;
  }
}

.flex-1 { flex: 1; }
</style>
