# F01a native smoke

Durum: **passed** — 2026-09-21, Mustafa fiziksel iPhone'da test edip “tamamdır dostum” diyerek ekran görüntüsü paylaştı.

- Test edilen kod commit'i: `cda7fa25dc1e803fc7d71cfa79a79db231d82450`; yalnız ignore'lu mobil .env güncel LAN adresine ayarlandı.
- İlk satır: `0.0 sn · Bağlantı çalışıyor ğüşiöç`.
- İkinci satır: `1.1 sn · İkinci parça ulaştı: ĞÜŞİÖÇ`.
- Son durum: **Tamamlandı**. Türkçe karakterler doğru; iki event'in ayrı alınma zamanları ekranda görünüyor.
- Kanıt: [iPhone ekran görüntüsü](images/f01a_iphone_stream.png), ekran saati 17:45.
- Platform: fiziksel iPhone / Expo Go. Tam cihaz modeli, iOS ve kurulu Expo Go sürümü kullanıcıdan alınmadı; **not_verified**. SDK 57 proje sürümüdür, cihaz sürümü yerine yazılmaz.
- Önceki engeller: Expo Go/CLI hesap girişi, Python için macOS gelen bağlantı izni ve mobil .env LAN adresi düzeltildi.
- Bu yalnız debug transport kanıtıdır; DB/tool mutasyonu veya web/mobil ortak teklif kanıtı değildir. F01b sonradan tamamlandı; ilgili raporlar F01b kabul kaydındadır.

## F07 tam uygulama — 2026-09-21

Durum: **not_verified**. Expo sohbet, kaynak sheet, müşteri/teklif seçimi ve kanonik taslak uygulanıyor.
iOS export/Doctor/typecheck ve Node transport testleri ayrı raporlanır; fiziksel cihaz sonucu sayılmaz.
Mustafa'ya Q-1001 mevcut adet → “BlueScan Air 1 adet daha ekle.” → aynı isteği retry → web aynı
adet/sürüm kontrolü gönderildi. Klavye, kaynak açma, kaydırma, karanlık mod ve cihaz sürüm bilgisi bekleniyor.

Mustafa 19:25 ekran görüntüsünde gerçek uygulamanın iPhone'da açıldığını gösterdi:
[Karanlık mod başlangıcı](images/f07/native-launch-dark.png). Mavi Kırmızı Market A.Ş. / Q-1001
bağlamı yüklenmiş, mesaj kutusu ve Sohbet/Teklif sekmeleri görünür. Bu görüntü **native açılış**
kanıtıdır; henüz mesaj gönderimi, mutation/retry veya klavye açıkken kullanım kanıtı değildir.

### F07 ilk mobil mutation ve ortak state — 19:29

Mustafa'nın fiziksel iPhone görüntüleri Q-1001 **sürüm2, PRD-BC-110 adet2, birim7990.00,
brüt/net15980.00, indirim0.00, stoklu** gösteriyor. Önceki API gözlemi sürüm1/adet1 idi.
`channel=mobile` oturumunun gerçek logunda başarılı add_to_quote ve mutation_applied=true görüldü.
Web'de aynı müşteri/teklif seçilip aynı sürüm/adet/tutarlar gözlendi (yalnız API cevabı değil).

- [Native sürüm ve toplam](images/f07/native-quote-v2.png)
- [Native kalem ve adet](images/f07/native-quote-quantity2.png)
- [Web karşılığı](images/f07/web-quote-v2.png), erişilebilir DOM: `f07_web_shared_state.txt`.

**Mobil add → web ortak state: passed.** Native retry, kaynak sheet, kademeli chat görünümü ve
klavye etkileşimi henüz not_verified. Statik teklif ekranı streaming zamanlamasını kanıtlamaz.


## F07 fiziksel retry ve mobil inceleme düzeltmesi — 2026-09-21
Mustafa “aynı isteği tekrar gönder butonuna bastım” diyerek fiziksel etkileşimi doğruladı.
Salt okunur `python3 scripts/check_f07_native_retry.py` exit0: aynı message_id ile iki ayrı attempt;
ilki mutation_applied=true, ikincisi replayed=true/mutation_applied=false. Q-1001 sürüm2,
PRD-BC-110 adet2, net15980.00 değişmedi. Kanıt: reports/f07_native_retry.txt.
Native kaynak sheet, klavye ve gerçek sohbet metninin kademeli görünümü hâlâ not_verified.

Bağımsız native kaynak/görüntü incelemesinde iki bulgu düzeltildi: başarısız retry önceki metni/kaynakları
silmez; sekmeler tab rolü/selected durumunu bildirir. Node regresyonları fiziksel gözlem yerine geçmez.
`npm test` 19 passed exit0; `npm run typecheck` exit0; `npm run lint` exit0.
Kanıtlar reports/f07_retry_fix_{tests,typecheck,lint}.txt. Base SHA e311738; değişiklik commit'i aşağıda.

iOS export ve delivery kontrolü exit0: f07_retry_fix_ios.txt, f07_retry_fix_delivery.txt. Bağımsız inceleme iki düzeltmeyi kabul etti; reports/f07_native_finish_review.md.
