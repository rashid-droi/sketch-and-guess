<script setup>
import { ref } from 'vue';

const props = defineProps(['onJoin']);

const playerName = ref('');
const roomId = ref('');
const isCreating = ref(false);

const handleJoin = async () => {
  if (!playerName.value) return alert('Please enter your name');
  
  const endpoint = roomId.value ? 'join-room' : 'create-room';
  const body = roomId.value 
    ? { room_id: roomId.value, player_id: Math.random().toString(36).substr(2, 9), player_name: playerName.value }
    : { player_id: Math.random().toString(36).substr(2, 9), player_name: playerName.value };

  try {
    const response = await fetch(`http://localhost:8000/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    if (!response.ok) throw new Error('Action failed');
    const data = await response.json();
    
    props.onJoin({
      roomId: data.room_id,
      playerId: body.player_id,
      playerName: body.player_name,
      initialPlayers: data.players
    });
  } catch (err) {
    alert(err.message);
  }
};
</script>

<template>
  <div class="lobby-container">
    <div class="glass-card lobby-card">
      <h1 class="title">Sketch & Guess</h1>
      <p class="subtitle">Join and compete with friends in real-time!</p>
      
      <div class="form-group">
        <label>Your Name</label>
        <input v-model="playerName" type="text" placeholder="Enter name..." class="input-field" />
      </div>

      <div class="form-group">
        <label>Room ID (Optional)</label>
        <input v-model="roomId" type="text" placeholder="Leave empty to create new..." class="input-field" />
      </div>

      <button @click="handleJoin" class="btn-primary w-full mt-4">
        {{ roomId ? 'Join Room' : 'Create Room' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.lobby-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 90vh;
}

.lobby-card {
  padding: 3rem;
  width: 100%;
  max-width: 480px;
  text-align: center;
}

.title {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #fff, var(--text-muted));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--text-muted);
  margin-bottom: 2rem;
}

.form-group {
  text-align: left;
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  opacity: 0.8;
}

.w-full { width: 100%; }
.mt-4 { margin-top: 1rem; }
</style>
