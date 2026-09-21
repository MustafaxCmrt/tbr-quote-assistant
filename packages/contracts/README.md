# packages/contracts

Web ve mobilin ortak kullandığı **tek sahipli** sözleşme paketi (F05'te sabitlenir):

- Quote DTO tipleri (`quote_id`, `version`, `items[]`, `gross_total_try`, `discount_total_try`, `net_total_try`, `applied_rules`)
- SSE event zarfı (`schema_version`, `session_id`, `message_id`, `attempt_id`, `event_seq`, `type`, `payload`)
  ve event tipleri: `message_start`, `tool_call_start`, `tool_call_result`, `sources`, `text_delta`, `done`, `error`
- Saf SSE parser: incremental UTF-8 decode, buffer koruma, LF/CRLF çerçeve, bir chunk ≠ bir event; unit testli

Kaynak doğruluğu: backend'in ürettiği `openapi.json` / JSON Schema. Python–TS alan uyumu testle denetlenir.
İstemciler alan adlarını yeniden adlandırmaz.
