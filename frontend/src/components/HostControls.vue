<script setup>
import { computed } from 'vue';

const MIN_PLAYERS = 2;

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
  playerCount: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(['start-game']);

const isStartDisabled = computed(() => {
  return props.playerCount < MIN_PLAYERS;
});

const statusMessage = computed(() => {
  if (isStartDisabled.value) {
    return `Waiting for at least ${MIN_PLAYERS} players to join... (${props.playerCount}/${MIN_PLAYERS})`;
  }
  return 'Ready to start!';
});

const handleStartGame = () => {
  emit('start-game');
};
</script>

<template>
  <div v-if="status === 'waiting'" class="host-controls">
    <h4>Host Controls</h4>
    <p>{{ statusMessage }}</p>
    <button 
      @click="handleStartGame" 
      :disabled="isStartDisabled"
      class="btn-start"
    >
      Start Game
    </button>
  </div>
</template>

<style scoped>
.host-controls {
  background-color: #fff8e1;
  border: 1px solid #ffecb3;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 2rem;
  text-align: center;
}

h4 {
  margin-top: 0;
  color: #c09100;
}

p {
  color: #616161;
}

.btn-start {
  background-color: #28a745;
  color: white;
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-start:hover {
  background-color: #218838;
}

.btn-start:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}
</style>
