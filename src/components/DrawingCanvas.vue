<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useGameStore } from '../stores/gameStore';

const props = defineProps({
  isDrawer: Boolean,
  onDraw: Function,
  clearCounter: Number
});

const canvasRef = ref(null);
const ctx = ref(null);
const isDrawing = ref(false);

// Local settings
const color = ref('#6366f1');
const brushSize = ref(8);
const selectedTool = ref('pen'); // 'pen' or 'eraser'
const lastEmit = ref(0);

// Use store to filter own drawings
const gameStore = useGameStore();

onMounted(() => {
  setupCanvas();
  // Listen for drawing data from other players
  window.addEventListener('remote-draw', handleRemoteDraw);
});

const setupCanvas = () => {
  const canvas = canvasRef.value;
  const dpr = window.devicePixelRatio || 1;
  
  // Set logical size
  canvas.width = 800 * dpr;
  canvas.height = 550 * dpr;
  
  ctx.value = canvas.getContext('2d');
  ctx.value.scale(dpr, dpr);
  
  ctx.value.lineCap = 'round';
  ctx.value.lineJoin = 'round';
};

onUnmounted(() => {
  window.removeEventListener('remote-draw', handleRemoteDraw);
});

const handleRemoteDraw = (event) => {
  const data = event.detail;
  
  // DEDUPLICATION: Don't draw your own remote messages back
  if (data.player_id === gameStore.gameState.playerId) return;

  const { x, y, color: rColor, size: rSize, type, tool: rTool } = data;
  
  // Set composition mode based on tool
  ctx.value.globalCompositeOperation = rTool === 'eraser' ? 'destination-out' : 'source-over';
  
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
  if (e.cancelable) e.preventDefault();
  startDrawing(e.touches[0]);
};

const handleTouchMove = (e) => {
  if (!props.isDrawer) return;
  if (e.cancelable) e.preventDefault();
  draw(e.touches[0]);
};

const handleTouchEnd = (e) => {
  if (!props.isDrawer) return;
  if (e.cancelable) e.preventDefault();
  stopDrawing();
};

// Watch for external clear requests (e.g. from server)
watch(() => props.clearCounter, () => {
  console.log('[DEBUG] [Canvas] Clearing per external request');
  clearCanvas();
});

const startDrawing = (e) => {
  if (!props.isDrawer) return;
  isDrawing.value = true;
  
  const rect = canvasRef.value.getBoundingClientRect();
  // Use logical units (800x550) for coordinate mapping to sync with ctx.scale(dpr, dpr)
  const scaleX = 800 / rect.width;
  const scaleY = 550 / rect.height;
  
  const x = (e.clientX - rect.left) * scaleX;
  const y = (e.clientY - rect.top) * scaleY;
  
  ctx.value.globalCompositeOperation = selectedTool.value === 'eraser' ? 'destination-out' : 'source-over';
  ctx.value.beginPath();
  ctx.value.moveTo(x, y);
  
  emitDraw('start', x, y);
};

const draw = (e) => {
  if (!isDrawing.value || !props.isDrawer) return;
  
  const rect = canvasRef.value.getBoundingClientRect();
  const scaleX = 800 / rect.width;
  const scaleY = 550 / rect.height;
  
  const x = (e.clientX - rect.left) * scaleX;
  const y = (e.clientY - rect.top) * scaleY;
  
  ctx.value.globalCompositeOperation = selectedTool.value === 'eraser' ? 'destination-out' : 'source-over';
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
      size: brushSize.value,
      tool: selectedTool.value
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
        <label class="hide-mobile">TOOL</label>
        <div class="tool-buttons">
          <button 
            @click="selectedTool = 'pen'" 
            :class="{ active: selectedTool === 'pen' }"
            class="tool-btn"
            title="Pen"
          >
            ✏️
          </button>
          <button 
            @click="selectedTool = 'eraser'" 
            :class="{ active: selectedTool === 'eraser' }"
            class="tool-btn"
            title="Eraser"
          >
            🧽
          </button>
        </div>
      </div>

      <div class="tool-group">
        <label class="hide-mobile">COLOR</label>
        <input v-model="color" type="color" class="color-picker" />
      </div>

      <div class="tool-group flex-1">
        <label class="hide-mobile">SIZE: {{ brushSize }}px</label>
        <div class="size-controls">
          <div class="quick-sizes">
            <button @click="brushSize = 4" :class="{ active: brushSize === 4 }" class="size-btn">S</button>
            <button @click="brushSize = 12" :class="{ active: brushSize === 12 }" class="size-btn">M</button>
            <button @click="brushSize = 24" :class="{ active: brushSize === 24 }" class="size-btn">L</button>
          </div>
          <input v-model="brushSize" type="range" min="1" max="50" class="brush-slider" />
        </div>
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
  /* Only disable touch-action if actively drawing to allow page scroll for guessers */
  touch-action: v-bind("isDrawer ? 'none' : 'pan-y'");
}

.drawing-cursor {
  cursor: crosshair;
}

.canvas-toolbar {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  padding: 0.75rem 1.25rem;
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid var(--border-glass);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none; /* Firefox */
}

.canvas-toolbar::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

@media (max-width: 1024px) {
  .canvas-toolbar {
    gap: 1rem;
    padding: 0.5rem 1rem;
  }
}

.tool-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex-shrink: 0;
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
  flex-shrink: 0;
}

.tool-buttons, .size-controls, .quick-sizes {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.tool-btn, .size-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-glass);
  color: white;
  width: 44px;
  height: 44px;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 1.25rem;
}

.tool-btn:hover, .size-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.tool-btn.active, .size-btn.active {
  background: var(--brand-teal);
  border-color: var(--brand-teal);
  box-shadow: 0 4px 15px var(--primary-glow);
  transform: scale(1.05);
}

.size-btn {
  width: 36px;
  height: 36px;
  font-size: 0.75rem;
  font-weight: 800;
  border-radius: 0.5rem;
}

.size-controls {
  flex: 1;
  width: 100%;
}

.color-picker::-webkit-color-swatch {
  border: none;
  border-radius: 0.25rem;
}

.brush-slider {
  width: 100px;
  cursor: pointer;
  accent-color: var(--brand-teal);
}

@media (max-width: 768px) {
  .brush-slider {
    width: 60px;
  }
  
  .hide-mobile {
    display: none;
  }
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
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.75rem;
    padding: 0.75rem 0.5rem;
    overflow-x: visible;
  }
  
  .tool-btn, .size-btn, .color-picker {
    width: 38px;
    height: 38px;
    border-radius: 0.5rem;
  }

  .btn-clear {
    padding: 0.5rem 0.75rem;
    font-size: 0.7rem;
    border-radius: 0.5rem;
    width: 100%; /* Make clear button full width on small screens to be prominent */
    max-width: 150px;
  }
  
  .quick-sizes {
    gap: 0.25rem;
  }

  .show-mobile { display: inline-block; }
}

.flex-1 { flex: 1; }
</style>
