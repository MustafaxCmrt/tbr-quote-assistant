# AI kullanımı

F00 kaynak analizi ve plan denetimi önceki Claude Code oturumunda yapıldı; uygulama testi sayılmaz.
F01a'da Codex, Mustafa'nın kapsamıyla API debug SSE, Expo ekranı, ortak parser, test ve belgeleri yazdı;
uv/npm kurulumlarını, curl zamanlı aktarımı, TypeScript/lint/parser ve iOS bundle kontrollerini çalıştırdı.
Gerçek komut/sonuçlar `reports/` altında. Expo SDK seçimi resmî sürüm ve App Store kayıtlarıyla kontrol edildi.

İnsan girdisi: Mustafa kapsamı ve Docker yasağını belirledi; fiziksel iPhone debug gözlemini ekran görüntüsüyle doğruladı.
Manuel insan kod denetimi veya native başarı yapılmış gibi gösterilmez. Uygulama ücretli API/provider çağırmaz.

F01b'de Codex PostgreSQL şeması, Alembic revision, JSON importer, readiness, sınırlı DB rolü,
Compose ve React/Vite iskeletini yazdı. Gerçek PostgreSQL'de 7 integration testi, restart snapshot
karşılaştırması, boş volume başlangıcı, build/lint ve tarayıcı smoke çalıştırıldı. İlk init izin
hatası veriyi silmeden düzeltildi; başarısız çıktılar raporlarda korundu. AI testleri insan
kod denetimi yerine sunulmaz; golden/tool/chat kabulü bu checkpoint'te henüz yapılmadı.

F02: Codex Türkçe normalizasyon, read DTO/araçlar, EvidenceBundle, snapshot quote ve saf fiyatlamayı geliştirdi. 47 unit/PostgreSQL testi, gerçek HTTP smoke ve lint exit 0. Firma cevabı vault güncellemesiyle okundu; ADR-005/007 accepted aday tercihi olarak belgelendi. Golden/chat henüz çalıştırılmadı.

F03: Codex tek transaction executor, üç gerçek mutation wrapper, server key/receipt ve DB lock
korumalarını yazdı. Aynı/farklı key yarışları, stale replay, atomik grup rollback, admin fiyat/stok
kilidi, backorder, replacement ve restart sonrası gerçek wrapper replay PostgreSQL üzerinde test edildi.
Salt okunur ikinci AI incelemesinde kanıtlanmış önemli kusur bulunmadı; altı test açığı raporlandı.
Bu açıklar için eklenen testler dahil son gerçek PostgreSQL/unit koşusu 94 passed; ayrıntı reports/f03_acceptance.md.
Bu inceleme insan denetimi veya ampirik mutation score değildir.

F04: Codex genel Türkçe niyet/slot planlayıcı, kalıcı mesaj planı, kaynaklı template yanıtı ve
HTTP golden runner yazdı. Bağımsız salt-okunur AI incelemesinin dört somut parser/guard bulgusu
regresyonlarla düzeltildi; ilk negatif testlerdeki sayı ayrıştırma hataları da giderildi.
Son gerçek koşu 136 passed (22 golden dahil); gerçek HTTP smoke/lint/delivery exit0.
Sistem LLM tool calling yaptığını iddia etmez; provider adaptörü ve API harcaması yoktur.

F05: Codex gerçek executor eventleri, SSE envelope, güvenli hata/başarısız log, geçmiş, disconnect
sonrası devam ve ortak TS reducer ekledi. 142 backend testi, 12 parser/reducer testi; API ve proxy
üstünden curl -N kademeli aktarım gözlemi passed. Commit sonrası render hatası ve disconnect
regresyonları gerçek DB üstünde koşuldu. Native tam chat henüz insan tarafından denenmedi.

F06: Codex backend CRUD ve React admin/chat/quote/log ekranlarını yazdı. 144 gerçek backend testi,
web build/typecheck/lint, tarayıcıdan yeni ürün/bilgi ekleme, sohbet mutation/retry, ikinci istemci ve
gerçek API kesintisi/toparlanma kanıtları raporlandı. Impeccable becerisiyle ayrı AI arayüz okuyucusu
stale metadata ve kontrast bulgularını bildirdi; düzeltmeleri doğruladı. Ayrı documenter mevcut
tasarım tokenlarını belgeledi. Otomatik tasarım detector'ı izin hatasıyla çalışmadı; insan review denmedi.

