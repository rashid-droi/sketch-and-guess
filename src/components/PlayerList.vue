<script setup>
import { computed, ref } from 'vue';

const props = defineProps(['players', 'currentDrawerId']);

const searchQuery = ref('');

// Sorting logic: Drawer first, then score descending, then name alphabetical
const sortedPlayers = computed(() => {
  if (!props.players) return [];
  
  return [...props.players].sort((a, b) => {
    // 1. Current drawer always first
    if (a.player_id === props.currentDrawerId) return -1;
    if (b.player_id === props.currentDrawerId) return 1;
    
    // 2. Sort by score descending
    const scoreA = a.score || 0;
    const scoreB = b.score || 0;
    if (scoreB !== scoreA) {
      return scoreB - scoreA;
    }
    
    // 3. Fallback to alphabetical name
    return (a.player_name || '').localeCompare(b.player_name || '');
  });
});

// Search/Filter logic
const processedPlayers = computed(() => {
  if (!searchQuery.value.trim()) return sortedPlayers.value;
  const query = searchQuery.value.toLowerCase().trim();
  return sortedPlayers.value.filter(player => 
    player.player_name.toLowerCase().includes(query)
  );
});

// Pre-calculate ranks in a map to avoid O(N^2) in the template
const playerRanks = computed(() => {
  if (!props.players) return new Map();
  
  const scoreSorted = [...props.players].sort((a, b) => (b.score || 0) - (a.score || 0));
  const ranks = new Map();
  scoreSorted.forEach((p, index) => {
    ranks.set(p.player_id, index);
  });
  return ranks;
});

const getRank = (playerId) => {
  return playerRanks.value.get(playerId) ?? 999;
};
</script>

<template>
  <div class="player-list-container glass-card">
    <div class="list-header">
      <div class="header-main">
        <span class="header-text">PLAYERS</span>
        <span class="player-count">{{ players.length }}</span>
      </div>
      
      <div class="search-box" v-if="players.length > 8">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Search..." 
          class="search-input"
        />
      </div>
    </div>

    <div class="list-content custom-scrollbar">
      <div 
        v-for="(player, index) in processedPlayers" 
        :key="player.player_id" 
        class="player-card"
        :class="{ 
          'is-drawer': player.player_id === currentDrawerId,
          'has-guessed': player.guessed_this_round,
          'is-top-3': getRank(player.player_id) < 3 && player.player_id !== currentDrawerId,
          'rank-1': getRank(player.player_id) === 0,
          'rank-2': getRank(player.player_id) === 1,
          'rank-3': getRank(player.player_id) === 2
        }"
      >
        <div class="player-avatar">
          {{ (player.player_name || '?').charAt(0).toUpperCase() }}
          <div v-if="getRank(player.player_id) < 3" class="rank-badge">
            {{ getRank(player.player_id) + 1 }}
          </div>
        </div>
        
        <div class="player-info">
          <div class="name-row">
            <span class="player-name">{{ player.player_name || 'Anonymous' }}</span>
            <div v-if="player.streak >= 2" class="streak-pill">
              🔥 {{ player.streak }}
            </div>
            <span v-if="player.player_id === currentDrawerId" class="drawing-tag">DRAWING</span>
            <span v-if="player.guessed_this_round && player.player_id !== currentDrawerId" class="guessed-tag">✓</span>
          </div>
          <span class="player-score">{{ player.score || 0 }} pts</span>
        </div>

        <div v-if="player.player_id === currentDrawerId" class="drawer-badge-pulse">
          <span class="pencil-icon">🎨</span>
        </div>
      </div>
      
      <div v-if="processedPlayers.length === 0" class="empty-search">
        No players found
      </div>
    </div>
  </div>
</template>

<style scoped>
.player-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%; /* Ensure it doesn't grow past container */
  background: rgba(15, 23, 42, 0.4);
  overflow: hidden;
  position: relative;
}

