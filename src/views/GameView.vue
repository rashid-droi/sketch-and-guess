<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGameStore } from '../stores/gameStore';
import GameRoom from '../components/GameRoom.vue';

const route = useRoute();
const router = useRouter();
const gameStore = useGameStore();

onMounted(() => {
  const roomId = route.params.id;
  
  // If we don't have a player name (e.g. direct link), redirect to home
  // In a real app, you might show a "Enter Name" modal here instead
  if (!gameStore.gameState.playerName) {
    router.push('/');
    return;
  }

  gameStore.connect(roomId, gameStore.gameState.playerId, gameStore.gameState.playerName);
});

onUnmounted(() => {
  gameStore.resetState();
});
</script>

<template>
  <div class="game-view">
    <GameRoom 
      :gameState="gameStore.gameState" 
      :onSend="gameStore.send" 
    />
  </div>
</template>

<style scoped>
.game-view {
  min-height: 100vh;
}
</style>
