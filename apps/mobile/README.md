# Mobil — F01a debug stream

Expo SDK 57 (`expo` 57.0.24), React Native 0.86.3, React 19.2.3, TypeScript 6.0.3.
21 Eylül 2026 tarihinde App Store kaydı Expo Go 57.0.9'u gösteriyor:
[App Store](https://apps.apple.com/us/app/expo-go/id982107779), [SDK 57](https://expo.dev/changelog/sdk-57).
Telefondaki gerçek Expo Go/iOS sürümü ve görsel sonuç **not_verified**; Mustafa kaydedecek.

Repo kökünde `npm ci`; ardından `apps/mobile` içinde `npm start` (Expo LAN).
`.env.example` şablonundaki `EXPO_PUBLIC_API_BASE_URL` değerini yerel `.env` içine
`http://<MAC_LAN_IP>:8000` olarak yaz. Gerçek IP sadece ignore'lu `.env` içindedir.
Fiziksel telefonda `localhost` kullanma. Değişiklik sonrası Expo'yu yeniden başlat.
API başlatma ve iPhone kontrol adımları [ana README](../../README.md) içinde.

`expo/fetch` ile POST yapılır, `response.body.getReader()` ortak `@tbr/contracts` parser'ını
besler. İki satır yaklaşık bir saniye arayla gelir; `done` alınırsa “Tamamlandı” görünür.
15 saniye zaman aşımı, bağlantı hatası, eksik done ve kapalı debug endpoint'i Türkçe açıklanır;
kısmi satırlar korunur, buton yeniden denemeye açılır. Aynı anda ikinci test başlatılmaz.

Geçici debug ekranıdır; gerçek chat, kaynak kartları veya kalıcı teklif içermez.
Mobil Docker Compose dışında çalışır. Mağaza yayını/EAS build yapılmadı.
