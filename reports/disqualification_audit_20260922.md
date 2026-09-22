# Video öncesi diskalifiye denetimi — 22 Eylül 2026

**Sonuç: Teslime hazır / diskalifiye riski yok denemez. Fiyat ve stok maddesiyle doğrudan çelişen iki P1 davranış gerçek PostgreSQL üzerinde yeniden üretildi.** Bulgular giderilmeden final video ve teslim onayı önerilmez. Bu bir inceleme; uygulama kodu değiştirilmedi.

## Kapsam ve sürüm

- Yerel HEAD: `45ef56d2a039a5c70e59b6bf4c17260aa0afdcf7`. Başlangıç çalışma ağacı temizdi.
- Case PDF'nin dört sayfası okundu; diskalifiye listesi s.3, ayrıntılı fiyat/stok kuralları s.1.
- Kök/API/web/mobil AGENTS, vault bağlamı/kararlar/takip/günlük/F09, 21–22 Eylül commit geçmişi, kaynak JSON'lar, kritik backend ve istemci durum kodu, eski kabul kanıtları incelendi.
- Güncel kodla gerçek PostgreSQL testleri, HTTP üzerinden ayrı taze veritabanlarında özel denemeler, canlı salt okunur ortak durum kontrolü, history/env/bundle taraması yapıldı.
- Çalışan API'deki 27 Python dosyasının hash'i yerel kodla aynı. Seçilmiş beş çalışan web dosyası da aynı. Bulgular yalnız eski bir aday sürüme ait değil. [Sürüm kanıtı](disqualification_versions_20260922.json).
- Demo DB resetlenmedi veya denetim için değiştirilmedi; test-db üzerinde yeni veritabanları kullanıldı ve korundu. Ücretli provider çağrısı, deploy, görünürlük değişikliği, push veya dış mesaj yapılmadı.

## Beş diskalifiye maddesi

| Madde | Sonuç | Dayanak |
|---|---|---|
| Gizli değer commit etmek | İncelenen kapsamda bulunmadı | 700 blob / 48 commit / 3 tag tarandı; yerel gizli değerler ve özel dosya yolları bulunmadı. |
| Mutasyonları sahte/mock bırakmak | Bulgu yok | SQL yazımları, transaction, row lock, kalıcı receipt, partial unique index; gerçek PostgreSQL testleri ve tarihli fiziksel mobil receipt kanıtı. |
| Kaynaksız politika cevabı | İncelenen cevaplarda doğrulanmış ihlal yok | Knowledge kayıtları gerçek retrieval'dan geliyor; renderer kaynak kimliği doğruluyor; politika golden'ları geçti. Ayrı uyumluluk yönlendirme eksikliği aşağıda. |
| Fiyat/stok kuralını açıkça ihlal etmek | **İki doğrulanmış P1** | Limit üstü öneri ve olumsuzlanmış bekleme onayıyla gerçek stok dışı ekleme. |
| Web/mobil farklı teklif durumu | Güncel veri karşılaştırmasında fark yok | 10 quote için API, web proxy ve mobilin yapılandırılmış API adresi tam DTO eşit; fiziksel ekranın bu oturumda yeniden gözlenmesi yapılmadı. |

## P1-1 — Yalnız öneri istenirken fiyat sınırı sessizce kayboluyor

**Mesaj:** `8.500 lirayı geçmeyen endüstriyel barkod okuyucu öner.`

**Beklenen:** 8.500 TL üstündeki ürün önerilmez. Para ifadesi desteklenmiyorsa sınır sorulur ve sınırsız öneri üretilmez.

**Gerçek:** HTTP 200; `trusted_constraints.max_price_try=null`. `recommended_product_ids` ve kullanıcı cevabı içinde **PRD-BC-120 / 12.950,00 TL** var. Kullanıcıya doğrudan `Stoklu aday` olarak yazılıyor. Teklif değişmiyor; ancak PDF yalnız eklemeyi değil limit üstü otomatik öneriyi de yasaklıyor.

**Neden:** `apps/api/app/services/normalization.py:53` para miktarını yalnız `TL` ile topluyor. `apps/api/app/orchestration/planner.py:219` çözülemeyen fiyat kısıtında durmayı sadece `mutating` mesajlara uyguluyor. Salt okunur yol, eksik sınırla aramaya devam ediyor (`planner.py:276–286`).

**Kontrol:** Aynı talep `8.500 TL altında ...` biçiminde gönderildiğinde `max_price_try=8500` ve limit üstü öneri yok. Bu, arama motorunun filtreyi uygulamadığı iddiası değil; filtreye aktarılmadan kaybolan kullanıcı kısıtı.

**Düzeltme yönü:** Fiyat güvenliği öneri/arama ve mutasyon için ortak olmalı; ayrıştırılamayan açık sınırda netleştirme istenmeli. Bu genel dil davranışı üzerinden doğrulanmalı; belirli deneme cümlesine exact-match eklenmemeli.

## P1-2 — Olumsuzlanmış bekleme cümlesi açık onay sayılıyor

