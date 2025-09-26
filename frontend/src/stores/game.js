import { defineStore } from 'pinia';
import * as api from '@/services/api';

export const useGameStore = defineStore('game', {
  /**
   * Defines the initial state of the store.
   */
  state: () => ({
    /** @type {Array<Object>} A list of public games available to join. */
    publicGames: [],
    /** @type {Object|null} The full real-time state of the current game. */
    currentGame: null,
    /** @type {boolean} A flag to indicate when an API call is in progress. */
    isLoading: false,
  }),

  /**
   * Defines computed properties based on the state.
   */
  getters: {
    /**
     * A convenience getter to check if the user is currently in a game.
     * @param {object} state - The store's state.
     * @returns {boolean} True if the user is in a game, false otherwise.
     */
    isInGame: (state) => state.currentGame !== null,
  },

  /**
   * Defines methods that can be called to interact with the store and perform actions,
   * such as fetching data from the backend.
   */
  actions: {
    /**
     * Fetches the list of public games from the backend and updates the state.
     */
    async fetchPublicGames() {
      this.isLoading = true;
      try {
        const games = await api.getPublicGames();
        this.publicGames = games;
      } catch (error) {
        console.error('Failed to fetch public games:', error);
        // Here you might want to set an error state to show a message in the UI
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Creates a new game.
     * @param {object} settings - The settings for the new game.
     * @returns {Promise<string|null>} The ID of the new game, or null on failure.
     */
    async createGame(settings) {
      this.isLoading = true;
      try {
        const response = await api.createGame(settings);
        // We expect the backend to return an object with a gameId
        return response.gameId;
      } catch (error) {
        console.error('Failed to create game:', error);
        return null;
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Joins an existing game.
     * @param {string} gameId - The ID of the game to join.
     * @returns {Promise<boolean>} True on success, false on failure.
     */
    async joinGame(gameId) {
      this.isLoading = true;
      try {
        await api.joinGame(gameId);
        return true;
      } catch (error) {
        console.error('Failed to join game:', error);
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Starts the current game (host only).
     */
    async startGame() {
      if (!this.currentGame) return;
      this.isLoading = true;
      try {
        await api.startGame(this.currentGame.gameId);
      } catch (error) {
        console.error('Failed to start game:', error);
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Casts a vote for a player.
     * @param {string} votedForId - The UID of the player to vote for.
     */
    async castVote(votedForId) {
        if (!this.currentGame) return;
        // No need to set isLoading for a quick action like voting
        try {
            await api.castVote(this.currentGame.gameId, votedForId);
        } catch (error) {
            console.error('Failed to cast vote:', error);
        }
    },

    /**
     * Used by the Firestore listener to update the current game state.
     * @param {object} gameData - The latest game data from Firestore.
     */
    setCurrentGame(gameData) {
      this.currentGame = gameData;
    },

    /**
     * Resets the current game state when a player leaves a game.
     */
    leaveGame() {
      this.currentGame = null;
    },
  },
});
