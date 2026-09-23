# Bilinen sınırlamalar

Bu teslim, case'in kapsamına göre yerel olarak çalışan bir demodur. Aşağıdaki sınırlamalar bilinçli
olarak kapsam dışında bırakıldı veya bilinen trade-off'lardır.

## Güvenlik ve dağıtım

- **Kimlik doğrulama ve rol yetkisi yoktur.** Müşteri seçimi demo bağlamıdır, kimlik doğrulama değildir.
  Okuma, sohbet ve teklif uçları anahtarsızdır; yalnız ürün/bilgi yazma uçları `X-Admin-Key` ister
  (anahtar yapılandırılmamışsa `503`).
- **Mobil demo için yerel ağ açılımı.** `API_BIND_HOST=0.0.0.0` ile aynı ağdaki cihazlar müşteri, teklif
  ve oturum listelerini okuyabilir ve sohbetle teklif değiştirebilir. Web'deki işlem kayıtları ekranı mobil
  oturumları da gösterdiği için `/api/chat/sessions` oturum kimliklerini döndürür; bu kimlikler mesaj ve
  araç logu okumaya yeter. Bu yüzden yerel ağ açılımı yalnız güvenilen ağda ve demo süresince yapılmalıdır.
- **Rate limit ve eşzamanlı akış sınırı yoktur.** Veritabanı bağlantı havuzu SQLAlchemy varsayılanıdır
  (5 + 10 bağlantı, dolunca 30 sn sonra hata). İstek gövdesi 256 KiB ile sınırlıdır (`413`). API
  konteyneri 512 MB / 256 süreç, web 1 GB / 512 süreç sınırıyla çalışır. Üretimde rate limit bir ters
  proxy katmanında ele alınmalıdır.
- Compose'daki web servisi Vite geliştirme sunucusudur; üretim derlemesi alınır ama üretim barındırması
  doğrulanmamıştır. API belgesi (`/docs`) açıktır.
- Gizli değer taraması (`scripts/check_delivery.py`, `scripts/check_git_history.py`) bilinen anahtar
  biçimlerini, yerel IP'yi ve kullanıcı yolunu arar; her olası gizli değer biçimini bulma garantisi yoktur.
- Mobil uygulama Expo Go ile çalışır; EAS build ve mağaza yayını yapılmadı. Kayıtlı `npm audit` çıktısında
  Expo geliştirme araçlarının bağımlılık zincirinde 10 orta seviye bildirim vardır
  ([rapor](reports/f07_npm_audit.txt)). Önerilen `--force` çözümü Expo SDK'yı çok eski bir sürüme
  düşürdüğü için uygulanmadı.

## Türkçe dil anlama

- Planlayıcı kural tabanlıdır; genel doğal dil kapsamı iddia edilmez. İlke şudur: ürün, miktar, fiyat
  sınırı, onay veya özelliğin kime ait olduğu kesinleşmezse **teklif değiştirilmez, netleştirme sorulur**.
  Bu yüzden bazı meşru cümlelerde gereksiz soru sorulabilir; yanlış kalıcı değişiklik yapılmaz.
- Harici dil modeli bağlantısı yoktur. `OPENAI_API_KEY` tanımlansa bile bu sürümde model çağrılmaz;
  sağlayıcı zaman aşımı veya modelden yedek moda geçiş test edilmedi. Sistem LLM tool calling olarak sunulmaz.
- **Netleştirme sorulan ifadeler (örnekler):**
  - Rakamla yazılmamış miktar: `iki adet`, `2–3 adet`, `adet: 2`, `2'şer`, birimsiz sayı (`Air 2 ekle`).
    Miktar belirtilmezse 1 kabul edilir.
  - Çözülemeyen fiyat sınırı: `8K TL`, yazıyla karmaşık tutarlar, ikinci bir para ifadesi
    (`8.500 TL altında…; bütçem 5.000 lira`), toplam veya belirsiz bütçe (aşağıya bakın).
  - Onay veya izin, düz ve kesin bir ifadeyle verilmemişse: soru (`onay var mı`, `doğru mu`), koşul
    (`onay varsa`), çekince (`gibi görünüyor`, `galiba`), aktarım (`dedi`) veya hâlâ yapılacak bir kontrol
    (`teyit et`, `doğrula`). Alıntılanan veya varsayım olarak yazılan komutlar da uygulanmaz.
  - Plus sürümü, tam model adı, Plus alias'ı veya ürün kodu yazılmadan seçilmez (`Plus model` sorulur).
  - Değiştirmede bir özelliğin (QR, 2D, 58mm…) eski ürüne mi yeni ürüne mi ait olduğu belli değilse.
