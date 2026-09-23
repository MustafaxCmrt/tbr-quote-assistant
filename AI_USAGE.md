# Yapay zekâ kullanımı

Bu projeyi yapay zekâ kod ajanlarıyla geliştirdim. Kodun büyük bölümünü ajanlar yazdı. Benim işim çalışma
düzenini kurmak, işi ajanlar arasında bölmek, kararları vermek ve sonucu kendim doğrulamaktı. Bu belge kimin
neyi yaptığını ayrı ayrı anlatır.

## Kullandığım araçlar

| Araç | Ne için kullandım |
|---|---|
| ChatGPT | Görev PDF'inin ve dataset'in analizi; mimari, fazlar, test matrisi ve açık kararları içeren uygulama planı |
| Claude Code (Anthropic; Opus 5 ve Opus 5.5, ilk kurulumda Fable 5.1) | Planın denetimi ve bağımsız kod denetimleri; teslim öncesi güvenlik sertleştirmesi, arayüz düzenlemesi, denetim bulgularının düzeltilmesi, belgeler |
| Codex (OpenAI; GPT-6 Astra) | İlk uygulama: veritabanı, altı araç, planlayıcı, SSE akışı, web ve mobil; son aşamada bağımsız yeniden denetimler |
| Obsidian | Ajanların ortak hafızası: plan, karar defteri, çalışma günlüğü (depo dışında tutuldu) |

Claude'un yazdığı commit'ler git geçmişinde `Co-Authored-By: Claude …` satırı taşır.

Uygulamanın kendisi çalışırken hiçbir yapay zekâ modelini çağırmaz (yedek mod, `provider_calls=0`).
Yapay zekâyı ürünün içinde değil, geliştirme sürecinde kullandım.

## Kurduğum çalışma düzeni

Kendimi bu projede bir şef gibi konumlandırdım. Bir ajan işi yaparken diğeri onu denetledi; ben işi dağıttım,
raporları taşıdım, sonucu takip ettim ve karar verdim.

```text
  Yazan ajan ──── kod ve test ────►  Denetleyen ajan
       ▲                                   │
       │                                rapor
   görev ve karar                          │
       │                                   ▼
       └────────────────────────────────  Ben  ── telefonda ve web'de kendi denemem
```

**Önce plan.** Kod yazılmadan önce ChatGPT'nin hazırladığı planı Claude'a denetlettim. Bu denetim, plandaki
"Plus ürün daha pahalıdır" varsayımının yanlış olduğunu buldu. Veride bazı Plus ürünler temel üründen ucuzdu ve
bu varsayım üç golden senaryoyu bozabilirdi. Bulgular koda geçmeden plana işlendi.

**Ortak hafıza.** Ajanlar bir oturumdan diğerine hafıza taşımaz. Bu yüzden proje dışında bir not klasörü kurdum:
ana bağlam, karar defteri, çalışma günlüğü ve iş takibi. Her ajan oturuma bunları okuyarak başladı. Bitirirken
çalıştırdığı komutu, çıkış kodunu ve commit'i günlüğe yazdı. Bağlam dolduğunda ya da ajan değiştiğinde iş
kaldığı yerden devam etti.

**Ortak kurallar.** İki ajana da aynı kural dosyasını verdim (depo dışında). Başlıcaları:

- Çalıştırılmayan test "geçti" diye raporlanmaz; her sonuç komut ve çıkış koduyla yazılır.
- Firmanın dataset'i ve golden senaryo dosyası değiştirilmez. Kodda senaryo numarasına veya golden mesajına göre
  özel davranış yazmak yasaktır; sistem genel kurallarla çalışmalıdır.
- Testler gerçek PostgreSQL'de koşar. Beklentiyi gevşetmek, fixture değiştirmek ya da testi atlamak yasaktır.
- İsteğim plandaki bir karardan sapıyorsa ajan önce "planda X deniyor, emin misin?" diye uyarır.
- İki ajan aynı dosyada aynı anda çalışmaz.
- Push, veri silme, depoyu herkese açma ve dış servislere harcama yalnız benim açık onayımla yapılır.

**Yazan ve denetleyen ayrı.** Yazan ajanın kendi testlerini yeterli saymadım; önemli aşamalardan sonra kodu
diğer ajana denetlettim. İlk aşamada Codex yazdı, Claude denetledi. Teslim öncesindeki son turlarda roller yer
değiştirdi: Claude düzeltmeleri yaptı, Codex dört tur bağımsız yeniden denetim yaptı.
Denetçi yalnız kodu okumadı; çalışan API'ye yüzlerce Türkçe cümle gönderip veritabanındaki sonucu kontrol etti.
Raporu ben okudum, hangi bulgunun uygulanacağına karar verdim ve yazan ajana ilettim. Ajan her bulguyu önce
başarısız bir testle yeniden üretti, sonra düzeltti. Codex'in dört turda denediği 409 cümle kalıcı teste
dönüştü.

