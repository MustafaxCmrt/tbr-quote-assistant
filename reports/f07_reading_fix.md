# Sohbet okuma düzeltmesi


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
