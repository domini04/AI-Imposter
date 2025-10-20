<script setup>
import { onMounted, onUnmounted, computed, ref, watch } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { useGameStore } from '@/stores/game';
import {
  subscribeToGame,
  unsubscribeFromGame,
  subscribeToMessages,
  unsubscribeFromMessages
} from '@/services/game_listener';
import { getCurrentUser } from '@/services/firebase';
import { getEndReasonMessage } from '@/utils/gameMessages';
import GameStatusDisplay from '@/components/GameStatusDisplay.vue';
import PlayerList from '@/components/PlayerList.vue';
import HostControls from '@/components/HostControls.vue';
import ChatDisplay from '@/components/ChatDisplay.vue';
import MessageInput from '@/components/MessageInput.vue';
import VotingInterface from '@/components/VotingInterface.vue';
import RoundTimer from '@/components/RoundTimer.vue';

const route = useRoute();
const gameStore = useGameStore();
const currentUser = ref(null);
const messages = ref([]);
const submissionMessage = ref('');
const hostActionMessage = ref('');
const voteFeedback = ref('');
const phaseMessage = ref('');
const autoTallyInProgress = ref(false);

// Create a reactive reference to the current game from the store.
const game = computed(() => gameStore.currentGame);

// Computed property to check if the current user is the host of the game.
const isHost = computed(() => {
  return game.value && currentUser.value && game.value.hostId === currentUser.value.uid;
});

// A computed property to safely get the current round's question
const currentQuestion = computed(() => {
  if (game.value?.rounds?.length) {
    const latestRound = game.value.rounds
      .slice()
      .sort((a, b) => b.round - a.round)[0];
    return latestRound?.question || '';
  }
  return '';
});

const currentRoundNumber = computed(() => game.value?.currentRound ?? 0);

const isAnswerPhase = computed(() => game.value?.roundPhase === 'ANSWER_SUBMISSION');
const isVotingPhase = computed(() => game.value?.roundPhase === 'VOTING');
const isWaitingStatus = computed(() => game.value?.status === 'waiting');
const hasSubmittedAnswer = computed(() => gameStore.answerStatus === 'submitted');
const isSubmittingAnswer = computed(() => gameStore.answerStatus === 'submitting');

const roundStartTime = computed(() => game.value?.roundStartTime);
const roundEndTime = computed(() => game.value?.roundEndTime);

const roundSummary = computed(() => game.value?.lastRoundResult || null);

const roundsToHideSenderNames = computed(() => {
  if (!messages.value?.length) {
    return [];
  }
  return [1];
});

watch([
  () => game.value?.roundPhase,
  () => game.value?.currentRound,
], ([phase, round]) => {
  autoTallyInProgress.value = false;

  if (!phase) {
    phaseMessage.value = '';
    return;
  }

  if (phase === 'ANSWER_SUBMISSION') {
    if (round === 1) {
      phaseMessage.value = 'Collecting answers. No voting this round—answers will reveal and the next question will begin. Player names stay hidden during the first round so everyone reads the answers without bias.';
    } else {
      phaseMessage.value = 'Collecting answers. Once revealed, voting will open to pick the impostor.';
    }
  } else if (phase === 'VOTING') {
    phaseMessage.value = 'Voting in progress. All human players must cast a vote before the game continues.';
  } else if (phase === 'ROUND_ENDED') {
    phaseMessage.value = 'Round complete. Preparing the next question…';
  } else if (phase === 'GAME_ENDED') {
    phaseMessage.value = roundSummary.value?.endCondition
      ? getEndReasonMessage(roundSummary.value.endCondition)
      : 'Game over.';
  } else {
    phaseMessage.value = '';
  }
});

watch(() => game.value?.currentRound, () => {
  submissionMessage.value = '';
  voteFeedback.value = '';
});

const handleTimerExpired = async () => {
  if (!isHost.value || autoTallyInProgress.value) return;
  autoTallyInProgress.value = true;
  hostActionMessage.value = '';

  try {
    if (game.value?.roundPhase === 'ANSWER_SUBMISSION') {
      await gameStore.tallyAnswers();
      hostActionMessage.value = 'Answers tallied automatically.';
    } else if (game.value?.roundPhase === 'VOTING') {
      await gameStore.tallyVotes();
      hostActionMessage.value = 'Votes tallied automatically.';
    }
  } catch (error) {
    hostActionMessage.value = error.message || 'Automatic tally failed. Please retry.';
    autoTallyInProgress.value = false;
  }
};

const handleSubmitAnswer = async (text) => {
  await gameStore.submitAnswer(text);

  if (gameStore.answerStatus === 'submitted') {
    submissionMessage.value = 'Answer submitted! Waiting for reveal…';
  } else if (gameStore.answerStatus === 'error') {
    submissionMessage.value = gameStore.answerError || 'Failed to submit answer.';
  }
};

const handleTallyAnswers = async () => {
  hostActionMessage.value = '';
  try {
    await gameStore.tallyAnswers();
    hostActionMessage.value = 'Answers tallied successfully.';
  } catch (error) {
    hostActionMessage.value = error.message || 'Failed to tally answers.';
  }
};

const handleTallyVotes = async () => {
  hostActionMessage.value = '';
  try {
    await gameStore.tallyVotes();
    hostActionMessage.value = 'Votes tallied successfully.';
  } catch (error) {
    hostActionMessage.value = error.message || 'Failed to tally votes.';
  }
};

