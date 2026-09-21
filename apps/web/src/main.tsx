import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

function App() {
  const [status, setStatus] = useState("Bağlantı kontrol ediliyor…");
  const [pending, setPending] = useState(false);
  async function check() {
    setPending(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? ""}/health/ready`, {
        signal: AbortSignal.timeout(5000),
      });
      setStatus(response.ok ? "Bağlantı hazır" : "Sistem henüz hazır değil");
    } catch {
      setStatus("Bağlantı kurulamadı. Tekrar deneyebilirsin.");
    } finally {
      setPending(false);
    }
  }
  useEffect(() => { void check(); }, []);
  return <main><p className="brand">THE BLUE RED</p><h1>Teklif asistanı</h1>
    <p>Yönetim ekranı hazırlanıyor.</p>
    <section aria-label="Bağlantı durumu"><p role="status">{status}</p>
      <button disabled={pending} onClick={() => void check()}>{pending ? "Kontrol ediliyor…" : "Bağlantıyı kontrol et"}</button>
    </section></main>;
}

createRoot(document.getElementById("root")!).render(<App />);
