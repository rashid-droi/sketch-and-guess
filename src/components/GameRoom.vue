<script setup>
import { ref, computed, watch } from 'vue';
import Timer from './Timer.vue';
import PlayerList from './PlayerList.vue';
import DrawingCanvas from './DrawingCanvas.vue';
import ChatBox from './ChatBox.vue';
import LoadingBar from './LoadingBar.vue';

const props = defineProps(['gameState', 'onSend']);

const quickGuess = ref('');

const submitQuickGuess = () => {
  if (!quickGuess.value.trim()) return;
  props.onSend('chat', { message: quickGuess.value });
  
  // Reset to first letter hint and re-focus
  if (props.gameState.maskedWord && props.gameState.maskedWord.length > 0) {
    const firstLetter = props.gameState.maskedWord.charAt(0);
    quickGuess.value = (firstLetter !== '_' && firstLetter !== ' ') ? firstLetter : '';
  } else {
    quickGuess.value = '';
  }
  
  focusInput(); // Re-focus and set cursor at end
};

const isLeader = computed(() => {
  return props.gameState.hostId === props.gameState.playerId;
});

const isStarting = ref(false);
const isQuitting = ref(false);

const triggerStart = async () => {
  const rid = props.gameState.roomId?.toUpperCase();
  console.log(`[DEBUG] [START_CLICKED] Attempting to start game for Room: ${rid}`);
  
  if (!rid) {
    console.error('[DEBUG] [ERROR] No Room ID found in gameState!');
    return;
  }

  if (props.gameState.players.length < 2) {
    alert('At least 2 players are required to start!');
    return;
  }
  
  isStarting.value = true;
  try {
    const apiHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    const url = `http://${apiHost}/start-game/${rid}`;
    console.log(`[DEBUG] [FETCH] Calling: ${url}`);
    
    const resp = await fetch(url, { method: 'POST' });
    if (resp.ok) {
      console.log('[DEBUG] [SUCCESS] Start Game API call succeeded');
    } else {
      console.error(`[DEBUG] [ERROR] API returned status: ${resp.status}`);
    }
  } catch (err) {
    console.error('[DEBUG] [FETCH_ERROR] Failed to start game:', err);
  } finally {
    isStarting.value = false;
  }
};

const triggerQuit = async () => {
  console.log('[DEBUG] [QUIT_BUTTON_CLICKED] Starting triggerQuit function...');
  const rid = props.gameState.roomId?.toUpperCase();
  const leaderStatus = isLeader.value;
  console.log(`[DEBUG] [QUIT_ATTEMPT] RoomID: ${rid}, IsLeader: ${leaderStatus}`);
  
  if (!rid) {
    console.error('[DEBUG] [QUIT_ERROR] Room ID is missing from state');
    return;
  }
  
  // Removed confirm dialog as it was not showing for user
  isQuitting.value = true;
  try {
    const apiHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    const url = `http://${apiHost}/quit-game/${rid}`;
    console.log(`[DEBUG] [QUIT_FETCH] POSTing to: ${url}`);
    
    const resp = await fetch(url, { method: 'POST' });
    console.log(`[DEBUG] [QUIT_RESPONSE] Status: ${resp.status} ${resp.statusText}`);
    
    if (!resp.ok) {
      const errorDetail = await resp.text();
      console.error(`[DEBUG] [QUIT_SERVER_ERROR] ${errorDetail}`);
      alert(`Failed to quit: ${resp.statusText}`);
    }
  } catch (err) {
    console.error('[DEBUG] [QUIT_NETWORK_ERROR]', err);
    alert('Network error: Could not reach the server to quit the game.');
  } finally {
    isQuitting.value = false;
  }
};const triggerPause = async () => {
  const rid = props.gameState.roomId?.toUpperCase();
  if (!rid) return;
  try {
    const apiHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    await fetch(`http://${apiHost}/pause-game/${rid}`, { method: 'POST' });
  } catch (err) { console.error('[DEBUG] [PAUSE_ERROR]', err); }
};

