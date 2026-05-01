<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useGameStore } from '../stores/gameStore';

const router = useRouter();
const gameStore = useGameStore();

const playerName = ref('');
const roomIdInput = ref('');
const loading = ref(false);

const handleAction = async (isJoin = false) => {
  if (!playerName.value.trim()) return alert('Please enter your name');
  if (isJoin && !roomIdInput.value.trim()) return alert('Please enter a room ID');
  
  loading.value = true;
  const endpoint = isJoin ? 'join-room' : 'create-room';
  const playerId = Math.random().toString(36).substr(2, 9);
  
  const body = isJoin 
    ? { room_id: roomIdInput.value.trim().toUpperCase(), player_id: playerId, player_name: playerName.value }
    : { player_id: playerId, player_name: playerName.value };

  try {
    const apiHost = window.location.hostname === 'localhost' ? 'localhost:8000' : `${window.location.hostname}:8000`;
    const response = await fetch(`http://${apiHost}/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Action failed');
    }
    
    const data = await response.json();
    
    // Set initial player list and identity in store
    gameStore.gameState.players = data.players;
    gameStore.gameState.playerName = playerName.value;
    gameStore.gameState.playerId = playerId;
    
    // Navigate to the room
    router.push(`/room/${data.room_id}`);
  } catch (err) {
    alert(err.message);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="home-container">
    <div class="glass-card home-card">
      <div class="header-section">
        <div class="logo-orb">🎨</div>
        <h1 class="title">Sketch & Guess</h1>
        <p class="subtitle">Real-time multiplayer drawing game</p>
      </div>
      
      <div class="form-section">
        <div class="form-group">
          <label>YOUR NAME</label>
          <input 
            v-model="playerName" 
            type="text" 
            placeholder="e.g. Picasso" 
            class="input-field" 
          />
        </div>

        <div class="divider">
          <span>JOIN AN EXISTING ROOM</span>
        </div>

        <div class="form-group">
          <label>ROOM ID</label>
          <input 
            v-model="roomIdInput" 
            type="text" 
            placeholder="ENTER ROOM CODE" 
            class="input-field code-input"
            @keyup.enter="handleAction(true)"
          />
        </div>

        <div class="actions">
          <button 
            @click="handleAction(true)" 
            class="btn-secondary"
            :disabled="loading"
          >
            JOIN ROOM
          </button>
          
          <div class="or-divider">OR</div>
          
          <button 
            @click="handleAction(false)" 
            class="btn-primary"
            :disabled="loading"
          >
            CREATE NEW ROOM
          </button>
        </div>
      </div>

      <footer class="footer">
        SELECT
      </footer>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: radial-gradient(circle at center, #1e293b, #0f172a);
}

.home-card {
  padding: 3.5rem;
  width: 100%;
  max-width: 500px;
  text-align: center;
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.logo-orb {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  display: inline-block;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.title {
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  background: linear-gradient(135deg, #fff 30%, var(--primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--text-muted);
  font-size: 1.1rem;
  margin-bottom: 2.5rem;
}

.form-group {
  text-align: left;
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--accent);
  margin-bottom: 0.5rem;
  letter-spacing: 0.1em;
}

.code-input {
  text-transform: uppercase;
  font-family: monospace;
  letter-spacing: 0.2em;
  font-weight: 700;
  text-align: center;
}

.divider {
  display: flex;
  align-items: center;
  margin: 2rem 0;
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.divider::before, .divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border-glass);
  margin: 0 1rem;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.btn-primary, .btn-secondary {
  width: 100%;
  padding: 1rem;
  border-radius: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, var(--primary), #818cf8);
  color: white;
  box-shadow: 0 10px 20px -5px var(--primary-glow);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  color: white;
  border: 1px solid var(--border-glass);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.or-divider {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
}

.footer {
  margin-top: 3rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  opacity: 0.5;
}

.input-field {
  width: 100%;
}

@media (max-width: 480px) {
  .home-card {
    padding: 2rem 1.5rem;
    max-width: 90%;
    margin: 1rem;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .logo-orb {
    font-size: 2.5rem;
  }
  
  .subtitle {
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
  }
  
  .divider {
    margin: 1.5rem 0;
  }
}
</style>
