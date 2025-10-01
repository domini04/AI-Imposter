<script setup>
import { ref, onMounted } from 'vue';
import { useGameStore } from '@/stores/game';
import { useRouter } from 'vue-router';

// Define props and emits for component communication
const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
});
const emit = defineEmits(['close']);

// Access store and router
const gameStore = useGameStore();
const router = useRouter();

// Local state for the form fields
const gameSettings = ref({
  language: 'en',
  aiCount: 1,
  privacy: 'public',
  aiModelId: null,
});

const isCreating = ref(false);
const modelsLoading = ref(false);

onMounted(async () => {
  if (!gameStore.availableModels.length) {
    modelsLoading.value = true;
    await gameStore.fetchModels();
    modelsLoading.value = false;
  }

  if (gameStore.availableModels.length && !gameSettings.value.aiModelId) {
    gameSettings.value.aiModelId = gameStore.availableModels[0].id;
  }
});

const handleCreate = async () => {
  isCreating.value = true;
  const newGameId = await gameStore.createGame(gameSettings.value);
  isCreating.value = false;

  if (newGameId) {
    // If game is created successfully, close the modal and navigate
    emit('close');
    router.push({ name: 'GameRoom', params: { id: newGameId } });
  } else {
    alert('Failed to create the game. Please try again.');
  }
};

const handleCancel = () => {
  emit('close');
};
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="handleCancel">
    <div class="modal-content">
      <h2>Create New Game</h2>
      <form @submit.prevent="handleCreate">
        <!-- Language Selection -->
        <div class="form-group">
          <label>Language</label>
          <div class="radio-group">
            <label>
              <input type="radio" v-model="gameSettings.language" value="en" /> English
            </label>
            <label>
              <input type="radio" v-model="gameSettings.language" value="ko" /> Korean
            </label>
          </div>
        </div>

        <!-- AI Count Selection -->
        <div class="form-group">
          <label>Number of AI Impostors</label>
          <div class="radio-group">
            <label>
              <input type="radio" v-model="gameSettings.aiCount" :value="1" /> 1
            </label>
            <label>
              <input type="radio" v-model="gameSettings.aiCount" :value="2" /> 2
            </label>
          </div>
        </div>

        <!-- Model Selection -->
        <div class="form-group">
          <label>AI Model</label>
          <div v-if="modelsLoading" class="loading">Loading models...</div>
          <div v-else-if="!gameStore.availableModels.length" class="empty-state">
            <p>No AI models available. Please try again later.</p>
          </div>
          <div v-else class="model-list">
            <label v-for="model in gameStore.availableModels" :key="model.id" class="model-option">
              <input
                type="radio"
                v-model="gameSettings.aiModelId"
                :value="model.id"
              />
              <span class="model-name">{{ model.display_name }}</span>
              <span class="model-provider">({{ model.provider.toUpperCase() }})</span>
              <p class="model-description">{{ model.description }}</p>
            </label>
          </div>
        </div>

        <!-- Privacy Selection -->
        <div class="form-group">
          <label>Privacy</label>
          <div class="radio-group">
            <label>
              <input type="radio" v-model="gameSettings.privacy" value="public" /> Public
            </label>
            <label>
              <input type="radio" v-model="gameSettings.privacy" value="private" /> Private
            </label>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="form-actions">
          <button type="button" @click="handleCancel" class="btn-secondary" :disabled="isCreating">
            Cancel
          </button>
          <button type="submit" class="btn-primary" :disabled="isCreating || !gameSettings.aiModelId">
            {{ isCreating ? 'Creating...' : 'Create Game' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 2rem;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

h2 {
  margin-top: 0;
  margin-bottom: 2rem;
  text-align: center;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.radio-group {
  display: flex;
  gap: 1rem;
}

.radio-group label {
  font-weight: normal;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

button {
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
.btn-primary:disabled {
  background-color: #a0c3e6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #f0f0f0;
  color: #333;
}
.btn-secondary:hover {
  background-color: #e0e0e0;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.model-option {
  display: block;
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.model-option:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.model-option input {
  margin-right: 0.75rem;
}

.model-name {
  font-weight: bold;
}

.model-provider {
  margin-left: 0.5rem;
  color: #555;
}

.model-description {
  margin: 0.5rem 0 0;
  color: #666;
  font-size: 0.9rem;
}

.loading {
  color: #777;
}

.empty-state {
  color: #a00;
  font-size: 0.95rem;
}
</style>
