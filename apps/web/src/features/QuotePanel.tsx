import type { Quote, QuoteLine } from "../contracts";
import { money } from "../api/client";
export function QuotePanel({
  quote,
  stale,
  updated,
  refresh,
}: {
  quote: Quote | null;
  stale: boolean;
  updated: string;
  refresh: () => void;
}) {
  const rows = (items: QuoteLine[]) =>
    items.map((p) => (
      <tr key={p.quote_item_id}>
        <td>
          <strong>{p.name_tr}</strong>
          <small>{p.sku}</small>
          <span
            className={
              "tag " + (p.fulfillment_status === "in_stock" ? "" : "warning")
            }
          >
            {
              (
                {
                  in_stock: "Stoklu",
                  out_of_stock: "Stok dışı",
                  backorder: "Beklemeli",
                } as Record<string, string>
              )[p.fulfillment_status]
            }
          </span>
          {p.status !== "active" && (
            <small>
              {p.status === "replaced" ? "Değiştirildi" : "Kaldırıldı"}
            </small>
          )}
        </td>
        <td className="num">{p.quantity}</td>
        <td className="num">{money(p.unit_price_try)}</td>
        <td className="num">{money(p.gross_total_try)}</td>
        <td className="num">
          {money(p.discount_total_try)}
          {p.rule_ids.map((id) => (
            <small key={id}>{id}</small>
          ))}
        </td>
        <td className="num">
          <strong>{money(p.net_total_try)}</strong>
        </td>
      </tr>
    ));
  return (
    <section className="quote-panel">
      <div className="section-head">
        <h2>Teklif kalemleri</h2>
        <button className="secondary" onClick={refresh}>
          Yenile
        </button>
      </div>
      <p className={stale ? "error-text" : "muted"} role="status">
        {stale && "Bağlantı kesildi; son kayıtlı görünüm. Yenilemeyi dene. "}
        {quote
          ? `Sürüm ${quote.version} · Son başarılı kontrol ${updated}`
          : stale ? "Henüz kayıt alınamadı." : "Teklif yükleniyor…"}
      </p>
      {quote && (
        <>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Ürün</th>
                  <th>Adet</th>
                  <th>Birim</th>
                  <th>Brüt</th>
                  <th>İndirim</th>
                  <th>Net</th>
                </tr>
              </thead>
              <tbody>{rows(quote.items)}</tbody>
            </table>
            {quote.items.length === 0 && (
              <p className="empty">
                Bu teklif henüz boş. Sohbette bir ürün ekleyerek
                başlayabilirsin.
              </p>
            )}
          </div>
          <dl className="totals">
            <div>
              <dt>Brüt toplam</dt>
              <dd>{money(quote.gross_total_try)}</dd>
            </div>
            <div>
              <dt>İndirim</dt>
              <dd>− {money(quote.discount_total_try)}</dd>
            </div>
            <div className="net">
              <dt>Net teklif</dt>
              <dd>{money(quote.net_total_try)}</dd>
            </div>
          </dl>
          <p className="muted">
            Taslak teklif stok rezervasyonu yapmaz. Fiyatlar sunucudaki kayıtlı
            tekliften alınır.
          </p>
          {quote.rule_ids.length > 0 && (
            <details>
              <summary>Uygulanan fiyat kuralları</summary>
              <ul>
                {quote.rule_ids.map((id) => (
                  <li key={id}>{id}</li>
                ))}
              </ul>
              <p className="muted">
                Çakışmada tek ve en özel kural uygulanır; bu, firmanın kararı
                adaya bıraktığı belgelenmiş tercihtir.
              </p>
            </details>
          )}
          {quote.history.length > 0 && (
            <details>
              <summary>Kalem geçmişi ({quote.history.length})</summary>
              <div className="table-scroll">
                <table>
                  <tbody>{rows(quote.history)}</tbody>
                </table>
              </div>
            </details>
          )}
        </>
      )}
    </section>
  );
}
