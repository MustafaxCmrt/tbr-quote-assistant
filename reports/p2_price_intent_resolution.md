# P2 — fiyat niyetinde yanlış alarm, v5

Teşhis doğrulandı ve dar kapsamda düzeltildi. `has_price_ceiling_intent` içindeki `kadar/ucuz`
kontrolü metnin herhangi bir rakamını kabul ediyordu. Süre, adet ve model rakamları fiyat
netleştirmesi üretiyordu. Bu bir yanlış ret bulgusuydu; yeni bir fiyat/stok ihlali gösterilmedi.

Uygulama commit’i: `3a07ceceb07f16c4e2efb0c4998233032b294484`.
Yerel aday etiketi: `demo-candidate-20260922-v5`; belge commit’i de aynı uygulama kodunu taşır.
Push yapılmadı.

## Değişiklik ve kapsam

- `apps/api/app/services/normalization.py:32`: tek geniş rakam kontrolü yerine tutar + isteğe bağlı
  para birimi/hâl eki + `kadar/ucuz` komşuluğu aranır. Ondalık/apostrof sınırları için ham metin
  kullanılır; model kodunun ortasından sayı alınmaz. Üretim diff’i +9/-1 satır, yalnız bu dosya.
- `apps/api/tests/test_safety_review.py`: 41 ek parametrik örnek; mevcut assertion'lar korunur.
  5 HTTP/DB yanlış alarm örneği, yardımcı fonksiyon varyasyonları, 8 yeni P1 read/write kontrolü
  ve yazıyla altı adedin mutasyon yapmaması dahil. Bu dosyada toplam 106 test vardır.
- Planner, şema, migration, executor, DTO, istemciler, source/golden fixture değişmedi.

## Gereksinim → kalıcı kanıt

| Gereksinim | Test |
|---|---|
| Teslim/süre/adet sorularında boş notice, gerçek delivery_policy/warranty kaynakları; aramada sınırsız filtre; sıfır receipt ve DTO/satır/sürüm korunması | `test_non_monetary_read_has_no_ceiling_or_mutation` |
| Adet, süre, 2D/4G/Model80/80 mm fiyat tavanı değildir; doğrudan parasal ilişki ve desteklenmeyen tutarlar korunur | `test_ceiling_marker_requires_adjacent_amount` |
| Para birimsiz apostroflu tutar, lira/₺/8 bin/üstü olmayan netleştirmesi; TL’ye kadar ve TL’den ucuz için 8500 kesin filtresi, read/write sıfır etki | `test_ceiling_never_disappears_from_read_or_write` |
| Kaç TL / 3 adet fiyatı normal okuma; şimdiye kadar helper davranışı aynı | `test_price_information_is_not_a_ceiling_or_mutation`, `test_ceiling_intent_distinguishes_information` |
| Altı adet, varsayılan 1 adede dönüşmez; receipt/sürüm/satır değişmez | `test_written_six_never_defaults_to_one` |
| Önceki fiyat sınırı, stok/onay, idempotency ve golden davranışları korunur | Tam paket: 335 passed; 22 golden passed, 0 failed/error/skipped/not_run |

## Gerçek koşular

Komutların tam argv, UTC, SHA, exit ve ham çıktıları aşağıdaki dosyalardadır.
Compose test koşuları mevcut 512 MB / 1 CPU / konteyner swap kapalı override ile sırayla çalıştı.

| Koşu | Exit | Sonuç / çıktı |
|---|---:|---|
| Kırmızı: `pytest -q tests/test_safety_review.py` | 1 | 17 failed, 89 passed — [red](p2_price_intent_red.txt); 5 gerçek HTTP hatası + 12 helper yanlış alarmı |
| Dar yeşil: `pytest -q tests/test_safety_review.py tests/unit/test_normalization.py` | 0 | 147 passed — [green](p2_price_intent_green.txt) |
| Tam: `docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml --profile test run --build --rm --no-deps … test pytest -q` | 0 | 335 passed, 60.42s — [tam komut/çıktı](p2_price_intent_full.txt) |
| Golden export, tam koşunun içinde | 0 | 22 passed, her senaryoda yukarıdaki gerçek SHA — [JSON](p2_price_intent_golden.json) |
| `uv run --directory apps/api --locked ruff check app tests` | 0 | [ruff](p2_price_intent_ruff.txt) |
| `python3 scripts/check_delivery.py` | 0 | Source 12 dosya byte aynı; taranan private dosya/anahtar biçimleri yok — [teslim](p2_price_intent_delivery.txt) |
| API LAN build/start, yalnız API (`--no-deps`) | 0 | [build](p2_price_intent_api_build.txt) |
| Demo GET ve kod hash doğrulaması | 0 | [önce](p2_price_intent_runtime_before.txt), [sonra](p2_price_intent_runtime_after.txt) |
| `docker compose --profile test stop test-db` | 0 | [stop](p2_price_intent_testdb_stop.txt); volume silinmedi |

İlk kırmızı/dar yeşil/ruff raporlarında base SHA v4 belge commit’idir; pending değişiklikler
vardır. Tam paket/export commit edilmiş v5 uygulama kodunda çalıştı; SHA git’ten programatik alındı.

## Demo, kaynaklar ve kalan sınırlar

- Canlı demo DB’ye yazılmadı. API yeniden kurulumunda seed/migration çalıştırılmadı.
  10 teklifin tam DTO’su (Q-1001/Q-1004 dahil) önce/sonra değişmedi; direkt API, web proxy ve
  mobilin ayarlı API adresi aynı DTO’ları döndürdü. Bu fiziksel telefon gözlemi değildir.
- Çalışan API’nin 27 Python dosyasının hash’i yerel dosyalarla birebir aynı.
- Ölçülen swap önce/ara/sonra 470.62 MB; artış gözlenmedi. Test DB kapalı, API telefon için LAN’da.
- Genel Türkçe sayı çözümleyicisi eklenmedi. Para birimsiz tutar/lira/₺/8 bin netleştirmeleri;
  `Altı adet` için güvenli ama fiyat odaklı ret sürüyor. Mutasyon yolundaki ayrı muhafazakâr
  `has_price_intent` kontrolü değişmedi; karmaşık ekleme cümleleri hâlâ gereksiz soru üretebilir.
- İstemci kodu/testleri bu dar değişiklikte yeniden çalıştırılmadı; v4’ün 22 istemci testi tarihsel kanıttır.
  Yeni temiz clone, fiziksel prova ve video yapılmadı. Kusursuz genel dil anlayışı iddiası yoktur.

## v6 bağımsız denetim eki

Bağımsız Claude incelemesinde v5’in bin içeren bazı para sınırlarını öneri yolunda kaçırdığı bulundu. Önceki bin testleri yalnız altında işaretçisini kapsıyordu. Kırmızı/yeşil kanıt ve dar düzeltme: [v6 P1 çözüm raporu](p1_bin_ceiling_resolution.md). Önceki test sonuçları bütün dil biçimlerinin güvenli olduğunu kanıtlamaz.
