import { useEffect, useState } from "react";
import { api } from "../api/client";
interface Session {
  session_id: string;
  channel: string;
  created_at: string;
}
interface Log {
  log_id: number;
  message_id: string;
  attempt_id: string;
  tool_sequence: number;
  tool_name: string;
  success: boolean;
  duration_ms: number;
  replayed: boolean;
  mutation_applied: boolean;
  input: unknown;
  output: unknown;
  sources: unknown;
}
export function Logs({ quoteId }: { quoteId: string }) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [session, setSession] = useState("");
  const [logs, setLogs] = useState<Log[]>([]);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let live = true;
    api<Session[]>("/api/chat/sessions?quote_id=" + encodeURIComponent(quoteId))
      .then((rows) => {
        if (live) {
          setSessions(rows);
          setSession(rows[0]?.session_id ?? "");
        }
      })
      .catch((e) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [quoteId, reload]);
  useEffect(() => {
    let live = true;
    setError("");
    if (session)
      api<Log[]>("/api/tool-calls?session_id=" + session)
        .then((rows) => live && setLogs(rows))
        .catch((e) => live && setError(e.message));
    else setLogs([]);
    return () => {
      live = false;
    };
  }, [session, reload]);
  return (
    <>
      <div className="page-head">
        <div>
          <h1>İşlem kayıtları</h1>
          <p className="muted">
            Gerçek araç çağrıları, sonuçları ve tekrar denemeleri.
          </p>
        </div>
        <button className="secondary" onClick={() => setReload((v) => v + 1)}>
          Kayıtları yenile
        </button>
      </div>
      <label>
        Oturum
        <select value={session} onChange={(e) => setSession(e.target.value)}>
          <option value="">Oturum seç</option>
          {sessions.map((s) => (
            <option key={s.session_id} value={s.session_id}>
              {s.channel === "mobile" ? "Mobil" : "Web"} ·{" "}
              {new Date(s.created_at).toLocaleString("tr-TR")} ·{" "}
              {s.session_id.slice(0, 8)}
            </option>
          ))}
        </select>
      </label>
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
      {!logs.length && (
        <p className="empty">
          Bu oturumda henüz araç kaydı yok. Sohbetten bir mesaj gönder.
        </p>
      )}
      <div className="log-list">
        {logs.map((l) => (
          <details key={l.log_id} className="log-entry">
            <summary>
              <span>
                {l.tool_sequence}. {l.tool_name}
              </span>
              <span className={"tag " + (!l.success ? "warning" : "")}>
                {l.replayed
                  ? "Tekrar · değişiklik yok"
                  : l.mutation_applied
                    ? "Kaydedildi"
                    : l.success
                      ? "Okundu"
                      : "Hata"}
              </span>
              <small>{l.duration_ms} ms</small>
            </summary>
            {l.replayed && (
              <p>İkinci deneme algılandı; teklif tekrar değiştirilmedi.</p>
            )}
            <p className="wrap muted">
              Mesaj: {l.message_id}
              <br />
              Deneme: {l.attempt_id}
            </p>
            <h3>Girdi</h3>
            <pre>{JSON.stringify(l.input, null, 2)}</pre>
            <h3>Sonuç</h3>
            <pre>{JSON.stringify(l.output, null, 2)}</pre>
            <h3>Kaynaklar</h3>
            <pre>{JSON.stringify(l.sources, null, 2)}</pre>
          </details>
        ))}
      </div>
    </>
  );
}
