# v6 — bin içeren fiyat sınırının öneride kaybolması

Bağımsız Claude denetiminin bulgusu doğrulandı. v5’in süre/adet/model yanlış alarmını gideren
komşuluk kuralı, araya giren `bin` çarpanını kaçırıyordu. Öneri yolunda fiyat netleştirmesi
atlanıyordu; kullanıcı denetiminde sınırsız arama ve limit üstü stoklu aday gösterildi.
Önceki regresyon testleri `bin` sözcüğünü yalnız `altında` ile kapsıyordu. Bu boşluk önceki
uygulamada ve test incelemesinde kaçtı; 335 testin geçmesi bütün fiyat biçimlerini güvenceye almıyordu.
Yazıyla `on bin` örneği v4’te de bulunuyordu; bütün örnekler v5’in yeni hatası diye sunulmaz.

Kod commit’i: `fa3352b3d14cb5738166907eb673b3ae5f203284`.
Yerel aday: `demo-candidate-20260922-v6`. Push yapılmadı.

## Düzeltme ve sınırı

Üretimde yalnız `apps/api/app/services/normalization.py` değişti: **+9/-2 satır**, 29–31’de ortak
tutar sonu örüntüsü, 39’da sınır işareti ve 48’de para birimiyle kullanımı. `bin`, para birimi veya
sınır ekine doğrudan bağlıysa parasal tutarın son parçasıdır. Önündeki tutarın rakamla (`8 bin`) ya da
yazıyla (`on bin`, `yüz bin`) olması bu güvenlik kararını değiştirmez. Birim araya giriyorsa
(`8 bin adede kadar`) parasal ilişki kurulmaz. Model kodunun içinden parça alınmaz.

Değer ayrıştırması genişletilmedi; `8 bin` 8000’e dönüştürülmez. Güvenli sonuç netleştirmedir.
Planner, executor, şema, migration, DTO, istemciler ve orijinal source/golden fixture değişmedi.
Mevcut assertion’lar korunarak `test_safety_review.py` içine **35 ek parametrik örnek** eklendi.

## Gereksinim / test kanıtı

| Gereksinim | Kesin test adı |
|---|---|
| 8 bine kadar / 8 bin liraya kadar / 8 bin TL’ye kadar / 10 bin liradan ucuz / on bin liraya kadar / 8 bin TL civarı; ayrıca yüz bin, sekiz bin, TRY ve ₺ civarı varyantları | `test_bin_money_expression_has_ceiling_intent` (10 helper) |
| Her biçim öner ve ekle yollarında fiyat netleştirmesi, boş öneri, search/mutasyon tool’u yok, receipt yok, DTO/sürüm/tüm satırlar aynı | `test_bin_ceiling_never_becomes_unbounded_search` (20 gerçek HTTP/izole PostgreSQL) |
| Yazıyla süre/adet ve BIN8 model kodu fiyat sınırı değildir | `test_written_number_with_non_money_unit_is_not_ceiling` (5 helper) |
| v5’in 5 okuma örneği: normal yanıt, gerçek politika kaynağı veya sınırsız normal ürün araması | `test_non_monetary_read_has_no_ceiling_or_mutation` |
| 8500 TL’ye kadar kesin filtre; para birimsiz tutar/lira/₺/8 bin altında netleştirmesi | `test_ceiling_never_disappears_from_read_or_write` |
| Normal kaç TL/adet fiyat soruları | `test_price_information_is_not_a_ceiling_or_mutation` |
| Altı adet asla 1 adet eklemeye dönüşmez | `test_written_six_never_defaults_to_one` |

Son incelemede aynı kontrolün `8 bin ₺ civarı` biçimini de kaçırdığı görüldü. Bu ek örnek
önce helper + HTTP öneri yolunda kırmızıya bağlandı: [2 failed, 37 passed, 102 deselected;
exit1](p1_bin_ceiling_currency_red.txt). Para birimi son eki artık aynı tutar parçasını kullanır.
İlk tam koşu (367 passed, 268046f) [ilk çıktı](p1_bin_ceiling_full_initial.txt) ve
[ilk golden](p1_bin_ceiling_golden_initial.json) içinde tarihsel olarak korundu. Aşağıdaki
son koşu son uygulama SHA’sına aittir; ilk koşunun SHA/metadata alanları değiştirilmedi.