**Bağlam:** `CUST-ANK-002`, `Q-1002`; müşteri `allow_backorder=true`, `PRD-BC-130` stok **0**.

**Mesaj:** `PRD-BC-130 1 adet ekle, bekleyebilirim demiyorum.`

**Beklenen:** Açık olumlu bekleme onayı yok; stok dışı ekleme reddedilmeli veya netleştirilmeli.

**Gerçek:** HTTP 200; `explicit_backorder_consent=true`. Gerçek `add_to_quote` çağrısında `mutation_applied=true`; DB'de **1 receipt**, **1 adet aktif/beklemeli PRD-BC-130**, teklif sürümü **1 → 2**. Bu sadece yanlış yanıt metni değil, kalıcı mutasyon.

**Neden:** `apps/api/app/orchestration/planner.py:267–271` cümlenin içinde `bekleyebilirim` geçmesini yeterli sayıyor; `demiyorum` ifadesi onayı iptal etmiyor. `services/mutations.py` içindeki guard iki boolean'ı doğru kontrol etse de kendisine yanlış üretilmiş trusted consent geliyor.

**Kontroller:** Onaysız `PRD-BC-130 1 adet ekle.` mesajı reddediliyor; olumlu `PRD-BC-130 1 adet ekle, bekleyebilirim.` mesajı bir kez ekliyor. Olumsuzlanan ifade de olumlu ifadeyle aynı etkiyi yapıyor.

**Düzeltme yönü:** Olumlu bekleme onayı, olumsuzlama/alıntı/varsayım bağlamından ayrılmalı; kesin olmayan onay mutasyona izin vermemeli.

Her iki P1 için [son deneme çıktısı](disqualification_probes_20260922_final.txt), [tam HTTP cevapları / önce-sonra DTO / gerçek tool bayrakları](disqualification_probe_20260922.json) ve [yeniden çalıştırılabilir deneme betiği](disqualification_probe_20260922.py) saklandı. Deneme komutunun exit 0 olması betiğin tamamlandığını gösterir; ürün kurallarının geçtiği anlamına gelmez. Sekiz örneğin her biri ayrı taze test DB'de çalıştı. İlk denemeler ayrı çıktıda korundu; final dosya revize edilmiş cümlelerin sonuçlarını içerir.

## Sağlam bulunan tarafların kanıtı

### Gizli değerler ve kaynak dosyalar

`python3 scripts/check_git_history.py`: exit 0; 700 blob, 48 commit, 3 tag, 316 tree. Mevcut üç gizli değer ve yerel LAN adresi değerleri açıklanmadan karşılaştırıldı. Her commit ağacında `.env` ve özel talimat dosyaları kontrol edildi. [History](disqualification_history_20260922.txt).

Kök `.env` ve `apps/mobile/.env` mevcut ve Git tarafından ignore ediliyor. Mobildeki public alan API adresi; public isimli bir secret alanı bulunmadı. Admin key Vite proxy sürecinde kalıyor. Güncel web build ve mevcut mobil export içindeki toplam sekiz dosyada üç yerel gizli değere/tanınan anahtar biçimlerine eşleşme bulunmadı. [Bundle](disqualification_bundles_20260922.json).

`python3 scripts/check_delivery.py`: exit 0; 12 orijinal kaynak dosya başlangıç commit'iyle byte düzeyinde aynı. [Teslim taraması](disqualification_delivery_20260922.txt).

Sınır: Tanınmayan secret biçimleri, erişilemeyen Git nesneleri ve ekran görüntülerinin OCR ile denetimi bu taramanın kapsamı değil. `.env` değerleri hiçbir rapora yazılmadı.

### Gerçek mutasyon ve tekrarsızlık

Executor `engine.begin()` transaction'ı altında quote/product/customer kilitlerini alıyor; gerçek mutation wrapper'ları SQL ile insert/update yapıyor. Receipt kaydı etkiyle aynı transaction içinde; başarılı tool result ancak commit sonrası yayınlanıyor. Replay de gerçek wrapper'a giriyor. Aktif ürün tekilliği PostgreSQL partial unique index ile korunuyor; replace geçmişi ve snapshot fiyat saklanıyor. Golden senaryoların DB önce-sonra, tool sırası, yasak çağrı, kaynak, stok ve tekrar istek kontrolleri geçti.

Önceki fiziksel iPhone v3 denemesi de mobil add ve aynı-message retry için applied/replayed ayrımını, tek receipt'i gösteriyor: [22 Eylül kayıtlı fiziksel deneme DB kanıtı](hardening_native_smoke_db.txt). Bu oturumda yeni fiziksel deneme yapılmış gibi sunulmaz.

### Kaynaklar ve AI kullanımı

Politika metni `get_knowledge_entries` çıktısından geliyor. `EvidenceBundle.require()` renderer'ın product/knowledge/price_rule claim kimliklerini tool kaynaklarıyla karşılaştırıyor. İade ve diğer politika golden'ları kaynaklarla, mutasyonsuz geçti. Özel aktif lisans iadesi denemesi de `KNE-RET-001` ve ek kaydını döndürdü.

