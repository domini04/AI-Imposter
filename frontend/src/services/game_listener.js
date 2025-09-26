import { db } from './firebase';
import { doc, onSnapshot, collection, query, orderBy } from 'firebase/firestore';

// This variable will hold the function to unsubscribe from the current listener.
// This ensures we only have one active game listener at a time.
let activeGameListener = null;
let activeMessagesListener = null;

/**
 * Subscribes to real-time updates for a specific game document in Firestore.
 *
 * @param {string} gameId - The ID of the game to listen to.
 * @param {function} callback - The function to call with the new game data whenever it changes.
 *                              It will be called with null if the document is deleted.
 */
export const subscribeToGame = (gameId, callback) => {
  // If there's already an active listener, unsubscribe from it before starting a new one.
  if (activeGameListener) {
    console.log('Unsubscribing from previous game listener.');
    activeGameListener();
  }

  console.log(`Subscribing to real-time updates for game: ${gameId}`);
  
  // Get a reference to the specific game document.
  const gameDocRef = doc(db, 'game_rooms', gameId);

  // onSnapshot returns an unsubscribe function. We store it in our activeListener variable.
  activeGameListener = onSnapshot(
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
  if (activeGameListener) {
    console.log('Unsubscribing from active game listener.');
    activeGameListener();
    activeGameListener = null;
  }
};

/**
 * Subscribes to real-time updates for the messages subcollection of a game.
 *
 * @param {string} gameId - The ID of the game whose messages to listen to.
 * @param {function} callback - The function to call with the array of messages.
 */
export const subscribeToMessages = (gameId, callback) => {
  if (activeMessagesListener) {
    activeMessagesListener();
  }

  const messagesRef = collection(db, 'game_rooms', gameId, 'messages');
  const messagesQuery = query(messagesRef, orderBy('timestamp', 'asc'));

  activeMessagesListener = onSnapshot(
    messagesQuery,
    (querySnapshot) => {
      const messages = [];
      querySnapshot.forEach((doc) => {
        messages.push({ id: doc.id, ...doc.data() });
      });
      callback(messages);
    },
    (error) => {
      console.error(`Error listening to messages for game ${gameId}:`, error);
      callback([]);
    }
  );
};

/**
 * Unsubscribes from the currently active messages listener.
 */
export const unsubscribeFromMessages = () => {
  if (activeMessagesListener) {
    console.log('Unsubscribing from active messages listener.');
    activeMessagesListener();
    activeMessagesListener = null;
  }
};
