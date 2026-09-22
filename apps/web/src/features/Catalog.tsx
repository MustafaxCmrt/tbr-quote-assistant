import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError, categories, topics, money } from "../api/client";
import { TableScroll } from "./TableScroll";
interface RecordRow {
  product_id?: string;
  knowledge_id?: string;
  sku?: string;
  name_tr?: string;
  category?: string;
  price_try?: string;
  stock_qty?: number;
  topic?: string;
  title?: string;
  body?: string;
  source?: string;
}
export function Catalog({ kind }: { kind: "products" | "knowledge" }) {
  const isProduct = kind === "products";
  const [items, setItems] = useState<RecordRow[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("");
  const [inStock, setInStock] = useState(false);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [fields, setFields] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const params = new URLSearchParams({
      query,
      limit: "20",
      offset: String(offset),
    });
    if (filter) params.set(isProduct ? "category" : "topic", filter);
    if (inStock && isProduct) params.set("in_stock_only", "true");
    api<{ items: RecordRow[]; total: number }>("/api/" + kind + "?" + params, {
      signal: controller.signal,
    })
      .then((result) => {
        if (!controller.signal.aborted) {
          setItems(result.items);
          setTotal(result.total);
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [kind, isProduct, query, filter, inStock, offset, reload]);
  const changeQuery = (value: string) => {
    setQuery(value);
    setOffset(0);
  };
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    const data = new FormData(event.currentTarget);
    const val = (key: string) => String(data.get(key) ?? "").trim();
    setPending(true);
    setFields({});
    setError("");
    const payload = isProduct
      ? {
          sku: val("sku"),
          name_tr: val("name_tr"),
          category: val("category"),
          brand: val("brand"),
          price_try: val("price_try").replace(",", "."),
          stock_qty: Number(val("stock_qty")),
          min_order_qty: Number(val("min_order_qty")),
          delivery_days: Number(val("delivery_days")),
          warranty_months: Number(val("warranty_months")),
          tags: val("tags")
            .split(",")
            .map((x) => x.trim())
            .filter(Boolean),
          aliases: {
            tr: val("aliases")
              .split(",")
              .map((x) => x.trim())
              .filter(Boolean),
          },
          substitute_product_ids: val("substitute_product_ids")
            .split(",")
            .map((x) => x.trim())
            .filter(Boolean),
          notes: val("notes"),
        }
      : {
          topic: val("topic"),
          locale: "tr",
          title: val("title"),
          body: val("body"),
          source: val("source"),
          effective_from: val("effective_from"),
          applies_to: val("applies_to")
            .split(",")
            .map((x) => x.trim())
            .filter(Boolean),
        };
    try {
      await api("/api/" + kind, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setNotice(
        isProduct
          ? "Ürün kaydedildi; sohbet aramasında kullanılabilir."
          : "Bilgi kaydedildi; ilgili konu aramasında kullanılabilir.",
      );
      setForm(false);
      setOffset(0);
      setQuery("");
      setFilter("");
      setReload((r) => r + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Kayıt tamamlanamadı.");
      if (e instanceof ApiError) setFields(e.fields);
    } finally {
      setPending(false);
    }
  }
  // Inputs already carry `required`; the visual mark is hidden from screen readers.
  const title = (label: string, required = true) => (
    <span>
      {label}
      {required && (
        <span className="required-mark" aria-hidden="true">
          {" "}
          *
        </span>
      )}
    </span>
  );
  const field = (
    name: string,
    label: string,
    type = "text",
    initial = "",
    required = true,
  ) => (
    <label key={name}>
      {title(label, required)}
      <input
        name={name}
        type={type}
        defaultValue={initial}
        required={required}
        aria-invalid={!!fields[name]}
        aria-describedby={fields[name] ? name + "-error" : undefined}
        min={type === "number" ? 0 : undefined}
        step={type === "number" ? "1" : undefined}
      />
      {fields[name] && (
        <small className="error-text" id={name + "-error"}>
          {fields[name]}
        </small>
      )}
    </label>
  );
  return (
    <>
      <div className="page-head">
        <div>
          <h1>{isProduct ? "Ürünler" : "Bilgi bankası"}</h1>
          <p className="muted">
            {isProduct
              ? "Katalog, stok ve arama adları."
              : "Kaynaklı yanıtların dayandığı kayıtlar."}
          </p>
        </div>
        <button
          onClick={() => {
            setForm(!form);
            setError("");
          }}
        >
          {form ? "Formu kapat" : isProduct ? "Ürün ekle" : "Bilgi ekle"}
        </button>
      </div>
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
      {form && (
        <form className="editor" onSubmit={save}>
          <h2>{isProduct ? "Yeni ürün" : "Yeni bilgi kaydı"}</h2>
          <p className="muted">
            Kayıt kimliğini sunucu oluşturur. Alanlar Türkçe girilmelidir.{" "}
            <span className="required-mark">*</span>
            {" "}işaretli alanlar zorunludur.
          </p>
          <div className="form-grid">
            {isProduct ? (
              <>
                {field("name_tr", "Ürün adı")}
                {field("sku", "SKU")}
                {field("brand", "Marka")}
                <label>
                  {title("Kategori")}
                  <select name="category">
                    {Object.entries(categories).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </label>
                {field("price_try", "Birim fiyat (TL)", "text", "0.00")}
                {field("stock_qty", "Stok", "number", "0")}
                {field("min_order_qty", "Minimum adet", "number", "1")}
                {field("delivery_days", "Sevk süresi (gün)", "number", "0")}
                {field("warranty_months", "Garanti (ay)", "number", "0")}
                {field("tags", "Özellikler (virgülle)", "text", "", false)}
                {field("aliases", "Arama adları (virgülle)", "text", "", false)}
                {field(
                  "substitute_product_ids",
                  "Alternatif ürün ID’leri (virgülle)",
                  "text",
                  "",
                  false,
                )}
                <label className="wide">
                  Notlar
                  <textarea name="notes" rows={2} />
                </label>
              </>
            ) : (
              <>
                {field("title", "Başlık")}
                <label>
                  {title("Konu")}
                  {/* Chat retrieves only these topics; free text saved records it never cites. */}
                  <select name="topic" required defaultValue="">
                    <option value="" disabled>
                      Konu seç
                    </option>
                    {Object.entries(topics).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                  {fields.topic && (
                    <small className="error-text">{fields.topic}</small>
                  )}
                </label>
                {field("source", "Kaynak yolu")}
                {field(
                  "effective_from",
                  "Geçerlilik başlangıcı",
                  "date",
                  new Date().toISOString().slice(0, 10),
                )}
                {field(
                  "applies_to",
                  "İlgili ürün/kategoriler (virgülle)",
                  "text",
                  "",
                  false,
                )}
                <label className="wide">
                  {title("İçerik")}
                  <textarea
                    name="body"
                    required
                    rows={5}
                    aria-invalid={!!fields.body}
                  />
                  {fields.body && (
                    <small className="error-text">{fields.body}</small>
                  )}
                </label>
              </>
            )}
          </div>
          <button disabled={pending}>
            {pending ? "Kaydediliyor…" : "Kaydet"}
          </button>
        </form>
      )}
      <div className="filters">
        <label className="grow">
          {isProduct ? "Ürün veya SKU ara" : "Başlık ara"}
          <input
            value={query}
            onChange={(e) => changeQuery(e.target.value)}
            placeholder={isProduct ? "Örn. BlueScan" : "Örn. iade"}
          />
        </label>
        <label>
          {isProduct ? "Kategori" : "Konu"}
          <select
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">Tümü</option>
            {Object.entries(isProduct ? categories : topics).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        {isProduct && (
          <label className="check">
            <input
              type="checkbox"
              checked={inStock}
              onChange={(e) => {
                setInStock(e.target.checked);
                setOffset(0);
              }}
            />
            Yalnız stoklu
          </label>
        )}
      </div>
      <p className="muted" role="status">
        {loading ? "Kayıtlar yükleniyor…" : `${total} kayıt`}
      </p>
      <TableScroll>
        <table>
          <thead>
            <tr>
              {(isProduct
                ? ["Ürün / SKU", "Kategori", "Birim fiyat", "Stok"]
                : ["Başlık / Kimlik", "Konu", "Kaynak"]
              ).map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((p) =>
              isProduct ? (
                <tr key={p.product_id}>
                  <td>
                    <strong>{p.name_tr}</strong>
                    <small>
                      {p.sku} · {p.product_id}
                    </small>
                  </td>
                  <td>{categories[p.category!] ?? p.category}</td>
                  <td className="num">{money(p.price_try!)}</td>
                  <td>
                    <span className={"tag " + (!p.stock_qty ? "warning" : "")}>
                      {p.stock_qty} adet
                    </span>
                  </td>
                </tr>
              ) : (
                <tr key={p.knowledge_id}>
                  <td>
                    <details>
                      <summary>{p.title}</summary>
                      <p className="preserve">{p.body}</p>
                    </details>
                    <small>{p.knowledge_id}</small>
                  </td>
                  <td>{topics[p.topic!] ?? p.topic}</td>
                  <td className="wrap">{p.source}</td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </TableScroll>
      {!loading && !items.length && (
        <p className="empty">
          Bu filtrelerle kayıt bulunamadı. Aramayı değiştir veya yeni kayıt
          ekle.
        </p>
      )}
      <div className="pagination">
        <button
          className="secondary"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - 20))}
        >
          Önceki
        </button>
        <span>
          {total ? offset + 1 : 0}–{Math.min(offset + 20, total)} / {total}
        </span>
        <button
          className="secondary"
          disabled={offset + 20 >= total}
          onClick={() => setOffset(offset + 20)}
        >
          Sonraki
        </button>
      </div>
    </>
  );
}
