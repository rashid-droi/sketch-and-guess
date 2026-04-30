<script setup>
import { ref, computed, watch } from 'vue';
import Timer from './Timer.vue';
import PlayerList from './PlayerList.vue';
import DrawingCanvas from './DrawingCanvas.vue';
import ChatBox from './ChatBox.vue';

const props = defineProps(['gameState', 'onSend']);

const quickGuess = ref('');

const submitQuickGuess = () => {
  if (!quickGuess.value.trim()) return;
  props.onSend('chat', { message: quickGuess.value });
  
  // Instead of clearing to empty, reset to the first letter hint
  if (props.gameState.maskedWord && props.gameState.maskedWord.length > 0) {
    const firstLetter = props.gameState.maskedWord.charAt(0);
    quickGuess.value = (firstLetter !== '_' && firstLetter !== ' ') ? firstLetter : '';
  } else {
    quickGuess.value = '';
  }
};

const isLeader = computed(() => {
  return props.gameState.players.length > 0 && 
         props.gameState.players[0].player_id === props.gameState.playerId;
});

const triggerStart = () => {
  if (props.gameState.players.length < 2) {
    alert('At least 2 players are required to start!');
    return;
  }
  fetch(`http://localhost:8000/start-game/${props.gameState.roomId}`, { method: 'POST' });
};

// Auto-populate the first letter hint for guessers
watch(() => props.gameState.maskedWord, (newMask) => {
  if (!props.gameState.isDrawer && newMask && newMask.length > 0) {
    const firstLetter = newMask.charAt(0);
    // Only pre-fill if it's an actual letter (not an underscore)
    if (firstLetter !== '_' && firstLetter !== ' ') {
      quickGuess.value = firstLetter;
    }
  } else if (props.gameState.isDrawer) {
    quickGuess.value = ''; // Clear if drawer
  }
}, { immediate: true });
</script>

<template>
  <div class="game-dashboard">
    <!-- Top Navigation Bar -->
    <header class="glass-card game-header">
      <div class="header-left">
        <div class="room-pill">
          <span class="label">ROOM</span>
          <span class="value">{{ gameState.roomId }}</span>
        </div>
      </div>

      <div class="header-center">
        <div v-if="gameState.status === 'IN_PROGRESS'" class="round-status">
          <div class="word-hint">
            <span v-if="gameState.isDrawer" class="full-word">{{ gameState.currentWord }}</span>
            <input 
              v-else 
              v-model="quickGuess"
              @keyup.enter="submitQuickGuess"
              class="masked-word-input" 
              type="text" 
              :placeholder="gameState.maskedWord.split('').join(' ')" 
              autocomplete="off"
              title="Type your guess here!"
            />
            <div v-if="gameState.wordLength" class="word-length-indicator">
              {{ gameState.wordLength }} letters
            </div>
          </div>
        </div>
        <div v-else class="waiting-status">
          <span class="pulse-text">WAITING FOR PLAYERS...</span>
        </div>
      </div>

      <div class="header-right">
        <Timer :time="gameState.timer" />
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="game-layout">
      <!-- Drawing Canvas Section (Primary) -->
      <main class="canvas-chamber">
        <div v-if="gameState.status === 'IN_PROGRESS' && gameState.players.length < 2" class="error-overlay glass-card">
          <span class="error-text">⚠️ OPPONENT DISCONNECTED. WAITING FOR PLAYERS...</span>
        </div>
        <DrawingCanvas 
          v-else
          :isDrawer="gameState.isDrawer" 
          :onDraw="(data) => onSend('draw', data)" 
        />
      </main>

      <!-- Sidebars Row (Mobile Split) -->
      <div class="sidebars-row">
        <!-- Chat Section -->
        <aside class="sidebar-left">
          <ChatBox 
            :messages="gameState.messages" 
            :onSend="onSend" 
          />
        </aside>

        <!-- Players Section -->
        <aside class="sidebar-right">
          <PlayerList 
            :players="gameState.players" 
            :currentDrawerId="gameState.currentDrawer" 
          />
          <div v-if="isLeader && gameState.status === 'LOBBY'" class="lobby-actions">
            <button @click="triggerStart" class="btn-primary start-btn">
              START GAME
            </button>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mobile-nav { display: none; }

.game-dashboard {
  height: 100dvh;
  max-height: 100dvh;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  gap: 1rem;
  background: transparent; /* Inherit site-wide linear gradient */
  overflow: hidden; /* Lock the main page */
}

.game-header {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  align-items: center;
  padding: 1rem 1.5rem;
  z-index: 100;
}

.header-left { display: flex; align-items: center; }
.header-center { display: flex; justify-content: center; }
.header-right { display: flex; justify-content: flex-end; }

.room-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-glass);
  border-radius: 2rem;
  font-size: clamp(0.7rem, 1.5vw, 0.9rem);
  font-weight: 700;
  color: var(--text-muted);
}

.room-id {
  color: var(--accent);
  letter-spacing: 0.05em;
  font-family: monospace;
}

