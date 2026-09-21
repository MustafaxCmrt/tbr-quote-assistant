import type { Quote, QuoteLine } from "@tbr/contracts";

const text = (v: unknown) => typeof v === "string";
const texts = (v: unknown) => Array.isArray(v) && v.every(text);
function isLine(v: unknown): v is QuoteLine {
  if (typeof v !== "object" || v === null) return false;
  const l = v as Record<string, unknown>;
  return (
    [
      "quote_item_id", "product_id", "sku", "name_tr", "status",
      "unit_price_try", "gross_total_try", "discount_total_try", "net_total_try",
    ].every((k) => text(l[k])) &&
    Number.isSafeInteger(l.quantity) &&
    texts(l.rule_ids)
  );
}
/** Screens read these fields directly; a drifted payload must not crash rendering. */
export function isQuote(v: unknown): v is Quote {
  if (typeof v !== "object" || v === null || Array.isArray(v)) return false;
  const q = v as Record<string, unknown>;
  return (
    ["quote_id", "customer_name", "status", "gross_total_try", "discount_total_try", "net_total_try"].every(
      (k) => text(q[k]),
    ) &&
    Number.isSafeInteger(q.version) &&
    texts(q.rule_ids) &&
    Array.isArray(q.items) &&
    q.items.every(isLine) &&
    Array.isArray(q.history) &&
    q.history.every(isLine)
  );
}
export function acceptQuote(
  current: Quote | null,
  incoming: Quote,
  selected: string,
): Quote | null {
  if (incoming.quote_id !== selected) return current;
  if (current?.quote_id === selected && current.version > incoming.version)
    return current;
  return incoming;
}
