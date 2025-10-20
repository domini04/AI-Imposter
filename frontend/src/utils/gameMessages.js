/**
 * Game UI Message Utilities
 *
 * This module provides functions to derive user-facing messages from game state enums.
 * Keeps presentation logic in the frontend instead of storing messages in the database.
 *
 * Benefits:
 * - Clean separation: Data warehouse stores only analytical data
 * - Easy to update: Change UI text without database migrations
 * - i18n ready: Can add language support without backend changes
 */

/**
 * Map of end condition enums to user-facing messages.
 * These match the backend enum values in GameResultLastRound.endCondition
 */
export const END_REASON_MESSAGES = {
  all_impostors_eliminated: 'All impostors have been eliminated. Humans win!',
  max_rounds_reached: 'Maximum rounds reached with surviving impostors. AI win.'
}

/**
 * Get user-facing message for a game end condition.
 *
 * @param {string} endCondition - The end condition enum value
 * @returns {string} User-facing message to display
 *
 * @example
 * getEndReasonMessage('all_impostors_eliminated')
 * // Returns: 'All impostors have been eliminated. Humans win!'
 */
export function getEndReasonMessage(endCondition) {
  return END_REASON_MESSAGES[endCondition] || 'Game over.'
}
