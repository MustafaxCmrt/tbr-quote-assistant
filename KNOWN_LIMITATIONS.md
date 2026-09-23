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


## Güncel dil davranışı

23 Eylül tam denetim turunda (Mustafa talimatıyla v8 dondurması yalnız denetim bulguları için kaldırıldı; [çözüm kaydı](reports/audit_fix_resolution.md)):
bir TL tutarı ayrıştırılsa bile mesajda ayrıştırılamayan ikinci bir para ifadesi (`bütçem 5.000 lira`, `₺5.000`, `5 bin TL`) kalırsa arama/öneri/mutasyon yapılmadan netleştirme istenir. `max_price_try` yalnız birim liste fiyatı sınırıdır; **toplam bütçe kontrolü yoktur**: para bağlamında `toplam` veya adet > 1 ile `bütçe` geçen mesajlar birim sınırına çevrilmez, birim sınırı sorulur. Tırnak içindeki, koşul/aktarılan söz biçimindeki (`eklersem`, `ekle dersem`) ya da önce onay isteyen komutlar salt okuma olarak cevaplanır. Belirtilmiş ama rakamla yazılmamış miktar (`iki adet`, `2–3 adet`, Unicode eksi) sorulur; belirtilmemiş miktar 1 kabul edilir. Açık değiştirme hedefi (`X'i Y ile değiştir`) yalnız kayıtlı alternatifse ve fiyat/stok/özellik filtrelerinden geçiyorsa uygulanır. Bunlar sınırlı dilbilgisi kurallarıdır; genel doğal dil kapsamı iddia edilmez.

23 Eylül yeniden denetim turu ([çözüm kaydı](reports/reaudit_fix_resolution.md)): fiyat sınırı önce kapsamına göre sınıflanır. Toplam (`toplam`, `hepsi`, `tamamı`, `sepet/teklif tutarı`, `birlikte`) her zaman, belirsiz bütçe (`bütçe`, `harcama`, `maliyet`) yazmada ve çok adetli okumada sorulur; açık birim ifadesi (`birim`, `adet başı`, `tanesi`) birim sınırı olarak uygulanır. Tutara bağlı ikinci para ifadesi veya binlik çıplak ikinci tutar sorulur; `para birimi TRY` sınır sayılmaz. Tek tırnak/backtick alıntıdaki komut uygulanmaz; alıntı dışındaki açık komut uygulanır. Birim-önce (`adet: 2`), dağıtma (`2'şer`), ayrık işaret, kesir ve birimsiz sayı (`Air 2 ekle`) miktarları sorulur. Değiştirmede hedef özelliği konuma göre hedefe bağlanır. Komuttan önceki `;` özellik cümleciği tüm ürünlere uygulanır; soru içeren ürün cümleciği eklenmez. Bu muhafazakâr kurallar bazı meşru mesajlarda gereksiz netleştirme üretebilir (örn. `%7 indirimle ekle`, `kalemin tamamını 9.000 TL altında değiştir`); mutasyon yapmazlar.

23 Eylül ikinci yeniden denetim turu ([çözüm kaydı](reports/reaudit2_fix_resolution.md)): sınır sözcüğüne bitişik sayı (`limitim 500`, `bütçem beş yüz`, `500'ün altında`) para birimi olmasa da ayrıştırılamayan limit sayılır ve sorulur; birim niteliği olmayan bir bütçe/harcama sözcüğü (`masraf`, `ödeyeceğim`, `ayırdım`) başka yerdeki birim ifadesine rağmen belirsiz bütçedir. İşlem fiilinin yanındaki onay yalnız verilmiş biçimde (`onay alındı/verdim`, `onaylıyorum`) komutu çalıştırır; diğer her onay ifadesi salt okumadır. Kapanmayan alıntı mesajın geri kalanını alıntılar. Cümleler `;` gibi kapsamlanır; komuttan önceki veya sonraki cümlede kendi `ekle` fiili olmayan ürün eklenmez, sorulur. Ortak fiilli nesne yalnız katalog/özellik/miktar sözcüklerinden oluşmalıdır. `X yerine Y ekle` açık `değiştir` biçimini ister. Her ürünün miktarı ayrı denetlenir. `58 mm`, `203 dpi` gibi ölçüler zorunlu katalog etiketidir. Değiştirmede adı geçen kaynağın isim öbeği dışındaki her özellik hedefin koşuludur. Bu kurallar daha muhafazakârdır ve bazı meşru mesajlarda gereksiz soru üretebilir (örn. `BlueScan Air çok iyi. 2 adet ekle.`, `GreenScan Eco ile BlueScan Air ekle`, `Air ve müşterinin istediği Eco ekle`, fiyat bağlamında birimsiz `en fazla 3`); mutasyon yapmazlar.

