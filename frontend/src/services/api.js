import { getCurrentUser } from './firebase.js';

// The base URL for your FastAPI backend.
// It's best practice to use environment variables for this.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * A helper function to get the Firebase Auth ID token from the current user.
 * This token is required to authenticate with our secure backend.
 * @returns {Promise<string|null>} The ID Token, or null if no user is signed in.
 */
const getAuthToken = async () => {
  const user = await getCurrentUser();
  if (!user) {
    console.error("API request failed: No user is signed in.");
    return null;
  }
  try {
    return await user.getIdToken();
  } catch (error) {
    console.error("Error getting auth token:", error);
    return null;
  }
};

/**
 * A generic, centralized request handler for all API calls to the backend.
 * It automatically handles adding the Authorization header.
 * @param {string} endpoint - The API endpoint to call (e.g., '/games').
 * @param {string} method - The HTTP method (e.g., 'GET', 'POST').
 * @param {object} [body] - The request body for 'POST' or 'PUT' requests.
 * @returns {Promise<any>} The JSON response from the API.
 */
const request = async (endpoint, method, body) => {
  const token = await getAuthToken();
  if (!token) {
    // If we can't get a token, we can't make an authenticated request.
    throw new Error("Authentication token is not available.");
  }

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  const config = {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    // Try to parse a JSON error response from the backend, otherwise use status text.
    const errorData = await response.json().catch(() => ({ message: response.statusText }));
    // FastAPI often puts the error message in a 'detail' field.
    throw new Error(errorData.detail || errorData.message || 'API request failed');
  }

  // Handle responses with no content (like a 204 No Content).
  if (response.status === 204) {
    return null;
  }

  return response.json();
};


// ============================================================================
//                          Exported API Functions
// ============================================================================
// Each function corresponds to an endpoint in the backend API.
// ============================================================================


// --- Game Management ---

/**
 * Fetches a list of all public, joinable games from the backend.
 * @returns {Promise<Array>} A promise that resolves to an array of game objects.
 */
export const getPublicGames = () => {
  return request('/api/v1/games', 'GET');
};

export const getModels = () => {
  return request('/api/v1/models', 'GET');
};

/**
 * Sends a request to the backend to create a new game.
 * @param {object} settings - The configuration for the new game.
 * @param {string} settings.language - The language ('en' or 'ko').
 * @param {number} settings.aiCount - The number of AI players.
 * @param {string} settings.privacy - The privacy setting ('public' or 'private').
 * @returns {Promise<object>} A promise that resolves to the new game's data.
 */
export const createGame = (settings) => {
  return request('/api/v1/games', 'POST', settings);
};

/**
 * Sends a request for the current user to join a specific game.
 * @param {string} gameId - The ID of the game to join.
 * @returns {Promise<object>} A promise that resolves on successful join.
 */
export const joinGame = (gameId) => {
  return request(`/api/v1/games/${gameId}/join`, 'POST');
};

// --- In-Game Actions ---

/**
 * Sends a request to start the game (host only).
 * @param {string} gameId - The ID of the game to start.
 * @returns {Promise<null>} A promise that resolves when the game has started.
 */
export const startGame = (gameId) => {
  return request(`/api/v1/games/${gameId}/start`, 'POST');
};

/**
 * Submits a vote for a player during the voting phase.
 * @param {string} gameId - The ID of the current game.
 * @param {string} votedForId - The UID of the player being voted for.
 * @returns {Promise<object>} A promise that resolves on successful vote.
 */
export const castVote = (gameId, votedForId) => {
  return request(`/api/v1/games/${gameId}/vote`, 'POST', { votedForId });
};

export const submitAnswer = (gameId, answer) => {
  return request(`/api/v1/games/${gameId}/submit-answer`, 'POST', { answer });
};

export const tallyAnswers = (gameId) => {
  return request(`/api/v1/games/${gameId}/tally-answers`, 'POST');
};

export const tallyVotes = (gameId) => {
  return request(`/api/v1/games/${gameId}/tally-votes`, 'POST');
};
