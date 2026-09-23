# Yeniden denetim bulgularının çözümü — 2026-09-23 (v10)

Kaynak: Codex bağımsız yeniden denetimi `reports/reaudit_20260923.md` (aday `01d77c6` / uygulama `fde6015`,
86/100, backend 51/60; 83 ek varyantta 15 yanlış mutasyon, 4 gereksiz netleştirme, 1 eksik politika yanıtı).
Uygulayan: Claude, Mustafa'nın açık talimatıyla ("kalan kısımları kapatalım"), faz faz ve her faz ayrı commit.

Yaklaşım: bu tur bulguları tek tek cümle yamasıyla değil, **kapsam** düzeyinde kapattım (fiyat sınırının neye
uygulandığı, komutun hangi alıntı/cümlecikte olduğu, miktarın hangi biçimde yazıldığı, özelliğin hangi ürüne ait
olduğu). Denetimin 83 varyantının tamamı `apps/api/tests/test_reaudit_matrix.py` içinde kalıcı HTTP/DB testi oldu;
denetim dışında aynı sınıflardan 19 yeni ifadeyle kendi saldırgan probe'larımı da ekledim (`test_hardening_variants`).
Şema, executor, mutations, tool sözleşmeleri, DTO, contracts, Compose, `data/source/` ve golden fixture değişmedi.

## Bulgu → düzeltme → kanıt