23 Eylül üçüncü yeniden denetim turu ([çözüm kaydı](reports/reaudit3_fix_resolution.md)): sınır sözcüğüne bağlı sayı (`azami/max/üst sınır/en çok 500`, `beş yüz`, `500 ödeyebilirim`) okumada da yazmada da fiyat kontrolünü açar; tutar çözülemezse arama yapılmadan sorulur. Bu yüzden fiyat dışı `en çok 2 ürün` gibi ifadeler de fiyat sorusu üretebilir. Onay ve izin (`izin/iznim`) yalnız düz, verilmiş ifadeyle işlemi çalıştırır; soru veya koşul içindeki onay (`onay var mı`, `onay var ise`) salt okumadır. Değiştirmede çekim eki (`Air'i`) kaynak öbeğini kapatır; ürün adı içermeyen özellik cümleciği (`QR zorunlu;`) hedefe bağlanır; adsız kaynakta hedefin önündeki bağlanamayan özellik sorulur. Ölçü koşulu (`58mm`, `300dpi`) her cümlecikte zorunludur; genel alternatif araması yalnız kalemin kayıtlı alternatiflerini aday alır. Denetçinin teslim engeli saymadığı U10 sınırları sürer: ürün ayrı bir önceki cümledeyse (`BlueScan Air. Bundan 1 adet ekle.`), `ile` bağlacıyla iki ürün (`Air ile Eco ekle`) veya ortak nesnede katalog dışı bağlam sözcüğü (`Müşteriye Air ve Eco ekle`) varsa sorulur; mutasyon yapılmaz.

23 Eylül dördüncü yeniden denetim turu ([çözüm kaydı](reports/reaudit4_fix_resolution.md)): fiyat adı (`fiyat/ücret/tutar/bedel/maliyet`) ile aynı cümlede `geçmesin/aşmasın/fazla olmasın` geçerse tutarın biçimi ne olursa olsun fiyat sınırıdır; yazılı sayı çekimli olabilir (`beş yüzü`, `beş bini`) ve `…'den fazlası/azı` tutarı sınırlar. Tutar çözülemezse arama yapılmadan sorulur; `fiyatı 8.500 TL'yi geçmesin` 8.500 birim tavanıdır. Adet/süre birimine bağlı `en fazla 2 adet`, `en çok 3 iş günü` fiyat sayılmaz. Verilmiş onay ifadesinin tamamıyla değerlendirilir: soru/etiket soru (`doğru mu`, `değil mi`), çekince (`gibi görünüyor`, `galiba`), aktarım (`dedi`) veya koşul (`sanırsan`) varsa ya da mesajda `teyit/doğrula/kontrol` isteniyorsa işlem salt okumadır; `Onay kesinleşti`, `İzin çıktı/geldi`, `Onaylıdır` verilmiş sayılır. Genel alternatif değişiminde de adsız kaynağın kendi sıfatı dışındaki özellik sorulur; alternatifin sıfatı (`QR'lı alternatifle`) hedef koşuludur; kayıtlı alternatifi olmayan kalemde arama yapılmaz ve öneriler yalnız kayıtlı alternatiflerdir. Adı geçen kaynağın kendi öbeğindeki özellik/ölçü (`58mm BluePrint 80 ürününü`) ve güncellenen/kaldırılan kalem için yazılan özellik o kalemde yoksa mutasyonsuz sorulur. Bu muhafazakâr kurallar bazı meşru mesajlarda gereksiz soru üretebilir (örn. onay mesajında ilgisiz `stok kontrolü` sözcüğü, fiyat adıyla aynı cümlede fiyat dışı `geçmesin`); U10 sınırları değişmedi.

