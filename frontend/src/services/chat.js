import { db } from './firebase';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';

export const submitPendingAnswer = async (gameId, { authorId, content, roundNumber }) => {
  const pendingRef = collection(db, 'game_rooms', gameId, 'pending_messages');

  await addDoc(pendingRef, {
    authorId,
    content,
    roundNumber,
    submittedAt: serverTimestamp(),
  });
};
