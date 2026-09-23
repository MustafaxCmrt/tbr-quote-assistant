# Dördüncü yeniden denetim bulgularının çözümü — 2026-09-23 (v13)

Kaynak: Codex bağımsız dördüncü yeniden denetimi `reports/reaudit4_20260923.md` (aday `c63e5cd` / uygulama `ae69ff9`,
90/100, backend 54/60; eski 337 denemede beklenmeyen mutasyon yok; 91 yeni denemede 24 beklenti dışı kayıt: 11 P1 tanığı
üç grupta — W01 fiyat sınırı, W02 onay/teyit, W03 adsız kaynakta genel alternatif; P2: W04 kayıtlı alternatif dışı öneri,
UX11–UX13 gereksiz netleştirme; OBS01 executor guard'ının 422'si).
Uygulayan: Claude, Mustafa'nın önceki turlardaki talimatı doğrultusunda ("doğruysa implemente geç"), faz faz ve her faz ayrı commit.

Codex'in 91 denemesi (87 önceden yazılmış + 4 ayırıcı) oracle'larıyla kalıcı HTTP/DB testine çevrildi
(`apps/api/tests/test_reaudit4_matrix.py`). Düzeltmeden önce **24 kırmızı / 67 yeşil**, Codex'in sayısıyla birebir
([kayıt](reaudit4_fix_matrix_red.txt)). Ortak doğrulayıcıya yalnız tam öneri listesi oracle'ı eklendi (`recommendations`,
Codex'in `s_read_good`/`s_dpi_read_good` beklentisi). Şema, executor, mutations, tool sözleşmeleri, DTO, contracts,
migration, Compose, istemciler, `data/source/` ve golden fixture değişmedi.

## Bulgu → düzeltme → kanıt

| Bulgu | Commit | Düzeltme | Kırmızı → yeşil |
|---|---|---|---|
| **W01 P1** `beş yüzü/beş bini geçmesin/aşmasın`, `500'den fazlasını ödeyemem` fiyat sınırını açmıyor; limit üstü öneri/ekleme | `3e09e50` | Üç ayrı tanıma, hepsi okuma ve yazmada aynı giriş kapısında: (1) yazılı sayı çekim ekini taşıyabilir (`yüzü`, `bini`, `yüzden`, `dördü`); (2) `…'den fazlası/azı` hangi fiil gelirse gelsin tutarı sınırlar; (3) **tutar biçiminden bağımsız**: fiyat adı (`fiyat/ücret/tutar/bedel/maliyet`) ile aynı cümlede `geçmesin/aşmasın/fazla olmasın` varsa fiyat sınırıdır. Tutar çözülemezse arama yapılmadan sorulur. Yan kazanç: `fiyatı 8.500 TL'yi geçmesin` artık 8.500 birim tavanı olarak çözülüyor (önceden soruyordu). Zamir `ona/onu`, `saat beşe kadar` sayı sayılmaz. | 5 ([pA](reaudit4_fix_pA_check.txt)) |
| **UX11 P2** `en çok 3 iş günü`, `en fazla 2 adet` fiyat sorusu | `3e09e50` | Adet/süre birimine bağlı `en fazla/en çok/max/azami N` fiyat değil; `iş günü` süre birimi. | 2 |
| **W02 P1** `Onay var, doğru mu?`, `İzin verildi, öyle mi?`, `Onay var sanırsan`, `Onay var gibi görünüyor; teyit ettikten sonra` ekliyor | `3b99cf3` | Verilmiş onay artık bitişik sözcüğe göre değil, **ifadesinin tamamıyla** (önceki komut fiilinden sonrakine ya da cümle sonuna kadar) değerlendirilir. Soru eki/etiket soru (`mı`, `doğru mu`, `değil mi`), çekince (`gibi`, `galiba`, `sanırım`), aktarım (`diye`, `dedi`) veya koşul (`ise`, `sanırsan`, `verildiyse`) varsa onay bekliyor sayılır; komut fiili olmadan `?` ile biten onay da öyle. Kullanıcı hâlâ bir kontrol istiyorsa (`teyit et`, `doğrula`, `kontrol`) onay bekler. | 5 ([pB](reaudit4_fix_pB_check.txt)) |
| **UX12 P2** `Onay kesinleşti`, `İzin çıktı`, `Onaylıdır` reddediliyor | `3b99cf3` | Bu olumlu biçimler (ve `geldi`) izin listesinde; aynı ifade kontrolünden geçer (`Onay kesinleşti mi?` salt okuma). | 3 |
| **W03 P1** `QR zorunlu okuyucuyu stoklu alternatifle değiştir` QR'yi düşürüp BC-120'ye değiştiriyor | `f5b3ac5` | Açık hedef dalındaki kural genel alternatif dalına da uygulandı: adsız kaynakta yalnız kaynak isminin kendi sıfatları (`QR'lı okuyucuyu`) kaynağındır; alternatifin önündeki başka özellik sorulur. Alternatifin kendi sıfatları (`QR'lı alternatifle`, `kablosuz stoklu alternatifle` — `77ccd81`) hedef koşuludur. | 1 ([pC](reaudit4_fix_pC_check.txt)) |
| **W04 P2** kaynak ürün veya kayıtsız aday öneriliyor | `f5b3ac5` | Kayıtlı alternatifi olmayan kalemde aramadan durulur. Genel alternatif sorgusundan metinde kalan ID/SKU'lar (kaynağın kendisi) çıkarılır; arama yalnız kayıtlı alternatif ID'leriyle sınırlanır. Planlanan ve yürütülen arama aynı argümanlarla çalışır. | 3 |
| **OBS01** `BluePrint 80 miktarını 2 adede güncelle; 58 mm zorunlu` executor'da 422 | `f5b3ac5` | Güncelleme/`daha`/`toplam`/kaldırma kalemi, belirtilen özellik veya ölçüyü taşımıyorsa planlayıcı HTTP 200 ile mutasyonsuz sorar. Executor guard'ı kaldırılmadı. | 1 |
| **UX13 P2** `Air'in QR'lı modelini`, `58mm stoklu alternatifle`, `80 mm BluePrint 80 …` gereksiz ret | `f5b3ac5` | Ölçüler (`80mm`, `80 mm`) sıfat öbeğine girer; iyelik eki (`Air'in`) kaynak öbeğini kapatmaz, baş isim (`modelini`) kaynağı tamamlar; genel dalda tek adı geçen kaynak doğrudan kaynaktır. Negatif eş: adı geçen kaynağın kendi öbeğindeki özellik o kalemde yoksa sorulur (`58mm BluePrint 80 ürününü …`, `Air'in 1D modelini …`). | 4 |
| **U10 P2** | — | Davranış değişmedi; belgeli, teslim engeli değil. | — |
| **B10 P2** | — | Bilinçli olarak düzeltilmedi; KNOWN_LIMITATIONS. | — |