.word-hint-chamber {
  flex: 1;
  display: flex;
  justify-content: center;
}

.word-hint {
  font-size: clamp(1.2rem, 3.5vw, 2.2rem);
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.word-length-indicator {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.1em;
  margin-top: 0.5rem;
  opacity: 0.8;
}

.full-word { color: var(--accent); text-shadow: 0 0 20px rgba(0, 150, 143, 0.5); }

.masked-word-input {
  background: transparent;
  border: none;
  border-bottom: 2px dashed rgba(255, 255, 255, 0.2);
  color: var(--text-main);
  font-family: inherit;
  font-size: inherit;
  font-weight: inherit;
  letter-spacing: inherit;
  text-transform: uppercase;
  text-align: center;
  width: 100%;
  max-width: 300px;
  outline: none;
  transition: all 0.3s ease;
  cursor: text;
}

.masked-word-input::placeholder {
  color: var(--text-main);
  opacity: 0.8;
}

.masked-word-input:focus {
  border-bottom: 2px dashed var(--primary);
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem 0.5rem 0 0;
}

.pulse-text {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.1em;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.game-layout {
  display: grid;
  grid-template-columns: 280px 1fr 340px;
  gap: 1rem;
  flex: 1;
  min-height: 0; /* Critical for internal scrolling */
  overflow: hidden;
}

.canvas-chamber {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: auto;
}

.sidebar-left, .sidebar-right {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.sidebar-left :deep(.chat-wrapper),
.sidebar-left :deep(.chat-container),
.sidebar-right :deep(.player-list-container) {
  flex: 1;
  min-height: 0;
  max-height: 100% !important;
  width: 100%;
}

.sidebar-left {
  order: -1;
}

.lobby-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 1rem;
}

.start-btn {
  padding: 1.25rem;
  font-size: 1rem;
  letter-spacing: 0.1em;
  box-shadow: 0 10px 25px -5px var(--primary-glow);
}

.error-overlay {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.05);
  border: 2px dashed rgba(239, 68, 68, 0.3);
}

.error-text {
  font-size: 1.25rem;
  font-weight: 800;
  color: #ef4444;
  letter-spacing: 0.1em;
  text-align: center;
}

/* Unified Responsive Stacking Grid */
.game-layout {
  display: grid;
  grid-template-columns: 340px 1fr 280px;
  gap: var(--fluid-padding);
  flex: 1;
  min-height: 0;
  height: 100%;
}

/* MacBook / Large Screen Refinements */
@media (max-width: 1440px) {
  .game-layout {
    grid-template-columns: 300px 1fr 240px;
    gap: 1rem;
  }
}

/* Laptop / iPad Pro Landscape */
@media (max-width: 1200px) {
  .game-layout {
    grid-template-columns: 280px 1fr 220px;
  }
}

.sidebars-row {
  display: contents; /* Default to grid placement on desktop */
}

/* iPad / Tablet Portrait */
@media (max-width: 1024px) {
  .game-layout {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 280px;
  }
  
  .canvas-chamber {
    min-height: 0;
  }
  
  .sidebars-row {
    display: flex;
    gap: 1rem;
    min-height: 0;
  }
  
  .sidebar-left, .sidebar-right {
    flex: 1;
    height: 100%;
    min-height: 0;
  }
}

/* Small Tablet / Large Mobile */
@media (max-width: 768px) {
  .game-dashboard {
    padding: max(0.25rem, env(safe-area-inset-top)) max(0.25rem, env(safe-area-inset-right)) max(0.25rem, env(safe-area-inset-bottom)) max(0.25rem, env(safe-area-inset-left));
    height: 100dvh;
    max-height: 100dvh;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    display: block; /* Remove flex to prevent shrinking bugs */
  }

  .game-header {
    border-radius: 1rem;
    margin-bottom: 0.25rem;
    padding: 0.75rem;
  }

  .game-layout {
    display: block; /* Standard block stacking prevents squishing */
    height: auto;
  }

  .canvas-chamber {
    height: 50dvh; /* SIGNIFICANTLY EXPANDED */
    min-height: 400px;
    width: 100%;
    margin-bottom: 0.5rem;
  }

  .sidebars-row {
    order: 2;
    display: flex;
    flex-direction: row;
    gap: 0.25rem;
    height: 450px;
    width: 100%;
  }

  .sidebar-left, .sidebar-right {
    width: 50%;
    height: 100%;
    padding: 0;
  }
  
  .lobby-actions {
    order: 3;
    padding: 0.5rem 0;
  }
}

/* Phone / Small Mobile */
@media (max-width: 480px) {
  .canvas-chamber {
    height: 55dvh; /* EVEN LARGER ON PHONES */
    min-height: 350px;
  }
  
  .sidebars-row {
    display: block;
    height: auto;
  }

  .sidebar-left, .sidebar-right {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 40dvh !important;
    min-height: 250px;
    margin-bottom: 1rem;
  }
}
</style>
