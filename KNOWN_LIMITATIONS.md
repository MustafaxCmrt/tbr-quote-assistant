# Bilinen sınırlamalar

- F00–F06 tamamlandı. F07'de iPhone açılışı, ürün ekleme, web ile ortak teklif, aynı isteğin tekrarı,
  kaynak aç/kapat ve klavye erişimi doğrulandı. Son okuma konumu ve parça parça aktarım da Mustafa tarafından doğrulandı. Güncel kanıt: [kabul tablosu](reports/acceptance.md).
- Mustafa’nın bildirimiyle cihaz iPhone 16e, iOS 26.6.2 ve Expo Go 57.0.9 / SDK 57.0.0 olarak kaydedildi. Karanlık modda temel iPhone
  akışları gözlendi; açık tema, büyük yazı, tablet ve VoiceOver için fiziksel kabul iddiası yoktur.
- Üretim authentication/RBAC yoktur. Müşteri seçimi demo bağlamıdır; kimlik doğrulama değildir.
  Uygulama yerel demo içindir. PostgreSQL host portu kapalıdır; API runtime DB rolü şema değiştiremez.
- Web müşteri seçicisi yalnız ad ve şehri gösterir; fiyat seviyesi (`price_tier`) ve bekleme uygunluğu
  (`allow_backorder`) ekranda görünmez. Bu kurallar sunucuda uygulanır ve sohbet cevabında kaynak kaydıyla açıklanır.
- Ürün/bilgi yazma uçları (`POST/PATCH/DELETE /api/products|knowledge`) `.env` içindeki `ADMIN_API_KEY`
  değerini `X-Admin-Key` başlığında ister; anahtar yapılandırılmamışsa 503 döner. Web paneli başlığı Vite
  proxy'si üzerinden sunucu tarafında ekler; değer tarayıcı bundle'ına ve mobil uygulamaya girmez. Okuma,
  sohbet ve teklif uçları anahtarsızdır: LAN telefon demosunda (`API_BIND_HOST=0.0.0.0`) aynı ağdaki
  cihazlar müşteri/teklif/oturum listelerini okuyabilir ve sohbetle teklif değiştirebilir. Web admin log
  ekranı mobil oturumlarını da gösterdiği için `/api/chat/sessions` oturum kimliklerini döndürür; bu
  kimlikler transcript ve tool log okumaya yeter. LAN adımı yalnız güvenilen ağda, demo süresince açılır.
- Rate limit ve eşzamanlı akış tavanı yoktur; SQLAlchemy havuzu varsayılan 5+10 bağlantıdır ve dolunca
  30 sn sonra hata verir. İstek gövdesi 256 KiB ile sınırlıdır (413). API container'ı 512 MB / 256 süreç,
  web 1 GB / 512 süreç sınırıyla çalışır. Üretimde rate limit ters proxy katmanında ele alınmalıdır.
- İndirim kuralı kalemin fiyat snapshot'ını, ama ürünün güncel kategori/SKU/etiket alanlarını kullanır.
  Yönetim panelinde bu alanlar değişirse mevcut taslak tekliflerin indirimi sürüm artmadan değişebilir;
  katalog fiyat değişikliği eski teklifi etkilemez.
- Compose web servisi Vite geliştirme sunucusudur. Production bundle derlenmiştir; production
  hosting doğrulanmamıştır.
- Türkçe deterministik intent/slot çözümleme sınırlı bir dilbilgisine dayanır. Plus için katalog tam adı/Plus alias’ı, kısa model+Plus veya ID/SKU gerekir; genel “Plus model” netleştirilir. Referans betimleyicileri kategori içi tag’lerle sınırlıdır; “X için” ve “acil olarak” bağlamı ayrılır. “Şimdiye/bugüne kadar” zaman ifadesidir; rakamsız bütçe/limit/tavan netleştirme ister. Harici LLM adapter'ı,
  ücretli API çağrısı ve provider timeout/fallback geçiş testi yoktur. Gerçek altı tool ve kaynaklı
  anahtarsız fallback vardır; bu uygulama LLM tool calling diye sunulmaz.