**Kaynak sınırı.** 16 GB belleği olan bilgisayarımda aynı anda tek Docker yığını ve tek test koşusu çalıştırdım.
Bir koşuda test konteyneri bellek sınırını aştığında sınırı artırmadım; kök neden arandı ve bulundu
(FastAPI'nin uç nokta önbelleğinde eski uygulama nesnelerinin tutulması), sonra düzeltildi.

## Benim verdiğim kararlar

- **Firmaya sorduğum iki konu.** Biri indirimlerin çakışması, diğeri golden senaryolardaki çağrı listesinin nasıl
  okunacağıydı. Firma kararı bana bıraktı; seçenekleri karşılaştırıp seçimi yaptım ve gerekçesiyle kaydettim:
  [0001](docs/decisions/0001-indirim-cakismasi.md), [0002](docs/decisions/0002-golden-beklenti-yorumu.md).
- **Katalog yazmasına admin anahtarı.** Telefonla demo için API'yi yerel ağa açınca ürün ve bilgi kayıtlarını
  değiştiren uçlar da ağa açılıyordu. Kimlik doğrulama planda kapsam dışıydı; Claude bunu hatırlattı. Ben yine de
  bu uçlara anahtar eklenmesine karar verdim. Anahtar sunucu tarafında kalır; tarayıcı ve telefon onu görmez.
- **Tasarım kapsamı.** Arayüzün öne çıkmasını istedim ama kapsamı daralttım. Firma logosu, renkleri ve dar ekran
  düzeni yapıldı. Web'e koyu tema, animasyon ya da yeni kütüphane eklenmedi.
- **Belirsizlikte soru.** Türkçe fiyat ifadeleri için ardı ardına yama yapılıyordu. Bir noktada fiyat
  ayrıştırıcısını dondurdum. Sonra onu yalnız bağımsız denetimin bulduğu açıklar için yeniden açtım. Kelime
  kelime yama yerine kural düzeyinde çözümü onayladım: ürün, miktar, fiyat sınırı veya onay kesinleşmezse
  sistem teklifi değiştirmez, soru sorar. Bedeli, bazı meşru cümlelerde gereksiz soru sorulmasıdır
  ([bilinen sınırlamalar](KNOWN_LIMITATIONS.md)).

## Neyi nasıl doğruladım

Güveni bir ajanın "tamam" demesine değil, doğrulanabilir kanıta dayandırdım: kendi denemelerim, otomatik
testler ve bağımsız denetimler.

**Kendi denemelerim.** iPhone 16e'de (iOS 26.6.2, Expo Go SDK 57) şunları denedim: sohbet akışı, teklife ürün
ekleme, aynı değişikliğin web panelinde görünmesi, aynı mesajı tekrar gönderince miktarın ikinci kez artmaması,
kaynak panelini açıp kapatma, klavye ve uzun yanıtta okuma konumu. Denerken bulduğum sorunlar:

- Yanıt kademeli akmıyor, tek parça görünüyordu; ekran her seferinde en sona kayıyordu. Düzeltildi, yeniden
  denedim.
- Web yeniden derlendikten sonra telefon "sunucuya ulaşılamadı" dedi: API yerel ağa kapalı olarak yeniden
  başlamıştı. Düzeltildi ve README'ye uyarı eklendi.

**Otomatik testler.** Ajanlar testleri çalıştırdı, sonuçları ben okudum. Son durumda 1015 backend testi
(22 golden senaryo dahil) gerçek PostgreSQL'de geçiyor. Web ve mobilin ortak mantığı için 25 istemci testi var.
Kanıtlar ve yeniden üretme komutları: [reports/README.md](reports/README.md).

**Bağımsız denetimler.** Her büyük aşamadan sonra kodu diğer ajana denetlettim. Video öncesinde ayrıca özel bir
"diskalifiye denetimi" istedim: PDF'teki diskalifiye sebepleri (gizli değer, fiyat ve stok kuralı, kaynaksız
cevap, web ve mobilin farklı durum göstermesi) tek tek kontrol edildi.

## Yapay zekânın hataları ve nasıl yakalandı

Ajanların yazdığı kodu doğru kabul etmedim. Gerçek örnekler:

- **Fiyat sınırı kaçtı.** `8.500 lirayı geçmeyen endüstriyel barkod okuyucu öner.` cümlesinde sınır algılanmadı
  ve 12.950 TL'lik ürün önerildi. Video öncesi diskalifiye denetimi buldu; düzeltildi ve kalıcı teste eklendi.
- **Olumsuz cümle onay sanıldı.** `PRD-BC-130 1 adet ekle, bekleyebilirim demiyorum.` cümlesiyle stokta olmayan
  ürün teklife eklendi. Aynı denetimde bulundu ve düzeltildi.
- **Planlayıcıda yorum hataları.** Claude'un bağımsız incelemesi, Codex'in yazdığı planlayıcıda dört ciddi yorum
  hatası buldu. Codex bunları önce 13 başarısız testle gösterdi, sonra düzeltti.
- **Düzeltme yeni hata getirdi.** Bir fiyat düzeltmesi "bin" ile yazılan tutarlarda yeni bir hata oluşturdu.
  Bağımsız Claude denetimi bunu yakaladı, ben Codex'e ilettim ve düzeltildi.
- **Son denetim turları.** Codex, Claude'un düzeltmelerinde dört turda yeni Türkçe ifade açıkları buldu. Örneğin
  fiyat sınırının yazıyla verilmesi ya da koşullu bir onay. Her tur kalıcı teste dönüştü. Ardından yapılan kapanış
  denetiminde engelleyici bulgu kalmadı.
- **Her öneri uygulanmadı.** Güvenlik denetiminin 14 önerisinin her biri önce kodda doğrulandı. Bazıları
  gerekçeyle reddedildi; örneğin biri aynı mesajın iki kez uygulanması riskini doğuruyordu.
