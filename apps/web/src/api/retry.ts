import type { StreamState } from "../contracts";

/** Keep the previous answer until this attempt supplies replacement text.
 * Sources change with that text so a failed reconnect cannot erase its citations. */
export function visibleAttemptContent(
  state: StreamState,
): Partial<Pick<StreamState, "text" | "sources">> {
  return state.text || state.status === "done"
    ? { text: state.text, sources: state.sources }
    : {};
}

/** Placeholder for an answer without text; a finished attempt is never "processing". */
export function emptyAnswerLabel(status: string, error?: string): string {
  if (error) return "Yanıt alınamadı.";
  return status === "done" || status === "completed" ? "Yanıt tamamlandı." : "İstek işleniyor…";
}