- Hazır deterministik yanıt SSE üzerinden 50 ms aralıkla, en fazla 80 metin parçasında aktarılır.
  Bu bilinçli şablon aktarım hızıdır; LLM token üretimi değildir. Transaction aktarım beklemeleri
  sırasında açık tutulmaz. Uzun yanıtta planlanan ek bekleme en fazla 4 saniyedir.
- Her token için kalıcı replay / Last-Event-ID desteği yoktur. Bağlantı kesilse de kabul edilen işlem
  commit olabilir; aynı mesaj kimliğiyle retry ve kanonik teklif refetch gerekir. Mobil sohbet yerel
  bellektedir; uygulama yeniden açıldığında yerel geçmiş/oturum sıfırlanır, DB teklif ve receipt'leri korunur.
- SSE UTF-8/çerçeve ayrıştırması ve JSON/zarf doğrulaması vardır. Henüz genel amaçlı sınırsız kötü niyetli
  SSE girdisine karşı parser buffer limiti yoktur; istemci yapılandırılmış yerel API'yi tüketir.
  Sözleşme bilinçli olarak katıdır: bilinmeyen olay tipi veya `event_seq` boşluğu akış hatasıdır. Yeni olay
  tipi `schema_version` artışı ve istemci güncellemesiyle birlikte eklenir; üç yüzey aynı repodan yayınlanır.
- Aynı mesaj kimliği aynı teklife başka bir oturumdan gelirse işlem ikinci kez uygulanmaz,
  `IDEMPOTENCY_CONFLICT` ile reddedilir. Oturum değişse bile tekrar eden mesajın miktarı iki kez artırmaması
  için bilinçli tercihtir. Sunucu oturumu tanımıyorsa (ör. yeni volume) mobil bir sonraki denemede yeni oturum açar.
- Retry ilk mesajın kayıtlı planını ve netleştirme notunu korur; bu sırada katalog değişmişse yeniden çalıştırılan arama sonuçları ilk değerlendirmeden farklı olabilir. Yeni niyet/güncel seçim için yeni mesaj gerekir. Planlama okumaları ayrı tool log değildir; loglar executor çağrılarını gösterir. Mutasyon fiyat/stok guard'ları kilit altında güncel veriye uygulanır.
- Retrieval küçük kataloğu tarar; büyük katalog performansı ölçülmemiştir. Yeni yönetim kayıtları
  retrieval'a katılır; açıkça adı verilen pasif ürün ilgisiz ürüne dönüştürülmez.
- ADR-005/007, firmanın kararı adaya bırakması sonrası kabul edilen aday tercihleridir; firmanın
  tarif ettiği indirim/çağrı eşitliği kuralı diye sunulmaz.
- Test DB'leri ve ayrı fresh-start volume'leri teşhis için tutulur; disk kullanımı zamanla artar.
  Otomatik yıkıcı temizlik yoktur. Çok sayıda tam koşudan sonra (bu hostta ~2.300 veritabanı) PostgreSQL
  paylaşımlı istatistik belleği Docker'ın 64 MB `/dev/shm` sınırını aşar ve testler `DiskFullError` verir;
  README'deki komutla eski `tbr_test_*` veritabanları elle silinir ([kayıt](reports/hardening_testdb_cleanup.txt)). Debug endpoint varsayılan kapalıdır; yalnız `DEBUG_STREAM_SMOKE=1` ile açılır.
- Expo geliştirme araçlarının `xcode → uuid` zincirinde 10 orta seviye npm audit bildirimi vardır;
  [audit raporu](reports/f07_npm_audit.txt) exit 1'dir. Önerilen force çözümü SDK46'ya gerilettiği için
  uygulanmadı. Prebuild/EAS/mağaza yayını yapılmadı.
- Bilinen kod kalitesi trade-off'ları: `build_plan` tek büyük fonksiyondur (`planner.py`); okuma tool'ları da
  mesajın teklif kilidi altında çalışır (daha geniş ama basit tutarlılık); `/docs` açıktır; web/mobil bileşen
  testleri yoktur, saf parser/reducer/istemci/durum testleri vardır.
- Secret taramaları tanınan anahtar biçimlerini ve mevcut yerel hassas değerleri kontrol eder;
  her olası secret biçiminin bulunacağı garantisi değildir. Git taraması erişilebilir yerel ref'lerle sınırlıdır.
