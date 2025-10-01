<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';

const props = defineProps({
  roundStart: {
    type: String,
    required: false,
    default: null,
  },
  roundEnd: {
    type: String,
    required: false,
    default: null,
  },
  phase: {
    type: String,
    required: false,
    default: 'ANSWER_SUBMISSION',
  },
  autoTrigger: {
    type: Boolean,
    default: false,
  }
});

const emit = defineEmits(['expired']);

const remainingMs = ref(0);
let intervalId = null;
let emitted = false;

const parseTimestamp = (timestamp) => {
  return timestamp ? new Date(timestamp).getTime() : null;
};

const updateRemaining = () => {
  const end = parseTimestamp(props.roundEnd);
  if (!end) {
    remainingMs.value = 0;
    return;
  }
  const now = Date.now();
  remainingMs.value = Math.max(end - now, 0);

  if (remainingMs.value === 0 && props.autoTrigger && !emitted) {
    emitted = true;
    emit('expired');
  }
};

const formattedTime = computed(() => {
  const totalSeconds = Math.floor(remainingMs.value / 1000);
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  return `${minutes}:${seconds}`;
});

const phaseLabel = computed(() => {
  switch (props.phase) {
    case 'ANSWER_SUBMISSION':
      return 'Answer Submission';
    case 'VOTING':
      return 'Voting';
    case 'ROUND_ENDED':
      return 'Round Ended';
    default:
      return props.phase;
  }
});

watch(() => props.roundEnd, () => {
  startTimer();
});

const startTimer = () => {
  clearInterval(intervalId);
  emitted = false;
  updateRemaining();
  intervalId = setInterval(updateRemaining, 1000);
};

onMounted(() => {
  startTimer();
});

onUnmounted(() => {
  clearInterval(intervalId);
});
</script>

<template>
  <div class="round-timer">
    <span class="phase">Phase: {{ phaseLabel }}</span>
    <span class="countdown">Time left: {{ formattedTime }}</span>
  </div>
</template>

<style scoped>
.round-timer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #e3f2fd;
  border: 1px solid #90caf9;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  color: #0d47a1;
  font-weight: 600;
}

.countdown {
  font-variant-numeric: tabular-nums;
}
</style>