const triggerResume = async () => {
  const rid = props.gameState.roomId?.toUpperCase();
  if (!rid) return;
  try {
    const apiHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    await fetch(`http://${apiHost}/resume-game/${rid}`, { method: 'POST' });
  } catch (err) { console.error('[DEBUG] [RESUME_ERROR]', err); }
};

const triggerReset = async () => {
  const rid = props.gameState.roomId?.toUpperCase();
  if (!rid) return;
  try {
    const apiHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    await fetch(`http://${apiHost}/reset-game/${rid}`, { method: 'POST' });
  } catch (err) { console.error('[DEBUG] [RESET_ERROR]', err); }
};

const guessInput = ref(null);
const guessInputMobile = ref(null);
const rotationHintDismissed = ref(false);

const focusInput = () => {
  const input = window.innerWidth <= 1024 ? guessInputMobile.value : guessInput.value;
  if (input && (props.gameState.status === 'IN_PROGRESS' || props.gameState.status === 'DRAWING') && !props.gameState.isDrawer) {
    setTimeout(() => {
      input.focus();
      if (input.setSelectionRange) {
        const len = input.value.length;
        input.setSelectionRange(len, len);
      }
    }, 200);
  }
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

// Auto-focus logic for guessers
watch(
  [() => props.gameState.status, () => props.gameState.isDrawer],
  ([status, isDrawer]) => {
    if (status === 'IN_PROGRESS' && !isDrawer) {
      focusInput();
    }
  }
);
</script>

<template>
  <div class="game-dashboard">
    <!-- Orientation Hint (Mobile Only) -->
    <div v-if="gameState.status !== 'LOBBY' && !rotationHintDismissed" class="orientation-hint">
      <div class="hint-content">
        <div class="rotate-icon">🔄</div>
        <h3>ROTATE FOR BETTER EXPERIENCE</h3>
        <p>Landscape mode provides a much larger drawing canvas!</p>
        <button @click="rotationHintDismissed = true" class="btn-primary hint-dismiss-btn">OK, GOT IT</button>
      </div>
    </div>

    <!-- Top Navigation Bar -->
    <header class="glass-card game-header">
      <div class="header-left">
        <div class="room-pill">
          <span class="label">ROOM</span>
          <span class="value">{{ gameState.roomId }}</span>
        </div>
      </div>

      <div class="header-center">
        <div v-if="gameState.status === 'DRAWING' || gameState.status === 'ROUND_END'" class="round-status">
          <div class="word-hint">
            <span v-if="gameState.isDrawer || gameState.status === 'ROUND_END'" class="full-word">{{ gameState.currentWord }}</span>
            <div v-else class="guess-input-wrapper hide-mobile-tablet">
              <template v-if="!gameState.hasGuessedCorrectly">
                <div class="input-glow-bar header-input">
                  <input 
                    ref="guessInput"
                    v-model="quickGuess"
                    @keyup.enter="submitQuickGuess"
                    class="masked-word-input" 
                    type="text" 
                    :placeholder="gameState.maskedWord.split('').join(' ')" 
                    autocomplete="off"
                    spellcheck="false"
                  />
                  <button @click="submitQuickGuess" class="header-send-btn">
                    <span class="btn-text">SEND</span>
                    <span class="btn-icon">➜</span>
                  </button>
                </div>
              </template>
              <div v-else class="correct-guess-badge">
                <span class="check">✓</span> YOUR GUESS IS CORRECT!
              </div>
            </div>
            <div v-if="gameState.wordLength && gameState.status === 'DRAWING'" class="word-length-indicator">
              {{ gameState.wordLength }} letters
            </div>
          </div>
        </div>
        <div v-else-if="gameState.status === 'CHOOSING'" class="waiting-status">
          <span class="pulse-text">SELECTING WORD...</span>
        </div>
        <div v-else-if="gameState.status === 'GAME_OVER'" class="waiting-status">
          <span class="pulse-text">GAME OVER</span>
        </div>
        <div v-if="gameState.status === 'LOBBY'" class="lobby-status">
          <LoadingBar indeterminate label="WAITING FOR PLAYERS" />
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
        <!-- Status Overlays -->

        <div v-if="gameState.status === 'ROUND_END'" class="overlay round-end-overlay glass-card">
          <div class="overlay-content">
            <span class="label">THE WORD WAS</span>
            <h2 class="revealed-word">{{ gameState.currentWord }}</h2>
            <LoadingBar 
              :progress="(5 - (gameState.timer || 0)) / 5 * 100" 
              label="Next round starting soon" 
            />
          </div>
        </div>

        <div v-if="gameState.status === 'GAME_OVER'" class="overlay game-over-overlay glass-card">
          <div class="overlay-content full-width">
            <h1 class="game-over-title">🏆 SESSION COMPLETE</h1>
            
            <!-- MVP Section -->
            <div v-if="gameState.mvps" class="mvp-badges">
              <div class="mvp-badge">
                <span class="badge-icon">⚡</span>
                <span class="badge-label">FASTEST GUESSER</span>
                <span class="badge-value">{{ gameState.mvps.guesser }}</span>
              </div>
              <div class="mvp-badge drawer-badge">
                <span class="badge-icon">🎨</span>
                <span class="badge-label">BEST DRAWER</span>
                <span class="badge-value">{{ gameState.mvps.drawer }}</span>
              </div>
              <div class="mvp-badge streak-badge">
                <span class="badge-icon">🔥</span>
                <span class="badge-label">LONGEST STREAK</span>
                <span class="badge-value">{{ gameState.mvps.streak }}</span>
              </div>
            </div>

            <!-- Detailed Leaderboard -->
            <div class="final-leaderboard-container">
              <div v-for="(player, idx) in gameState.players" :key="player.player_id" class="final-player-row">
                <div class="rank">#{{ idx + 1 }}</div>
                <div class="name">{{ player.player_name }}</div>
                <div class="stats-group">
                  <div class="stat-item">
                    <span class="s-label">GUESSES</span>
                    <span class="s-value">{{ player.total_correct_guesses }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="s-label">STREAK</span>
                    <span class="s-value">{{ player.best_streak }}</span>
                  </div>
                </div>
                <div class="total-score">{{ player.score }} <span class="pts">pts</span></div>
              </div>
            </div>

            <div v-if="isLeader" class="restart-controls">
              <button 
                @click="triggerReset" 
                class="btn-primary play-again-btn"
                :disabled="isStarting"
              >
                {{ isStarting ? 'RESTARTING...' : 'PLAY AGAIN' }}
              </button>
            </div>
          </div>
        </div>        <div v-if="gameState.status === 'PAUSED'" class="overlay pause-overlay glass-card">
          <div class="overlay-content">
            <div class="pause-icon">⏸</div>
            <h1 class="pause-title">GAME PAUSED</h1>
            <p class="pause-subtitle">WAITING FOR HOST TO RESUME</p>
            <div v-if="isLeader" class="restart-controls">
              <button @click="triggerResume" class="btn-primary resume-btn">
                RESUME GAME
              </button>
            </div>
          </div>
        </div>

        <div v-if="gameState.status === 'DRAWING' && gameState.players.length < 2" class="error-overlay glass-card">
          <span class="error-text">⚠️ OPPONENT DISCONNECTED. WAITING FOR PLAYERS...</span>
        </div>
        
        <DrawingCanvas 
          v-else
          :isDrawer="gameState.isDrawer" 
          :clearCounter="gameState.clearCounter"
          :onDraw="(data) => onSend('draw', data)" 
        />

        <!-- Tablet & Mobile Guess Input Deck -->
        <div 
          v-if="gameState.status === 'DRAWING' && !gameState.isDrawer" 
          class="tablet-guess-deck"
        >
          <div class="guess-input-container">
            <template v-if="!gameState.hasGuessedCorrectly">
              <div class="input-glow-wrapper">
                <input 
                  ref="guessInputMobile"
                  v-model="quickGuess"
                  @keyup.enter="submitQuickGuess"
                  class="tablet-input-field" 
                  type="text" 
                  placeholder="Type your guess..."
                  autocomplete="off"
                  spellcheck="false"
                />
                <button 
                  @click="submitQuickGuess" 
                  class="tablet-send-btn"
                  aria-label="Send Guess"
                >
                  <span class="btn-text">SEND</span>
                  <span class="btn-icon">➜</span>
                </button>
              </div>
            </template>
            <div v-else class="correct-guess-badge mobile">
              <span class="check">✓</span> YOUR GUESS IS CORRECT!
            </div>
          </div>
        </div>
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
            :myPlayerId="playerId"
          />
        </aside>
      </div>

      <!-- Host Actions (Integrated Position) -->
      <div v-if="isLeader" class="host-action-footer">
        <template v-if="gameState.status !== 'GAME_OVER'">
          <!-- Lobby Action -->
          <button 
            v-if="gameState.status === 'LOBBY'"
            @click="triggerStart" 
            class="btn-primary start-btn-footer"
            :disabled="isStarting"
          >
            {{ isStarting ? 'STARTING...' : 'START GAME' }}
          </button>

          <!-- Active Session Actions -->
          <button 
            v-if="gameState.status === 'DRAWING'"
            @click="triggerPause" 
            class="btn-warning pause-btn-footer"
          >
            PAUSE GAME
          </button>
          
          <button 
            v-if="gameState.status === 'PAUSED'"
            @click="triggerResume" 
            class="btn-primary resume-btn-footer"
          >
            RESUME GAME
          </button>

          <button 
            v-if="gameState.status !== 'LOBBY'"
            @click="triggerQuit" 
            class="btn-danger quit-btn-footer"
            :disabled="isQuitting"
          >
            {{ isQuitting ? 'QUITTING...' : 'QUIT GAME' }}
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mobile-nav { display: none; }

.game-dashboard {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  padding: clamp(0.5rem, 2vw, 1.5rem);
  gap: clamp(0.5rem, 2vh, 1.5rem);
  background: transparent;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
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
  display: inline-block;
  background: linear-gradient(135deg, #f59e0b, #ea580c);
  color: white;
  padding: 0.2rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  margin-top: 0.5rem;
  text-transform: uppercase;
  box-shadow: 0 4px 10px rgba(234, 88, 12, 0.3);
  animation: badgeIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
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

@media (max-width: 768px) {
  .masked-word-input {
    max-width: 180px;
  }
}

.guess-input-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  max-width: 350px;
  position: relative;
}

.guess-send-btn {
  background: linear-gradient(135deg, var(--brand-teal), #0d9488);
  color: white;
  border: none;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  box-shadow: 0 4px 15px rgba(0, 150, 143, 0.4);
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.guess-send-btn:hover:not(:disabled) {
  transform: scale(1.1) rotate(-5deg);
  filter: brightness(1.1);
}

.guess-send-btn:active:not(:disabled) {
  transform: scale(0.9);
}

.guess-send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  filter: grayscale(1);
  box-shadow: none;
}

.send-icon {
  font-size: 1.2rem;
  margin-left: 2px;
  margin-bottom: 2px;
}

@media (max-width: 1024px) {
  .guess-input-wrapper {
    max-width: 100%;
    justify-content: center;
    gap: 0.5rem;
  }
  
  .guess-send-btn {
    width: 40px;
    height: 40px;
  }
  
  .send-icon {
    font-size: 1rem;
  }
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
  grid-template-columns: minmax(260px, 1fr) 3fr minmax(300px, 1.2fr);
  gap: clamp(0.75rem, 2vw, 1.5rem);
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
}

.canvas-chamber {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  width: 100%;
  position: relative;
  gap: 0.75rem;
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

.error-overlay, .overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
  backdrop-filter: blur(4px);
  background: rgba(0, 0, 0, 0.7);
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.round-end-overlay {
  background: rgba(15, 23, 42, 0.8);
  border: 2px solid var(--primary);
}

.game-over-overlay {
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(35px);
  border: 1px solid var(--accent);
  padding: 2rem 0;
  align-items: flex-start; /* Ensure start from top for scrolling */
}

.game-over-title {
  font-size: clamp(2rem, 8vw, 3.5rem);
  font-weight: 900;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, var(--accent), #f59e0b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 20px rgba(255, 205, 0, 0.3));
}

.overlay-content {
  text-align: center;
  animation: zoomIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  margin: auto; /* Help centering when content is smaller than container */
}

@keyframes zoomIn {
  from { transform: scale(0.8); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.overlay-content.full-width {
  width: 95%;
  max-width: 800px;
  padding: 1rem;
}

.mvp-badges {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}

.restart-controls {
  margin-top: 3rem;
  display: flex;
  justify-content: center;
}

.play-again-btn {
  padding: 1.25rem 5rem;
  font-size: 1.5rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  border-radius: 1.5rem;
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 0 40px rgba(16, 185, 129, 0.4);
  animation: pulse 2s infinite;
  transition: all 0.3s ease;
  cursor: pointer;
}

.play-again-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 0 60px rgba(16, 185, 129, 0.6);
}

.mvp-badge {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-glass);
  padding: 1.25rem;
  border-radius: 1.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  min-width: 160px;
  flex: 1;
  max-width: 240px;
  animation: bounceIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.mvp-badge.drawer-badge { border-color: var(--accent); }
.mvp-badge.streak-badge { border-color: #f87171; }

.badge-icon { font-size: 2rem; }
.badge-label { font-size: 0.6rem; font-weight: 800; color: var(--text-muted); letter-spacing: 0.1em; }
.badge-value { font-size: 1.1rem; font-weight: 700; color: white; }

.final-leaderboard-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 40vh;
  overflow-y: auto;
  padding-right: 1rem;
}

.final-player-row {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  padding: 1rem 1.5rem;
  border-radius: 1rem;
  gap: 1.5rem;
}

.final-player-row .rank { font-size: 1.2rem; font-weight: 800; color: var(--accent); width: 40px; }
.final-player-row .name { flex: 1; text-align: left; font-weight: 700; font-size: 1.1rem; }

.stats-group { display: flex; gap: 2rem; }
.stat-item { display: flex; flex-direction: column; align-items: flex-start; }
.s-label { font-size: 0.5rem; font-weight: 800; color: var(--text-muted); }
.s-value { font-size: 1rem; font-weight: 700; color: white; }

.total-score { font-size: 1.4rem; font-weight: 800; color: var(--primary); }
.pts { font-size: 0.7rem; color: var(--text-muted); }

@keyframes bounceIn {
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.selection-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #111 !important;
  margin-bottom: 2rem;
  letter-spacing: 0.05em;
}

.word-options {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  margin-bottom: 2rem;
}

.word-choice-btn {
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-glass);
  border-radius: 1rem;
  color: #000;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s ease;
}

.word-choice-btn:hover {
  background: var(--primary);
  transform: translateY(-5px);
  box-shadow: 0 10px 20px var(--primary-glow);
}

.selection-timer {
  font-size: 0.9rem;
  color: #000;
  font-weight: 700;
}

.choosing-overlay .status-text {
  color: #000 !important;
  font-weight: 900;
}

.revealed-word {
  font-size: 3.5rem;
  font-weight: 900;
  color: #111;
  margin: 0.5rem 0 1.5rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.sidebar-footer {
  margin-top: auto; /* Push to bottom */
  padding: 1rem;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid var(--border-glass);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.host-badge {
  font-size: 0.65rem;
  font-weight: 900;
  color: var(--accent);
  letter-spacing: 0.2em;
  text-align: center;
  text-shadow: 0 0 10px var(--accent);
}

.start-btn-sidebar {
  width: 100%;
  padding: 0.8rem;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  box-shadow: 0 4px 15px var(--primary-glow);
  animation: pulse 2s infinite;
}

.hero-actions {
  margin-top: 1rem;
}

.start-btn-hero {
  padding: 1rem 4rem;
  font-size: 1.5rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  background: var(--primary);
  border-radius: 1.5rem;
  box-shadow: 0 0 50px var(--primary-glow);
  animation: heroPulse 2s infinite;
  transition: all 0.3s ease;
}

.start-btn-hero:hover {
  transform: scale(1.1);
  box-shadow: 0 0 70px var(--primary-glow);
}

.btn-danger {
  background: linear-gradient(135deg, #ef4444, #b91c1c);
  color: white !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.quit-btn-sidebar {
  width: 100%;
  padding: 0.8rem;
  font-size: 0.9rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
}

.quit-btn-sidebar:hover {
  background: linear-gradient(135deg, #f87171, #dc2626);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
  transform: translateY(-2px);
}

@keyframes heroPulse {
  0% { transform: scale(1); box-shadow: 0 0 30px var(--primary-glow); }
  50% { transform: scale(1.05); box-shadow: 0 0 60px var(--primary-glow); }
  100% { transform: scale(1); box-shadow: 0 0 30px var(--primary-glow); }
}

.mobile-guess-chamber {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-top: 1px solid var(--border-glass);
}

.guess-input-container {
  display: flex;
  gap: 0.5rem;
}

.mobile-input-field {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-glass);
  border-radius: 0.75rem;
  padding: 0.8rem 1rem;
  color: white;
  font-size: 1rem;
}

.mobile-send-btn {
  background: var(--brand-teal);
  color: white;
  border: none;
  padding: 0 1.5rem;
  border-radius: 0.75rem;
  font-weight: 800;
  cursor: pointer;
}

.mobile-hint-text {
  text-align: center;
  font-size: 0.7rem;
  color: var(--accent);
  margin-top: 0.5rem;
  font-weight: 800;
  letter-spacing: 0.2em;
}

.show-mobile-tablet { display: none; }

@media (max-width: 1024px) {
  .show-mobile-tablet { display: block; }
  .hide-mobile-tablet { display: none; }
}

.lobby-hero-actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
}

.start-btn-hero {
  padding: 1.2rem 4rem;
  font-size: 1.5rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  border-radius: 1rem;
  box-shadow: 0 0 40px var(--primary-glow);
  animation: heroPulse 2s infinite;
  transition: all 0.3s ease;
}

@keyframes heroPulse {
  0% { transform: scale(1); box-shadow: 0 0 20px var(--primary-glow); }
  50% { transform: scale(1.05); box-shadow: 0 0 50px var(--primary-glow); }
  100% { transform: scale(1); box-shadow: 0 0 20px var(--primary-glow); }
}

.lobby-footer-actions {
  padding: 1.5rem;
  display: flex;
  justify-content: center;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid var(--border-glass);
}

.start-btn-under-canvas {
  padding: 1rem 5rem;
  font-size: 1.5rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  border-radius: 1rem;
  background: var(--primary);
  box-shadow: 0 0 50px var(--primary-glow);
  animation: canvasPulse 2s infinite;
  transition: all 0.3s ease;
}

@keyframes canvasPulse {
  0% { transform: scale(1); box-shadow: 0 0 30px var(--primary-glow); }
  50% { transform: scale(1.05); box-shadow: 0 0 70px var(--primary-glow); }
  100% { transform: scale(1); box-shadow: 0 0 30px var(--primary-glow); }
}

.quit-btn-under-canvas {
  padding: 1rem 5rem;
  font-size: 1.5rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  border-radius: 1rem;
  background: linear-gradient(135deg, #ef4444, #b91c1c);
  box-shadow: 0 0 50px rgba(239, 68, 68, 0.4);
  animation: dangerPulse 2s infinite;
  transition: all 0.3s ease;
  cursor: pointer;
}

@keyframes dangerPulse {
  0% { transform: scale(1); box-shadow: 0 0 30px rgba(239, 68, 68, 0.3); }
  50% { transform: scale(1.05); box-shadow: 0 0 70px rgba(239, 68, 68, 0.5); }
  100% { transform: scale(1); box-shadow: 0 0 30px rgba(239, 68, 68, 0.3); }
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
  grid-template-columns: 340px 1fr 300px;
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
    grid-template-rows: auto auto;
    gap: 1rem;
  }
  
  .canvas-chamber {
    min-height: clamp(400px, 60dvh, 800px);
    height: auto;
  }
  
  .sidebars-row {
    display: flex;
    gap: 1rem;
    height: 320px;
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
    padding: max(0.5rem, env(safe-area-inset-top)) max(0.5rem, env(safe-area-inset-right)) max(0.5rem, env(safe-area-inset-bottom)) max(0.5rem, env(safe-area-inset-left));
    min-height: 100dvh;
    height: auto;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .game-header {
    grid-template-columns: auto 1fr auto;
    padding: 0.75rem;
    gap: 0.5rem;
    border-radius: 0.75rem;
  }

  .game-layout {
    display: flex;
    flex-direction: column;
    height: auto;
    gap: 0.75rem;
  }

  .canvas-chamber {
    height: auto;
    min-height: clamp(450px, 75dvh, 900px);
    width: 100%;
    margin: 0;
  }

  .sidebars-row {
    order: 2;
    display: flex;
    flex-direction: row;
    gap: 0.75rem;
    height: auto;
    min-height: 320px;
  }

  .sidebar-left, .sidebar-right {
    flex: 1;
    min-width: 0;
    height: 320px;
  }
}

/* Phone / Small Mobile */
@media (max-width: 480px) {
  .canvas-chamber {
    min-height: clamp(400px, 65dvh, 600px);
  }
  
  .sidebars-row {
    flex-direction: column;
    gap: 0.75rem;
  }

  .sidebar-left, .sidebar-right {
    height: auto;
    min-height: 280px;
    max-height: 40dvh;
  }
}
.show-mobile-tablet { display: none; }
.hide-mobile-tablet { display: flex; }

@media (max-width: 1024px) {
  .show-mobile-tablet { display: flex; }
  .hide-mobile-tablet { display: none !important; }
}

.mobile-guess-chamber {
  width: 100%;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(12px);
  padding: 1rem;
  border-top: 1px solid var(--border-glass);
  margin-top: auto;
  justify-content: center;
  align-items: center;
  z-index: 50;
}

.mobile-guess-chamber .guess-input-wrapper {
  max-width: 100%;
  gap: 1rem;
}

.mobile-guess-chamber .masked-word-input {
  max-width: 100%;
  font-size: 1.5rem;
  border-bottom: 2px solid var(--primary);
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.mobile-guess-chamber .guess-send-btn {
  width: 54px;
  height: 54px;
}
.correct-guess-badge {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid #10b981;
  color: #10b981;
  padding: 0.5rem 1.5rem;
  border-radius: 2rem;
  font-weight: 800;
  font-size: 0.9rem;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  animation: successSlide 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
}

.correct-guess-badge .check {
  background: #10b981;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
}

.correct-guess-badge.mobile {
  width: 100%;
  justify-content: center;
  padding: 1rem;
  font-size: 1rem;
}

@keyframes successSlide {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.btn-warning {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white !important;
  box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
}

.btn-warning:hover {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
}

.pause-overlay {
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(35px);
}

.pause-icon {
  font-size: 5rem;
  margin-bottom: 1rem;
  animation: float 3s ease-in-out infinite;
}

.pause-title {
  font-size: 3rem;
  font-weight: 900;
  letter-spacing: 0.2em;
  color: #f59e0b;
  text-shadow: 0 0 30px rgba(245, 158, 11, 0.4);
}

.pause-subtitle {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.1em;
  margin-bottom: 2rem;
}

.pause-btn-under-canvas, .resume-btn-under-canvas {
  padding: 1rem 3rem;
  font-size: 1.2rem;
  font-weight: 900;
  border-radius: 1rem;
  transition: all 0.3s ease;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.lobby-footer-actions {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  padding: 1.5rem;
}
.host-action-footer {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: auto;
  z-index: 1000;
  grid-column: 1 / -1; /* Centering fix for desktop/tablet grid */
}

.start-btn-footer, .pause-btn-footer, .resume-btn-footer, .quit-btn-footer {
  padding: 0.75rem 2rem;
  font-size: 1.1rem;
  font-weight: 800;
  border-radius: 0.75rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  min-width: 180px;
}

.quit-btn-footer {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
}

.quit-btn-footer:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(239, 68, 68, 0.5);
}

@media (max-width: 768px) {
  .host-action-footer {
    flex-direction: column;
    gap: 0.75rem;
    padding: 1.5rem;
    background: rgba(15, 23, 42, 0.95);
  }
  
  .start-btn-footer, .pause-btn-footer, .resume-btn-footer, .quit-btn-footer {
    width: 100%;
    min-width: unset;
    padding: 1rem;
  }
}
.tablet-guess-deck {
  display: none;
  position: sticky;
  bottom: 0;
  left: 0;
  width: 100%;
  padding: clamp(0.5rem, 2vw, 1.25rem);
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(30px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 500;
  box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.4);
}

@media (max-width: 1024px) {
  .tablet-guess-deck {
    display: block;
  }
}

.guess-input-container {
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  justify-content: center;
}

.input-glow-wrapper {
  display: flex;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1.5rem;
  padding: 0.35rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  width: 100%;
  min-height: 54px;
}

.input-glow-wrapper:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 30px rgba(16, 185, 129, 0.2);
  background: rgba(255, 255, 255, 0.08);
}

.tablet-input-field {
  flex: 1;
  background: transparent;
  border: none;
  color: white;
  padding: 0.75rem 1rem;
  font-size: 1.1rem;
  font-weight: 600;
  outline: none;
}

.input-glow-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 0.25rem 0.5rem;
  transition: all 0.3s ease;
}

.input-glow-bar:focus-within {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--primary-glow);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.1);
}

.header-send-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  border-radius: 0.75rem;
  padding: 0.5rem 1rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.9rem;
}

.header-send-btn:active {
  transform: scale(0.95);
  filter: brightness(0.9);
}

.tablet-send-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  border-radius: 1rem;
  padding: 0.75rem 1.5rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.tablet-send-btn:active {
  transform: scale(0.95);
  filter: brightness(0.9);
}

.tablet-send-btn .btn-icon {
  font-size: 1.2rem;
}

@media (max-width: 480px) {
  .tablet-send-btn .btn-text {
    display: none;
  }
  .tablet-send-btn {
    padding: 0.75rem;
    aspect-ratio: 1;
  }
}
.mobile-word-info {
  display: flex;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.length-badge {
  background: linear-gradient(135deg, #f59e0b, #ea580c);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 2rem;
  font-size: 0.8rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  box-shadow: 0 4px 10px rgba(234, 88, 12, 0.3);
  animation: badgeIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes badgeIn {
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

@media (max-width: 480px) {
  .game-dashboard {
    padding: 0.5rem;
  }
  
  .game-header {
    padding: 0.75rem;
    margin-bottom: 0.25rem;
  }

  .canvas-chamber {
    height: 45dvh;
    min-height: 300px;
  }

  .sidebars-row {
    height: 35dvh !important;
  }
  
  .host-action-footer {
    padding: 1rem;
    gap: 0.5rem;
  }
}

/* Orientation Hint Styles */
.orientation-hint {
  display: none; /* Hidden by default */
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  z-index: 9999;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
  color: white;
}

.rotate-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  animation: rotatePhone 2s ease-in-out infinite;
}

.orientation-hint h3 {
  font-weight: 900;
  letter-spacing: 0.05em;
  color: var(--accent);
  margin-bottom: 0.5rem;
}

.orientation-hint p {
  font-size: 0.9rem;
  color: var(--text-muted);
  max-width: 250px;
  margin-bottom: 2rem;
}

.hint-dismiss-btn {
  padding: 0.8rem 2rem;
  font-size: 0.9rem;
  font-weight: 800;
  border-radius: 2rem;
  width: 100%;
  max-width: 200px;
}

@keyframes rotatePhone {
  0% { transform: rotate(0deg); }
  25% { transform: rotate(90deg); }
  75% { transform: rotate(90deg); }
  100% { transform: rotate(0deg); }
}

@media (max-width: 768px) and (orientation: portrait) {
  .orientation-hint {
    display: flex;
  }
}
</style>
