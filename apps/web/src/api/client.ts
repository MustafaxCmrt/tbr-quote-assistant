import { createSseParser, parseChatEvent, type ChatEvent } from "../contracts";
export const base = (import.meta.env.VITE_API_BASE_URL ?? "").replace(
  /\/$/,
  "",
);
export class ApiError extends Error {
  fields: Record<string, string>;
  constructor(message: string, fields: Record<string, string> = {}) {
    super(message);
    this.fields = fields;
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(base + path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
      signal: options.signal ?? AbortSignal.timeout(10000),
    });
  } catch {
    throw new ApiError(
      "Sunucuya ulaşılamadı. Bağlantıyı kontrol edip tekrar dene.",
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const fields: Record<string, string> = {};
    if (Array.isArray(body.detail))
      for (const field of body.detail)
        fields[String(field.loc?.[1] ?? "form")] =
          "Bu alanın biçimini ve sınırlarını kontrol et.";
    throw new ApiError(
      body.error?.detail ??
        "Bilgiler kaydedilemedi. İşaretli alanları kontrol et.",
      fields,
    );
  }
  return response.status === 204
    ? (undefined as T)
    : ((await response.json()) as T);
}
export async function stream(
  body: object,
  signal: AbortSignal,
  receive: (event: ChatEvent) => void,
) {
  const response = await fetch(base + "/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(body),
    signal,
  });
  if (
    !response.ok ||
    !response.body ||
    !response.headers.get("content-type")?.includes("text/event-stream")
  )
    throw new ApiError("Sohbet akışı açılamadı. Aynı mesajla tekrar dene.");
  const parser = createSseParser();
  const reader = response.body.getReader();
  let terminal = false;
  try {
    while (!terminal) {
      const next = await reader.read();
      if (next.done) break;
      for (const wire of parser.push(next.value)) {
        const event = parseChatEvent(wire);
        receive(event);
        if (event.type === "done" || event.type === "error") {
          terminal = true;
          break;
        }
      }
    }
    parser.finish();
    if (!terminal)
      throw new ApiError(
        "Bağlantı tamamlanmadan kesildi. Aynı mesajla tekrar dene.",
      );
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}
export const money = (value: string) =>
  new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(
    Number(value),
  );
export const categories: Record<string, string> = {
  barcode_scanner: "Barkod okuyucu",
  pos_terminal: "El terminali",
  receipt_printer: "Fiş yazıcı",
  label_printer: "Etiket yazıcı",
  software: "Yazılım",
  accessory: "Aksesuar",
  service: "Hizmet",
  bundle: "Kit",
};
export const topics: Record<string, string> = {
  return_policy: "İade",
  delivery_policy: "Teslimat",
  warranty: "Garanti",
  quote_validity: "Teklif geçerliliği",
  discount_policy: "İndirim",
  stock_rule: "Stok",
  service_policy: "Hizmet",
  compatibility: "Uyumluluk",
  quote_idempotency: "Tekrarlı istek",
  price_ceiling: "Fiyat limiti",
  fallback: "Yedek mod",
};
