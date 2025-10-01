<script setup>
defineProps({
  players: {
    type: Array,
    required: true,
  },
  hostId: {
    type: String,
    required: true,
  },
  status: {
    type: String,
    required: true,
  },
  currentUserId: {
    type: String,
    default: null,
  },
});
</script>

<template>
  <aside class="player-list-container">
    <h3>Players ({{ players.length }})</h3>
    <ul class="player-list">
      <li v-for="(player, index) in players" :key="player.uid" class="player-item">
        <span
          class="player-name"
          :class="{ 'current-user': player.uid === currentUserId }"
        >
          <template v-if="status === 'waiting'">
            Player {{ index + 1 }}
          </template>
          <template v-else>
            {{ player.gameDisplayName }}
          </template>
        </span>
        <span
          v-if="status === 'waiting' && player.uid === hostId"
          class="host-tag"
          title="Game Host"
        >
          👑
        </span>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.player-list-container {
  background-color: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
}

.player-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.player-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  font-size: 1.1rem;
}

.player-item:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}

.host-tag {
  font-size: 1.2rem;
}

.current-user {
  color: #0d47a1;
  font-weight: bold;
}
</style>
