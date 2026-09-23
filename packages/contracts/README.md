# Ortak sözleşmeler (`@tbr/contracts`)

Backend'in SSE olaylarını ve teklif verisini web ile mobilin aynı şekilde okuması için saf TypeScript
paketi. Mobil paketi doğrudan kullanır; web, kendi Docker derlemesi için `scripts/sync_web_contracts.py`
ile üretilen kopyasını kullanır.

| Dosya | İçerik |
|---|---|
| `src/sse.ts` | `createSseParser()`: bayt düzeyinde artımlı SSE ayrıştırıcı (UTF-8, LF/CRLF/CR satır sonları, yorum satırları, çok satırlı `data`, `id`) |
| `src/chat.ts` | Olay tipleri (`message_start`, `tool_call_start`, `tool_call_result`, `sources`, `text_delta`, `done`, `error`); `parseChatEvent()` sürüm 1 zarfını ve içeriği doğrular; `reduceChatEvent()` akış durumunu günceller; `Quote`, `QuoteLine`, `Source` tipleri |
| `sse_events.schema.json`, `quote_dto.schema.json` | Backend şemalarından üretilen JSON Schema (`scripts/export_stream_schemas.py`) |
| `tool_inputs.schema.json` | Altı aracın doğrulama şeması (`scripts/export_tool_schemas.py`) |

Ayrıştırıcı uygulama olaylarına özel davranış içermez; geçersiz UTF-8 veya geçersiz olay içeriği hata
verir, boş satırla bitmeyen son olay atılır. Testler repo kökünde `npm test` ile çalışır.
