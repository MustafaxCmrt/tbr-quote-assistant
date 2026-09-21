import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, stream } from "../api/client";
import { initialStream, reduceChatEvent, type Source } from "../contracts";
interface Message {
  id: string;
  user: string;
  text: string;
  sources: Source[];
  status: string;
  error?: string;
}
interface History {
  message_id: string;
  body: string;
  status: string;
  final_response: { text: string; sources: Source[] } | null;
}
export function ChatPanel({
  quoteId,
  customerId,
  refresh,
  onBusy,
}: {
  quoteId: string;
  customerId: string;
  refresh: () => void;
  onBusy: (busy: boolean) => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [session, setSession] = useState("");
  const [error, setError] = useState("");
  const active = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let live = true;
    setMessages([]);
    setSession("");
    setError("");
    const saved = localStorage.getItem("tbr-session:" + quoteId);
    if (saved)
      api<History[]>("/api/chat/sessions/" + saved + "/messages")
        .then((rows) => {
          if (live) {
            setSession(saved);
            setMessages(
              rows.map((r) => ({
                id: r.message_id,
                user: r.body,
                text: r.final_response?.text ?? "",
                sources: r.final_response?.sources ?? [],
                status: r.status,
                error: r.status === "failed"
                  ? "Önceki istek tamamlanamadı. Teklifi kontrol edip aynı mesajla tekrar deneyebilirsin."
                  : undefined,
              })),
            );
          }
        })
        .catch(() => {
          if (live) localStorage.removeItem("tbr-session:" + quoteId);
        });
    return () => {
      live = false;
      active.current?.abort();
    };
  }, [quoteId]);
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "nearest" });
  }, [messages]);
  async function send(user: string, id: string = crypto.randomUUID()) {
    if (active.current || !user.trim()) return;
    const controller = new AbortController();
    active.current = controller;
    setBusy(true);
    onBusy(true);
    setError("");
    const timer = setTimeout(() => controller.abort(), 45000);
    setMessages((prev) => [
      ...prev.filter((m) => m.id !== id),
      { id, user, text: "", sources: [], status: "processing" },
    ]);
    setText("");
    try {
      let currentSession = session;
      if (!currentSession) {
        const result = await api<{ session_id: string }>("/api/chat/sessions", {
          method: "POST",
          body: JSON.stringify({
            customer_id: customerId,
            quote_id: quoteId,
            channel: "web",
          }),
        });
        currentSession = result.session_id;
        setSession(currentSession);
        localStorage.setItem("tbr-session:" + quoteId, currentSession);
      }
      let state = initialStream(currentSession, id);
      await stream(
        {
          session_id: currentSession,
          quote_id: quoteId,
          message_id: id,
          message: user,
          channel: "web",
        },
        controller.signal,
        (event) => {
          state = reduceChatEvent(state, event);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === id
                ? {
                    ...m,
                    text: state.text,
                    sources: state.sources,
                    status: state.status,
                    error: state.error,
                  }
                : m,
            ),
          );
          if (
            state.needsRefetch &&
            (event.type === "tool_call_result" ||
              event.type === "done" ||
              event.type === "error")
          )
            refresh();
        },
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id
            ? {
                ...m,
                status: "error",
                error:
                  "Akış kesildi. İşlem kaydedilmiş olabilir; teklif yenilendi. Aynı mesajla tekrar deneyebilirsin.",
              }
            : m,
        ),
      );
    } finally {
      clearTimeout(timer);
      active.current = null;
      setBusy(false);
      onBusy(false);
      refresh();
    }
  }
  function submit(e: FormEvent) {
    e.preventDefault();
    void send(text.trim());
  }
  return (
    <section className="chat-panel">
      <div className="section-head">
        <h2>Teklif asistanı</h2>
        <span className="tag">Kaynaklı yedek mod</span>
      </div>
      <p className="muted">
        Ürün ekle, miktarı güncelle veya bir politika sor.
      </p>
      <div
        className="conversation"
        aria-live="polite"
        aria-relevant="additions text"
      >
        {!messages.length && (
          <div className="empty">
            <h3>Bu teklif için ne yapalım?</h3>
            <p>Örneğin, “9.000 TL altında kablosuz QR okuyucu ekle.”</p>
            <button
              className="secondary"
              onClick={() =>
                setText("İade süresi nedir ve teklifimde hangi ürün var?")
              }
            >
              İade koşullarını sor
            </button>
          </div>
        )}
        {messages.map((m) => (
          <article className="exchange" key={m.id}>
            <p className="user-message">{m.user}</p>
            <div className="assistant-message">
              <p className="preserve">{m.text || (m.error ? "Yanıt alınamadı." : "İstek işleniyor…")}</p>
              {m.error && (
                <p role="alert" className="error-text">
                  {m.error}
                </p>
              )}
              {m.sources.length > 0 && (
                <details>
                  <summary>Kaynaklar ({m.sources.length})</summary>
                  <ul className="sources">
                    {m.sources.map((s) => (
                      <li key={s.kind + ":" + s.source_id}>
                        <strong>{s.title}</strong>
                        <small>
                          {
                            {
                              product: "Ürün",
                              knowledge: "Bilgi",
                              price_rule: "Fiyat kuralı",
                            }[s.kind]
                          }{" "}
                          · {s.source_id}
                        </small>
                        <p className="preserve">{s.excerpt}</p>
                        <small>{s.source}</small>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
              {!busy && (
                <button
                  className="text-button"
                  onClick={() => void send(m.user, m.id)}
                >
                  {m.status === "error"
                    ? "Aynı mesajla tekrar dene"
                    : "Tekrar gönder (aynı istek)"}
                </button>
              )}
            </div>
          </article>
        ))}
        <div ref={bottom} />
      </div>
      {error && <p role="alert">{error}</p>}
      <form className="composer" onSubmit={submit}>
        <label htmlFor="chat-message">Mesajın</label>
        <textarea
          id="chat-message"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={2000}
          rows={3}
          placeholder="Ürün veya teklif hakkında yaz…"
          disabled={busy}
        />
        <div className="composer-actions">
          <small>{text.length}/2000</small>
          {busy ? (
            <button
              type="button"
              className="secondary"
              onClick={() => active.current?.abort()}
            >
              Akışı durdur
            </button>
          ) : (
            <button disabled={!text.trim()}>Gönder</button>
          )}
        </div>
      </form>
    </section>
  );
}
