import { Component, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { api } from "./api/client";
import { acceptQuote } from "./api/state";
import type { Quote } from "./contracts";
import { QuotePanel } from "./features/QuotePanel";
import { ChatPanel } from "./features/ChatPanel";
import { Catalog } from "./features/Catalog";
import { Logs } from "./features/Logs";
import logo from "./assets/bluered-logo.png";
import "./style.css";
interface Customer {
  customer_id: string;
  name: string;
  city: string;
  price_tier: string;
}
interface QuoteSummary {
  quote_id: string;
  version: number;
}
type Page = "quote" | "products" | "knowledge" | "logs";
function App() {
  const [page, setPage] = useState<Page>("quote");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customer, setCustomer] = useState("");
  const [quotes, setQuotes] = useState<QuoteSummary[]>([]);
  const [quoteId, setQuoteId] = useState("");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [error, setError] = useState("");
  const [stale, setStale] = useState(false);
  const [updated, setUpdated] = useState("");
  const [busy, setBusy] = useState(false);
  const selected = useRef("");
  selected.current = quoteId;
  useEffect(() => {
    api<Customer[]>("/api/customers")
      .then((rows) => {
        setCustomers(rows);
        setCustomer(rows[0]?.customer_id ?? "");
      })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    let live = true;
    setQuoteId("");
    setQuote(null);
    setQuotes([]);
    if (customer)
      api<QuoteSummary[]>(
        "/api/quotes?customer_id=" + encodeURIComponent(customer),
      )
        .then((rows) => {
          if (live) {
            setQuotes(rows);
            setQuoteId(rows[0]?.quote_id ?? "");
          }
        })
        .catch((e) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [customer]);
  const refresh = useCallback(() => {
    const id = selected.current;
    if (!id) return;
    void api<Quote>("/api/quotes/" + encodeURIComponent(id))
      .then((fresh) => {
        if (selected.current !== id) return;
        setQuote((prev) => acceptQuote(prev, fresh, selected.current));
        setStale(false);
        setUpdated(new Date().toLocaleTimeString("tr-TR"));
      })
      .catch(() => {
        if (selected.current === id) setStale(true);
      });
  }, []);
  useEffect(() => {
    setQuote(null);
    refresh();
    const timer = setInterval(() => {
      if (document.visibilityState === "visible") refresh();
    }, 2500);
    window.addEventListener("focus", refresh);
    return () => {
      clearInterval(timer);
      window.removeEventListener("focus", refresh);
    };
  }, [quoteId, refresh]);
  const changePage = (next: Page) => {
    if (busy) return;
    setPage(next);
  };
  return (
    <div className="app-shell">
      <a className="skip" href="#workspace">
        İçeriğe geç
      </a>
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            changePage("quote");
          }}
          aria-label="The Blue Red ana sayfa"
        >
          <img src={logo} alt="The Blue Red" width="1192" height="215" />
        </a>
        <p className="workspace-name">Teklif asistanı</p>
        <nav aria-label="Ana gezinme">
          {(
            [
              ["quote", "Teklif & sohbet"],
              ["products", "Ürünler"],
              ["knowledge", "Bilgi bankası"],
              ["logs", "İşlem kayıtları"],
            ] as [Page, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              aria-current={page === key ? "page" : undefined}
              disabled={busy && page !== key}
              onClick={() => changePage(key)}
            >
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <strong>Tek kayıt, ortak teklif.</strong>
          <p>Web ve mobil aynı kayıtlı teklif üzerinden çalışır.</p>
          <small>Yerel demo ortamı</small>
        </div>
      </aside>
      <main id="workspace">
        <header className="context-bar">
          <label>
            Müşteri
            <select
              aria-label="Müşteri"
              value={customer}
              onChange={(e) => setCustomer(e.target.value)}
              disabled={busy}
            >
              {customers.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.name} · {c.city}
                </option>
              ))}
            </select>
          </label>
          <label>
            Teklif
            <select
              aria-label="Teklif"
              value={quoteId}
              onChange={(e) => setQuoteId(e.target.value)}
              disabled={busy}
            >
              {quotes.map((q) => (
                <option key={q.quote_id} value={q.quote_id}>
                  {q.quote_id}
                </option>
              ))}
            </select>
          </label>
          <span className={"connection " + (stale ? "warning" : "")}>
            {stale
              ? "Son kayıt gösteriliyor"
              : quote
                ? "Kayıt güncel"
                : "Bağlanıyor…"}
          </span>
        </header>
        <div className="workspace-body">
          {error && (
            <p role="alert" className="error-text">
              {error}{" "}
              <button className="secondary" onClick={() => location.reload()}>
                Tekrar bağlan
              </button>
            </p>
          )}
          {page === "quote" && (
            <>
              <div className="page-head">
                <div>
                  <h1>Teklif & sohbet</h1>
                  <p className="muted">
                    İhtiyacı yaz, kaynakları gör, kayıtlı teklifi takip et.
                  </p>
                </div>
                {quote && (
                  <span className="tag">{quote.quote_id} · Taslak</span>
                )}
              </div>
              <div className="work-grid">
                <QuotePanel
                  quote={quote}
                  stale={stale}
                  updated={updated}
                  refresh={refresh}
                />
                {quoteId && (
                  <ChatPanel
                    key={quoteId}
                    quoteId={quoteId}
                    customerId={customer}
                    refresh={refresh}
                    onBusy={setBusy}
                  />
                )}
              </div>
            </>
          )}
          {page === "products" && <Catalog key="products" kind="products" />}
          {page === "knowledge" && <Catalog key="knowledge" kind="knowledge" />}
          {page === "logs" && quoteId && (
            <Logs key={quoteId} quoteId={quoteId} />
          )}
        </div>
      </main>
    </div>
  );
}
/** A render fault must not leave a blank admin page; quote data stays on the server. */
class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <main id="workspace">
        <p role="alert">
          Ekran beklenmeyen bir hatayla durdu. Teklif ve katalog verileri sunucuda korunur.
        </p>
        <button type="button" onClick={() => window.location.reload()}>
          Sayfayı yenile
        </button>
      </main>
    );
  }
}
createRoot(document.getElementById("root")!).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
);
