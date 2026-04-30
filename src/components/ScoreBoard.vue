<script setup>
import { computed } from 'vue';

const props = defineProps(['players']);

const sortedLeaderboard = computed(() => {
  return [...props.players].sort((a, b) => (b.score || 0) - (a.score || 0));
});
</script>

<template>
  <div class="scoreboard-container glass-card">
    <div class="scoreboard-header">
      <h2 class="title">LEADERBOARD</h2>
      <div class="trophy-icon">🏆</div>
    </div>

    <div class="leaderboard-list">
      <div 
        v-for="(player, index) in sortedLeaderboard" 
        :key="player.player_id" 
        class="leaderboard-item"
        :class="{ 'top-three': index < 3 }"
      >
        <div class="rank-badge" :class="`rank-${index + 1}`">
          {{ index + 1 }}
        </div>
        
        <div class="player-info">
          <span class="player-name">{{ player.player_name || player.name }}</span>
        </div>

        <div class="score-pill">
          {{ player.score || 0 }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scoreboard-container {
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.4);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.scoreboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 0.875rem;
  font-weight: 800;
  letter-spacing: 0.2em;
  color: var(--text-muted);
}

.trophy-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 0 10px rgba(234, 179, 8, 0.5));
}

.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.leaderboard-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 1rem;
  border: 1px solid var(--border-glass);
  transition: transform 0.2s ease;
}

.leaderboard-item:hover {
  transform: translateX(5px);
  background: rgba(255, 255, 255, 0.06);
}

.rank-badge {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 800;
  margin-right: 1rem;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-muted);
}

/* Podium Styling */
.top-three {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

.rank-1 { background: #eab308; color: #000; box-shadow: 0 0 15px rgba(234, 179, 8, 0.4); }
.rank-2 { background: #94a3b8; color: #000; }
.rank-3 { background: #b45309; color: #fff; }

.player-info {
  flex: 1;
}

.player-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-main);
}

.score-pill {
  padding: 0.25rem 0.75rem;
  background: var(--primary-glow);
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 2rem;
  font-size: 0.8rem;
  font-weight: 800;
}

.top-three .score-pill {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-color: rgba(255, 255, 255, 0.2);
}
</style>