F07: Codex Expo native sohbet/kaynak sheet/kanonik teklif/bağlam seçimini ve typed expo/fetch
client'ını yazdı. UUID için Expo Crypto resmî belgesi kullanıldı. Node transport testleri ve iOS export
native kullanıcı kabulünün yerine sunulmaz. Mustafa gerçek iPhone'da add/shared quote/retry, kaynak aç/Kapat, klavye ve kademeli yanıtın okuma konumunu doğruladı. Cihaz/iOS/Expo Go sürüm metadatası henüz not_verified.


F08: Mustafa'nın isteğiyle Claude CLI üzerinden `claude-opus-5`, `--effort xhigh` ile bağımsız
salt okunur kaynak incelemesi yapıldı. CLI sonucu exit0/is_error=false ve modelUsage `claude-opus-5`.
Mevcut Claude aboneliği kullanıldı; uygulamaya provider adaptörü eklenmedi. İlk varsayılan model
çağrısı istek netleşince durduruldu ve başarılı inceleme sayılmadı. Reviewer'a 30 seçilmiş kaynak/test/
sözleşme dosyası satır numaralarıyla verildi; araçlar kapalıydı ve reviewer test çalıştırmadı.
Dört P1 yorumlama bulgusu raporlandı. Codex bunlar için HTTP üzerinden gerçek PostgreSQL'de 13
regresyon yazdı; düzeltmeden önce 13 failed kanıtı korundu. Düzeltme ve yeniden doğrulama kaydı
`reports/f08_review_resolution.md` içindedir. Toplam-hedef concurrency ve diğer hipotezler açıkken
bağımsız kabul tamamlandı denmez. Kaynak review insan kod denetimi değildir.

F08 düzeltme sonrası: 179 backend testi (22 golden dahil) gerçek PostgreSQL koşusunda geçti.
Tanınmayan/olumsuzlanan komut, toplam-hedef yarışması, draft dışı mutasyon, özellik eşanlamları,
eşit ürün seçimi ve renderer kaynak doğrulaması için regresyonlar eklendi. İlk başarısız koşular
saklandı. Aynı Opus5/xhigh ayarıyla odaklı takip review başlatıldı; sonucu henüz bekleniyor.
Canlı API ve web proxy stream testi yenilendi; önceki fiziksel demo teklif/receipt kayıtları salt
okunur kontrolle korunduğu doğrulandı. Yeni fiziksel cihaz gözlemi yapıldığı iddia edilmez.

F08 final: takip review da eski sürümde üç yorumlama sınıfını açık buldu. Codex ek regresyonlarla
bunları ve kısmi replace belirsizliğini düzeltti; e84b2a6 üzerinde204test/22golden passed.
Son F08 kapı kararı Codex'in rapor/test değerlendirmesidir; Claude son sürüme onay verdi denmez.

F09: remote fresh clone f0febc4; separate Compose volume. README setup exit0; 204 PostgreSQL tests passed (41.65s), clients/build/Expo check exit0. reports/f09_acceptance.md maps actual evidence. Native fresh-clone/video/access/send remain not_verified.

2026-09-21 takip P2: Codex üç bulguyu önce10failed ile doğruladı; Plus katalog seçimi, kategori içi referans ve zaman/negasyon ayrımını düzeltti. Önerilen rakam kontrolü ve Acil marka çakışması ek düzeltme gerektirdi. Runtime53b9948: odaklı19passed; tam225passed/22golden. Yeni Claude review/fiziksel cihaz onayı iddia edilmez.

V2 remote clone81765bd/tagdemo-candidate-20260921-v2:225passed44.48s;19istemci testi, install/typecheck/lint/webbuild/Expo check exit0. Yeni volume ile aynı tbr-f09-clean/18001/15173 projesi; eski volume korundu. DB/APIrestart+reseed+receipt replay geçti; anaQ1001 tamDTO aynı.