## Gerçek koşular ve exit kodları

Tam argv, UTC, base commit ve ham çıktı bağlantılardadır. Kırmızı ve dar yeşil sırasında base SHA
v5 belge commit’idir; yeni test/kod henüz commit edilmemiştir. Tam paket commit edilmiş v6 kodunda
çalıştı. Golden SHA git’ten programatik alındı; 22 senaryonun her birinde aynı gerçek SHA doğrulandı.

| Koşu | Exit | Sonuç |
|---|---:|---|
| `pytest -q tests/test_safety_review.py` kırmızı | 1 | [19 failed, 119 passed](p1_bin_ceiling_red.txt): 9 öneri + 1 yazıyla ekleme netleştirmesi + 9 helper başarısız |
| `pytest -q tests/test_safety_review.py tests/unit/test_normalization.py` | 0 | [182 passed, 19.10s](p1_bin_ceiling_green_final.txt) |
| `docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml --profile test run --build --rm --no-deps … test pytest -q` | 0 | [370 passed, 65.90s; tam argv](p1_bin_ceiling_full.txt) |
| Tam koşunun golden export’u | 0 | [22 passed; 0 failed/error/skipped/not_run](p1_bin_ceiling_golden.json) |
| `uv run --directory apps/api --locked ruff check app tests` | 0 | [ruff](p1_bin_ceiling_ruff_final.txt) |
| `python3 scripts/check_delivery.py` | 0 | [12 kaynak dosya byte aynı, tanınan private dosya/anahtar kontrolleri](p1_bin_ceiling_delivery_final.txt) |
| `python3 scripts/check_git_history.py` | 0 | [erişilebilir yerel geçmiş taraması](p1_bin_ceiling_history_final.txt) |
| `env API_BIND_HOST=0.0.0.0 docker compose up -d --build --no-deps --wait api` | 0 | [API healthy](p1_bin_ceiling_api_build.txt) |
| Salt okunur demo/runtime kontrolü | 0 | [önce](p1_bin_ceiling_runtime_before.txt), [sonra](p1_bin_ceiling_runtime_after.txt) |
| `docker compose --profile test stop test-db` | 0 | [stop](p1_bin_ceiling_testdb_stop.txt) |

Testler mevcut 512 MB / 1 CPU / test konteynerinde swap kapalı override ile sırayla çalıştı.
Başlangıç host swap 889.31 MB, ara 881.31/873.31 MB, son 873.31 MB; ölçümlerde artış gözlenmedi.
Limit artırılmadı, test-db durduruldu; down -v/reset/veri silme yapılmadı.

API yeniden kurulumunda `--no-deps` ile seed/migration çalıştırılmadı. Canlı demo DB’ye yazılmadı;
HTTP mutasyon testleri ayrı test DB’lerindeydi. Canlıda yalnız GET kullanıldı: Q-1001/Q-1004 dahil
10 teklifin tam DTO’su önce/sonra aynı; direkt API/web proxy/mobilin ayarlı adresi aynı veriyi döndürdü.
Çalışan 27 API Python dosyasının hash’i yerel dosyalarla aynı. API telefon için LAN’da bırakıldı.
Mevcut salt okunur `p2_price_intent_runtime_check.py` betiği yeniden kullanıldı.

Kalan sınırlar: tutar çözümleyicisi hâlâ sınırlı; genel yazıyla sayı/para anlayışı iddiası yok.
`Altı adet` güvenli ama fiyat odaklı ret mesajını korur; ayrı mutasyon fiyat niyeti koruması
muhafazakâr kalır. Retry eski kalıcı planı korur; düzeltme yeni mesajlarda değerlendirilir.
Yeni fiziksel telefon/video veya temiz clone doğrulaması yapılmadı. İstemci kodu değişmediği için
bu tur istemci testleri yeniden çalıştırılmadı; eski sonuçlar tarihsel kanıttır.

## Son tur / v7

Onaylı test DB temizliği, para sözcüğü + sınır işareti güvenlik ağı ve ayrıştırıcının dondurulması: [son doğrulama raporu](final_ceiling_resolution.md). Önceki kanıtlar tarihsel olarak korunur.
