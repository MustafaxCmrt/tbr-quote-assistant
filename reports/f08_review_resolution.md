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

## Katalog ve özellik yazımları — üçüncü düzeltme

`f08_catalog_review_before.txt`: exit1/5failed. Wi-Fi/USB C/çevrimdışı artık normalize edilen
arama gölgesinde wifi/usb-c/offline ile aynı özellik olur; özgün veri ve gösterim metni değişmez.
Eşit güçlü ürünlerde fiyat/ID sıralaması kullanıcı tercihi sayılmaz; planner ürün kodu ister.
Yeni canlı model/alias kategori sözcüğü olmadan da okuma ve ekleme yoluna girebilir.
Koşullu eklemede de ilk ürün ve hedef için tek anlamlı seçim gerekir.

| Requirement | Evidence |
|---|---|
| "Açık özellikler kesin filtre" | `test_feature_spelling_variants_do_not_drop_hard_constraints`: Wi-Fi/USB C/çevrimdışı gereğini taşımayan adlandırılmış ürün için boş öneri, aynı quote, receipt0. |
| Geçerli açık özellik isteği çalışsın | `test_feature_spelling_variants_accept_matching_products`: uygun stoklu üç gerçek SKU için quantity1/version2/receipt1. |
| "belirsiz niyette soru sor" | `test_generic_tied_product_choice_requires_clarification`: Barkod okuyucu ekle → ürün kodu sorusu, aynı quote/receipt0. |
| "yeni eklenen kayıtlar … çalışmalı" | `test_new_live_model_without_category_is_readable_and_addable`: kategori içermeyen yeni MorMartı Nova model adıyla read tek doğru ürün; add2/net2468. |
| Korunan mevcut akış | `f08_catalog_review_after.txt`: chat + golden22 + numeric unit, 83passed/exit0 (son üç olumlu örnek bu koşudan sonra eklendi). |

Olumlu Wi-Fi testinin ilk seçiminde PRD-POS-220 yanlışlıkla stoklu varsayılmıştı; özgün JSON'da
stok0 olduğu doğrulandı. Ürün kuralı/veri/assertion gevşetilmedi: "uygun stoklu ürün" testi için
stok15 olan PRD-POS-230 seçildi. İlk 1failed/5passed çıktı `f08_catalog_positive.txt` içinde korunur.

Son özellik olumlu/olumsuz koşusu: `pytest -q tests/test_chat.py -k feature_spelling`, 6passed/exit0; f08_catalog_positive_final.txt. Ruff/delivery exit0; source12 değişmedi.


## Kaynak doğrulaması ve kalan P2 değerlendirmesi

Tautolojik `bundle.require(list(sources))` kaldırıldı. Renderer artık yayımlayacağı knowledge,
ürün (stoklu/stoksuz) ve son teklifin ürün/fiyat kuralı kimliklerini tool çıktısından toplar;
bunları ayrı kaynak listesinden doğrular. Eksik/ilgisiz kaynakla yanıt yayımlanmaz.

| Requirement | Evidence |
|---|---|
| "Her politika cevabı gerçek knowledge_id içerir"; ürün/fiyat kuralı kaynağı doğrulansın | `test_rendered_claim_requires_matching_tool_evidence`: beş çıktı türünde boş kaynak ve yanlış ID SOURCE_NOT_GROUNDED; doğru kaynakla render succeeds, kaynak aynı ve metindeki gerçek ID doğrulanır. |
| Gerçek koşu | `uv run --directory apps/api --locked pytest -q tests/unit/test_templates.py`: önce5failed/exit1, sonra5passed/exit0; f08_grounding_before.txt / f08_grounding_after.txt. Ruff exit0, f08_grounding_lint.txt. |

Migration hipotezi: `test_unique_active_item_and_history_and_checks` gerçek migration kurulmuş
PostgreSQL üzerinde duplicate aktif satırın ve invalid quantity'nin IntegrityError olmasını sınar;
`test_same_and_distinct_key_concurrency` aynı anda tek aktif satır davranışını doğrular. Bunlar
model tanımına bakılarak verilmiş sonuçlar değildir; son toplu koşuda tekrar yer alır.
Planlama okumaları ile executor loglarının ayrılığı ve retry'da eski notice korunması P2 kapsamıyla
KNOWN_LIMITATIONS içinde açıklandı. Retry'ı yeniden planlamak çift/istenmeyen yeni etkiler
üretebileceğinden kalıcı plan korunur; mutation guard'ları güncel/kilitli veriyle çalışır.
Auth yokluğu, rule registry seçimi, session dahil olmayan key'in fail-closed conflict davranışı
belgelenmiş tasarım sınırlarıdır; üretim yetkilendirmesi iddia edilmez.

