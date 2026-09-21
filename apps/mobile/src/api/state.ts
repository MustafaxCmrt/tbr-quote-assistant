import type { Quote } from "@tbr/contracts";
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