const handleVote = async (targetId) => {
  voteFeedback.value = '';
  await gameStore.castVote(targetId);
  if (gameStore.voteStatus === 'submitted') {
    voteFeedback.value = 'Vote submitted!';
  } else if (gameStore.voteStatus === 'error') {
    voteFeedback.value = gameStore.voteError || 'Failed to submit vote.';
  }
};

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
  <div v-if="game" class="game-room-container">
    <header class="game-room-header">
      <RouterLink to="/" class="home-link">
        <span class="home-icon" aria-hidden="true">←</span>
        <span class="home-text">Back to Lobby</span>
      </RouterLink>
    </header>

    <div class="game-room-layout">
      <aside class="side-panel">
        <PlayerList :players="game.players" :host-id="game.hostId" :status="game.status" :current-user-id="currentUser?.uid" />
        <HostControls 
          v-if="isHost"
          :status="game.status"
          :player-count="game.players.length"
          :round-phase="game.roundPhase"
          :is-tallying="autoTallyInProgress"
          @start-game="gameStore.startGame()"
          @tally-answers="handleTallyAnswers"
          @tally-votes="handleTallyVotes"
        />
        <p v-if="hostActionMessage" class="host-feedback">{{ hostActionMessage }}</p>
      </aside>
      
      <main class="main-content">
        <section class="top-status">
          <GameStatusDisplay 
            :status="game.status" 
            :current-round="game.currentRound"
            :question="currentQuestion"
          />
          <RoundTimer
            v-if="game.status === 'in_progress'"
            :round-start="roundStartTime"
            :round-end="roundEndTime"
            :phase="game.roundPhase"
            :auto-trigger="isHost"
            @expired="handleTimerExpired"
          />
          <p v-if="phaseMessage" class="phase-message">{{ phaseMessage }}</p>
        </section>

        <div :class="['content-grid', { 'with-voting': isVotingPhase }]">
          <div class="chat-column">
            <ChatDisplay
              :messages="messages"
              :players="game.players"
              :rounds="game.rounds"
              :hide-sender-name-rounds="roundsToHideSenderNames"
            />
            <section v-if="isAnswerPhase" class="answer-section">
              <MessageInput
                :disabled="hasSubmittedAnswer"
                :is-submitting="isSubmittingAnswer"
                placeholder="Share your answer for this round…"
                @submit="handleSubmitAnswer"
              />
              <p v-if="submissionMessage" class="submission-feedback">{{ submissionMessage }}</p>
            </section>
            <section v-else-if="!isWaitingStatus && !isVotingPhase" class="answer-inactive">
              <template v-if="game.roundPhase === 'GAME_ENDED' && roundSummary">
                <div class="round-summary">
                  <h3>Final Vote Result (Round {{ roundSummary.round }})</h3>
                  <p>{{ roundSummary.summary }}</p>
                  <ul>
                    <li v-for="vote in roundSummary.votes" :key="vote.targetId">
                      {{ vote.voteCount }} vote(s) for {{ vote.targetName }} ({{ vote.isImpostor ? 'AI' : 'Human' }})
                    </li>
                  </ul>
                  <p v-if="roundSummary.endCondition" class="end-reason">
                    {{ getEndReasonMessage(roundSummary.endCondition) }}
                  </p>
                </div>
              </template>
              <p v-else>Waiting for the next answer submission phase…</p>
            </section>
          </div>

          <VotingInterface
            v-if="isVotingPhase"
            :players="game.players"
            :current-user-id="currentUser?.uid"
            :disabled="gameStore.voteStatus === 'submitted'"
            :is-submitting="gameStore.voteStatus === 'submitting'"
            @vote="handleVote"
            class="voting-panel"
          />
        </div>
        <p v-if="voteFeedback" class="vote-feedback">{{ voteFeedback }}</p>
      </main>
    </div>
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
  max-width: 1600px;
  margin: 1rem auto 2rem;
}

.game-room-container {
  max-width: 1800px;
  margin: 0 auto;
  padding: 0 2rem;
}

.game-room-header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 1.5rem 0 0.5rem;
}

.home-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.1rem;
  border-radius: 999px;
  text-decoration: none;
  background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%);
  color: #fff;
  font-weight: 600;
  letter-spacing: 0.01rem;
  box-shadow: 0 4px 10px rgba(13, 71, 161, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.home-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(13, 71, 161, 0.3);
}

.home-icon {
  font-size: 1.1rem;
  font-weight: 700;
}

.home-text {
  font-size: 0.95rem;
}

.side-panel {
  /* Styling for the sidebar where the player list will be */
}

.main-content {
  display: flex;
  flex-direction: column;
}

.top-status {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #fff;
  padding-bottom: 0.5rem;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr; /* Default: single column */
  gap: 1.25rem;
}

.content-grid.with-voting {
  grid-template-columns: 2fr 1fr; /* Two columns when voting */
}

.chat-column {
  min-height: calc(100vh - 260px);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.main-content :deep(.voting-panel) {
  align-self: start;
  position: sticky;
  top: 6.5rem; /* below sticky status */
  max-height: calc(100vh - 7.5rem);
  overflow: auto;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
  font-size: 1.5rem;
  color: #777;
}

.answer-section {
  margin-top: 2rem;
}

.submission-feedback {
  margin-top: 0.5rem;
  color: #2e7d32;
}

.answer-inactive {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  color: #555;
}

.round-summary {
  background-color: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.round-summary ul {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
}

.round-summary .end-reason {
  margin-top: 0.75rem;
  font-weight: bold;
  color: #c62828;
}

.host-feedback {
  margin-top: 0.5rem;
  color: #2e7d32;
}

.vote-feedback {
  margin-top: 1rem;
  color: #1565c0;
}

.phase-message {
  margin-bottom: 1rem;
  color: #37474f;
  font-size: 1rem;
}
</style>
