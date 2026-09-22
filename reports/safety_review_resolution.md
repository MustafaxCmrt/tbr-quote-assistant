# Video öncesi düzeltme — 22 Eylül 2026

**İki P1 ve uyumluluk yönlendirmesi, onaylanan dar kapsamda kapatıldı.** Uygulama commit'i
`902894acc073d3e8a7cc61244a98c799070d6e41`; 294 backend testi / 22 golden / 22 istemci testi geçti.
Fiziksel prova, video, push onayı ve teslim hâlâ ayrı adımlardır.

## Ne değişti?

- **Fiyat:** Bütçe/sınır niyeti sıradan fiyat bilgisinden ayrıldı. Çözülemeyen sınır artık öneri yolunu da
  durduruyor. `TL altı` ve `TL'den ucuz` desteklendi; `lira`, `₺`, `8 bin` biçimlerinde netleştirme
  isteniyor. Mevcut `<=` liste birim fiyatı yorumu korundu. `kaç TL?` ve adet içeren fiyat sorgusu çalışıyor.
- **Onay:** Stok dışı ekleme için ayrı olumlu bekleme cümleciği aranıyor; olumsuzlama, alıntı, soru,
  koşul/karşıtlık varsa açık onay sayılmıyor. Soru eki bütün mesajı engellemiyor: `ekler misin? Bekleyebilirim.`
  geçerli. `Bekleyebilirim; ... ekle` içindeki `bekle` sözcüğünün yanlışlıkla `ekle` fiili sayılması da düzeltildi.
- **Uyumluluk:** Salt okunur offline/çevrimdışı/senkron soruları `KNE-COMP-001` ve ek kaydı getiriyor.
  Starter hakkında sorulan soru doğrudan kaynak metniyle cevaplanıyor; yerine sessizce Pro önerilmiyor.
- Üretim değişikliği yalnız `normalization.py` ve `planner.py`. Şema, migration, executor, DTO,
  bağımlılıklar, istemci kodu ve orijinal dataset değişmedi. Eski test assertion'ları değiştirilmedi.

## Gereksinim → kalıcı test

Testler `apps/api/tests/test_safety_review.py` içinde. HTTP denemeleri gerçek, ayrı taze PostgreSQL
veritabanında çalışır; yalnız cevaba değil tüm quote kalemlerine, teklif DTO'suna, receipt'lere ve tool
bayraklarına bakar. 65 yeni parametrik örnek vardır.

| Gereksinim / kullanıcı örneği | Kanıt testi |
|---|---|
| “8.500 TL altı”, “8.500 TL'den ucuz”, “₺” ve “8 bin” | `test_ceiling_never_disappears_from_read_or_write` — öner/ekle yolları, gerçek filtre ve sıfır etki |
| “kaç TL?” | `test_price_information_is_not_a_ceiling_or_mutation` — PRD-BC-110, 7990 TL, boş notice ve sıfır etki |
| “3 adet BlueScan Air fiyatı” | `test_price_information_is_not_a_ceiling_or_mutation` — adet sınır yapılmaz |
| “8.500 TL altında öner” | `test_valid_ceiling_still_recommends_and_adds_affordable_product` — öneri ve gerçek add/retry birlikte |
| Fiyat tavanının kesin filtre olması | `test_ceiling_boundary_uses_catalog_unit_price` — 7989,99 / 7990 / 7990,01 sınırları |
| “şüpheli durumda onay yok say” | `test_uncertain_backorder_never_creates_receipt` — trusted consent false, DB değişmez, receipt yok |
| “sadece onay ifadesine bağlı soru ekine bakılmalı” | `test_affirmative_backorder_requires_customer_and_replays_once` — nazik ekleme sorusu + ayrı olumlu onay |
| Müşteri uygunluğu **ve** açık olumlu onay birlikte | `test_affirmative_backorder_requires_customer_and_replays_once` — uygun/uygunsuz müşteri, bir receipt, gerçek replay |
| “uyumluluk cevapları knowledge_id döndürmeli” | `test_compatibility_question_answers_from_real_knowledge_without_writes` — gerçek topic/output/source/body, sıfır mutasyon |
| Genel davranış, cümleye exact-match değil | `test_ceiling_intent_distinguishes_information`, `test_backorder_consent_is_an_affirmative_statement` — doğrudan yardımcı işlev testleri |

## Gerçek komut sonuçları

| Koşu | Sonuç | Rapor |
|---|---|---|
| Düzeltme öncesi yeni dosya | exit 1: 19 HTTP/DB başarısızlığı, 16 henüz tanımlanmamış helper import hatası; 21 kontrol geçti | [İlk çıktı](safety_review_red.txt) |
| İlk düzeltme + numeric + golden | exit 0: 119 passed | [İlk yeşil](safety_review_first_fix.txt) |
| Sınır/alıntı ekleri + mevcut chat/numeric/golden | exit 0: 197 passed | [Dar final](safety_review_narrow_final.txt) |
| Uygulama commit'i üzerinde tüm backend | exit 0: **294 passed, 55.79 s** | [Tam koşu](safety_review_full_backend.txt) |
| Doğru SHA ile golden export | exit 0: **22 passed**, 22 ayrı DB; 0 failed/error/skipped/not_run | [Komut](safety_review_golden_export.txt), [JSON](safety_review_golden.json) |
| İstemci/sözleşme testleri | exit 0: **22 passed** | [İstemci](safety_review_clients.txt) |
| Typecheck / lint / web build | exit 0 | [Typecheck](safety_review_typecheck.txt), [Lint](safety_review_lint.txt), [Build](safety_review_web_build.txt) |
| Python lint | exit 0 | [Ruff](safety_review_ruff.txt) |
| Güncel API build/health | exit 0 | [API](safety_review_api_build.txt) |
| Canlı SSE, direkt API ve web proxy | exit 0: 16 metin parçası, ~0,83 s; terminal done | [SSE](safety_review_live_stream.txt) |