2026-09-21 teslim öncesi sertleştirme (Claude Opus 5, Mustafa'nın açık uygulama talimatıyla): salt okunur mimari/güvenlik denetiminin 14 bulgusu önce kodda doğrulandı. B1 (yazma uçlarına admin anahtarı) ADR-012'den sapma olduğu için Mustafa onayıyla uygulandı; B5/D4/D5 önerileri gerekçeyle reddedildi (sıra boşluğu, çift uygulama riski, admin log regresyonu). Regresyonlar önce 4+3 failed, sonra geçti; tam 229 passed; v3 clone bf92756 temiz kurulum/runtime/istemci exit0. Kayıt: reports/hardening_resolution.md. Fiziksel iPhone add + tekrar gönderimi Mustafa doğruladı (22 Eylül); DB'de tek etki (reports/hardening_native_smoke_db.txt).

2026-09-22 görsel düzenleme (Claude, Mustafa'nın isteği; kapsamı Mustafa daralttı: karanlık tema web'e eklenmedi, kütüphane/animasyon yok): firma logosu Mustafa'nın indirdiği dosyadan işlendi, palet logoya hizalandı, dar ekran gezinme/tablo düzeltildi, mobil kart tutarlılığı. Doğrulama: web build/typecheck/lint/22 istemci testi/Expo iOS export/teslim taraması exit0; Playwright + yerel Chrome ile 4 genişlik × 4 sayfa taşma ölçümü. Kayıt: reports/design_polish.md. Mobil görünüm cihazda henüz görülmedi (not_verified).


2026-09-22 video öncesi düzeltme (Codex, Mustafa'nın onayladığı dar plan): iki P1 ve uyumluluk
okuma yönlendirmesi iki üretim dosyasında düzeltildi. İlk denemede 19 HTTP/DB regresyonu başarısız,
16 henüz eklenmemiş yardımcı işlev testi import hatalı, 21 kontrol başarılıydı; çıktı korundu.
Son durumda 65 yeni parametrik örnek dahil 294 backend testi ve 22 istemci testi geçti.
Test yazımı code-testing-agent; son assertion/boşluk değerlendirmesi assertion-quality ve
test-gap-analysis yönergeleriyle aynı ajan tarafından yapıldı; bağımsız inceleme veya ampirik mutation
skoru iddiası yoktur. Statik eşleme aracı tree-sitter-language-pack eksikliği nedeniyle çalışmadı;
ek kurulum yapılmadı. Test konteyneri 512 MB / 1 CPU ve swap kapalı ayarla, işler sırayla çalıştırıldı.
Test DB servisi bitince durduruldu. Fiziksel prova/video Mustafa'ya aittir.

2026-09-22 P2 (Codex, Mustafa talimatı): yalnız normalization.py içinde tutar/işaretçi ilişkisi daraltıldı; code-testing-agent odaklı akışıyla 41 ek parametrik örnek, kırmızı 17 failed → tam 335 passed/22 golden; demo DB’ye yazılmadı, testler sırayla çalıştı, push yapılmadı.

2026-09-22 v6 (Codex, Mustafa talimatı): bağımsız Claude denetiminin bulduğu v5 bin-fiyat regresyonu doğrulandı; yalnız normalization.py düzeltildi, code-testing-agent odaklı akışıyla helper + izole HTTP/DB regresyonları eklendi; önceki testlerin bin/kadar birleşimini kaçırdığı çözüm raporunda açıklandı.

2026-09-22 v7 (Codex, Mustafa talimatı): onaylı test-db temizliği 2163→0; yalnız normalization.py içinde para sözcüğü + sınır işareti güvenlik ağı eklendi, izole helper/HTTP/DB ve demo regresyonlarıyla doğrulandı; fiyat ayrıştırıcısı bu turdan sonra DONDURULDU.

2026-09-22 v8 (Codex, Mustafa talimatı, Claude bağımsız denetim bulgusu): yalnız has_price_ceiling_intent içinde en ucuz/şimdiye kadar/bugüne kadar yanlış alarmı daraltıldı; True beklentisi düzeltilip helper ve izole HTTP/DB testleri eklendi, ayrıştırıcı yeniden DONDURULDU.
