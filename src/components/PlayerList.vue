<script setup>
const props = defineProps(['players', 'currentDrawerId']);
</script>

<template>
  <div class="player-list-container glass-card">
    <div class="list-header">
      <span class="header-text">PLAYERS</span>
      <span class="player-count">{{ players.length }} / 6</span>
    </div>

    <div class="list-content">
      <div 
        v-for="player in players" 
        :key="player.player_id" 
        class="player-card"
        :class="{ 'is-drawer': player.player_id === currentDrawerId }"
      >
        <div class="player-avatar">
          {{ player.player_name.charAt(0).toUpperCase() }}
        </div>
        
        <div class="player-info">
          <span class="player-name">{{ player.player_name }}</span>
          <span class="player-score">{{ player.score || 0 }} pts</span>
        </div>

        <div v-if="player.player_id === currentDrawerId" class="drawer-badge">
          <span class="pencil-icon">✏️</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.player-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  min-height: 0;
  background: rgba(15, 23, 42, 0.4);
  overflow: hidden;
}

.list-header {
  padding: 1.25rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-glass);
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
  background: rgba(34, 211, 238, 0.1);
  padding: 0.2rem 0.6rem;
  border-radius: 1rem;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.player-card {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid transparent;
  border-radius: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.player-card.is-drawer {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(99, 102, 241, 0.05));
  border-color: var(--primary);
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.1);
  transform: scale(1.02);
}

.player-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.1rem;
  color: white;
  margin-right: 1rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.player-card.is-drawer .player-avatar {
  background: var(--accent);
  box-shadow: 0 0 15px rgba(34, 211, 238, 0.4);
}

.player-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.player-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-main);
}

.player-score {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}

.drawer-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(34, 211, 238, 0.3);
}

.pencil-icon {
  font-size: 0.9rem;
}

/* Responsive Mobile View (Split Column) */
@media (max-width: 768px) {
  .player-list-container {
    height: 100%;
    border-radius: 1rem;
  }

  .list-header {
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-glass);
  }

  .header-text { font-size: 0.6rem; }
  .player-count { font-size: 0.55rem; padding: 0.1rem 0.4rem; }

  .list-content {
    padding: 0.5rem;
    gap: 0.4rem;
  }

  .player-card {
    padding: 0.4rem 0.6rem;
    border-radius: 0.75rem;
  }

  .player-avatar {
    width: 24px;
    height: 24px;
    font-size: 0.7rem;
    margin-right: 0.6rem;
  }

  .player-name { font-size: 0.75rem; }
  .player-score { font-size: 0.6rem; }

  .drawer-badge {
    width: 18px;
    height: 18px;
  }
  .pencil-icon { font-size: 0.6rem; }
}
</style>
