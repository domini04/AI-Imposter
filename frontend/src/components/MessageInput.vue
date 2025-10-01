<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
  placeholder: {
    type: String,
    default: 'Share your answer…',
  },
  maxLength: {
    type: Number,
    default: 280,
  }
});

const emit = defineEmits(['submit']);

const inputValue = ref('');
const remainingChars = computed(() => props.maxLength - inputValue.value.length);

watch(() => props.disabled, (disabled) => {
  if (disabled) {
    inputValue.value = '';
  }
});

const handleSubmit = () => {
  if (props.disabled || props.isSubmitting) return;
  const trimmed = inputValue.value.trim();
  if (!trimmed) return;
  emit('submit', trimmed);
  inputValue.value = '';
};
</script>

<template>
  <div class="message-input">
    <textarea
      v-model="inputValue"
      :placeholder="placeholder"
      :maxlength="maxLength"
      :disabled="disabled || isSubmitting"
      @keydown.enter.prevent="handleSubmit"
    />
    <div class="toolbar">
      <span class="char-count">{{ remainingChars }}</span>
      <button
        type="button"
        class="btn-send"
        :disabled="disabled || isSubmitting || !inputValue.trim()"
        @click="handleSubmit"
      >
        {{ isSubmitting ? 'Submitting…' : 'Submit Answer' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.message-input {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

textarea {
  width: 100%;
  min-height: 120px;
  padding: 0.75rem;
  border-radius: 8px;
  border: 1px solid #ddd;
  resize: vertical;
  font-size: 1rem;
  line-height: 1.4;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.char-count {
  color: #777;
  font-size: 0.9rem;
}

.btn-send {
  background-color: #007bff;
  color: white;
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-send:disabled {
  background-color: #aac6f5;
  cursor: not-allowed;
}

.btn-send:not(:disabled):hover {
  background-color: #005dc3;
}
</style>
