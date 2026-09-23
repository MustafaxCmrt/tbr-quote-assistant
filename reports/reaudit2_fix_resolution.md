# İkinci yeniden denetim bulgularının çözümü — 2026-09-23 (v11)

Kaynak: Codex bağımsız ikinci yeniden denetimi `reports/reaudit2_20260923.md` (aday `317c5de` / uygulama `3e5aa4d`,
88/100, backend 52/60; 126 yeni denemede 27 P1 tanığı yedi grupta: N01–N07; P2: U04–U07, N08, matris oracle'ı).
Uygulayan: Claude, Mustafa'nın açık talimatıyla ("doğruysa implemente geç, bu kısmı da bitirelim"), faz faz ve her faz ayrı commit.

Önce her bulgu denetimin HTTP/DB kanıtı ve kod okumasıyla doğrulandı. Sonra Codex'in **126 denemesinin tamamı**
(117 önceden yazılmış + 9 ayırıcı) oracle'larıyla birlikte kalıcı HTTP/DB testine çevrildi
(`apps/api/tests/test_reaudit2_matrix.py`). Düzeltmeden önce **41 kırmızı** ([kayıt](reaudit2_fix_matrix_red.txt)),
her fazdan sonra azaldı, sonunda 126/126 yeşil. Şema, executor, mutations, tool sözleşmeleri, DTO, contracts, Compose,
istemciler, `data/source/` ve golden fixture değişmedi.

Yaklaşım: yeni sözcük yamaları yerine her bulgunun **kapsam kuralı** düzeltildi. Bir fiyat sınırı hangi sayıya bağlı,
bir onay verilmiş mi yoksa ertelenmiş mi, bir ürün komutun nesnesi mi yoksa not/örnek mi, bir özellik değiştirilen
ürünün mü yoksa hedefin mi? Belirsiz kalan her durumda öneri ve mutasyon yapılmaz, soru sorulur.

## Bulgu → düzeltme → kanıt

| Bulgu | Commit | Düzeltme | Kırmızı → yeşil |
|---|---|---|---|
| **N01 P1** ikinci çıplak limit (`limitim 500`, `5000.`, `5.000.`, `bütçem beş yüz`) düşüyor | `cffed90` | Bir sınır sözcüğüne bitişik sayı (`limitim 500`, `en fazla 5.000`, `500'ün altında`, yazıyla `beş yüz`) para birimi olmasa da ayrıştırılamayan limittir. Binlik çıplak sayı cümle sonu noktasında da yakalanır. Tarih (`23.09.2026`), kampanya yılı ve kimlik numarası (`model numarası 2026`) tutar sayılmaz. Kaldırılan TL tutarının yerine yer tutucu konur; `BluePrint 80 [5.000 TL] altında` yan yana düşmez. | 13 matris vakası ([pA](reaudit2_fix_pA_check.txt)) |
| **N02 P1** birim ifadesi ayrı bütçeyi yutuyor; `masrafım`, `ödeyeceğim` | `cffed90` | Mesajda birim niteliği olmayan (`birim bütçem` değil) bir toplam veya bütçe/harcama sözcüğü varsa, başka yerdeki birim ifadesine rağmen kapsam **belirsiz bütçe** olur; yazmada ve çok adetli okumada sorulur. Bütçe sözcükleri: `masraf`, `gider`, `ödeme/ödeyeceğim`, `ayırdım` eklendi. | aynı |
| **U04 P2** `fiyat tutarı` toplam sayılıyor | `cffed90` | `fiyat tutarı` tek ürünün fiyatıdır; `sepet/teklif tutarı` toplam kalır. | aynı |
| **N03 P1** alıntı içi kesme, kapanmayan alıntı, ertelenmiş onay | `f517a2e` | Tek tırnak içindeki Türkçe kesme (`'Air'i ekle'`) alıntıyı bitirmez. Kapanmayan alıntı mesajın geri kalanını alıntılar. Onay artık **izin listesiyle** okunur: işlem fiilinin yanındaki `onay` yalnız verilmiş biçimde (`onay alındı/verdim/veriyorum`, `onaylıyorum`, `onaylandı`) komutu çalıştırır. `önce onayımı almalısın`, `onay vermedim`, `onay alacağım` salt okuma. `bana danış` da ertelenmiş onaydır. | 7 ([pB](reaudit2_fix_pB_check.txt)) |
| **U06 P2** alıntı dışı `toplam 4 adet olsun` engelleniyor | `f517a2e` | Alıntı dışı komut denetimi planlayıcının desteklediği `toplam N olsun` niyetini de komut sayar. | aynı |
| **N04 P1** not/örnek içindeki ürün ekleniyor | `22460fa` | Cümleler `;` cümlecikleri gibi kapsamlanır: not/örnek cümlesindeki ürün eklenmez, sorulur. Başka bölümün `ekle` fiilini paylaşan ürün yalnız katalog/özellik/miktar sözcüklerinden oluşuyorsa nesnedir (`Air ve Eco ekle`); `not: Eco müşterinin mevcut cihazı` değildir. Tek gereksinimde iki model adı geçerse sorulur. | 3 ([pC](reaudit2_fix_pC_check.txt)) |
| **N07 P1** `QR'lı Air yerine Eco ekle` Air'i artırıyor | `22460fa` | `X yerine Y ekle` ekleme yoluna girmez; açık `değiştir` biçimi istenir. `değiştir` içeren yerine cümleleri değiştirme yolunda kalır. | 2 |
| **N05 P1** bir ürünün `1 adet`i diğerinin çıplak `2`sini gizliyor | `d01e8d8` | Birimsiz sayı denetimi başka bir üründe birimli miktar olsa da çalışır; `Air 1 adet ve Eco 2 ekle`, `2x`, tam genişlikli rakam sorulur. | 4 ([pD](reaudit2_fix_pD_check.txt)) |
| **U05 P2** bağlam sayıları (yüzde, tarih, kampanya yılı, model numarası) | `cffed90`, `d01e8d8` | `%7`, `yüzde 7`, `23.09.2026`, `2026 kampanyası`, `model numarası 80` miktar veya tutar sayılmaz. | 1 + 5 |
| **N08 P2** `58 mm` koşulu yok sayılıyor | `d01e8d8` | Mesajdaki ölçü (`58 mm`, `58mm`, `203 dpi`) katalog etiketi olarak zorunlu koşuldur: aramada ve mutasyon anındaki `required_tags` guard'ında. | 2 |
| **N06 P1** hedef önce söylenince sondaki QR/2D düşüyor | `7d9e175` | Adı geçen kaynakla her özellik **hedefin** koşuludur; yalnız kaynağın kendi isim öbeğindekiler hariç (önündeki sıfatlar, `Air'i` eki, `BlueScan Air QR'lı ürününü` gibi baş isimle kapanan sıfatlar). Sıra (`Eco ile Air'i`, `Air'i Eco ile`) ve ayraç (virgül, nokta, `;`) sonucu değiştirmez. | 4 ([pE](reaudit2_fix_pE_check.txt)) |
| **U07 P2** kaynak adından sonraki sıfat hedefe gidiyor | `7d9e175` | Aynı kural: `BlueScan Air QR'lı ürününü` kaynağı tarif eder. | 1 |
| **Matris oracle'ı (P2)** | `cffed90`, `05fe5cd` | Ortak `check_variant`: reddedilen vakada hiçbir mutasyon tool'u **denenmemeli** (yalnız uygulanmamış değil); her uygulanan mutasyon için tam bir receipt ve bir version artışı; fiyat retlerinde `recommended_product_ids == []` (eski matriste denetçinin 4 fiyat vakası dahil). Eski 83 varyant bu sıkı oracle ile de geçti. | eski 83/83 |
| **B10 P2** katalog değişimi quote version | — | Bilinçli olarak düzeltilmedi; KNOWN_LIMITATIONS. | — |

### Oracle notları

- `f_width_80mm`: denetçinin beklediği `PRD-RP-310` katalogda yok (denetçi bunu kendi raporunda oracle hatası olarak ayırdı); doğru ürün `PRD-PRN-320` ile yazıldı.
- 41 kırmızının 2'si (`p_budget_read_one`, `p_budget_read_low`) benim eklediğim "reddedilen mesaj bir notice taşır" koşulundandı. Bunlar düz öneri istekleridir; oracle'da `read` olarak işaretlendi, uygulama bunlar için değişmedi.
- `q_unapproved` (`Onay vermedim, … ekle.`): denetçi yoruma açık saydı. İzin listesi kuralıyla artık salt okuma.

### Kendi probe'larım

Her faz için aynı sınıftan 32 yeni ifade (`test_own_probe`). Bunlar düzeltmeden **sonra** yazıldı. Gerçek kusur
olup olmadıklarını görmek için aynı testler v10 uygulama koduna (`317c5de`, ayrı git worktree) karşı koşuldu
([kayıt](reaudit2_fix_own_probes_on_v10.txt)): **16/32 v10'da başarısız**. 10'u yanlış mutasyondu (ikinci limit,
birim + harcama, kapanmayan `«` alıntı, `onay alacağım`, `bana danış`, `yerine`, `Air 3 adet ve Eco 5`,
`hedef 2D olsun`, `QR zorunlu,` öneki), 1'i uyarısız okumaydı (ikinci limit sessizce düştü), 5'i gereksiz
netleştirmeydi (iki ayrı `ekle` cümlesi, `%10 indirim var mı?`, `58 mm/80 mm fiş yazıcı`, kaynağın `rugged 2D` sıfatları).

## Son kapı (uygulama + test `05fe5cd62b9951d88d915360d24978c35de48bff`)

| Kontrol | Komut | Sonuç |
|---|---|---|
| Tam backend (yeniden build) | `docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml --profile test run --build --rm --no-deps -e EVIDENCE_COMMIT_SHA=<sha> test pytest -q` | **762 passed**, exit 0, 153 sn ([kayıt](reaudit2_fix_final_backend.txt)) |
| Golden dışa aktarımı | aynı override, `-e GOLDEN_REPORT_PATH=/evidence/reaudit2_fix_final_golden.json ... pytest -q tests/golden/test_chat_golden.py` | 22 passed; JSON'da 22 kayıt `passed`, hepsi `05fe5cd` ([kayıt](reaudit2_fix_final_golden.txt), [JSON](reaudit2_fix_final_golden.json)) |
| Ruff | `... test ruff check app tests` | exit 0 ([kayıt](reaudit2_fix_pF_ruff.txt)) |
| İstemciler ve teslim | `npm test`, `npm run lint`, `npm run typecheck`, `npm --prefix apps/web run build`, `python3 scripts/check_delivery.py` | 25 passed; hepsi exit 0; `git diff 88165fb HEAD -- data/source` 0 satır ([kayıt](reaudit2_fix_final_clients.txt)) |

Sayılar: 604 önceki test aynen geçiyor; +126 denetim matrisi, +32 kendi probe. İstemci kodu bu turda değişmedi.
`git diff 317c5de HEAD -- apps/api/tests`: 243 ekleme, 14 silme. Silinen 14 satır eski matris testinin gövdesidir;
ortak `check_variant` yardımcısına taşındı ve **güçlendirildi** (mutasyon denemesi yasağı, tam receipt/version
delta'sı, fiyat retlerinde boş öneri). Eski "pozitif vakada version ve receipt artmalı" koşulu da korunuyor
(`05fe5cd`). Uygulama farkı `apps/api/app` altında iki dosya: +220/−52.

## Ortam ve sınırlar

- Testler sırayla, tek test konteyneri 512 MB/1 CPU override'ı ile koştu; shm/bellek limiti artırılmadı. Bir kez zsh
  altında çalışan komutun exit kodu yakalanamadı (zsh `PIPESTATUS` tanımaz); o koşu kanıt sayılmadı, aynı komut bash
  betiğiyle yeniden koşuldu.
- Mustafa bu tur için yalnız `tbr_test_*` test DB temizliğini onayladı ("Evet, sil"). Temizlikler: Codex'ten kalan
  1180 → 0; bu turun koşularının ürettiği 1497, 897, 1268 → 0; sonda, Codex'in yeniden denetimi temiz başlasın diye
  741 → 0. Korunan DB listesi her seferinde aynı, sonra test-db stop/start (volume'a dokunulmadı). Kanıt:
  [temizlik kaydı](reaudit2_fix_testdb_cleanup.txt); en sonda test-db durduruldu, çalışan konteyner yok
  ([kayıt](reaudit2_fix_testdb_stop.txt)).
- Faz C commit'inde ruff hatası (kümede yinelenen iki öğe) commit'ten sonra görüldü; öğeler silindi, ruff exit 0 ile
  aynı yerel commit düzeltildi (davranış değişmedi, testler aynı).
- Testler `httpx.ASGITransport` ile gerçek FastAPI route'larını ve izole test PostgreSQL'i kullanır. Demo DB/API/web
  başlatılmadı; canlı Uvicorn/proxy SSE zamanlaması, temiz clone, fiziksel cihaz ve video bu tur **not_run**.
- Bu kurallar daha muhafazakâr. Bazı meşru mesajlarda gereksiz soru üretebilirler, mutasyon yapmazlar. Örnekler:
  `BlueScan Air çok iyi. 2 adet ekle.` (komuttan önceki cümlede ürün), `X yerine Y ekle` (açık `değiştir` istenir),
  `GreenScan Eco ile BlueScan Air ekle` (`ile` bağlacı), `Air ve müşterinin istediği Eco ekle` (katalog dışı sözcük
  taşıyan nesne), fiyat bağlamında birimsiz `en fazla 3`. KNOWN_LIMITATIONS'a yazıldı.
- `build_plan` yine büyüdü; kapsam yardımcıları ayrı ve test edilebilir, ama saf bir "çözümleme sonucu" nesnesine
  refactor teslim sonrası iştir.
- Push yapılmadı.
