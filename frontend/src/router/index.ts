import { createRouter, createWebHistory } from 'vue-router'
import LobbyView from '../views/LobbyView.vue'
import GameRoomView from '../views/GameRoomView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Lobby',
      component: LobbyView
    },
    {
      path: '/game/:id',
      name: 'GameRoom',
      component: GameRoomView
    }
  ]
})

export default router
