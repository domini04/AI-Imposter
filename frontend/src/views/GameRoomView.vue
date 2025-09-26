<script setup>
import { onMounted, onUnmounted, computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useGameStore } from '@/stores/game';
import { 
  subscribeToGame, 
  unsubscribeFromGame, 
  subscribeToMessages, 
  unsubscribeFromMessages 
} from '@/services/game_listener';
import { getCurrentUser } from '@/services/firebase';
import GameStatusDisplay from '@/components/GameStatusDisplay.vue';
import PlayerList from '@/components/PlayerList.vue';
import HostControls from '@/components/HostControls.vue';
import ChatDisplay from '@/components/ChatDisplay.vue';

const route = useRoute();
const gameStore = useGameStore();
const currentUser = ref(null);
const messages = ref([]);

// Create a reactive reference to the current game from the store.
const game = computed(() => gameStore.currentGame);

// Computed property to check if the current user is the host of the game.
const isHost = computed(() => {
  return game.value && currentUser.value && game.value.hostId === currentUser.value.uid;
});

// A computed property to safely get the current round's question
const currentQuestion = computed(() => {
  if (game.value && game.value.rounds && game.value.currentRound > 0) {
    const currentRoundData = game.value.rounds[game.value.currentRound - 1];
    return currentRoundData ? currentRoundData.question : '';
  }
  return '';
});

// When the component is mounted, subscribe to the game's real-time updates.
onMounted(async () => {
  currentUser.value = await getCurrentUser();
  const gameId = route.params.id;
  if (gameId) {
    // We subscribe to the listener and provide the store's action as the callback.
    // This directly pipes the real-time data into our central state.
    subscribeToGame(gameId, gameStore.setCurrentGame);
    subscribeToMessages(gameId, (newMessages) => {
      messages.value = newMessages;
    });
  } else {
    console.error('No game ID found in the route.');
    // Here you might want to redirect the user back to the lobby
  }
});

// When the component is unmounted (e.g., user navigates away), clean up.
onUnmounted(() => {
  // Unsubscribe from all Firestore listeners to prevent memory leaks.
  unsubscribeFromGame();
  unsubscribeFromMessages();
  // Clear the current game data from the store.
  gameStore.leaveGame();
});
</script>

<template>
  <div v-if="game" class="game-room-layout">
    <aside class="side-panel">
      <PlayerList :players="game.players" :host-id="game.hostId" :status="game.status" />
      <HostControls 
        v-if="isHost"
        :status="game.status"
        :player-count="game.players.length"
        @start-game="gameStore.startGame()"
      />
    </aside>
    
    <main class="main-content">
      <GameStatusDisplay 
        :status="game.status" 
        :current-round="game.currentRound"
        :question="currentQuestion"
      />
      <ChatDisplay :messages="messages" :players="game.players" />
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
  display: flex;
  flex-direction: column;
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
