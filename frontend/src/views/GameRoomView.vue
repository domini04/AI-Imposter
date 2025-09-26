<script setup>
import { onMounted, onUnmounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useGameStore } from '@/stores/game';
import { subscribeToGame, unsubscribeFromGame } from '@/services/game_listener';
import GameStatusDisplay from '@/components/GameStatusDisplay.vue';
import PlayerList from '@/components/PlayerList.vue';

const route = useRoute();
const gameStore = useGameStore();

// Create a reactive reference to the current game from the store.
const game = computed(() => gameStore.currentGame);

// A computed property to safely get the current round's question
const currentQuestion = computed(() => {
  if (game.value && game.value.rounds && game.value.currentRound > 0) {
    const currentRoundData = game.value.rounds[game.value.currentRound - 1];
    return currentRoundData ? currentRoundData.question : '';
  }
  return '';
});

// When the component is mounted, subscribe to the game's real-time updates.
onMounted(() => {
  const gameId = route.params.id;
  if (gameId) {
    // We subscribe to the listener and provide the store's action as the callback.
    // This directly pipes the real-time data into our central state.
    subscribeToGame(gameId, gameStore.setCurrentGame);
  } else {
    console.error('No game ID found in the route.');
    // Here you might want to redirect the user back to the lobby
  }
});

// When the component is unmounted (e.g., user navigates away), clean up.
onUnmounted(() => {
  // Unsubscribe from the Firestore listener to prevent memory leaks.
  unsubscribeFromGame();
  // Clear the current game data from the store.
  gameStore.leaveGame();
});
</script>

<template>
  <div v-if="game" class="game-room-layout">
    <aside class="side-panel">
      <PlayerList :players="game.players" :host-id="game.hostId" />
    </aside>
    
    <main class="main-content">
      <GameStatusDisplay 
        :status="game.status" 
        :current-round="game.currentRound"
        :question="currentQuestion"
      />
      <!-- The Chat Display and other components will go here later -->
    </main>
  </div>
  <div v-else class="loading-container">
    <p>Loading game data...</p>
  </div>
</template>

<style scoped>
.game-room-layout {
  display: grid;
  grid-template-columns: 250px 1fr; /* Sidebar and main content */
  gap: 2rem;
  max-width: 1200px;
  margin: 2rem auto;
}

.side-panel {
  /* Styling for the sidebar where the player list will be */
}

.main-content {
  /* Styling for the main game area */
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
  font-size: 1.5rem;
  color: #777;
}
</style>