- F08 uygulama kabul kapısı tamamlandı; kapsam ve review disposition reports/f08_acceptance.md içindedir. F09 v3 clone bf92756 temiz kurulum ve otomatik kontrolleri geçti (reports/hardening_resolution.md); final video/erişim/gönderim kapıları tamamlanmadı. Public dağıtım, görünürlük değişikliği ve teslim mesajı için insan onayı gerekir.


## 22 Eylül v4/v5/v6 düzeltmelerinin sınırları

- Para ayrıştırması hâlâ sınırlıdır. `TL altında`, `TL altı`, `TL’den ucuz` sayısal sınırları desteklenir;
  mevcut aday yorumu olan birim liste fiyatı `<=` korunur. `lira`, `₺`, `8 bin` gibi desteklenmeyen sınır
  biçimleri öneri ve mutasyonda netleştirme ister; sınırsız öneriye çevrilmez. `kaç TL?` ve adet içeren
  normal fiyat soruları sınır sayılmaz. Her doğal dil biçiminin anlaşıldığı iddia edilmez.
- Backorder onayı ayrı, açık bir olumlu cümlecik olmalıdır: `bekleyebilirim`, `beklemeyi kabul ediyorum`
  veya `backorder kabul ediyorum`. Olumsuzlama, alıntı, soru ve koşul şüphesinde onay verilmiş sayılmaz.
  Karmaşık ama olumlu ifadeler de güvenli biçimde reddedilebilir; müşteri uygunluğu ayrıca zorunludur.
- Salt okunur offline/senkron soruları gerçek uyumluluk kayıtlarını getirir; kaynak yoksa kaynak uydurulmaz.
- Düzeltmeler yeni mesaj planlarına uygulanır; retry mevcut kalıcı plan ve receipt davranışını korur.
- v4 uygulama commit’i `902894a`: 294 backend ve 22 istemci testi geçti. İki P1 ve uyumluluk yönlendirmesi
  kapatıldı; [çözüm raporu](reports/safety_review_resolution.md). v4 fiziksel prova/video/erişim/gönderim
  henüz tamamlanmadı. Yeni temiz kurulum, v3'ün tarihsel temiz clone kanıtıyla karıştırılmaz.

- v5: `kadar/ucuz` için herhangi bir rakam yeterli değildir; tutar doğrudan işaretçiye bağlanır.
  Süre/adet birimleri ve alfanümerik model kodları okuma sorularında yanlış fiyat uyarısı üretmez.
  Para birimsiz `8.500’e kadar` / `8.500’den ucuz` hâlâ netleştirme ister; `TL’ye kadar` desteklenir.
  Yazıyla miktar desteği eklenmedi: `Altı adet BlueScan Air ekle` hiçbir mutasyon yapmadan mevcut
  fiyat netleştirmesine döner. Mutasyon yolundaki daha muhafazakâr `has_price_intent` koruması
  değişmedi; karmaşık ekleme ifadelerinde gereksiz netleştirme hâlâ mümkündür.
- v5 uygulama commit’i `3a07cec`: 335 backend testi (22 golden dahil) geçti;
  [P2 kanıtı](reports/p2_price_intent_resolution.md). Yeni fiziksel cihaz/video doğrulaması yapılmadı.

- v6: bağımsız Claude denetimi, v5’in `bin` içeren bazı sınırları öneri yolunda kaçırdığını buldu.
  Önceki testler `bin` sözcüğünü yalnız `altında` ile sınamıştı. `bin` artık para birimine veya
  sınır işaretçisine doğrudan bağlı bir tutar parçası olarak tanınır: `8 bine kadar`, `on bin liraya
  kadar`, `8 bin TL civarı` netleştirme ister; arama/öneri ve mutasyon yapılmaz. Değer ayrıştırması
  genişletilmedi. `on güne kadar`, `8 bin adede kadar` ve v5 süre/adet/model kontrolleri korunur.
  Genel yazıyla sayı/para anlayışı veya bütün doğal dil biçimlerinin kapsandığı iddia edilmez.
- v6 uygulama commit’i `fa3352b`: 370 backend testi ve 22 golden geçti; [regresyon çözümü](reports/p1_bin_ceiling_resolution.md). Yeni fiziksel prova/video doğrulaması yapılmadı.
