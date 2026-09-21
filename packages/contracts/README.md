# Ortak sözleşmeler — F01a

`@tbr/contracts` şu anda yalnız saf SSE aktarım parser'ını dışa verir. Mobil aynı paketi tüketir;
web ileride aynı parser'ı kullanabilir. Quote DTO ve gerçek chat event zarfı F05'te sabitlenecek.

`createSseParser()` her HTTP akışı için ayrı örnek oluşturur. `push(Uint8Array)` tamamlanan
`{event, data, id?}` olaylarını döndürür. Artımlı UTF-8 decode, LF/CRLF/CR, yorum satırları,
çok satırlı data ve kalıcı SSE id desteklenir. `data` ham metindir; JSON/domain doğrulaması tüketicide yapılır.
`finish()` decoder'ı kapatır; boş satırla bitmeyen son olay atılır. Eksik/geçersiz UTF-8 hata verir.
Parser'ın `done` gibi uygulama olaylarına özel davranışı yoktur; bitiş ve hata durumları tüketiciye aittir.

Repo kökünde `npm test`: 8 test, tüm byte sınırlarını deneyen test dahil. `npm run typecheck`
ve `npm run lint` ortak paket ile mobil ekranı kontrol eder. Kanıtlar `reports/f01a_*.txt`.
