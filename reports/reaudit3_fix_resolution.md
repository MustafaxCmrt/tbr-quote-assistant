# Üçüncü yeniden denetim bulgularının çözümü — 2026-09-23 (v12)

Kaynak: Codex bağımsız üçüncü yeniden denetimi `reports/reaudit3_20260923.md` (aday `3fa6fcd` / uygulama `05fe5cd`,
89/100, backend 53/60; 228 eski deneme 228/228 geçti; 109 yeni denemede 23 P1 tanığı üç grupta: V01 fiyat, V02 onay,
V03 değiştirme hedefinin QR koşulu; P2: V04 ölçü, U08–U10 gereksiz netleştirme).
Uygulayan: Claude, Mustafa'nın önceki turlardaki talimatı doğrultusunda ("doğruysa implemente geç"), faz faz ve her faz ayrı commit.

Codex'in 109 denemesi (102 önceden yazılmış + 7 ayırıcı) oracle'larıyla kalıcı HTTP/DB testine çevrildi
(`apps/api/tests/test_reaudit3_matrix.py`). Düzeltmeden önce **39 kırmızı / 70 yeşil**, Codex'in sayısıyla birebir
([kayıt](reaudit3_fix_matrix_red.txt)). Şema, executor, mutations, tool sözleşmeleri, DTO, contracts, Compose,
istemciler, `data/source/` ve golden fixture değişmedi.

## Bulgu → düzeltme → kanıt

| Bulgu | Commit | Düzeltme | Kırmızı → yeşil |
|---|---|---|---|
| **V01 P1** `azami/max/üst sınır/en çok 500`, `beş yüz`, `bin`, `500 ödeyebilirim` fiyat kontrolüne girmiyor; limit üstü öneri/ekleme | `8b2cba0` | Sınır sözcüğüne bağlı sayı ve para birimli yazılı tutar (`beş yüz TL`) artık **fiyat niyetinin kendisini** açar. İkinci tutar kontrolü de aynı yardımcıyı kullanır. Böylece okuma ve yazma aynı giriş kapısından geçer ve tutar çözülemezse arama yapılmadan soru sorulur. `ödeyebilirim`, `harcayabilirim`, `geçmesin`, `aşmasın` sayıdan sonra gelen sınır sözcüğüdür. Sayıdan sonra yalnız çekim eki (`500'ün altında`) arada olabilir; `12 ay ödeme` gibi süreler etkilenmez. | 14 ([pA](reaudit3_fix_pA_check.txt)) |
| **U08 P2** `birim fiyatının tutarı` toplam sanılıyor | `8b2cba0` | Birim fiyat tamlaması tutarla birlikte birim kapsamı sayılır; `sepet tutarı` toplam kalır. | 1 |
| **V02 P1** `önce iznimi iste`, `iznimi aldıktan sonra`, `onay var mı…` işlemi çalıştırıyor | `fb1021a` | `izin/izni/iznim` da `onay` ile aynı izin listesine tabi. Verilmiş ifade bir soru ya da koşul içindeyse (`onay var mı`, `onay var ise`, `alındı mı`) verilmiş sayılmaz, komut salt okuma kalır. | 4 ([pB](reaudit3_fix_pB_check.txt)) |
| **U09 P2** `onayım mevcut/tamdır`, `onayı sağladım` reddediliyor | `fb1021a` | Bu verilmiş biçimler izin listesine eklendi (soru/koşul kontrolü korunarak). | 3 |
| **V03 P1** `Air'i QR destekli cihaz olan Eco ile` ve `QR zorunlu; okuyucuyu Eco ile` QR'yi düşürüyor | `2caf2c1` | Çekim eki (`Air'i`) kaynak öbeğini kapatır; ardından gelen sıfatlar hedefindir. Kaynağı ancak ekli baş isim (`Air QR'lı ürününü/modelini`) uzatır; ekisiz `cihaz/ürün olan` hedefin ilgi cümlesidir. Ürün adı geçmeyen özellik cümleciği (`QR zorunlu;`) kaynak adı olsa da olmasa da hedefe bağlanır. Adsız kaynakta yalnız kaynak isminin kendi sıfatları (`Kablosuz okuyucuyu`) kaynağındır; hedefin önündeki diğer özellik sorulur. | 5 ([pC](reaudit3_fix_pC_check.txt)) |
| **V04 P2** ayrı cümlecikteki `58mm/300dpi` uygulanmıyor; genel alternatifte ölçü düşüyor | `17a1642` | Kalan tüm dallar ortak `features()` kullanır (başta, sonda, `ve` sonrası). Genel `stoklu alternatif` değişiminde adı geçen kaynağın öbeği dışındaki her özellik alternatifin koşuludur. Arama yalnız kalemin kayıtlı alternatiflerini aday alır, kalemin kendisini asla (tek arama çağrısı ve golden `query_contains` korunur). | 6 ([pD](reaudit3_fix_pD_check.txt)) |
| **U10 P2** önceki cümledeki ürün, `ile` bağlacı, ortak nesnede bağlam sözcüğü | `83fe030` | Davranış değiştirilmedi; not/örnek ürününü eklememe korumasının belgeli bedeli (KNOWN_LIMITATIONS). Denetçi bunları teslim engeli saymadı. Kalıcı testte `safe(...)`: denetçinin beklediği ürünler **ya da** hiçbir mutasyon denenmeden değişmeyen teklif. Bilgi kaynağı beklentisi yalnız değişiklik sonucuna uygulanır. | 6 ([pE](reaudit3_fix_pE_check.txt)) |
| **Test belleği** tam koşu 512 MB'ta OOM (exit 137) | `ae69ff9` | Aşağıda. | — |
| **B10 P2** katalog değişimi quote version | — | Bilinçli olarak düzeltilmedi; KNOWN_LIMITATIONS. | — |

