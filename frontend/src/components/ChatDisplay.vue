<script setup>
import { computed } from 'vue';

const props = defineProps({
  messages: {
    type: Array,
    required: true,
  },
  players: {
    type: Array,
    required: true,
  }
});

// We group messages by round number for structured display
const groupedMessages = computed(() => {
  const groups = {};
  for (const message of props.messages) {
    const round = message.roundNumber || 0;
    if (!groups[round]) {
      groups[round] = [];
    }
    const senderId = message.senderId || message.authorId;
    const player = props.players.find(p => p.uid === senderId);
    groups[round].push({
      ...message,
      senderName: player ? player.gameDisplayName : (message.senderName || 'Unknown'),
      text: message.text || message.content || '',
    });
  }
  return groups;
});
</script>

<template>
  <div class="chat-display">
    <div v-if="!messages.length" class="empty-chat">
      <p>The conversation will appear here once the round begins.</p>
    </div>
    
    <div v-else class="chat-content">
      <div v-for="(roundMessages, roundNumber) in groupedMessages" :key="roundNumber" class="round-group">
        <h3 class="round-header">Round {{ roundNumber }}</h3>
        <div v-for="message in roundMessages" :key="message.id" class="message">
          <strong class="sender-name">{{ message.senderName }}:</strong>
          <p class="message-text">{{ message.text }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-display {
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 1.5rem;
  flex-grow: 1; /* Allows it to take up available space */
  overflow-y: auto; /* Adds scrolling for long chats */
  height: 500px; /* Example height */
}

.empty-chat {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #888;
}

.round-group {
  margin-bottom: 2rem;
}

.round-header {
  font-size: 1.2rem;
  color: #007bff;
  border-bottom: 2px solid #007bff;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.message {
  margin-bottom: 1rem;
}

.sender-name {
  font-weight: bold;
  color: #333;
}

.message-text {
  margin: 0.25rem 0 0 0;
  padding-left: 1rem; /* Indent message text */
  white-space: pre-wrap;
}
</style>