F08 son tam koşu: commit313a486, `docker compose --profile test run --build --rm -e GOLDEN_REPORT_PATH=/evidence/golden_results.json -e EVIDENCE_COMMIT_SHA=313a4865dd2bcf15dec7fefd01d0c57f984eb01b -v <repo>/reports:/evidence test pytest -v`: exit0,179passed40.92s. reports/f08_review_full_backend.txt ve golden_results.json yenilendi. Opus5/xhigh odaklı takip review session6425 çalışıyor; verdict bekleniyor.

## Opus 5 takip bulguları — 9 ek ifade ve ortak tespit

`f08_claude_followup.md` kabul vermedi: üç yorumlama sınıfının kısmen açık kaldığını gösterdi.
Reviewer yalnız kaynak okudu; CLI exit0/is_error=false/modelclaude-opus-5,397.4sn.
Codex yeni örnekleri gerçek HTTP/PostgreSQL testine ekledi: önce9failed/11passed
(`f08_followup_regressions_before.txt`); düzeltme sonrası chat+golden+numeric
**109passed19.93s/exit0** (`f08_followup_regressions_final.txt`).

- Para niyeti ve sayı çözümleme aynı `PRICE_CEILING_MARKERS` listesini kullanır; TL/₺/lira/TRY
  tanınır. Ayrıştırılamayan tutar netleştirme ister. Sınırlı parser'ın tüm dil ifadelerini
  anladığı iddia edilmez; önceki genel ifade bunun yerine okunmalıdır.
- Plus olumsuzlukları kontrol edilir; pozitif Plus seçimi tam model+Plus ya da açık ID/SKU ister.
- Ürün kategorisinin geçmesi teslim tarihi/indirim/fiyat alanını yazma yetkisi vermez.
- Canlı katalogdaki ek betimleyiciler de referans seçerken korunur. Örneğin endüstriyel ürün
  isteği standart BlueScan Air satırına çözülmez. Eşleşme tag kadar ad/alias içinde de olabilir;
  ilk fazla geniş tag filtresinin iki golden hatası f08_followup_regressions_after.txt'de saklandı.

| Requirement | Evidence |
|---|---|
| "Açık max_price … kesin filtre" | `test_review_price_expression_never_silently_drops_ceiling`: lira/en fazla/üstüne çıkmadan yeni örnekleri, aynı quote ve receipt0. |
| "belirsiz niyette soru sor" | `test_review_unsupported_or_unmatched_intent_clarifies_without_mutation`: Plus olmadan/istemiyorum/Plus'suz; okuyucu teslim tarihi/indirim; endüstriyel ürün örneklerinde aynı quote, notice, receipt0 ve mutation tool yok. |
| Tek para belirteci sözleşmesi | `test_every_supported_ceiling_marker_has_matching_intent_detection`:9marker, tespitTrue ve Decimal5000; `test_currency_without_supported_amount_requests_clarification`:5currency, tespitTrue ama çözümlenmiş tutarNone. |
| Gerçek koşu | 109-test birleşik komut yukarıda; numeric unit33passed; son lint/delivery exit0: f08_followup_lint_final.txt/f08_followup_delivery.txt. |

Kalan reviewer hipotezlerinin sözleşme kontrolü: replace quantity dış sözleşmede `integer > 0|null`;
önceki satır tamamen replaced olur. Bu tam satır değişimidir, kısmi split işlemi değildir.
Doğal dilde kısmi değişim niyeti ayrıca netleştirilmelidir; kapsamlı semantik kabul henüz kapanmadı.
Kaynak quote JSON'da validity alanı yok; var olmayan expiry kuralı uydurulmaz.

### Miktarlı replace hipotezi

