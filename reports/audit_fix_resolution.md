# Tam denetim bulgularının çözümü — 2026-09-23

Kaynak: bağımsız tam denetim raporu `reports/full_audit_20260922.md` (Codex; HEAD `88165fb`, puan 82/100).
Uygulayan: Claude, Mustafa'nın açık talimatıyla ("doğruysa implemente geç, faz faz, her faz sonunda commit").
Önce her bulgu kod okuması ve denetimin gerçek HTTP/DB probe kayıtlarıyla (`full_audit_20260922_probes.json`,
`full_audit_20260922_total_budget_probes.json`) doğrulandı; B01–B07 probe'larla, B08/B09 kodla birebir tutarlıydı.

**Plan sapması:** v8'de fiyat ayrıştırıcısı DONDURULMUŞTU. B01/B02 bu dondurmayı gerektirdiği için Mustafa'nın
açık talimatıyla yalnız bu denetim bulguları kapsamında kaldırıldı (karar defterine yazıldı). Şema, executor,
tool sözleşmeleri, DTO, `data/source/` ve golden fixture değişmedi; mevcut hiçbir assertion gevşetilmedi.

## Bulgu → düzeltme → regresyon

Tüm yeni testler `apps/api/tests/test_audit_regressions.py` içinde; gerçek chat HTTP girişinden, her örnek
taze seed'li ayrı PostgreSQL DB'sinde; olumsuz durumda quote/version/receipt/tool log değişmezliği doğrulanır.

| Bulgu | Commit | Düzeltme | Regresyon (kırmızı → yeşil) |
|---|---|---|---|
| B03 P1 alıntı/varsayım/önce onay mutasyonu | `362db82` | `has_unauthorized_command`: tırnak içindeki komut fiili, koşul/aktarılan söz (`eklersem`, `ekle dersem`, `diyelim`), ertelenmiş onay (`önce benden onay iste`, `onayımı bekle`) → salt okuma + açıklama. `Onay alındı`, `bana sormadan ekle`, `"BlueScan Air" 1 adet ekle` komut olarak kalır. | 8 failed ([red](audit_fix_p1_red.txt)) → [green](audit_fix_p1_green.txt) |
| B06 P1 yazıyla/Unicode eksi miktar | `1981a19` | Tipografik eksi/tire/artı işaretleri ayrıştırmadan önce ASCII'ye çevrilir; `2–3 adet` artık `3` olmaz. `has_unresolved_quantity`: belirtilmiş ama rakam olmayan miktar (`iki`, `birkaç`, `x2`) → soru. Belirtilmemiş miktar 1 kalır; `bir tane` 1'dir. | 6 failed ([red](audit_fix_p2_red.txt)) → [green](audit_fix_p2_green.txt) |
| B01 P1 ikinci/çözülemeyen para ifadesi | `2992ab8` | `has_unparsed_money`: ayrıştırılan TL tutarları çıkarıldıktan sonra metinde para ifadesi (`lira`, `₺`, `TRY`, `5 bin TL`) kalırsa arama/öneri/mutasyon yapılmadan netleştirme. | [red](audit_fix_p3_red.txt) → [green](audit_fix_p3_green.txt) |
| B02 P1 toplam bütçe birim sınırı sanılıyor | `2992ab8` | `has_total_budget_scope`: para bağlamında `toplam*` (ama `toplam 4 adet` değil) veya adet > 1 ile `bütçe*` → birim sınırı istenir, mutasyon yok. Toplam bütçe kontrolü eklenmedi (B04 kararı: çözülemezse sor). | aynı rapor; `Birim fiyatı 9.000 TL altında 2 adet` ve `toplam 3 adet olsun` kontrolleri yeşil |
| B04 P1 açık değiştirme hedefi yok sayılıyor | `e3a2480` | `product_mentions` ID/SKU/model adlarını (Plus dahil) konumlarıyla bulur. `Y ile / -(y)la / -(y)le` işaretli ürün, yoksa teklifte olmayan tek ürün hedef olur. Hedef kayıtlı alternatif olmalı ve fiyat/stok/özellik aramasından geçmeli; iki hedef veya uymayan hedefte teklif değişmez. Adıyla anılan mevcut kalem kaynak olur. | 9 failed ([red](audit_fix_p4_red.txt)) → [green](audit_fix_p4_green.txt); başarı testleri tam hedef ID'si ve DB `replaced/active` satırlarını doğrular |
| B05 P1 `;` sonrası koşul düşüyor | `8ef5c51` | İlk bölümde `ekle` varsa sonraki `;` bölümleri atılmaz: yalnız özellik içeren bölüm önceki ürüne bağlanır (nokta ile aynı), başka ürün adı kendi `ekle` fiiliyle aynı atomik gruba girer, fiilsiz ürün adı soru üretir. SCN-008 bağlam cümlesi ve SCN-011 notu aynı kalır. | 5 failed ([red](audit_fix_p5_red.txt)) → [green](audit_fix_p5_green.txt) |
| B07 P2 stok politikası yönlendirmesi | `fde6015` | Salt okuma mesajında stok dışı/backorder/bekleme + kural/politika/nedir → gerçek `stock_rule` knowledge (`KNE-STOCK-001`). | [red](audit_fix_p6_red.txt) → [green](audit_fix_p6_green.txt) |
| B09 P2 geçmişte en yeni kayıtlar görünmüyor | `fde6015` | Mesaj geçmişi en yeni 200, tool logu en yeni 500 kayıt; eskiden yeniye sıralı döner. | 205 mesaj/505 log ile HTTP testi |
| B08 P2 web retry içeriği siliyor | `fde6015` | Webe mobildeki `visibleAttemptContent` eşdeğeri eklendi; retry mesajı yerinde kalır, yeni metin gelene kadar önceki cevap ve kaynaklar korunur. | `apps/web/tests/retry.test.ts` ([istemci kanıtı](audit_fix_p6_clients.txt)) |
| B10 P2 katalog değişimi ve quote version | — | Düzeltilmedi; KNOWN_LIMITATIONS'da belgeli sınır olarak kalır. | — |
| B11 P2 belge özetleri | bu belge commit'i | README/KNOWN_LIMITATIONS/AI_USAGE/acceptance başı güncel SHA ve test sayısıyla hizalandı. | — |

