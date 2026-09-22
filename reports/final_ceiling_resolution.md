# Son tur — test DB temizliği ve fiyat güvenlik ağı (v7)

Kod: `995847783713dc1924881dee086785ec904380e5`. Yerel aday: `demo-candidate-20260922-v7`.
**Fiyat ayrıştırıcısı bu turdan sonra DONDURULDU.** Push yapılmadı.

## Temizlik ve değişiklik

Mustafa’nın ilettiği bağımsız koşu 290 passed / 80 errors ile test-db shared-memory kapasite
sorununa düşmüştü. Onaylı temizlikte gerçek sayım **2163 → 0**: yalnız `test-db` servisindeki
literal `tbr_test_` önekli DB’ler düşürüldü. README’nin DROP üretimi kullanıldı; ON_ERROR_STOP ile
hata gizlenmedi. `postgres`, `tbr_test`, `template0`, `template1` korundu. `db` servisine, canlı
`tbr_quotes` verisine veya volume’lara dokunulmadı. Kanıt: [cleanup](final_testdb_cleanup.txt),
[kullanılan dar kapsamlı betik](final_testdb_cleanup.py). Sonraki testler yeniden geçici DB oluşturur.

Üretimde yalnız `normalization.py` **+7/-2 satır**: para sözcüğü (`TL/TRY/lira*/₺`) ve sözcük
sınırlı PRICE_CEILING_MARKERS işareti birlikteyse sınır niyeti true olur. Tutar çözülemezse mevcut
planner netleştirmesi arama/öneri/mutasyonu durdurur. Bitişik tutar ve bin kuralları korunur;
ayrıştırıcıya yeni tutar biçimi eklenmedi. Şema/migration/executor/DTO/istemci/source/golden fixture
aynı; mevcut assertion’lar zayıflatılmadı. `test_safety_review.py` içinde **24 ek parametrik test** var.

## Gereksinim → kanıt

| Gereksinim | Test |
|---|---|
| 8K TL / sekiz yüz lira / beş yüz lira, öner ve ekle: notice, search/öneri/mutasyon yok; receipt/DTO/sürüm/satırlar aynı | `test_currency_marker_safety_net_prevents_unbounded_search` |
| Para sözcüğü + sınır işareti genel kuralı | `test_currency_word_and_marker_form_safety_net` |
| Sözcük içindeki rastlantısal marker/para parçası kabul edilmez | `test_safety_net_respects_word_boundaries` |
| Para sözcüksüz süre/adet/model; Bin adete kadar indirim sorusu | `test_non_monetary_read_has_no_ceiling_or_mutation` |
| Sınır işaretsiz kaç TL/adet fiyat soruları | `test_price_information_is_not_a_ceiling_or_mutation` |
| TL’ye kadar, altında, altı, TL’nin altında 8500 filtresi ve tüm önceki fiyat korumaları | `test_ceiling_never_disappears_from_read_or_write` |
| Altı adet sıfır mutasyon | `test_written_six_never_defaults_to_one` |
| Q-1001 ekleme (adet2/sürüm+1/receipt1), Q-1004 replace (<=9000/geçmiş/sürüm+1/receipt1), kaynaklı iade (sıfır etki) | `test_frozen_parser_demo_messages` |
| Backorder olumlu/şüpheli onayları ve 22 golden | Mevcut testler dahil tam paket |

## Gerçek komutlar / exit

Tam argv, UTC, SHA ve çıktılar bağlantılarda bulunur. Testler sırayla mevcut 512 MB/1 CPU/test
konteynerinde swap kapalı override ile çalıştı. Test DB ayrı servistir; shm_size/limit artırılmadı.

| Koşu | Exit | Sonuç |
|---|---:|---|
| `python3 reports/final_testdb_cleanup.py` | 0 | 2163 → 0, hedef dışı DB listesi aynı |
| `pytest -q tests/test_safety_review.py` kırmızı | 1 | [7 failed, 158 passed](final_ceiling_red.txt); 3 HTTP öneri + 4 helper |
| `pytest -q tests/test_safety_review.py tests/unit/test_normalization.py` | 0 | [206 passed, 22.22s](final_ceiling_green.txt) |
| `docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml --profile test run --build --rm --no-deps … test pytest -q` | 0 | [394 passed, 69.19s, 0 error](final_ceiling_full.txt); tam paket, filtre/skip yok |
| Aynı tam koşunun golden export’u | 0 | [22 passed, 0 failed/error/skipped/not_run](final_ceiling_golden.json); tüm SHA’lar gerçek kod commit’i |
| `uv run --directory apps/api --locked ruff check app tests` | 0 | [ruff](final_ceiling_ruff.txt); ilk Decimal yazım uyarısı davranış değişmeden düzeltildi, ilk çıktı korundu |
| `python3 scripts/check_delivery.py` | 0 | [source/teslim](final_ceiling_delivery.txt): 12 kaynak dosya byte aynı |
| API LAN build/start (`--no-deps`, seed çalıştırmadan) | 0 | [API healthy](final_ceiling_api_build.txt) |
| Mevcut salt okunur runtime kontrol betiği, before/after | 0 | [önce](final_ceiling_runtime_before.txt), [sonra](final_ceiling_runtime_after.txt) |
| `docker compose --profile test stop test-db` | 0 | [test DB durduruldu](final_ceiling_testdb_stop.txt) |

Kırmızı/dar yeşil/ruff base SHA v6 belge commit’idir (pending değişiklikler vardı); son tam paket
commit edilmiş uygulamada çalıştı ve golden SHA git’ten programatik alındı. Golden metadata değiştirilmedi.

Canlı demo DB’ye yazılmadı. 10 teklifin tam DTO’su (Q-1001/Q-1004 dahil) API yeniden kurulumundan
önce/sonra aynı; direkt API/web proxy/mobilin ayarlı API adresi eşit. Çalışan 27 Python dosyasının
hash’i yerelle aynı. Bu fiziksel cihaz gözlemi değildir. API telefon için LAN’da; test-db kapalı.
Host swap başlangıç/ara/son ölçümleri 865.31 MB; artış gözlenmedi.

Kalan sınır: para sözcüğü ve bitişik rakam olmayan yazıyla tutarlar (`sekiz yüze kadar`) hâlâ
kaçabilir. Para ve süre ifadeleri aynı mesajdaysa muhafazakâr kural gereksiz netleştirebilir.
Altı adet güvenli retle kalır; retry eski planı korur, düzeltme yeni mesajlara uygulanır.
Yeni fiziksel prova/video/temiz clone veya istemci testi bu tur yapılmadı. Freeze gereği yeni
ayrıştırıcı genişletmesi yapılmayacak; sonraki iş fiziksel demo ve teslimdir.
