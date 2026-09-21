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


## F07 kaynak ve klavye cihaz gözlemi — 2026-09-21 19:38–19:39
Mustafa: “klavye açıkken göndere ulaşamıyorum klavye butonun üstünde kalıyor” — **failed**.
Önceki durum: reports/images/f07/native-keyboard-overlap-before.png.
Mustafa Bilgi kaynağına basıp Kapat ile kapanmasını doğruladı — **passed (insan gözlemi)**.
Yanıt/kaydırma/kaynak düğmeleri: native-policy-response.png, native-policy-sources.png. Statik görüntüler zamanlama kanıtı değildir; streaming timing not_verified.
Salt okunur API kontrolünde yeni mobile mesaj ea204128-43f4-456c-a509-6f66a3495678 yalnız get_knowledge_entries ×2/get_quote çağırmış, mutation_applied sayısı0.

Düzeltme: nested Chat KeyboardAvoidingView kaldırıldı; tek KAV ekran kökünde SafeAreaView'ı sarar (iOS padding, Android height).
Kurulu RN hesaplaması yerel frame ile keyboard screenY'yi karşılaştırıyordu; root yerleşimi koordinat farkını kaldırır. Sabit cihaz/header yüksekliği tahmin edilmedi.
Kaynak: https://reactnative.dev/docs/keyboardavoidingview ; kurulu node_modules/react-native/Libraries/Components/Keyboard/KeyboardAvoidingView.js.
Bağımsız Codex native reviewer kaynak diff'inde yeni koordinat/flex hatası bulmadı; fiziksel tekrar kontrolü **not_verified**.
`npm run typecheck`, `npm run lint`, iOS export exit0: reports/f07_keyboard_typecheck.txt, f07_keyboard_lint.txt, f07_keyboard_ios.txt.
Mustafa'dan Reload ardından klavye açıkken input/Gönder ve akışın kademeli olup olmadığını tekrar gözlemesi istendi. F07 açık.


## F07 klavye passed; okuma konumu ve görünür aktarım düzeltmesi
Mustafa yeni 19:44 fiziksel iPhone görüntüsüyle input/Gönder'in klavye üstünde erişilebilir olduğunu doğruladı.
Kanıt: reports/images/f07/native-keyboard-fixed.png. Klavye temel kullanım **passed**; büyük yazı/tablet iddiası yok.
Mustafa kaynak aç/Kapat için passed; yanıt tek seferde görünüyor ve otomatik sona kaydırıyor diye iki sorun bildirdi.

Chat sürekli scrollToEnd yapmaz; yeni gönderimde mesajın başına tek sefer konumlanır. Kullanıcı sürükleyince bekleyen otomatik konumlanma iptal olur.
Kısa son mesaj viewport yüksekliğini doldurur, yeni mesajın başına ulaşmak için alan sağlar. Retry eski layout koordinatını kullanmaz; yeni ölçüm alır.
Deterministik yanıt hazırlandıktan sonra SSE text_delta artık en az80 karakter/parça ve50ms aralıkla iletilir;
en fazla80 parça (planlanan ek bekleme toplamı4sn). Bu bilinçli **şablon aktarım hızı**, model token üretimi değildir.
Transaction pacing başlamadan tamamlanır; kısmi yanıt/error/receipt kuralları aynı.

6 gerçek PostgreSQL SSE testi passed, typecheck/lint/iOS export exit0: reports/f07_reading_stream_tests.txt,
f07_reading_final_typecheck.txt, f07_reading_final_lint.txt, f07_reading_final_ios.txt.
API LAN demo bind korunarak yalnız API yeniden build/start edildi; DB reset/recreate yapılmadı.
`python3 scripts/smoke_stream.py` exit0: curl-N doğrudan API'de16 text frame0.782sn, web proxy'de16 frame0.784sn.
Canlı aktarım kanıtı reports/f07_reading_live_stream.txt; **yeni native okuma/akış gözlemi not_verified**.