### Tam koşuda bellek sızıntısı (yeni, bu turda bulundu)

İlk son kapı koşusu 892 testin yaklaşık %85'inde **exit 137** ile öldü ([kayıt](reaudit3_fix_final_backend_oom.txt)).
Bellek sınırı (512 MB) artırılmadı; kök neden ölçüldü ([ölçüm](reaudit3_fix_memory.txt)). FastAPI 0.141.1 endpoint
çağrı kimliklerini modül düzeyinde bir `lru_cache` içinde tutuyor. `create_app` içindeki `/health/ready` endpoint'i
ise `app` değişkenine closure ile bağlıydı. Bu yüzden her testin app'i ve DB engine'i (derlenmiş SQL önbelleğiyle
birlikte) bellekte kalıyordu: test başına yaklaşık 0,65 MB. Endpoint artık engine'e `request.app` üzerinden ulaşıyor;
davranış aynı. Aynı 288 testte RSS 259 MB → 127 MB oldu, canlı nesne sayısı sabitlendi. Üretimde tek app olduğu için
bu yalnız test sürecini etkiliyordu, ama 762 testlik önceki koşu da sınıra yakındı.

### Kendi probe'larım

Aynı sınıflardan 21 yeni ifade (`test_own_probe`). Bunlar düzeltmeden sonra yazıldı; v11 koduna (`3fa6fcd`, ayrı git
worktree) karşı koşuldu ([kayıt](reaudit3_fix_own_probes_on_v11.txt)): **8/21 v11'de başarısız**. 7'si yanlış mutasyondu
(`onay alındı mı bilmiyorum`, `onay var ise`, `izni gelince`, `QR'lı model olan Eco ile`, `QR zorunlu, okuyucuyu uygun
alternatifle`, `QR zorunlu okuyucuyu Eco ile`, `Air ürününü QR'lı stoklu alternatifle`). 1'i doğru istekte yanlış
sonuçtu (`80mm zorunlu; fiş yazıcı ekle`).

## Son kapı (uygulama + test `ae69ff97287bec637c725398ea884b317e1ccd88`)

| Kontrol | Komut | Sonuç |
|---|---|---|
| Tam backend (yeniden build, 512 MB/1 CPU) | `docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml --profile test run --build --rm --no-deps -e EVIDENCE_COMMIT_SHA=<sha> test pytest -q` | **892 passed**, exit 0, 188 sn ([kayıt](reaudit3_fix_final_backend.txt)) |
| Golden dışa aktarımı | aynı override, `-e GOLDEN_REPORT_PATH=/evidence/reaudit3_fix_final_golden.json ... pytest -q tests/golden/test_chat_golden.py` | 22 passed; JSON'da 22 kayıt `passed`, hepsi `ae69ff9` ([kayıt](reaudit3_fix_final_golden.txt), [JSON](reaudit3_fix_final_golden.json)) |
| Ruff | `... test ruff check app tests` | exit 0 ([kayıt](reaudit3_fix_pF_ruff.txt)) |
| İstemciler ve teslim | `npm test`, `npm run lint`, `npm run typecheck`, `npm --prefix apps/web run build`, `python3 scripts/check_delivery.py` | 25 passed; hepsi exit 0; `git diff 88165fb HEAD -- data/source` 0 satır ([kayıt](reaudit3_fix_final_clients.txt)) |

Sayılar: 762 önceki test aynen geçiyor; +109 denetim matrisi, +21 kendi probe. İstemci kodu değişmedi.
`git diff 3fa6fcd HEAD -- apps/api/tests`: 162 ekleme, 1 silme. Silinen satır `if knowledge:`. Yeni hâli bilgi kaynağı
beklentisini yalnız `safe(...)` + değişmeyen teklif durumunda atlıyor; bu birleşimi kullanan önceki bir vaka yok
(doğrulandı), yani hiçbir mevcut assertion gevşemedi. Uygulama farkı: `main.py`, `planner.py`, `normalization.py`,
+86/−32.

## Ortam ve sınırlar

- Testler sırayla, tek test konteyneri 512 MB/1 CPU override'ı ile koştu; shm/bellek limiti artırılmadı. Bellek
  tanısı için geçici bir pytest eklentisi (`reports/_memprobe.py`) kullanıldı ve silindi, commit edilmedi.
- Mustafa bu tur için yalnız `tbr_test_*` test DB temizliğini onayladı ("Evet, sil"). Codex'ten kalan 960 DB, sonra bu
  turun koşularının ürettikleri (1224, 1153, 1163, 522, 920, 626, 318, 775) silindi; korunan DB listesi her seferinde
  aynı, volume'a dokunulmadı. Kanıt:
  [temizlik kaydı](reaudit3_fix_testdb_cleanup.txt). Sonda test-db durduruldu ([kayıt](reaudit3_fix_testdb_stop.txt)).
- Testler `httpx.ASGITransport` ile gerçek FastAPI route'larını ve izole test PostgreSQL'i kullanır. Demo DB/API/web
  başlatılmadı; canlı Uvicorn/proxy SSE zamanlaması, temiz clone, fiziksel cihaz ve video bu tur **not_run**.
- Yeni muhafazakâr davranışlar: fiyat bağlamı dışında da sınır sözcüğüne bağlı sayı fiyat sorusu açar (örn. `en çok 2
  ürün`); soru/koşul içindeki onay salt okumadır; adsız kaynakta hedefin önündeki bağlanamayan özellik sorulur. Mutasyon
  yapmazlar.
- Push yapılmadı.