- **Bilinen gereksiz netleştirmeler:** ürün önceki ayrı cümlede geçiyorsa (`BlueScan Air. Bundan 1 adet
  ekle.`), iki ürün `ile` ile bağlanmışsa (`Air ile Eco ekle`), ortak nesnede katalog dışı bir bağlam
  sözcüğü varsa (`Müşteriye Air ve Eco ekle`), onay mesajında ilgisiz bir `kontrol` sözcüğü geçiyorsa, fiyat
  adıyla aynı cümlede fiyat dışı bir `geçmesin` varsa. Bu durumlarda teklif değişmez.

## Fiyat ve teklif

- `max_price_try` **birim liste fiyatı** üst sınırıdır (`<=`). **Toplam bütçe kontrolü yoktur:** `toplam`,
  `hepsi`, `sepet tutarı` gibi toplam ifadeleri ve çok adetli istekte belirsiz `bütçe` birim sınırına
  çevrilmez, kullanıcıya sorulur.
- İndirimler toplanmaz, en özel tek kural uygulanır. Bu, firmanın adaya bıraktığı bir karardır
  ([karar kaydı 0001](docs/decisions/0001-indirim-cakismasi.md)).
- Kalemin birim fiyatı eklendiği anda saklanır. İndirim ise ürünün **güncel** kategori, SKU ve etiketlerine
  bakar: yönetim panelinde bu alanlar değişirse mevcut taslak tekliflerin indirimi teklif sürümü artmadan
  değişebilir. Katalog fiyat değişikliği eski teklifi etkilemez.
- Taslak teklif stok rezervasyonu yapmaz, stok miktarını düşürmez.
- Stokta olmayan ürün yalnız müşterinin `allow_backorder` yetkisi **ve** ayrı, açık bir bekleme onayıyla
  (`Bekleyebilirim.`) eklenir. Web müşteri seçicisi fiyat seviyesini ve bekleme yetkisini göstermez; bu
  kurallar sunucuda uygulanır ve sohbet cevabında kaynağıyla açıklanır.

## Akış, tekrar ve istemciler

- Yedek modda metin, hazırlanmış cevabın en fazla 80 parçaya bölünüp 50 ms aralıkla gönderilmesidir (en
  fazla 4 saniye ek süre); model token üretimi değildir. Transaction bu bekleme sırasında açık tutulmaz.
- Kalıcı olay tekrarı (`Last-Event-ID`) yoktur. Bağlantı kopsa da kabul edilen işlem commit olmuş olabilir;
  istemci aynı mesaj kimliğiyle yeniden dener ve teklifi yeniden okur. Tekrarsızlığı receipt sağlar.
- Aynı mesaj kimliği farklı içerikle gelirse `IDEMPOTENCY_CONFLICT` (`409`) döner. Yeniden deneme ilk
  mesajın kayıtlı planını kullanır; arada katalog değiştiyse yeniden çalışan aramanın sonucu ilk
  değerlendirmeden farklı olabilir. Güncel bir seçim için yeni mesaj gerekir.
- Araç logları yürütücünün çağrılarını gösterir; planlayıcının plan kurarken yaptığı okumalar ayrıca
  loglanmaz. Yazma anındaki fiyat ve stok kontrolleri ise kilit altında güncel veriyle tekrar yapılır.
- Mobil sohbet geçmişi uygulama belleğindedir; uygulama tamamen kapanınca sohbet sıfırlanır, teklif ve
  receipt'ler veritabanında kalır.
- SSE sözleşmesi bilinçli olarak katıdır: bilinmeyen olay tipi veya `event_seq` boşluğu akış hatasıdır.
  İstemci ayrıştırıcısında kötü niyetli sınırsız girdiye karşı tampon sınırı yoktur; istemciler yalnız
  yapılandırılmış API'yi tüketir.

## Performans, test ve bakım

- Retrieval küçük kataloğu tarar; büyük katalogda performans ölçülmedi.
- Web ve mobil için bileşen (UI) testi yoktur; ayrıştırıcı, reducer, istemci, yeniden deneme ve durum
  mantığı test edilir. Uçtan uca doğrulama backend HTTP/DB testleri ve fiziksel cihaz denemeleriyle yapıldı.
- Fiziksel test cihazı iPhone 16e (iOS 26.6.2, Expo Go SDK 57) oldu ve karanlık modda denendi. Açık tema,
  büyük yazı, tablet ve VoiceOver için fiziksel doğrulama yapılmadı.
- `build_plan` (`apps/api/app/orchestration/planner.py`) büyük tek bir fonksiyondur. Okuma araçları da
  mesajın teklif kilidi altında çalışır: daha geniş ama basit bir tutarlılık tercihi.
- Testler teşhis için her test veritabanını saklar. Çok sayıda tam koşudan sonra PostgreSQL'in paylaşımlı
  belleği Docker'ın 64 MB `/dev/shm` sınırını aşar ve testler `DiskFullError` verir. README'deki
  [temizlik komutu](README.md#sorun-giderme) yalnız geçici test veritabanlarını siler.
