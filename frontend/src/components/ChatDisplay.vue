<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  messages: {
    type: Array,
    required: true,
  },
  players: {
    type: Array,
    required: true,
  },
  hideSenderNameRounds: {
    type: Array,
    default: () => [],
  }
});

const messageOrderKeys = ref({});

const hiddenRounds = computed(() => {
  if (!Array.isArray(props.hideSenderNameRounds)) {
    return new Set();
  }
  return new Set(props.hideSenderNameRounds.map((round) => Number(round)));
});

const getMessageKey = (message, index) => {
  if (message.id) {
    return String(message.id);
  }

  const round = message.roundNumber ?? 0;
  const sender = message.senderId || message.authorId || 'anonymous';
  return `${round}-${sender}-${index}`;
};

watch(
  () => props.messages.map((msg, index) => getMessageKey(msg, index)),
  () => {
    const nextKeys = { ...messageOrderKeys.value };
    const activeKeys = new Set();

    props.messages.forEach((msg, index) => {
      const key = getMessageKey(msg, index);
      activeKeys.add(key);
      if (nextKeys[key] === undefined) {
        nextKeys[key] = Math.random();
      }
    });

    Object.keys(nextKeys).forEach((key) => {
      if (!activeKeys.has(key)) {
        delete nextKeys[key];
      }
    });

    messageOrderKeys.value = nextKeys;
  },
  { immediate: true }
);

// We group messages by round number for structured display
const groupedMessages = computed(() => {
  const groups = {};
  props.messages.forEach((message, index) => {
    const round = Number(message.roundNumber ?? 0);
    if (!groups[round]) {
      groups[round] = [];
    }

    const senderId = message.senderId || message.authorId;
    const player = props.players.find(p => p.uid === senderId);
    const key = getMessageKey(message, index);
    const orderKey = messageOrderKeys.value[key] ?? Math.random();

    groups[round].push({
      id: key,
      senderName: player ? player.gameDisplayName : (message.senderName || 'Unknown'),
      textLines: (message.text || message.content || '').split('\n'),
      hideSender: hiddenRounds.value.has(round),
      orderKey,
    });
  });

  Object.keys(groups).forEach((roundKey) => {
    const sorted = [...groups[roundKey]]
      .sort((a, b) => a.orderKey - b.orderKey)
      .map((message, sortedIndex) => ({
        ...message,
        displayIndex: sortedIndex + 1,
      }));
    groups[roundKey] = sorted;
  });

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
          <header class="answer-header">
            <strong class="answer-label">Answer {{ message.displayIndex }}</strong>
            <span v-if="!message.hideSender" class="sender-name">— {{ message.senderName }}</span>
          </header>
          <p
            v-for="(line, lineIndex) in message.textLines"
            :key="lineIndex"
            class="message-text"
          >
            {{ line }}
          </p>
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
  margin-bottom: 1.5rem;
  padding: 1rem;
  border-radius: 10px;
  background: linear-gradient(135deg, #ffffff 0%, #f5f9ff 100%);
  box-shadow: 0 2px 6px rgba(13, 71, 161, 0.08);
  border: 1px solid rgba(13, 71, 161, 0.08);
}

.message:first-of-type {
  margin-top: 0.5rem;
}

.answer-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.answer-label {
  display: inline-block;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #1565c0 0%, #1e88e5 100%);
  color: #fff;
  font-weight: 600;
  letter-spacing: 0.02rem;
  text-transform: uppercase;
  font-size: 0.85rem;
  box-shadow: 0 2px 4px rgba(21, 101, 192, 0.2);
}

.sender-name {
  font-weight: bold;
  color: #1a237e;
  font-size: 0.95rem;
}

.message-text {
  margin: 0;
  padding-left: 0.25rem;
  white-space: pre-wrap;
  line-height: 1.6;
  color: #334155;
}
</style>
