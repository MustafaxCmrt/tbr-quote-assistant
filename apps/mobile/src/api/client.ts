import {
  createSseParser,
  parseChatEvent,
  type ChatEvent,
} from "@tbr/contracts";

export type Transport = (
  url: string,
  init?: RequestInit,
) => Promise<Pick<Response, "ok" | "status" | "headers" | "body" | "json">>;

/** Transport is injected so byte framing and failures can be tested without a native bridge. */
export function createClient(
  baseUrl: string | undefined,
  transport: Transport,
) {
  const base = baseUrl?.trim().replace(/\/+$/, "");
  function address(path: string) {
    if (!base || !/^https?:\/\//.test(base))
      throw new Error(
        "API bağlantısı ayarlanmamış. Geliştirme ortamını kontrol et.",
      );
    return base + path;
  }
  async function request<T>(path: string, body?: object): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await transport(address(path), {
        method: body ? "POST" : "GET",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("request_failed");
      return (await response.json()) as T;
    } catch {
      // Native network exceptions may contain the private development hostname.
      throw new Error(
        "Sunucuya ulaşılamadı. Aynı ağı ve API bağlantısını kontrol edip yeniden dene.",
      );
    } finally {
      clearTimeout(timer);
    }
  }
  async function stream(
    body: object,
    signal: AbortSignal,
    receive: (event: ChatEvent) => void,
  ) {
    let response;
    try {
      response = await transport(address("/api/chat/stream"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(body),
        signal,
      });
    } catch {
      throw new Error("Akış açılamadı. Aynı mesajla tekrar deneyebilirsin.");
    }
    if (
      !response.ok ||
      !response.body ||
      !response.headers.get("content-type")?.includes("text/event-stream")
    ) {
      throw new Error("Akış açılamadı. Aynı mesajla tekrar deneyebilirsin.");
    }
    const parser = createSseParser();
    const reader = response.body.getReader();
    let terminal = false;
    try {
      while (!terminal) {
        const chunk = await reader.read();
        if (chunk.done) break;
        for (const wire of parser.push(chunk.value)) {
          const event = parseChatEvent(wire);
          receive(event);
          if (event.type === "done" || event.type === "error") {
            terminal = true;
            break;
          }
        }
      }
      parser.finish();
      if (!terminal) throw new Error("incomplete_stream");
    } catch {
      throw new Error(
        "Akış kesildi. İşlem kaydedilmiş olabilir; teklifi yenileyip aynı mesajla tekrar dene.",
      );
    } finally {
      await reader.cancel().catch(() => undefined);
      reader.releaseLock();
    }
  }
  return { request, stream };
}