PDF s.3'te AI kullanımı diskalifiye nedeni değil; `AI_USAGE.md` teslimatlar arasında. PDF s.1 deterministik orkestrasyona açıkça izin veriyor. Projede AI kullanımı belgelenmiş; runtime provider adaptörü yok ve SSE deterministik cevabın parçalara bölünmesi. Videoda bunu LLM token üretimi/LLM tool calling olarak anlatmamak gerekir.

### Web ve mobil ortak durum

Her iki istemci `/api/quotes/{id}` verisini okuyor; fiyatları yerelde yeniden hesaplamıyor. Geç gelen daha eski sürümü ve başka seçime ait cevabı reddeden kontroller var. Görünür/aktifken 2,5 saniyelik yenileme ve odak/yenileme kontrolleri kullanılıyor.

Bu oturumda 10 orijinal quote ID için üç ulaşım yolunun tam JSON DTO'ları eşit bulundu: direkt API, web proxy, mobil `.env`'indeki gerçek API adresi. [Karşılaştırma](disqualification_live_shared_20260922.json). Bu, Mac'ten yapılan bağlantı/veri doğrulamasıdır; iPhone ekran gözlemi değildir. Yenileme aralığı sırasında kısa gecikme olabilir; önceki ve yeni sürümler video çekiminde aynı anda karşılaştırılmamalı.

## Diskalifiye diye sınıflandırılmayan ek bulgular

1. **Uyumluluk sorusunda yönlendirme eksikliği:** `Starter lisansı offline çalışır mı?` mesajında `compatibility` knowledge çağrısı yok; `PRD-SW-520` önerisi ve yalnız fallback knowledge kayıtları dönüyor. Starter hakkında açık yanlış politika iddiası üretilmediği için bunu kanıtlanmış kaynaksız politika diskalifiyesi saymıyorum. Ancak soru cevaplanmıyor; fallback kaynağı uyumluluk kanıtı yerine geçmez. `planner.py:276–289` salt okunur kolunda uyumluluk yönlendirmesi eksik; uyumluluk çağrısı mutasyon gereksinimleri kolunda mevcut.
2. **GitHub yerel kodun gerisinde:** `git ls-remote --heads origin main` ile gerçek remote HEAD `3820642` doğrulandı. Yerelde `7fb0dac`, `7220b29`, `45ef56d` henüz remote'da yok. Son ikisi web form/knowledge topic değişiklikleriyle ilişkili. [Kesin sürümler](disqualification_versions_20260922.json). Remote'a otomatik push yapılmadı.
3. **Teslim belgelerinin güncel özetleri çelişiyor:** KNOWN_LIMITATIONS başındaki cihaz sürümü henüz kaydedilmedi cümlesi, daha sonraki kabul kayıtlarıyla uyuşmuyor. Eski F08 kabul raporları tarihsel başarıdır; bu rapordaki yeni P1'leri kapatmaz. Final video/test/kod aynı düzeltilmiş SHA üzerinde eşleştirilmeli.
4. **Mevcut sınırlar:** Üretim auth/RBAC yok; yerel demo tasarımı, polling gecikmesi, katalog metadata değişiminde sürüm artmadan indirim değişebilmesi belgeli. Bunlar yeni kanıtlanmış diskalifiye olarak sunulmuyor; final demoda özellikle aynı quote ve güncel sürüm görünmeli.

## Bu oturumda yeniden çalıştırılan kontroller

| Kontrol | Sonuç | Kanıt |
|---|---|---|
| `docker compose --profile test run --build --rm ... test pytest -v` | exit 0, **229 passed / 39.44 s** | [Backend](disqualification_backend_20260922.txt) |
| Golden JSON | **22 passed**, 0 failed/error/skipped/not_run, 22 ayrı DB | [Golden](disqualification_golden_20260922.json) |
| `npm test` | exit 0, **22 passed**, 0 skipped | [İstemci](disqualification_clients_20260922.txt) |
| `npm run typecheck` | exit 0 | [Typecheck](disqualification_typecheck_20260922.txt) |
| `npm run lint` | exit 0 | [Lint](disqualification_lint_20260922.txt) |
| `npm --prefix apps/web run build` | exit 0 | [Web build](disqualification_web_build_20260922.txt) |
| Özel HTTP/DB denemeleri | 8 örnek tamamlandı; **iki P1 doğrulandı** | [Çıktı](disqualification_probes_20260922_final.txt) |

**Önerilen sıra:** Önce iki P1'i genel davranış düzeyinde düzelt; başarısız örnekleri kalıcı regresyonlara dönüştür ve mevcut kontrolleri koru. Ardından aynı düzeltilmiş sürümde video provası/ortak quote/receipt kontrolü, sürüm eşleştirme ve teslim erişim kontrolü yap. Mevcut yeşil suite tek başına diskalifiye güvencesi değildir.
