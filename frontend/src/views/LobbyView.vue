<script setup>
import { onMounted, ref } from 'vue';
import { useGameStore } from '@/stores/game';
import { useRouter } from 'vue-router';
import CreateGameModal from '@/components/CreateGameModal.vue';

// Access our Pinia store
const gameStore = useGameStore();
const router = useRouter();

// State to control the visibility of the "Create Game" modal
const isCreateModalVisible = ref(false);

// Fetch the public games when the component is first mounted
onMounted(() => {
  gameStore.fetchPublicGames();
});

const handleRefresh = () => {
  gameStore.fetchPublicGames();
};

const handleJoinGame = async (gameId) => {
  const success = await gameStore.joinGame(gameId);
  if (success) {
    // If join is successful, navigate to the game room.
    // We'll create this route in the next step.
    router.push({ name: 'GameRoom', params: { id: gameId } });
  } else {
    // Optionally, show an error message to the user
    alert('Failed to join the game. It might be full or already in progress.');
  }
};

const handleCreateGame = () => {
  // This now just opens the modal
  isCreateModalVisible.value = true;
};
</script>

<template>
  <div class="lobby">
    <header class="lobby-header">
      <h1>Game Lobby</h1>
      <div class="actions">
        <button @click="handleRefresh" class="btn-secondary">Refresh ↻</button>
        <button @click="handleCreateGame" class="btn-primary">✨ Create New Game</button>
      </div>
    </header>

    <main class="game-list-container">
      <!-- Loading State -->
      <div v-if="gameStore.isLoading" class="loading">
        <p>Loading games...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!gameStore.publicGames.length" class="empty-state">
        <p>No public games are available.</p>
        <p>Why not create one?</p>
      </div>
      
      <!-- Game List -->
      <div v-else class="game-list">
        <div v-for="game in gameStore.publicGames" :key="game.gameId" class="game-card">
          <div class="game-details">
            <span class="language-tag">{{ game.language.toUpperCase() }}</span>
            <span class="players">Players: {{ game.playerCount }} / 5</span>
          </div>
          <button @click="handleJoinGame(game.gameId)" class="btn-join">Join Game →</button>
        </div>
      </div>
    </main>

    <!-- The Create Game Modal is now part of the lobby -->
    <CreateGameModal 
      :show="isCreateModalVisible" 
      @close="isCreateModalVisible = false" 
    />
  </div>
</template>

<style scoped>
/* A simple, modern theme for the lobby */
.lobby {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
  font-family: sans-serif;
  color: #333;
}

.lobby-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

.lobby-header h1 {
  margin: 0;
  font-size: 2rem;
}

.actions button {
  margin-left: 1rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}
.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #f0f0f0;
  color: #333;
}
.btn-secondary:hover {
  background-color: #e0e0e0;
}

.loading, .empty-state {
  text-align: center;
  padding: 4rem 0;
  color: #777;
}

.game-list {
  display: grid;
  gap: 1rem;
}

.game-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.game-details {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.language-tag {
  background-color: #e0e0e0;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: bold;
}

.players {
  font-size: 1.1rem;
}

.btn-join {
  background-color: #28a745;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-join:hover {
  background-color: #218838;
}
</style>
