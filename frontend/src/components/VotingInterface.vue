<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  players: {
    type: Array,
    required: true
  },
  currentUserId: {
    type: String,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  isSubmitting: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['vote']);

const selectedPlayer = ref(null);

const eligiblePlayers = computed(() => {
  return props.players.filter(player => !player.isEliminated && player.uid !== props.currentUserId);
});

const handleSubmit = () => {
  if (!selectedPlayer.value) return;
  emit('vote', selectedPlayer.value);
};
</script>

<template>
  <div class="voting-interface">
    <h3>Cast Your Vote</h3>
    <p>Select the player you believe is an impostor. You cannot vote for yourself.</p>

    <div v-if="!eligiblePlayers.length" class="no-options">
      <p>No eligible players to vote for.</p>
    </div>

    <ul v-else class="player-options">
      <li v-for="player in eligiblePlayers" :key="player.uid" class="player-option">
        <label>
          <input
            type="radio"
            name="vote"
            :value="player.uid"
            v-model="selectedPlayer"
            :disabled="disabled || isSubmitting"
          />
          <span class="player-name">{{ player.gameDisplayName }}</span>
        </label>
      </li>
    </ul>

    <button
      type="button"
      class="btn-submit"
      :disabled="!selectedPlayer || disabled || isSubmitting"
      @click="handleSubmit"
    >
      {{ isSubmitting ? 'Submitting vote…' : 'Submit Vote' }}
    </button>
  </div>
</template>

<style scoped>
.voting-interface {
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 2rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.player-options {
  list-style: none;
  padding: 0;
  margin: 1rem 0;
}

.player-option {
  margin-bottom: 0.5rem;
}

.player-option label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.player-name {
  font-size: 1rem;
}

.btn-submit {
  background-color: #dc3545;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-submit:disabled {
  background-color: #f5b5bc;
  cursor: not-allowed;
}

.btn-submit:not(:disabled):hover {
  background-color: #c82333;
}

.no-options {
  color: #777;
  font-style: italic;
}
</style>
