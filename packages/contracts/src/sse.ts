/** Transport parser only; JSON/domain validation belongs to the consumer. */
export interface SseEvent {
  event: string;
  data: string;
  id?: string;
}

/** Each stream owns one instance. No network, UI, or application dependencies. */
export function createSseParser() {
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let line = "";
  let skipLf = false;
  let event = "";
  let data: string[] = [];
  let id: string | undefined;
  let finished = false;

  function consume(text: string): SseEvent[] {
    const events: SseEvent[] = [];
    function endLine() {
      if (line === "") {
        if (data.length > 0) {
          events.push({ event: event || "message", data: data.join("\n"), ...(id !== undefined ? { id } : {}) });
        }
        event = "";
        data = [];
      } else if (!line.startsWith(":")) {
        const colon = line.indexOf(":");
        const field = colon < 0 ? line : line.slice(0, colon);
        let value = colon < 0 ? "" : line.slice(colon + 1);
        if (value.startsWith(" ")) value = value.slice(1);
        if (field === "event") event = value;
        if (field === "data") data.push(value);
        if (field === "id" && !value.includes("\0")) id = value;
      }
      line = "";
    }
    for (const character of text) {
      if (skipLf) {
        skipLf = false;
        if (character === "\n") continue;
      }
      if (character === "\r") {
        endLine();
        skipLf = true;
      } else if (character === "\n") {
        endLine();
      } else {
        line += character;
      }
    }
    return events;
  }

  return {
    push(chunk: Uint8Array): SseEvent[] {
      if (finished) throw new Error("SSE ayrıştırıcısı kapatıldı.");
      return consume(decoder.decode(chunk, { stream: true }));
    },
    finish(): SseEvent[] {
      if (finished) return [];
      finished = true;
      const events = consume(decoder.decode());
      // EOF never completes a frame: an event requires a terminating blank line.
      line = "";
      data = [];
      event = "";
      return events;
    },
  };
}