## Son kapı (uygulama commit'i `fde6015ba5b18772effcb480c4577e5f2cad46d9`)

| Kontrol | Komut | Sonuç |
|---|---|---|
| Tam backend (yeniden build) | `docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml --profile test run --build --rm --no-deps -e EVIDENCE_COMMIT_SHA=<sha> test pytest -q` | **451 passed**, exit 0 ([kayıt](audit_fix_final_backend.txt)) |
| Golden dışa aktarımı | aynı override, `-e GOLDEN_REPORT_PATH=/evidence/audit_fix_final_golden.json ... pytest -q tests/golden/test_chat_golden.py` | 22 passed, 0 failed/error/skipped/not_run; 22 kayıt da `fde6015` ([kayıt](audit_fix_final_golden.txt), [JSON](audit_fix_final_golden.json)) |
| Ruff | `... test ruff check app tests` | exit 0 ([kayıt](audit_fix_p6_ruff.txt)) |
| İstemciler | `npm test`, `npm run lint`, `npm run typecheck`, `npm --prefix apps/web run build` | 24 passed; hepsi exit 0 ([kayıt](audit_fix_p6_clients.txt)) |
| Teslim/kaynak | `python3 scripts/check_delivery.py` | exit 0; 12 kaynak dosya byte aynı ([kayıt](audit_fix_final_delivery.txt)) |

Önceki 402 testin tamamı değişmeden geçiyor; +49 backend (`test_audit_regressions.py`) ve +2 istemci testi eklendi.

## Ortam ve sınırlar

- Testler sırayla, tek test konteyneri 512 MB/1 CPU, swap kapalı override ile koştu; shm/bellek limitleri artırılmadı.
- test-db `/dev/shm` (64 MB) biriken 4319 geçici DB'nin istatistikleriyle doldu; bir kez segfault ile kurtarma moduna girdi, sonra shm hatası verdi. Mustafa'nın bu oturumdaki
  açık onayıyla yalnız `tbr_test_*` DB'leri silindi (4319 → 0, korunan DB listesi aynı), test-db iki kez stop/start edildi,
  volume'lara ve `db` servisine dokunulmadı ([kanıt](audit_fix_testdb_cleanup.txt)). Son olarak test-db durduruldu ([kayıt](audit_fix_testdb_stop.txt)).
- Demo DB/API/web bu turda çalıştırılmadı; canlı DB'ye yazılmadı. Yeni fiziksel cihaz, temiz clone veya video gözlemi yapılmadı.
- Denetimin kendi probe betikleri, rapor JSON'larını üzerine yazdığı için yeniden çalıştırılmadı; aynı mesajlar
  regresyon dosyasında aynı HTTP/DB yolundan doğrulanıyor.
- Kapsam sınırlı Türkçe dilbilgisidir; genel doğal dil kapsamı iddia edilmez. Belirsiz durumda soru sorulur, mutasyon yapılmaz.
- Push yapılmadı.