Katalog kategori/SKU/tag değişikliği indirim hesabını değiştirebilir ancak teklif `version` değerini artırmaz (denetim B10); fiyatlama girdileri snapshot'lanmadı. Kalem birim fiyatı snapshot olarak korunur.

Önceki v7/v8 notu: Sözcük sınırlı bir fiyat sınırı işaretiyle (`kadar`, `ucuz`, `altı`, `altında`, `geçmeyen`, `aşmayan`, `en fazla`, `bütçe*`, `limit*`, `tavan*`, `üstüne çıkmadan`) para sözcüğü (`TL`, `TRY`, `lira*`, `₺`) birlikteyse sınır niyeti kabul edilir; tutar çözülemiyorsa arama/öneri ve mutasyon yapılmadan netleştirme istenir. Bitişik sayısal tutar ve `bin` korumaları da sürer. `8.500 TL’ye kadar/altında/altı/TL’nin altında` 8500 birim liste fiyatı `<=` filtresini korur; `8K TL`, `sekiz yüz lira` ve `8 bin` gibi desteklenmeyen tutarlar ayrıştırılmaz. Para sözcüğü olmayan süre/adet/model örnekleri ve sınır işareti olmayan normal fiyat soruları korunur. Para sözcüğü ve bitişik rakam içermeyen yazıyla tutarlar (`sekiz yüze kadar`) hâlâ sınır olarak tanınmayabilir; genel doğal dil kapsamı iddia edilmez. Birbirinden bağımsız para ve süre ifadelerinin aynı mesajda bulunması güvenli tarafta gereksiz netleştirme üretebilir. Yazıyla miktar desteği eklenmedi: `Altı adet BlueScan Air ekle` mevcut güvenli retle hiçbir mutasyon yapmaz. “En ucuz” üstünlük ifadesi ve “şimdiye/bugüne kadar” sınır sayılmaz; v8 yalnız v7 güvenlik ağının yanlış alarmını daralttı, ayrıştırıcı yeniden **DONDURULDU**.

- Backorder onayı ayrı ve açık olumlu cümlecik olmalıdır; olumsuzlama, alıntı, soru ve koşul şüphesinde onay sayılmaz. Müşteri uygunluğu ayrıca zorunludur.
- Offline/senkron soruları gerçek uyumluluk kayıtlarına dayanır. Kaynak uydurulmaz.
- Düzeltme yeni mesaj planlarına uygulanır; retry eski kalıcı planı ve receipt davranışını korur.
- Yeni fiziksel cihaz/video veya temiz clone doğrulaması bu tur yapılmadı. Tarihsel sonuçlar güncel fiziksel prova yerine geçmez.
- Doğrulanan uygulama `77ccd81`: 1015 backend testi (22 golden + 83/126/109/91 yeniden denetim denemesi + 85 kendi probe dahil), 0 error; [son rapor](reports/reaudit4_fix_resolution.md). Önceki `ae69ff9`: 892 ([rapor](reports/reaudit3_fix_resolution.md)); `05fe5cd`: 762 ([rapor](reports/reaudit2_fix_resolution.md)); `3e5aa4d`: 604 ([rapor](reports/reaudit_fix_resolution.md)); `fde6015`: 451; v8 `0787bcb`: 402.
