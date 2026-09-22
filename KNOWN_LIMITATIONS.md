# Bilinen sınırlamalar

- F00–F06 tamamlandı. F07'de iPhone açılışı, ürün ekleme, web ile ortak teklif, aynı isteğin tekrarı,
  kaynak aç/kapat ve klavye erişimi doğrulandı. Son okuma konumu ve parça parça aktarım da Mustafa tarafından doğrulandı. Güncel kanıt: [kabul tablosu](reports/acceptance.md).
- Cihaz modeli, iOS ve kurulu Expo Go sürümü henüz kaydedilmedi. Karanlık modda temel iPhone
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
