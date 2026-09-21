# F08 bağımsız inceleme bulguları — çözüm kaydı

**Kabul açık.** Opus 5 / xhigh salt okunur review dört P1 bildirdi. Reviewer'ın kaynak izlemesi
Codex tarafından gerçek HTTP/PostgreSQL regresyonlarıyla sınandı. İlk koşu 13 failed;
`f08_review_regressions_before.txt` saklandı. Düzeltme sonrası chat + golden **57 passed / exit0**:
`f08_review_regressions_final.txt`. İlk düzeltmenin iki stok-alternatif golden senaryosunu fazla
engellediği koşu da `f08_review_regressions_after.txt` içinde saklandı. Assertion gevşetilmedi;
"stokta olmayan" kaynak seçimi ile olumsuzlanan özellik ayrıldı.

| Requirement | Evidence |
|---|---|
| "Açık max_price ve … guard"; P1-1 tanınmayan fiyat biçimi sessiz düşmesin | `test_review_price_expression_never_silently_drops_ceiling`: dört ifade, quote/version aynı, receipt0. Desteklenmeyen para ifadesi açık TL sınırı sorar. |
| "belirsiz niyette soru sor"; P1-2 olumsuzlanan Plus/özellik | `test_review_unsupported_or_unmatched_intent_clarifies_without_mutation`: Plus olmasın/Plus'sız/kablosuz olmayan için notice, aynı quote, receipt0 ve mutation tool yok. |
| "belirsiz niyette soru sor"; P1-3 ilgisiz kalem referansı | Aynı testin İndirimi kaldır/Daha ucuz/RedScan'den/Teslim tarihini değiştir örnekleri: aynı quote, receipt0, mutation tool yok. Canlı katalogdan brand/model ile pozitif referans gerekir; tek satır olması yeterli değildir. |
| "quantity semantics"; P1-4 kısmi çıkarma | `test_review_partial_removal_does_not_become_target_or_full_removal`: adet5 setup doğrulanır, 2 adet çıkar/sil sonrası hedef miktar sorulur, adet5/aynı version ve yalnız setup receipt'i korunur. |
| Geçerli mevcut senaryolar korunsun | `test_golden_message_through_http`: 22 senaryo aynı assertion'larla geçti; destekli stok-alternatif ve hedef adede güncelleme korunur. |
| Gerçek doğrulama | `docker compose --profile test run --build --rm test pytest -q tests/test_chat.py tests/golden/test_chat_golden.py`: 57 passed, exit0. `uv run --directory apps/api --locked ruff check app tests`: exit0. |

Bu patch yalnız planner ve chat regresyonlarını değiştirir. Yeni belirsiz ifadeleri tahmin ederek
mutasyon yapmak yerine açık ürün/limit/hedef miktar ister. Source JSON'lar değişmez.

## Açık inceleme maddeleri

- Toplam hedefin planlama ile uygulama arasında değişmesi (TOCTOU): eşzamanlılık regresyonu henüz yok,
  **not_verified**. F08 kapanmadan değerlendirilecek.
- Draft dışı quote: seed'de yalnız draft var (salt okunur JSON kontrolü); executor status koruması
  henüz değerlendirilmedi. Draft dışı durumu güvenli kabul etmiyoruz.
- Belirsiz ekleme sıralaması, Wi-Fi/USB C/çevrimdışı özellik eşanlamları ve canlı markanın kategori
  olmadan chat'ten bulunması: ayrıca ele alınacak. Mevcut golden başarısı bunları kanıtlamaz.
- Migration/index varlığı: mevcut gerçek PostgreSQL concurrency/unique test kanıtlarıyla eşlenecek.
- P2 source require totolojisi, planlama ile log aramalarının farkı ve kapsamlı auth eksikliği:
  review'da açıkça yazılı; son disposition henüz verilmedi.

Son tam 151-test koşusu bu patch'ten **öncedir**; 57-test koşusu tüm backend koşusu diye sunulmaz.
Demo API henüz bu patch ile yeniden build edilmedi; fiziksel yeniden doğrulama iddiası yok.
