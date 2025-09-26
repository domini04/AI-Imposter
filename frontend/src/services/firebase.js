// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth, signInAnonymously, onAuthStateChanged } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: import.meta.env.VITE_API_KEY,
  authDomain: import.meta.env.VITE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_APP_ID,
  measurementId: import.meta.env.VITE_MEASUREMENT_ID
};

// To find the firebaseConfig object for your project:
// 1. Go to your Firebase project console.
// 2. In the left-hand menu, click the gear icon and select "Project settings".
// 3. Under the "General" tab, scroll down to the "Your apps" section.
// 4. In the code snippet for your web app, you will find the `firebaseConfig` object.

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize and export Firebase services
const auth = getAuth(app);
const db = getFirestore(app);

/**
 * Signs the user in anonymously if they are not already signed in.
 * This function is idempotent, meaning it's safe to call multiple times.
 * @returns {Promise<User|null>} A promise that resolves with the user object or null on error.
 */
const signIn = async () => {
  // onAuthStateChanged is the recommended way to get the current user.
  // We use a Promise to wait for the initial state to be determined.
  const user = await new Promise((resolve, reject) => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      unsubscribe(); // Stop listening after we get the first status
      resolve(user);
    }, reject);
  });

  // If a user is already logged in, we don't need to do anything else.
  if (user) {
    return user;
  }

  // If no user, sign them in anonymously.
  try {
    const userCredential = await signInAnonymously(auth);
    return userCredential.user;
  } catch (error) {
    console.error("Error signing in anonymously:", error);
    return null; // Handle the error gracefully
  }
};

/**
 * A utility function to safely get the current user's authentication state.
 * @returns {Promise<User|null>} A promise that resolves with the current user object, or null if not logged in.
 */
const getCurrentUser = () => {
  return new Promise((resolve, reject) => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      unsubscribe();
      resolve(user);
    }, reject);
  });
};

export { auth, db, signIn, getCurrentUser };
