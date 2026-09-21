# Teslim öncesi mimari + güvenlik denetimi — çözüm kaydı

21 Eylül 2026. Salt okunur mimari/güvenlik denetimi 9 kod bulgusu (B1–B9) ve 5 belge bulgusu (D1–D5)
bildirdi. Her bulgu uygulamadan önce kaynak kodda doğrulandı. Önerilen düzeltmelerden ikisi
yanlış çıktı; B3'ün güvenlik gerekçesi de tutmadı. Bunlar aşağıda gerekçesiyle ayrıldı. B1, ADR-012
("auth/RBAC kapsam dışı") kararından küçük bir sapma olduğu için Mustafa'nın açık onayıyla uygulandı.

Önce yazılan regresyonlar düzeltmeden önce başarısız oldu:
[backend](hardening_regressions_before.txt) 4 failed / exit1 (B2'nin "Task exception was never
retrieved" izi dahil), [istemci](hardening_clients_before.txt) 3 failed / exit1. Düzeltme sonrası:
[backend odaklı](hardening_regressions_after.txt) 12 passed / exit0,
[istemci](hardening_clients_after.txt) 22/22 / exit0.

| Bulgu | Karar | Değişiklik / kanıt |
|---|---|---|
| B1 Auth yok; README LAN adımı admin yazmayı ağa açıyor | **Düzeltildi** | 6 yazma ucu `X-Admin-Key` ister (`secrets.compare_digest`); anahtar yoksa 503. `init_env.py` üretir, eski `.env`'e yalnız eksik anahtarı ekler. Vite proxy başlığı sunucu tarafında ekler. `test_admin_writes_require_the_configured_key_and_reads_stay_open`, `..._fail_closed_without_server_key` |
| B2 Commit sorgusu `OSError`/`TimeoutError` alınca akış `error` olmadan bitiyor | **Düzeltildi** | Sorgu 3 sn timeout ile çalışır; her hata `committed=true` kabul edilir ve terminal `error` olayı gönderilir. `test_stream_emits_error_frame_when_commit_probe_cannot_reach_database` |
| B3 `topic` serbest metin → her cevaba içerik enjeksiyonu | **B1 ile kapandı; `Literal` uygulanmadı** | Örnekteki saldırı zaten geçerli olan `topic:"fallback"` değerini kullanıyor; `Literal` onu durdurmaz. Asıl koruma yazma anahtarı. Serbest topic bilinçli: web formu `datalist` önerisiyle yeni konu kabul ediyor, `test_knowledge_crud_live_sources_and_context_lists` bunu doğruluyor |
| B4 Gövde boyut sınırı / kaynak sınırı yok | **Düzeltildi** | ASGI sınırı 256 KiB: `Content-Length` ve chunked gövde ayrı ayrı sayılır, 413 `PAYLOAD_TOO_LARGE`. 64 KiB yerine 256 KiB: şemaya uygun en büyük bilgi kaydı çok baytlı karakterlerle 64 KiB'ı aşabilir. Compose: api 512 MB / 256 pid, web 1 GB / 512 pid, `no-new-privileges`. `test_oversized_bodies_are_rejected_before_parsing` |
| B5 Bilinmeyen SSE olay tipi istemcide ölümcül | **Uygulanmadı, belgelendi** | Önerilen "bilinmeyen olayı atla" düzeltmesi `event_seq` sırasında boşluk bırakır, `reduceChatEvent` bu durumda "Akış sırası geçersiz" hatası fırlatır. Sunucu ve istemciler aynı repodan çıkıyor; katı sözleşme bilinçli. KNOWN_LIMITATIONS |
| B6 Mobil "API adresi ayarlanmamış" mesajı ağ hatasına dönüşüyor | **Düzeltildi** | Adres kontrolü `try` dışına alındı. `missing API address is reported as configuration...` |
| B7 Sunucu sıfırlanınca mobil oturum kalıcı geçersiz | **Düzeltildi (daraltılmış)** | Oturum yalnız stream açılışı 404 dönerse sıfırlanır (`SessionNotFoundError`), her hatada değil; mesaj kimliği korunur. `unknown server session is distinguishable...` |
| B8 Mobil teklif doğrulanmadan render; web ErrorBoundary yok | **Düzeltildi** | `isQuote` şekil kontrolü; geçersiz yanıt son geçerli teklifi "eski" gösterir. Web kökünde ErrorBoundary (typecheck/lint/build ile; bileşen testi yok). `mobile rejects a quote payload...` |
| B9 Web lint ve kontrat senkronu kapı dışında | **Düzeltildi** | Kök `lint` web kaynaklarını ve testlerini kapsar; `npm test` önce `check:contracts` çalıştırır. Web typecheck `npm --prefix apps/web run build` içinde |
| D1 Rate limit / eşzamanlılık tavanı yok | **Belgelendi** | KNOWN_LIMITATIONS |
| D2 Vite dev sunucusu teslim artefaktı | **Zaten belgeli** | Web loopback'e bağlı kalır; B1 web'i LAN'a açmaz |
| D3 İndirim canlı ürün alanlarından hesaplanıyor | **Belgelendi** | `quotes.py` canlı ürün satırlarını okur; fiyat snapshot'ı etkilenmez. KNOWN_LIMITATIONS |
| D4 `action_key` oturumdan bağımsız | **Uygulanmadı: öneri tehlikeli** | Anahtara `session_id` eklenirse aynı mesaj başka oturumdan (ör. B7 sonrası retry) gelince işlem ikinci kez uygulanır. Şu anki davranış `IDEMPOTENCY_CONFLICT` ile reddetmek; bilinçli ve belgeli |
| D5 `/api/chat/sessions` oturum kimliği döndürüyor | **Uygulanmadı: öneri regresyon** | PDF s.2 web admin'in oturum/tool loglarını görmesini ister; log ekranı mobil oturumlarını bu listeden seçer. Kimliği kaldırmak bu özelliği bozar. KNOWN_LIMITATIONS'ta güvenilen ağ sınırı olarak yazıldı |

## Tam doğrulama

| Kontrol | Sonuç |
|---|---|
| [Tam backend, gerçek PostgreSQL](hardening_full_backend.txt) | **229 passed / exit0** (225 + 4 yeni; 22 golden dahil) |
| [ruff](hardening_ruff.txt), [typecheck](hardening_typecheck.txt), [lint](hardening_lint.txt), [web build](hardening_web_build.txt), [kontrat](hardening_contracts.txt) | hepsi exit0 |
| [Teslim taraması](hardening_delivery.txt) | exit0; kaynak 12/12 aynı |
| Ana demo stack'i yeniden build (api, web sırayla; LAN bağlantısı korunarak) | Q-1001 tam DTO ve PRD-BC-110 build öncesi/sonrası aynı |
| [Çalışan stack: `check_admin_runtime.py --lan`](hardening_runtime_after.txt) | exit0: anahtarsız/yanlış anahtarlı yazma 401 (loopback ve LAN); web proxy geçerli yazma 200, geçersiz 422; okuma 200; 300 KB gövde 413; web'in sunduğu dosyalarda anahtar yok. Build öncesi aynı script: [exit1](hardening_runtime_before.txt), LAN'dan anahtarsız yazma doğrulamaya ulaşıyordu |
| [SSE smoke, API + web proxy](hardening_smoke_stream.txt) | exit0; 16 parça ~0,8 sn, kademeli |

İlk tam koşu 3 failed + 147 error verdi: [kayıt](hardening_full_backend_shm_full.txt). Neden kod değil, ortam:
ana test-db'de testlerin teşhis için sakladığı 2.348 veritabanı PostgreSQL paylaşımlı istatistik
belleğini Docker'ın 64 MB `/dev/shm` sınırının üstüne çıkardı (`DiskFullError`). Mustafa'nın onayıyla
yalnız bu `tbr_test_*` veritabanları silindi ([kayıt](hardening_testdb_cleanup.txt)); volume'lar,
demo DB ve temiz kurulum stack'i korundu. README'ye aynı temizlik komutu eklendi.

Uygulanmayanlar: mikroservis/Redis/kuyruk, tam RBAC, rate limiter, production hosting,
`data/source/` değişikliği. Fiziksel iPhone ile yeni doğrulama bu kayıtta yoktur: **not_verified**.
