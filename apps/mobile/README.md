# Mobil — gerçek sohbet ve ortak teklif

Expo 57.0.24, React Native 0.86.3, React 19.2.3, TypeScript 6.0.3; paketler lock dosyasında.
Yeni mesaj kimliği `expo-crypto` 57.0.3 `randomUUID()` ile üretilir; aynı gönderimin retry'ı aynı kimliği kullanır.
[Resmî Expo Crypto belgesi](https://docs.expo.dev/versions/latest/sdk/crypto/) Expo Go desteğini açıklar.

Repo kökünde `npm ci`, `python3 scripts/init_env.py`, ardından
`API_BIND_HOST=0.0.0.0 docker compose up --build -d --wait api web` çalıştır.
Bu seçenek yerel ağ demosu içindir; varsayılan loopback bind daha sınırlıdır. PostgreSQL host'a açılmaz.
`apps/mobile/.env` içinde `EXPO_PUBLIC_API_BASE_URL=http://<MAC_LAN_IP>:8001` yaz;
gerçek IP yalnız bu ignore'lu dosyada kalır. Fiziksel telefonda localhost kullanma.
`apps/mobile` içinde `npm start`; Expo Go'da QR okut veya daha önce açtığın projeyi yeniden aç.
`.env` değişince Expo'yu yeniden başlat. API ve Metro iki ayrı bağlantıdır.

Müşteri / teklif seçimi yeni bağlamda yeni sohbet oturumu açar. Sohbet `expo/fetch` POST,
`response.body.getReader()` ve ortak `@tbr/contracts` parser/reducer kullanır. Kaynak düğmeleri
başlık, ID, bölüm ve kaynak yolunu yerel sheet içinde gösterir. Ham HTML çalıştırılmaz.
Teklif tabı yalnız kanonik API tutarlarını gösterir; mutation/done/replay, uygulamaya dönüş,
manuel yenileme ve 2,5 saniyelik polling ile yenilenir. Eski sürüm yenisini ezmez.

Akışı durdurmak kabul edilmiş DB işlemini geri almaz. Kısmi yanıt korunur, aynı mesajla retry
yapılır. Uygulama tamamen kapanınca yerel sohbet/oturum belleği sıfırlanır; teklif DB'de kalır.
Mobil teklif hesabı veya offline mutation kuyruğu yoktur.

`npm test`, `npm run typecheck`, `npm run lint` repo kökünden çalışır. iOS export ve Doctor
raporları `reports/f07_*` altında. **Tam native chat/shared quote gözlemi not_verified**;
export veya Node transport testi native başarı yerine geçmez. F01 debug smoke Mustafa tarafından
gözlendi; `EXPO_PUBLIC_DEBUG_STREAM_SMOKE=1` eski debug ekranını açar (API'de de DEBUG_STREAM_SMOKE=1 gerekir).
Varsayılan gerçek uygulamadır. Mobil Compose dışında çalışır; EAS/mağaza yayını yapılmadı.

## iPhone kabul adımları

1. Mavi Kırmızı Market A.Ş. / Q-1001 seç; BlueScan Air mevcut adedini ve sürümü not et.
2. “BlueScan Air 1 adet daha ekle.” gönder. Parça parça yanıt, araç özetleri ve kaynakları gör.
3. Teklif tabında adet bir artmış olmalı; web aynı Q-1001'de aynı adet/sürümü göstermeli.
4. Aynı isteği tekrar gönder; adet/sürüm ikinci kez artmamalı. Yeni mesaj göndermek ayrı işlemdir.
5. Bir kaynak düğmesini aç/kapat; uzun mesajı kaydır ve klavye açıkken Gönder'in erişilebilirliğini dene.
6. Bağlantı sorunu olursa ilk üç kontrol: aynı Wi-Fi/yerel ağ izni, API health/8001 ve firewall izni,
   `.env` adresi ve değişiklikten sonra Metro'nun yeniden başlaması. macOS Python/Docker bağlantı
   izni sorarsa bu yerel demo API'sine gelen bağlantıya izin ver; güvenlik duvarını tamamen kapatma.
