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

## Toplam hedef ve taslak durumu — ikinci düzeltme

İki yeni HTTP regresyonu düzeltmeden önce başarısız: `f08_review_race_before.txt` (exit1).
İki planın da aynı başlangıç sürümünü görmesini deterministik bir asyncio barrier sağlar;
veritabanı, HTTP route, executor ve wrapper gerçek çalışır. Bu bir zamanlama şansı testi değildir.
Toplam hedef delta'sı sunucu planında başlangıç quote version'ını taşır. Executor bunu context'e
iletir, gerçek wrapper receipt aramasından **sonra**, quote kilidi altında yeni etki öncesi doğrular.
Eski hedef planı 409 ile yeni mesaj ister. Yeni mutasyon yalnız draft üzerinde uygulanır.
Başarılı receipt replay bu yeni durum/sürüm kontrollerinden önce döner; teklif tekrar değişmez.
Kamuya açık altı tool input'una alan eklenmedi, mevcut receipt hash şeması değiştirilmedi.

| Requirement | Evidence |
|---|---|
| "toplam … olsun" TOCTOU | `test_total_target_concurrency_rejects_stale_plan_and_preserves_replay`: iki eşzamanlı plan, bir200/bir409; toplam5/version2; başarısız plan retry409; araya update2 girince başarılı eski add replay200 ama adet2/version3 korunur; receipt2 ve gerçek add logları applied/replayed doğrulanır. |
| "taslak teklife ekler" | `test_non_draft_quote_rejects_new_mutation_but_allows_read_and_receipt_replay`: accepted state yeni ekleme409; politika okuma ve eski receipt replay200; tüm quote aynı/receipt1. |
| Odaklı gerçek koşu | `docker compose --profile test run --build --rm test pytest -q tests/test_chat.py -k 'total_target_concurrency or non_draft_quote'`: 2passed, exit0; `f08_review_race_after.txt`. |

Yukarıdaki iki açık hipotez bu regresyonlarla doğrulandı ve düzeltildi. Diğer açık review maddeleri
henüz kapanmadı. İlk lint import sırası hatası raporda korunur; düzeltilmiş Ruff exit0:
`f08_review_race_lint_final.txt`. Bu kayıt 151 eski testin yeni sürümde yeniden koşulduğunu iddia etmez.

Birleşik mutation + chat + golden koşusu: **104passed23.78s, exit0**; `f08_review_mutations_chat_golden.txt`. Son delivery scan exit0, orijinal12source aynı; `f08_review_race_delivery.txt`.
