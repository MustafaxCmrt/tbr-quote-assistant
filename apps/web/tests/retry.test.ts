import assert from "node:assert/strict";
import test from "node:test";
import { initialStream, type Source } from "../src/contracts";
import { emptyAnswerLabel, visibleAttemptContent } from "../src/api/retry";

test("web retry keeps previous text and citations through reconnect and early error", () => {
  const source: Source = { kind: "knowledge", source_id: "K-1", title: "İade", excerpt: "Önceki kaynak", source: "demo" };
  const previous = { text: "Önceki kısmi yanıt", sources: [source] };
  for (const status of ["connecting", "streaming", "error"] as const) {
    const next = { ...previous, ...visibleAttemptContent({ ...initialStream("s", "m"), status }) };
    assert.deepEqual(next, previous);
  }
});

test("web retry replaces text with the new attempt; a finished empty answer clears it", () => {
  const previous = { text: "Önceki yanıt", sources: [] as Source[] };
  const state = { ...initialStream("s", "m"), text: "Yeni parça", status: "streaming" as const };
  assert.deepEqual({ ...previous, ...visibleAttemptContent(state) }, { text: "Yeni parça", sources: [] });
  assert.deepEqual({ ...previous, ...visibleAttemptContent({ ...state, text: "", status: "done" }) }, { text: "", sources: [] });
});

test("an empty finished answer is labelled finished, not processing", () => {
  assert.equal(emptyAnswerLabel("done"), "Yanıt tamamlandı.");
  assert.equal(emptyAnswerLabel("completed"), "Yanıt tamamlandı.");
  assert.equal(emptyAnswerLabel("connecting"), "İstek işleniyor…");
  assert.equal(emptyAnswerLabel("streaming"), "İstek işleniyor…");
  assert.equal(emptyAnswerLabel("error", "Akış kesildi."), "Yanıt alınamadı.");
});