| Bulgu | Commit | Düzeltme | Kırmızı → yeşil |
|---|---|---|---|
| **R01 P1** toplam bütçe birim sınırına dönüşüyor; **U03** `Birim bütçem` reddi; **U02** `para birimi TRY` ikinci tutar sayılıyor | `f3ceb18` | `price_limit_scope`: sınır **total** (toplam, hepsi, tamamı, tümü, bütün, birlikte, sepet/teklif tutarı, tutar), **unit** (birim, adet başı, tanesi) veya belirsiz **budget** (bütçe, harcama) olarak sınıflanır. Total her zaman, budget yazmada ve çok adetli okumada netleştirilir; açık birim kapsamı öncelikli. `has_unparsed_money` artık yalnız tutara bağlı para ifadesini (5.000 lira, ₺5.000, beş bin lira) veya binlik çıplak ikinci tutarı (`bütçem 5.000`) sayar; `para birimi TRY`/`kaç TL` sınır değildir. `8.500 TL` ile `8500 TL` değerle karşılaştırılır. | [red](reaudit_fix_pA_red.txt) 10 failed → [green](reaudit_fix_pA_green.txt) |
| **R02 P1** tek tırnak içindeki komut çalışıyor; **U01a** `Benden onay alındı` reddi; **U01b** alıntı tüm mesajı kapatıyor | `2ec066d` | Düz tek tırnak ve backtick alıntı sayılır; açılış/kapanış kelime sınırında olmalı, Türkçe kesme ekleri (`Air'i`, `TL'ye`) alıntı değildir. Alıntıdaki komut, alıntı dışında komut yoksa mesajı salt okuma yapar; varsa planner yalnız alıntı dışı talimatla çalışır. `yazarsam/söylersem` aktarılan söz; gerçekleşmiş onay (`onay alındı`) komut, ertelenmiş onay (`önce onay al`) değil. Birinci şahıs soru (`ekleyelim mi`) ve komut + olumsuz komut karışımı notice ile açıklanır. | [red](reaudit_fix_pB_red.txt) 8 failed → [green](reaudit_fix_pB_green.txt) |
| **R03 P1** `adet: 2`, `2'şer`, `- 2 adet`, `1 / 2 adet` | `025c821` | Birim-önce (`adet:`/`miktar=`), dağıtma (`2'şer`, `ikişer`, `1'er`), ayrık işaret ve kesir biçimleri soru üretir; ayrık eksi miktarı işaretler, birim önündeki kesir reddedilir. `tek adet`, tam genişlikli `２` çalışır. | [red](reaudit_fix_pC_red.txt) 7 failed → [green](reaudit_fix_pC_green.txt) |
| **R04 P1** değiştirmede hedef özelliği (QR/2D) kayboluyor | `06a758b` | Hedef özellikleri kaynak ürünün katalog etiketleri çıkarılarak değil, **konumla** bulunur: öndeki adlı kaynaktan sonraki metin, yoksa hedefin hemen önündeki sıfatlar ve sonrası, ayrıca `;`/`stoklu` hedef cümleciği. Kaynağın sıfatları (`QR'lı BlueScan Air'i`) yalnız kaynağı tarif eder. | [red](reaudit_fix_pD_red.txt) 3 failed → [green](reaudit_fix_pD_green.txt) |
| **R05 P1** baştaki `QR zorunlu;` atlanıyor; **R06 P1** `ve` sonrası fiyat sorusu eklemeye dönüşüyor; **R08 P2** test kanıtı | `1cfafb5` | Komuttan önceki `;` cümlecikleri: özellik → istenen **her** ürüne bağlanır, ürün → soru, diğer → bağlam (SCN-008 aynı). Kendi ekleme fiili olmayan ve soru/bilgi isteyen ürün cümleciği (`fiyatı ne?`, `kaç TL`, `fiyatını göster`) eklenmez, netleştirilir. R08: test boş olmayan arama ve kalıcı plan adımında `qr` etiketini doğrular; mutasyon anındaki `REQUIRED_FEATURE_MISSING` reddi `test_mutations.py`'de. | [red](reaudit_fix_pE_red.txt) 6 failed → [green](reaudit_fix_pE_green.txt) |
| **R07 P2** `Stoğu biten ürünü bekleyebilir miyim?`; boş-done UI etiketi | `3b1dda6` | stok bitti/tükendi/yok, stoksuz, backorder, bekleme + soru → gerçek `stock_rule` (KNE-STOCK-001); `stokta olan` (SCN-021) etkilenmez, adı geçen ürün yine aranır. Web: metinsiz tamamlanmış yanıt `Yanıt tamamlandı.` gösterir. 83 varyant matrisi eklendi. | matris [red](reaudit_fix_matrix_red.txt) 22 failed/61 passed → 83/83; [pF](reaudit_fix_pF_green.txt) |
| Kendi probe'larım (aynı sınıflar) | `3e5aa4d` | `BlueScan Air 2 ekle`, `2x`, `Air'den 3 daha ekle` 1'e düşmez (birimsiz sayı; ürün adındaki model numarası maskelenir, fiyat mesajları önce). Dative `Sepete ... ekle` toplam sayılmaz. `maliyet/fatura/ödeme` belirsiz bütçe. | [red](reaudit_fix_pG_red.txt) 5 failed → [green](reaudit_fix_pG_green.txt) |
| **R09 P2** README iddiaları geniş | belge commit'i | README başlığı yalnız kanıtlananı söyler; B10 açık; testlerin ASGI HTTP route + izole test PostgreSQL olduğu, demo API/web'in başlatılmadığı yazılı. | — |
| **B10 P2** katalog değişimi quote version | — | Bilinçli olarak düzeltilmedi; KNOWN_LIMITATIONS. | — |

Matrisin 22 kırmızısı Codex'in 20 uyuşmazlığı + benim ek koşulum: `NO_CHANGE` beklenen salt-okuma dışı mesajlarda
kullanıcıya neden değişmediğini söyleyen notice istenir (`ekleyelim mi?`, `Air ekle; Eco ekleme`). İkisi de düzeltildi.

## Son kapı (uygulama `3e5aa4d1f5c56dba8961146a1544d96d422f6668`)

| Kontrol | Komut | Sonuç |
|---|---|---|
| Tam backend (yeniden build) | `docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml --profile test run --build --rm --no-deps -e EVIDENCE_COMMIT_SHA=<sha> test pytest -q` | **604 passed**, exit 0, 122 sn ([kayıt](reaudit_fix_final_backend.txt)) |
| Golden dışa aktarımı | aynı override, `-e GOLDEN_REPORT_PATH=/evidence/reaudit_fix_final_golden.json ... pytest -q tests/golden/test_chat_golden.py` | 22 passed, 0 failed/error/skipped/not_run; 22 kayıt `3e5aa4d` ([kayıt](reaudit_fix_final_golden.txt), [JSON](reaudit_fix_final_golden.json)) |
| Ruff | `... test ruff check app tests` | exit 0 ([kayıt](reaudit_fix_pG_ruff.txt)) |
| İstemciler | `npm test`, `npm run lint`, `npm run typecheck`, `npm --prefix apps/web run build` | 25 passed; hepsi exit 0 ([kayıt](reaudit_fix_pF_clients.txt)) |
| Teslim/kaynak | `python3 scripts/check_delivery.py` | exit 0; 12 kaynak byte aynı ([kayıt](reaudit_fix_final_delivery.txt)); `git diff 88165fb HEAD -- data/source` 0 satır |

Sayılar: 451 önceki test aynen geçiyor; +83 matris, +70 `test_audit_regressions.py` örneği; istemci 24 → 25.
`git diff 01d77c6 HEAD -- apps/api/tests`: 397 ekleme, 2 silme. Silinen 2 satır R08 testinin eski imzası ve
çağrısıdır; test parametreli hâle gelip assertion eklenerek **güçlendirildi**, gevşetilmedi.

## Ortam ve sınırlar

- Testler sırayla, tek test konteyneri 512 MB/1 CPU override'ı ile koştu; shm/bellek limiti artırılmadı.
- Mustafa bu tur için yalnız `tbr_test_*` test DB temizliğini onayladı. Temizlikler: Codex'ten kalan 1694 → 0;
  bu turun kendi test koşularının ürettiği 2247 → 0 ve 1589 → 0. Her seferinde korunan DB listesi aynı, sonra
  test-db stop/start (volume'a dokunulmadı). Kanıt: [temizlik kaydı](reaudit_fix_testdb_cleanup.txt); sonda test-db
  durduruldu ([kayıt](reaudit_fix_testdb_stop.txt)). Son temizlik kaydı final commit'ten sonra dosyaya eklendiği için
  final backend kaydında "tracked modifications: 1" bu rapor dosyasıdır, uygulama kodu değil.
- Codex uygulaması repoda arka planda git çalıştırıyor; bir kez 10 dakikalık sahipsiz `.git/index.lock` kaldı
  (lsof boş, git süreci yok) ve silindi, sonra kısa süreli kilitler için yeniden deneme kullanıldı.
- Testler `httpx.ASGITransport` ile gerçek FastAPI route'larını ve izole test PostgreSQL'i kullanır. Demo DB/API/web
  başlatılmadı; canlı Uvicorn/proxy SSE zamanlaması, temiz clone, fiziksel cihaz ve video bu tur **not_run**.
- Sınırlı Türkçe dilbilgisi; genel doğal dil kapsamı iddia edilmez. Muhafazakâr kurallar bazı meşru mesajlarda
  gereksiz netleştirme üretebilir (örn. `%7 indirimle ekle` birimsiz sayı, `kalemin tamamını 9.000 TL altında
  alternatifle değiştir` toplam kelimesi, fiyat bağlamında dört haneli yıl). Bunlar mutasyon yapmaz.
- `build_plan` daha da büyüdü; kapsam yardımcıları ayrı ve test edilebilir, ama saf bir "çözümleme sonucu" nesnesine
  refactor teslim sonrası iştir.
- Push yapılmadı.
