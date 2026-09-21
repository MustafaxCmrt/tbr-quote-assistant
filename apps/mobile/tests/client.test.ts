import assert from "node:assert/strict";
import test from "node:test";
import { createClient, isSessionNotFound, type Transport } from "../src/api/client";
import { initialStream, reduceChatEvent, type ChatEvent } from "@tbr/contracts";

const envelope = (seq: number, type: string, payload: object) => ({
  schema_version: 1,
  session_id: "session",
  message_id: "message",
  attempt_id: "attempt",
  event_seq: seq,
  type,
  payload,
});
const done = envelope(3, "done", {
  success: true,
  quote_id: "Q-1",
  quote_version: 2,
  mode: "fallback",
  source_ids: [],
});
const wire = (events: object[]) =>
  new TextEncoder().encode(
    events
      .map(
        (e) =>
          `event: ${(e as { type: string }).type}\r\ndata: ${JSON.stringify(e)}\r\n\r\n`,
      )
      .join(""),
  );
function response(bytes: Uint8Array, step = 1) {
  return new Response(
    new ReadableStream({
      start(controller) {
        for (let i = 0; i < bytes.length; i += step)
          controller.enqueue(bytes.slice(i, i + step));
        controller.close();
      },
    }),
    { headers: { "Content-Type": "text/event-stream" } },
  );
}

test("native transport posts identity and decodes every UTF-8 byte before terminal done", async () => {
  const requests: RequestInit[] = [];
  const transport: Transport = async (_url, init) => {
    requests.push(init!);
    return response(
      wire([
        envelope(1, "message_start", { mode: "fallback" }),
        envelope(2, "text_delta", { text: "Bağlantı ğüşiöç" }),
        done,
      ]),
    );
  };
  const client = createClient("http://example.test/", transport);
  const body = {
    session_id: "session",
    message_id: "message",
    quote_id: "Q-1",
    message: "bir adet ekle",
    channel: "mobile",
  };
  let state = initialStream("session", "message");
  await client.stream(body, new AbortController().signal, (e) => {
    state = reduceChatEvent(state, e);
  });
  assert.equal(state.text, "Bağlantı ğüşiöç");
  assert.equal(state.status, "done");
  assert.equal(state.needsRefetch, true);
  await client.stream(body, new AbortController().signal, () => {});
  assert.equal(requests[0].method, "POST");
  assert.deepEqual(JSON.parse(String(requests[0].body)), body);
  assert.equal(
    requests[1].body,
    requests[0].body,
    "retry transport must not replace caller message ID",
  );
});

test("EOF without terminal rejects and preserves delivered partial text", async () => {
  const events: ChatEvent[] = [];
  const client = createClient("http://example.test", async () =>
    response(
      wire([
        envelope(1, "message_start", { mode: "fallback" }),
        envelope(2, "text_delta", { text: "Kısmi yanıt" }),
      ]),
      4096,
    ),
  );
  await assert.rejects(
    client.stream({}, new AbortController().signal, (e) => events.push(e)),
    /Akış kesildi/,
  );
  assert.equal(events.length, 2);
  assert.equal(events[1].type, "text_delta");
});

test("controlled error is terminal, malformed content and native hostname never escape", async () => {
  const error = envelope(2, "error", {
    code: "OUT_OF_STOCK",
    detail: "Stok yok.",
    retryable: false,
    committed: false,
    quote_id: "Q-1",
  });
  let state = initialStream("session", "message");
  await createClient("http://example.test", async () =>
    response(
      wire([envelope(1, "message_start", { mode: "fallback" }), error]),
      1024,
    ),
  ).stream({}, new AbortController().signal, (e) => {
    state = reduceChatEvent(state, e);
  });
  assert.equal(state.status, "error");
  assert.equal(state.error, "Stok yok.");
  assert.equal(state.needsRefetch, false);
  const failed = createClient("http://example.test", async () => {
    throw new Error("private-host.invalid secret-token");
  });
  await assert.rejects(
    failed.request("/api/customers"),
    (e) =>
      e instanceof Error &&
      !/private-host|secret-token/.test(e.message) &&
      e.message.includes("Sunucuya"),
  );
  await assert.rejects(
    createClient(
      "http://example.test",
      async () => new Response("<html>proxy</html>"),
    ).stream({}, new AbortController().signal, () => {}),
    /Akış açılamadı/,
  );
});

test("missing API address is reported as configuration, not as a network failure", async () => {
  let calls = 0;
  const client = createClient(undefined, async () => {
    calls += 1;
    return new Response("{}");
  });
  await assert.rejects(client.request("/api/customers"), /API bağlantısı ayarlanmamış/);
  await assert.rejects(
    client.stream({}, new AbortController().signal, () => {}),
    /API bağlantısı ayarlanmamış/,
  );
  await assert.rejects(
    createClient("example.test", async () => new Response("{}")).request("/api/customers"),
    /API bağlantısı ayarlanmamış/,
  );
  assert.equal(calls, 0);
});

test("unknown server session is distinguishable so the next retry can open a new one", async () => {
  const client = createClient("http://example.test", async () =>
    new Response(JSON.stringify({ error: { code: "QUOTE_CONTEXT_MISMATCH" } }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    }),
  );
  await assert.rejects(
    client.stream({}, new AbortController().signal, () => {}),
    (e) => isSessionNotFound(e) && /yeni oturum/.test((e as Error).message),
  );
  await assert.rejects(
    createClient("http://example.test", async () => new Response("{}", { status: 503 })).stream(
      {},
      new AbortController().signal,
      () => {},
    ),
    (e) => !isSessionNotFound(e) && /Akış açılamadı/.test((e as Error).message),
  );
});
