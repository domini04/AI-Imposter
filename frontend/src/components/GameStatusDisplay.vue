<script setup>
import { computed } from 'vue';

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
  currentRound: {
    type: Number,
    required: true,
  },
  question: {
    type: String,
    default: '',
  },
});

const statusMessage = computed(() => {
  switch (props.status) {
    case 'waiting':
      return 'Waiting for host to start the game...';
    case 'in_progress':
      return `Round ${props.currentRound} of 3`;
    case 'voting':
      return `Voting for Round ${props.currentRound}`;
    case 'finished':
      return 'Game Over!';
    default:
      return 'Loading...';
  }
});
</script>

<template>
  <header class="game-status-header">
    <div class="status-message">
      <h2>{{ statusMessage }}</h2>
    </div>
    <div v-if="status === 'in_progress' && question" class="question-display">
      <p><strong>Question:</strong> {{ question }}</p>
    </div>
  </header>
</template>

<style scoped>
.game-status-header {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  text-align: center;
}

.status-message h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.question-display {
  margin-top: 1rem;
  font-size: 1.2rem;
  color: #555;
}
</style>