HTTP regresyonu kısmi replace niyetinin tamamına uygulanmasını doğruladı (önce1failed/2passed;
f08_partial_replace_before.txt). Miktarlı replace artık açık "tamamını" seçimi ister; miktarsız
standart alternatif akışı korunur. Araç sözleşmesi değişmez, doğrudan wrapper pozitif quantity
ile bütün satırı değiştirebilir.

| Requirement | Evidence |
|---|---|
| Kısmi niyette yanlış tam replacement olmasın | `test_review_partial_removal_does_not_become_target_or_full_removal[değiştir]`: başlangıç5 korunur, aynıquote/version ve yalnız setup receipt. |
| Açık tam değişim hedef miktarı çalışsın | `test_explicit_whole_line_replacement_can_set_target_quantity`: BC110qty5 historyreplaced; BC120qty2 active; version3 ve receipt2. |
| Gerçek koşu | `pytest -q tests/test_chat.py -k 'partial_removal or explicit_whole_line'`:4passed/exit0; f08_partial_replace_after.txt. Ruff exit0. |

Runtime satır yazma yolları kaynak taramasında `services/mutations.py` içindedir; admin ürün/knowledge
yazar, teklif kalemi yazmaz. Seed yalnız eksik kimlik ekler ve kullanıcı satırlarını üzerine yazmaz.
Yeni toplu koşu sonrası F08 kapısı tekrar değerlendirilecek; 179 eski tam koşu bu patch'i içermez.

## Claude takip P2'leri — 2026-09-21

Üç bulgu gerçek PostgreSQL/HTTP regresyonlarında doğrulandı. Önce 10 failed / 9 passed
(`f08_p2_before.txt`), sonra 19 passed (`f08_p2_after.txt`), exit 0.
İlk düzeltme koşusu 1 failed / 18 passed (`f08_p2_after_initial.txt`) olarak korundu.
Runtime commit: `53b99488bdd8427ed8a8b3a06c9e8ca6dba106d6`.

| Gereksinim | Exact test / kanıt |
|---|---|
| P2-1 katalog tam adı/Plus alias ve SKU | `test_plus_alias_selects_exact_catalog_product` (BC110, KIT610, ACC710 tam adları + ACC710 SKU); ürün/miktar, sürüm2, receipt1 |
| Plus model belirsizliği ve gerçek negasyon | `test_review_unsupported_or_unmatched_intent_clarifies_without_mutation`; notice, tam DTO aynı, receipt0, mutation tool yok |
| P2-2 amaç ve aciliyet bağlamı | `test_review_context_words_preserve_explicit_mutation[descriptor_context-purpose]` ve `[descriptor_context-urgent]`; qty3 veya removed geçmişi, sürüm2, receipt1 |
| P2-3 zaman ifadesi | `test_review_context_words_preserve_explicit_mutation[kadar-time]`; qty2, sürüm2, receipt1 |
| P2-3 istemiş olumlu geçmiş zaman | `test_review_context_words_preserve_explicit_mutation[istemis]`; qty3, sürüm2, receipt1 |
| Fiyat niyeti zaman/tutar ayrımı | `test_kadar_price_intent_distinguishes_time_and_amount`, `test_kadar_currency_ceiling_is_parsed`; rakamlı/rakamsız zaman, gerçek tutar, bütçe, karma zaman/fiyat |
| Gerçek tavan korunması | `test_review_price_expression_never_silently_drops_ceiling`, `test_every_supported_ceiling_marker_has_matching_intent_detection` |

Önerilen patch iki noktada yetersizdi: cümlede herhangi bir rakam aramak “şimdiye kadar
1 tane” hatasını korur; zaman öbekleri fiyat niyeti aramasından çıkarıldı. “Acil” yalnız
tag değil, hizmet adı başlangıcıdır; “acil olarak” zarfı referans çözümlemeden çıkarıldı.
Kategori içi endüstriyel/özellik filtreleri ve mutasyon anı guard'ları korunur.
Mevcut ceiling marker testi zaten rakam içeriyordu; assertion/girdi değiştirilmedi.
Tam koşu: `f08_release_backend.txt`, **225 passed / 46.89s**, exit 0; 22 golden passed.
Bu Codex doğrulamasıdır; yeni Claude onayı veya fiziksel iPhone testi değildir.
