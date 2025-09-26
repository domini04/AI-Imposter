import { db } from './firebase';
import { doc, onSnapshot } from 'firebase/firestore';

// This variable will hold the function to unsubscribe from the current listener.
// This ensures we only have one active game listener at a time.
let activeListener = null;

/**
 * Subscribes to real-time updates for a specific game document in Firestore.
 *
 * @param {string} gameId - The ID of the game to listen to.
 * @param {function} callback - The function to call with the new game data whenever it changes.
 *                              It will be called with null if the document is deleted.
 */
export const subscribeToGame = (gameId, callback) => {
  // If there's already an active listener, unsubscribe from it before starting a new one.
  if (activeListener) {
    console.log('Unsubscribing from previous game listener.');
    activeListener();
  }

  console.log(`Subscribing to real-time updates for game: ${gameId}`);
  
  // Get a reference to the specific game document.
  const gameDocRef = doc(db, 'game_rooms', gameId);

  // onSnapshot returns an unsubscribe function. We store it in our activeListener variable.
  activeListener = onSnapshot(
    gameDocRef,
    (docSnapshot) => {
      if (docSnapshot.exists()) {
        // If the document exists, call the callback with its data.
        // We also include the gameId for convenience.
        callback({ gameId: docSnapshot.id, ...docSnapshot.data() });
      } else {
        // If the document is deleted or doesn't exist, call back with null.
        console.warn(`Game document ${gameId} does not exist.`);
        callback(null);
      }
    },
    (error) => {
      console.error(`Error listening to game ${gameId}:`, error);
      // In case of an error, we might want to inform the user.
      callback(null);
    }
  );
};

/**
 * Unsubscribes from the currently active game listener.
 * This should be called when the component is unmounted to prevent memory leaks.
 */
export const unsubscribeFromGame = () => {
  if (activeListener) {
    console.log('Unsubscribing from active game listener.');
    activeListener();
    activeListener = null;
  }
};
