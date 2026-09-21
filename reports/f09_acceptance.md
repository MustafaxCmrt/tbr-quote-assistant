# F09 — Temiz kurulum ve teslim hazırlığı

21 Eylül 2026. Durum: **in_progress**; video ve gönderim yapılmış sayılmaz.
**Güncel aday v3 (`bf92756`) temiz clone provası:** [hardening_resolution.md](hardening_resolution.md#v3-temiz-clone-provası)
— 229 passed, runtime/admin anahtarı/istemci adımları exit0. Aşağıdaki tablo tarihsel v2 kaydıdır.
Doğrulanan clone commit: `81765bda71c4dd819d2b8004cf15409c8b9537bf`
(`demo-candidate-20260921-v2`); runtime son değişikliği `53b9948`.

| Kontrol | Sonuç / kanıt |
|---|---|
| Remote'dan yeni klasöre clone | exit0, [clone](f09_clone.txt); ignored dosya kopyalanmadı |
| README init/env, Compose build/up, yeni pgdata | exit0, [kurulum](f09_clean_setup.txt); ayrı tbr-f09-clean / loopback18001 ve15173; v2 named volumes, eski volume korundu |
| Gerçek PostgreSQL tam test | **225 passed / 44.48s**, exit0; [backend](f09_clean_backend.txt), 22 golden dahil |
| Alembic drift | exit0, yeni upgrade işlemi yok; aynı backend raporu |
| İstemci install/test/typecheck/lint, web build, Expo version check | 19 test passed; tamamı exit0, [istemciler](f09_clean_clients.txt) |
| Seed sayıları | 48/22/6/10/8/6; [runtime](f09_clean_runtime.txt) |
| Yeni add + aynı mesaj replay + kaynaklı politika | qty1→2, version1→2, net15980; ikinci etki yok, gerçek wrapper logları; provider_calls0 |
| DB/API restart ve tekrar seed | tam quote aynı; seed tüm tablolarda0 yeni kayıt; receipt replay kalıcı |
| Mevcut demo koruması | ana8001 Q1001 tam DTO önce/sonra eşit |
| Web görsel/AX kontrolü | Önceki v1 gözlemi tarihsel; v2 Plus spot kontrolü ayrı `f08_p2_web_spot.txt` içinde |

Runtime kontrolünün çalıştırılan kaynak kopyası: [script](f09_runtime_check_source.txt).
Bu script yeni clone için geçici `.git/f09-clone-path` dosyasını kullanır; genel kurulum komutu değildir.
V2 provası yeni runtime üzerinde tekrarlandı; önceki clone/volume silinmedi.
Docker image/npm cache bu hostta mevcuttu; cache-free farklı makine iddiası yoktur.

Fiziksel iPhone ana demo kabulü [native_smoke](native_smoke.md) içinde. Yeni clone'a telefon
bağlama testi **not_verified**; CLI typecheck/build native gözlemin yerine geçmez.
Cihaz bilgisi Mustafa tarafından bildirildi: iPhone16e, iOS26.6.2, Expo Go Client Version57.0.9/Supported SDK57.0.0 (yeni test koşusu değildir). Yeni final video, değerlendirici repo/video erişimi ve
insan onaylı gönderim hâlâ açık. F09 bu kapılar tamamlanmadan done değildir.

Git geçmişi taraması [f09_history.txt](f09_history.txt) exit0:587blob/38commit/2tag;
[source ve yerel değer taraması](f09_delivery.txt) exit0. Tanınmayan secret biçimlerine
ve fetch edilmemiş remote ref'lere ilişkin kapsam sınırı raporda korunur.
`npm ci` mevcut10moderate geliştirme bağımlılığı bildirimini tekrar gösterdi; install exit0
bu audit bildirimlerinin giderildiği anlamına gelmez (KNOWN_LIMITATIONS).

`gh repo view --json nameWithOwner,url,visibility,viewerPermission` exit0:
MustafaxCmrt/tbr-quote-assistant **PRIVATE**, mevcut kullanıcı ADMIN. Bu okuma
firma hesabının erişimini kanıtlamaz; görünürlük/izin değişmedi.

Önceki v1 demo replace rehearsal (bu rapor yenilenmedi): [f09_demo_replace.txt](f09_demo_replace.txt), exit0. README/demo sentence on isolated Q1004 changed BC120/12950 to BC110/7990, version1→2, quantity1 retained, old row replaced/history preserved, web proxy same DTO. Main demo Q1004 remained unchanged.