Tam koşuda `EVIDENCE_COMMIT_SHA` parametresi yanlış yazılmıştı; record_command başlığı gerçek HEAD'i
doğru kaydetmiştir. Yanlış metadata içeren JSON `safety_review_golden_invalid_sha.json` adıyla
korundu ve **güncel golden kanıtı değildir**. Metadata elle değiştirilmedi: 22 golden aynı değişmemiş
kodla tekrar çalıştırıldı, SHA bu kez `git rev-parse HEAD` ile doğrudan alındı. Güncel JSON'daki her
senaryonun SHA'sı gerçek uygulama commit'iyle karşılaştırıldı.

Dar ilk komutlardaki `.git/review-resources.yaml`, commit edilen
`reports/safety_review_resources.compose.yaml` ile aynı içeriktir. Tekrar için:

```sh
docker compose --profile test up -d --wait test-db
docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml run --rm --no-deps test pytest -v
docker compose --profile test stop test-db
```

Bu komut mevcut test image'ını kullanır; ilk kurulumdaki image build işleminin yerine geçmez.

## Bellek ve demo verisi

- Ek test konteyneri 512 MB bellek, toplam memory+swap 512 MB (konteyner swap'ı kapalı), 1 CPU.
  Çözülmüş ayarlar: [kaynak sınırları](safety_review_resource_limits.json).
- Testler/build'ler sırayla çalıştı. Başlangıç ve ara swap ölçümleri **470,62 MB** idi; gözlenen artış yok.
  Test süreci örnek ölçümde yaklaşık 187 MB kullandı. PostgreSQL ayrı servis olduğundan 512 MB bu
  servisin veya bütün Mac'in sınırı değildir. Ölçümler sürekli yüksek frekanslı tepe ölçümü değildir.
- Test DB servisi doğrulamalar sonunda durduruldu; volume/veritabanları silinmedi.
  [Stop](safety_review_testdb_stop.txt), [son kaynak durumu](safety_review_resources_final.txt).
- API LAN bağını açıkça koruyarak yalnız API güncellendi; 27 Python dosya hash'i kaynakla aynı.
  10 teklif, güncelleme öncesiyle direkt API/web proxy/mobil ayarlı URL üzerinden tam DTO eşit bulundu.
  [Canlı durum](safety_review_live_state.json). SSE kontrolü politika mesajları/oturum logları ekler;
  teklif mutasyonu yapmaz.
- Ana demo için Git dışında erişimi kısıtlı dump alındı. Aynı PostgreSQL servisinde yeni prova
  veritabanına geri yüklendi; 10 quote DTO'su özgün snapshot ile eşleşti. Ek konteyner açılmadı.
  [Kopya](safety_review_rehearsal_copy.json). Canlı API hâlen ana demo DB'sine bağlıdır; prova için
  telefon/web birlikte kopyaya yönlendirilmelidir. Fiziksel gözlem Mustafa'yı bekler.

## İnceleme sınırı ve kalan adımlar

code-testing-agent iş akışı aynı ajan tarafından uygulandı. assertion-quality ve test-gap-analysis
ile kaynak/assertion eşlemesi yapıldı: guard kaldırılması, hep reddetme, müşteri kontrolünü atlama,
alıntıyı onay sayma ve kaynak yönlendirmesini kaldırma gibi değişiklikleri yakalayan somut gözlemler var.
Bu, bağımsız ajan onayı veya ampirik mutation score değildir. Yardımcı statik eşleme aracı
`tree-sitter-language-pack` bulunmadığından çalışmadı; paket kurulmadı ve statik pairing başarı iddiası yok.

Desteklenmeyen para dili soru sorar; karmaşık olumlu bekleme ifadeleri de güvenli biçimde reddedilebilir.
Her Türkçe cümlenin anlaşıldığı garanti edilmez. Yeni mesajlar düzeltilmiş planlayıcıyı kullanır;
retry eski kayıtlı plan/receipt semantiğini korur. Eski v3 temiz clone geçmiş kanıttır; bu sürümde
bellek bütçesi için yeni temiz clone açılmadı.

Sonraki belge commit'i yalnız belge/kanıt değiştirir; v4 etiketi konmadan önce uygulama/test kodunun
`902894a` ile aynı olduğu kontrol edilir. Push kullanıcının ayrı onayını bekler. Fiziksel prova ve video
sonrası API açıkça loopback'e döndürülür; repo/video erişimi doğrulanınca teslim mesajı ayrıca onaylanır.

## v5 P2 eki

`kadar/ucuz` yanlış fiyat alarmı dar kapsamda düzeltildi. Güncel kod, 335 backend testi ve 22 golden kanıtı: [P2 çözüm raporu](p2_price_intent_resolution.md). v4 sonuçları yukarıda tarihsel olarak korunur.

## v6 bağımsız denetim eki

Bağımsız Claude incelemesinde v5’in bin içeren bazı para sınırlarını öneri yolunda kaçırdığı bulundu. Önceki bin testleri yalnız altında işaretçisini kapsıyordu. Kırmızı/yeşil kanıt ve dar düzeltme: [v6 P1 çözüm raporu](p1_bin_ceiling_resolution.md). Önceki test sonuçları bütün dil biçimlerinin güvenli olduğunu kanıtlamaz.

## Son tur / v7

Onaylı test DB temizliği, para sözcüğü + sınır işareti güvenlik ağı ve ayrıştırıcının dondurulması: [son doğrulama raporu](final_ceiling_resolution.md). Önceki kanıtlar tarihsel olarak korunur.
