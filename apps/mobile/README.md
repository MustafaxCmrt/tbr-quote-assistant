# Mobil uygulama (Expo)

Expo Go ile iPhone ve Android'de açılan Türkçe sohbet ve teklif uygulaması (fiziksel deneme iPhone'da
yapıldı). Expo SDK 57, React Native 0.86, React 19, TypeScript; paketler kökteki `package-lock.json` ile
kilitli. Docker Compose dışında, geliştirici makinesindeki Metro sunucusundan çalışır.

## Özellikler

- **Müşteri ve teklif seçimi:** her yeni seçim yeni bir sohbet oturumu açar.
- **Sohbet:** yanıt SSE ile parça parça gelir; araç çağrılarının özeti ve kaynak düğmeleri gösterilir.
  Kaynak düğmesi başlık, kimlik, bölüm ve kaynak yolunu bir alt sayfada açar; HTML çalıştırılmaz.
- **Teklif sekmesi:** yalnız API'nin hesapladığı tutarları gösterir. İşlem bitince, uygulamaya
  dönülünce, elle yenilemede ve 2,5 saniyede bir yenilenir; eski sürüm yenisinin üzerine yazılmaz.
- **Güvenli yeniden deneme:** her yeni mesaj `expo-crypto` ile benzersiz bir kimlik alır; bağlantı
  koparsa aynı mesaj aynı kimlikle tekrar gönderilir ve sunucu teklifi ikinci kez değiştirmez.
  Akışı durdurmak, kabul edilmiş işlemi geri almaz.
- Mobilde fiyat hesabı veya çevrimdışı işlem kuyruğu yoktur. Uygulama kapanınca sohbet belleği
  sıfırlanır; teklif veritabanında kalır.

## Çalıştırma

Adımlar: [kök README → Mobil uygulama](../../README.md#mobil-uygulama-expo-go). Kısaca:

```sh
API_BIND_HOST=0.0.0.0 docker compose up --build -d --wait api web   # API'yi yerel ağa aç
# apps/mobile/.env içine: EXPO_PUBLIC_API_BASE_URL=http://<MAC_LAN_IP>:8001
npm start --workspace @tbr/mobile                                     # QR'ı Expo Go ile okut
```

`apps/mobile/.env` git dışındadır; gerçek IP adresi yalnız bu dosyada kalır. Telefonda `localhost`
bilgisayara gitmez. Metro (uygulama kodu) ve API ayrı bağlantılardır; `.env` değişince Expo'yu
yeniden başlatın. Demo bitince API'yi `API_BIND_HOST=127.0.0.1` ile tekrar yerel adrese kapatın.

## Kod

| Yol | İçerik |
|---|---|
| `App.tsx` | Müşteri/teklif seçimi, Sohbet ve Teklif sekmeleri, kaynak alt sayfası |
| `src/screens/` | `Chat.tsx`, `Quote.tsx` |
| `src/api/` | HTTP ve SSE istemcisi, yeniden deneme ve teklif durumu |
| `src/shared/ui.tsx` | Ortak arayüz bileşenleri |
| `tests/` | İstemci, yeniden deneme ve durum testleri (`npm test`, repo kökünden) |

SSE ayrıştırıcı ve olay tipleri ortak [`@tbr/contracts`](../../packages/contracts/README.md) paketinden gelir.

`npm test`, `npm run typecheck` ve `npm run lint` repo kökünden çalışır.

Bağlantı testi için: mobil `.env` içinde `EXPO_PUBLIC_DEBUG_STREAM_SMOKE=1` ve API'de
`DEBUG_STREAM_SMOKE=1` verilirse, gerçek uygulama yerine veritabanı kullanmayan basit bir akış testi
ekranı açılır. Varsayılan gerçek uygulamadır. Mağaza veya EAS yayını yapılmadı.
