# Bilinen sınırlamalar

- F00–F06 tamamlandı. F07'de iPhone açılışı, ürün ekleme, web ile ortak teklif, aynı isteğin tekrarı,
  kaynak aç/kapat ve klavye erişimi doğrulandı. Son okuma konumu ve parça parça aktarım da Mustafa tarafından doğrulandı. Güncel kanıt: [kabul tablosu](reports/acceptance.md).
- Cihaz modeli, iOS ve kurulu Expo Go sürümü henüz kaydedilmedi. Karanlık modda temel iPhone
  akışları gözlendi; açık tema, büyük yazı, tablet ve VoiceOver için fiziksel kabul iddiası yoktur.
- Üretim authentication/RBAC yoktur. Müşteri seçimi demo bağlamıdır; kimlik doğrulama değildir.
  Uygulama yerel demo içindir. PostgreSQL host portu kapalıdır; API runtime DB rolü şema değiştiremez.
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
- Retry ilk mesajın kayıtlı planını ve netleştirme notunu korur; bu sırada katalog değişmişse yeniden çalıştırılan arama sonuçları ilk değerlendirmeden farklı olabilir. Yeni niyet/güncel seçim için yeni mesaj gerekir. Planlama okumaları ayrı tool log değildir; loglar executor çağrılarını gösterir. Mutasyon fiyat/stok guard'ları kilit altında güncel veriye uygulanır.
- Retrieval küçük kataloğu tarar; büyük katalog performansı ölçülmemiştir. Yeni yönetim kayıtları
  retrieval'a katılır; açıkça adı verilen pasif ürün ilgisiz ürüne dönüştürülmez.
- ADR-005/007, firmanın kararı adaya bırakması sonrası kabul edilen aday tercihleridir; firmanın
  tarif ettiği indirim/çağrı eşitliği kuralı diye sunulmaz.
- Test DB'leri ve ayrı fresh-start volume'leri teşhis için tutulur; disk kullanımı zamanla artar.
  Otomatik yıkıcı temizlik yoktur. Debug endpoint varsayılan kapalıdır; yalnız `DEBUG_STREAM_SMOKE=1` ile açılır.
- Expo geliştirme araçlarının `xcode → uuid` zincirinde 10 orta seviye npm audit bildirimi vardır;
  [audit raporu](reports/f07_npm_audit.txt) exit 1'dir. Önerilen force çözümü SDK46'ya gerilettiği için
  uygulanmadı. Prebuild/EAS/mağaza yayını yapılmadı.
- Secret taramaları tanınan anahtar biçimlerini ve mevcut yerel hassas değerleri kontrol eder;
  her olası secret biçiminin bulunacağı garantisi değildir. Git taraması erişilebilir yerel ref'lerle sınırlıdır.
- F08 uygulama kabul kapısı tamamlandı; kapsam ve review disposition reports/f08_acceptance.md içindedir. F09 v2 clone 81765bd temiz kurulum ve otomatik kontrolleri geçti (reports/f09_acceptance.md); final video/erişim/gönderim kapıları tamamlanmadı. Public dağıtım, görünürlük değişikliği ve teslim mesajı için insan onayı gerekir.