.list-header {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border-bottom: 1px solid var(--border-glass);
  background: rgba(15, 23, 42, 0.2);
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-text {
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: var(--text-muted);
}

.player-count {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--accent);
  background: rgba(255, 205, 0, 0.1);
  padding: 0.2rem 0.6rem;
  border-radius: 1rem;
}

.search-box {
  position: relative;
}

.search-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-glass);
  border-radius: 0.5rem;
  padding: 0.4rem 0.75rem;
  color: white;
  font-size: 0.8rem;
  outline: none;
  transition: all 0.2s ease;
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--primary);
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.player-card {
  display: flex;
  align-items: center;
  padding: 0.6rem 0.8rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid transparent;
  border-radius: 0.75rem;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

/* Drawer Styles */
.player-card.is-drawer {
  background: linear-gradient(135deg, rgba(255, 205, 0, 0.15), rgba(255, 205, 0, 0.05));
  border-color: var(--accent);
  box-shadow: 0 4px 15px rgba(255, 205, 0, 0.1);
  transform: scale(1.02);
  z-index: 10;
}

/* Top 3 Styles */
.player-card.is-top-3 {
  background: rgba(255, 255, 255, 0.06);
}

.player-card.rank-1 { border-left: 3px solid #ffd700; }
.player-card.rank-2 { border-left: 3px solid #c0c0c0; }
.player-card.rank-3 { border-left: 3px solid #cd7f32; }

.player-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1rem;
  color: white;
  margin-right: 0.75rem;
  position: relative;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.rank-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 14px;
  height: 14px;
  background: var(--accent);
  color: #000;
  font-size: 0.6rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  border: 1px solid rgba(0,0,0,0.2);
}

.player-card.is-drawer .player-avatar {
  background: var(--accent);
  color: #000;
  box-shadow: 0 0 10px rgba(255, 205, 0, 0.4);
}

.player-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.player-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-main);
  white-space: normal;
  word-break: break-word;
  line-height: 1.2;
}

.drawing-tag, .guessed-tag {
  font-size: 0.6rem;
  font-weight: 800;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  letter-spacing: 0.05em;
}

.drawing-tag {
  color: var(--accent);
  background: rgba(255, 205, 0, 0.1);
}

.guessed-tag {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  font-weight: 900;
}

.streak-pill {
  font-size: 0.65rem;
  background: rgba(248, 113, 113, 0.1);
  color: #f87171;
  padding: 0.1rem 0.5rem;
  border-radius: 2rem;
  font-weight: 800;
  animation: pulse 2s infinite;
}

.player-card.has-guessed {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.2);
}

.player-score {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 500;
}

.drawer-badge-pulse {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  animation: pulse-glow 2s infinite;
  box-shadow: 0 0 10px var(--accent);
}

.pencil-icon {
  font-size: 0.8rem;
}

.empty-search {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-size: 0.8rem;
  font-style: italic;
}

@keyframes pulse-glow {
  0% { transform: scale(1); box-shadow: 0 0 5px var(--accent); }
  50% { transform: scale(1.1); box-shadow: 0 0 15px var(--accent); }
  100% { transform: scale(1); box-shadow: 0 0 5px var(--accent); }
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

/* Responsive Scaling */
@media (max-width: 1024px) {
  .player-card {
    padding: 0.5rem 0.6rem;
  }
  .player-avatar {
    width: 32px;
    height: 32px;
    font-size: 0.9rem;
  }
}

@media (max-width: 768px) {
  .list-header {
    padding: 0.75rem;
  }
  .player-card {
    padding: 0.4rem 0.5rem;
    border-radius: 0.5rem;
  }
  .player-avatar {
    width: 28px;
    height: 28px;
    font-size: 0.8rem;
    margin-right: 0.5rem;
  }
  .player-name { font-size: 0.8rem; }
  .player-score { font-size: 0.65rem; }
  .drawing-tag { display: none; } /* Hide tag on mobile to save space */
  .drawer-badge-pulse { width: 20px; height: 20px; }
}
</style>

