import type { StreamState } from '@tbr/contracts';

/** Keep the previous answer until this attempt supplies replacement text.
 * Sources change with that text so a failed reconnect cannot erase its citations. */
export function visibleAttemptContent(state: StreamState): Partial<Pick<StreamState, 'text' | 'sources'>> {
  return state.text || state.status === 'done'
    ? { text: state.text, sources: state.sources }
    : {};
}