Denetimin "tüm Türkçe biçimleri çözmek şart değil" uyarısına uyuldu: yeni bir sayı ayrıştırıcısı yazılmadı. Fiyat
sınırının **tutar ayrıştırmasından bağımsız** tanınması (3. madde) W01 sınıfını kapatan asıl kuraldır; tek tek yeni sözcük
eklemek değildir.

## Kendi probe'larım

Aynı sınıflardan 32 yeni ifade (`test_own_probe`), beklentileri koşudan önce yazıldı. v12 uygulama koduna (`c63e5cd`,
`git archive` ile ayrı klasöre çıkarılıp test konteynerine salt okunur bağlandı) karşı koşuldu
([kayıt](reaudit4_fix_own_probes_on_v12.txt)): **24/32 v12'de başarısız**, 8'i iki sürümde de geçen kontrol eşi.

| Sınıf | v12'de | Örnekler |
|---|---|---|
| Yanlış kalıcı mutasyon | 10 | `ücreti dört bini aşmasın` ekledi; `Galiba onay var`, `Onay var; önce teyit et`, `Müdür onay var dedi` ekledi; `Kablosuz zorunlu okuyucuyu stoklu alternatifle`, `Okuyucuyu QR'lı alternatifle` BC-120'ye, `Okuyucuyu kablosuz stoklu alternatifle` kablosuz olmayan BC-120'ye değiştirdi; `Air'in 1D modelini`, `58mm BluePrint 80 ürününü` çelişkili kaynakla değiştirdi; `58 mm BluePrint 80 ürününü kaldır` 80mm kalemi kaldırdı |
| Limit üstü öneri | 4 | `yarım milyonu geçmesin`, `beş yüzden fazlasını ödeyemem`, `beş yüze kadar`, `500'ün üzerinde olmasın` |
| Kayıtlı alternatif dışı öneri | 2 | kaynak ID'si sorguda kaldı; alternatifi olmayan Saha Satış Kiti |
| Executor 422 (planlayıcı yerine) | 2 | `toplam 2 adet olsun; 58 mm zorunlu`, `1 adet daha ekle; 58 mm zorunlu` |
| Gereksiz netleştirme | 6 | `fiyatı 8.500 TL'yi geçmesin` (okuma/yazma), `En fazla 3 adet`, `en çok 5 iş günü`, `Onay geldi`, `Air'in QR'lı ürününü` |

