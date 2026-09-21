# Kabul kanıtları — 2026-09-21

**Teslim kabulü henüz tamamlanmadı.** F00–F07 ana kapıları tamam; F07 cihaz sürüm metadatası ve geniş erişilebilirlik kontrolleri
ayrıca açık. F08 için golden JSON ve Git geçmişi taraması hazır; bağımsız Claude review ve
F09 son temiz kurulum/video/erişim kapısı açık. Aşağıdaki sonuçlar kendi raporlarındaki commit ve kapsama aittir.

Son tam backend koşusu: [151 passed](f08_full_backend.txt), 22 golden dahil.
[36 negatif hedef eşlemesi](negative_acceptance.md); NEG-10 opsiyonel provider adapter olmadığı için not_run.

| Gereksinim | Durum / doğrudan kanıt |
|---|---|
| PostgreSQL 16, Compose başlangıç sırası, Alembic ve readiness | **passed:** [F01b](f01b_acceptance.md), [boş volume başlangıcı](f01b_fresh_stack.txt), [migration drift](f01b_migration_drift.txt) |
| JSON seed 48/22/6/10/8/6; idempotency ve veri koruma | **passed:** `test_seed_preserves_all_original_fields_and_counts`, `test_repeated_seed_preserves_edits_and_concurrent_calls`; [tam backend koşusu](f06_backend_final.txt) |
| Gerçek kısa transaction, rollback, tek aktif kalem, snapshot, replace geçmişi | **passed:** [F03 test eşlemesi](f03_acceptance.md), [tam backend koşusu](f06_backend_final.txt) |
| Kalıcı receipt; aynı mesaj gerçek wrapper replay; restart | **passed:** [restart replay](f03_restart_replay.txt), [son SSE testleri](f07_reading_stream_tests.txt), [fiziksel mobil retry](f07_native_retry.txt) |
| Fiyat/stok/özellik/backorder guard; eşzamanlı değişim | **passed:** F03 eşlemesindeki guard/concurrency testleri; [tam backend koşusu](f06_backend_final.txt). Bu, bütün olası güvenlik saldırılarının denetlendiği iddiası değildir. |
| Altı tool sözleşmesi, gerçek çağrı sırası/input/kaynak/DB etkisi | **passed:** [22 golden gerçek JSON](golden_results.json), [komut ve çıktı](f08_golden_evidence_run.txt). Her senaryo ayrı PostgreSQL DB; assertion'lar kaynak fixture'dan ayrı. |
| Kaynaklı retrieval ve anahtarsız fallback | **passed:** golden kaynak kökeni, mode/provider_calls=0 assertion'ları; [F04](f04_acceptance.md). Opsiyonel LLM adapter/provider timeout **uygulanmadı**, test edilmiş sayılmaz. |
| Yeni ürün/bilgi CRUD sonrası retrieval | **passed:** [F06](f06_acceptance.md), [gerçek web eklemesi/API kontrolü](f06_demo_api.txt); demo DB'deki eklemeler korunur. |
| Gerçek kademeli SSE; commit öncesi başarılı mutation eventi yok | **passed:** [curl-N API ve web proxy zamanlaması](f07_reading_live_stream.txt), [6 SSE testi](f07_reading_stream_tests.txt). Deterministik şablon aktarımıdır, LLM token üretimi değildir. |
| UTF-8/CRLF/çoklu/yarım SSE, geçersiz zarf, kısmi hata, eski quote sürümü | **passed:** [19 istemci/parser testi](f07_retry_fix_tests.txt). Node testleri fiziksel UI testi değildir. |
| Web admin/chat/draft, ikinci istemci ve offline recovery | **passed:** [F06 gerçek tarayıcı kanıtı](f06_acceptance.md) |
| Mobil add → web aynı persisted quantity/version/tutar | **passed:** [native kayıt](native_smoke.md), [web DOM](f07_web_shared_state.txt), images/f07/native-quote-v2.png ve web-quote-v2.png |
| iPhone klavye/input/Gönder ve Bilgi aç/Kapat | **passed:** Mustafa beyanı ve [klavye görüntüsü](images/f07/native-keyboard-fixed.png); [native kayıt](native_smoke.md) |
| Son mobil cevap başlangıcını koruma ve gözle görülür kademeli yanıt | **passed:** Mustafa son sürümde parça parça geliş ve sayfanın başında kalmayı doğruladı; [native kayıt](native_smoke.md). |
| Native sürüm/cihaz bilgisi, büyük yazı/tablet/VoiceOver | **not_verified:** cihaz modeli, iOS, kurulu Expo Go sürümü henüz verilmedi; proje SDK sürümü bunların yerine yazılmadı. |
| Kaynak dosyaları değişmedi; bundle/env/key kontrolü | **passed (sınırlı tarama):** [12 source ve son iOS bundle](f07_reading_delivery.txt). Tanınmayan secret biçimleri için tam garanti değildir. |
| Git geçmişinde private path/anahtar/current local değerler | **passed (erişilebilir yerel ref kapsamı):** [history scan](f08_git_history_scan.txt). Unreachable nesneler ve yerelde olmayan remote ref'ler kapsam dışı. |
| Bağımsız Claude güvenlik kabulü | **not_run:** ayrı Codex alan incelemeleri Claude veya insan denetimi yerine yazılmadı. |
| Son sürüm fresh clone yalnız README, demo videosu ve teslim erişimi | **not_run:** önceki F01b boş volume kanıtı son sürüm fresh-clone kabulü yerine geçmez. Gönderim/erişim değişimi insan onayında. |

`test_output.txt` yeni bir test koşusu değildir; mevcut gerçek koşuların komut/sonuç indeksidir.
Başarısız ilk denemeler raporlarda korunur. `skipped`, `not_run`, `not_verified` başarı değildir.
