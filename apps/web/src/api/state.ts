/** Late polls cannot overwrite a newer quote or a newly selected context. */
export function acceptQuote<T extends { quote_id: string; version: number }>(
  current: T | null,
  incoming: T,
  selected: string,
): T | null {
  if (incoming.quote_id !== selected) return current;
  return current?.quote_id === incoming.quote_id &&
    current.version > incoming.version
    ? current
    : incoming;
}