## Son kapı (uygulama + test `77ccd81b87403bf397b93dfd558f1e83818bcf53`)

| Kontrol | Komut | Sonuç |
|---|---|---|
| Tam backend (yeniden build, 512 MB/1 CPU/swap 0) | `docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml --profile test run --build --rm --no-deps -e EVIDENCE_COMMIT_SHA=<sha> test pytest -q` | **1015 passed**, exit 0, 215 sn ([kayıt](reaudit4_fix_final_backend.txt)) |
| Golden dışa aktarımı | aynı override, `-e GOLDEN_REPORT_PATH=/evidence/reaudit4_fix_final_golden.json ... pytest -q tests/golden/test_chat_golden.py` | 22 passed; JSON'da 22 kayıt `passed`, hepsi `77ccd81` ([kayıt](reaudit4_fix_final_golden.txt), [JSON](reaudit4_fix_final_golden.json)) |
| Ruff | `... test ruff check app tests` | exit 0 ([kayıt](reaudit4_fix_final_ruff.txt)) |
| İstemciler ve teslim | `npm test`, `npm run lint`, `npm run typecheck`, `npm --prefix apps/web run build`, `python3 scripts/check_delivery.py` | 25 passed; hepsi exit 0; `git diff 88165fb HEAD -- data/source` 0 satır; web/mobil/contracts/migration/Compose farkı (v12'ye göre) boş ([kayıt](reaudit4_fix_final_clients.txt)) |

Sayılar: 892 önceki test aynen geçiyor; +91 denetim matrisi, +32 kendi probe. `git diff c63e5cd HEAD -- apps/api/tests`:
yalnız ekleme, **silinen satır 0**; ortak doğrulayıcıya eklenen tek şey isteğe bağlı tam öneri listesi assertion'ı. Hiçbir
mevcut beklenti gevşetilmedi; bu turda `safe(...)` kullanılmadı. Uygulama farkı yalnız `planner.py` ve
`normalization.py`, +175/−33; test farkı +156/−0.

## Ortam ve sınırlar

- Testler sırayla, tek test konteyneri 512 MB/1 CPU override'ı ile koştu; shm/bellek limiti artırılmadı. Bir dar koşu
  shm dolduğu için 284 altyapı hatası verdi (`asyncpg.exceptions.DiskFullError: could not resize shared memory segment … No space left on device`; kod hatası değil). Temizlik ve UX13 düzeltmesinden sonra aynı komut 890/890 geçti; ilk koşunun kaydı aynı dosya adıyla (`reaudit4_fix_pC_check.txt`) bu yeniden koşuda üzerine yazıldı.
- Mustafa bu tur için yalnız `tbr_test_*` test DB temizliğini onayladı ("Evet, sil (Önerilen)"). Codex'ten kalan 1181 DB,
  sonra bu turun koşularının ürettikleri (2393, 966, 898) silindi; korunan DB listesi her seferinde aynı, volume'a
  dokunulmadı ([temizlik kaydı](reaudit4_fix_testdb_cleanup.txt)). Sonda test-db durduruldu, çalışan konteyner yok
  ([kayıt](reaudit4_fix_testdb_stop.txt)).
- Testler `httpx.ASGITransport` ile gerçek FastAPI route'larını ve izole test PostgreSQL'i kullanır. Demo DB/API/web
  başlatılmadı; canlı Uvicorn/proxy SSE zamanlaması, temiz clone, fiziksel cihaz ve video bu tur **not_run**.
- Yeni muhafazakâr davranışlar (mutasyon yapmazlar): fiyat adıyla aynı cümlede `geçmesin/aşmasın` varsa tutar
  çözülemezse sorulur; onay mesajında `teyit/doğrula/kontrol` geçerse onay bekler; adı geçen kaynağın kendi öbeğindeki
  özellik kalemde yoksa sorulur; kayıtlı alternatifi olmayan kalemde arama yapılmaz.
- Push yapılmadı.
