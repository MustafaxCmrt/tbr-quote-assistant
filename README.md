# The Blue Red — Teklif Asistanı

Hedef: kaynaklı Türkçe chat, altı gerçek tool ve web/mobil ortak kalıcı teklif durumu.
**21 Eylül 2026: yalnız F01a uygulanmıştır.** FastAPI debug SSE, Expo test ekranı ve ortak
parser hazırdır. iPhone debug streaming Mustafa tarafından doğrulandı; F01a tamamlandı. F01b ve tam F01 kapısı açıktır.

## Kurulum ve iPhone testi

Gerekenler: uv 0.12.17, Python 3.12.14, Node 24.21.0, npm 11.19.0.
Python sürümü `apps/api/.python-version`, Node `.node-version`; bağımlılıklar `uv.lock` ve kök `package-lock.json` ile kilitli.
Expo SDK 57, FastAPI 0.141.1 ve uvicorn 0.53.0 kurulup doğrulandı.

1. Repo kökünde kur ve API'yi başlat:

   ```sh
   cd /Users/comert/Desktop/tbr-quote-assistant
   uv sync --directory apps/api --locked
   npm ci
   DEBUG_STREAM_SMOKE=1 uv run --directory apps/api --locked uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
   ```

2. `apps/mobile/.env` dosyasına `EXPO_PUBLIC_API_BASE_URL=http://<MAC_LAN_IP>:8000` yaz.
   `<MAC_LAN_IP>` yerine Mac'in Wi-Fi ayarlarındaki IP adresini kullan. Bu oturumda yerel dosya hazırlandı;
   ağ değişirse güncelle. IP'yi rapora/örnek dosyaya/ekran görüntüsüne koyma. Telefonda localhost Mac'e gitmez.
3. İkinci terminalde Expo'yu başlat:

   ```sh
   cd /Users/comert/Desktop/tbr-quote-assistant/apps/mobile
   npm start
   ```

4. Expo Go ve Mac CLI’da aynı Expo hesabıyla giriş yap (`npx expo login`); ardından Expo’yu yeniden başlat. Mac ve iPhone aynı Wi-Fi'dayken App Store'daki güncel Expo Go'yu kullan. iPhone Kamerasıyla
   terminaldeki QR'ı okut, Expo Go'da aç; yerel ağ izni sorulursa izin ver.
5. **Stream testi** butonuna bas. Önce “Bağlantı çalışıyor ğüşiöç”, yaklaşık bir saniye sonra
   “İkinci parça ulaştı: ĞÜŞİÖÇ”, yaklaşık bir saniye sonra **Tamamlandı** görmelisin.
   Satırlar topluca değil, geldikçe görünmeli; başlarında geçen süre yer alır. İkinci denemede eski satırlar temizlenir.
6. macOS güvenlik duvarı sorarsa bu yerel test için Python/uvicorn ve Node'un gelen bağlantılarına izin ver;
   güvenlik duvarını tamamen kapatman gerekmez.
7. Çalışmazsa ilk üç kontrol: **(a)** aynı Wi-Fi, VPN/misafir ağı izolasyonu ve Expo Go yerel ağ izni;
   **(b)** iPhone Safari'den `http://<MAC_LAN_IP>:8000/health/live` açılıyor mu, API terminali çalışıyor mu;
   **(c)** `.env` adresi doğru mu, Expo yeniden başlatıldı mı, Expo Go SDK 57 ile uyumlu mu?

Metro QR bağlantısı ile API bağlantısı ayrıdır. Expo'nun açılması API erişimini tek başına kanıtlamaz.
Native sonuç **passed**: Mustafa iPhone ekranında 0.0/1.1 sn zamanları ve Tamamlandı durumunu paylaştı.
Kanıt `reports/native_smoke.md` içinde; tam cihaz/iOS/Expo Go sürüm bilgisi henüz bildirilmedi.

## Doğrulama

Repo kökünde:

```sh
npm test
npm run typecheck
npm run lint
npm exec --workspace @tbr/mobile -- expo install --check
PYTHONPATH=apps/api uv run --project apps/api --locked python scripts/check_debug_flag.py
# API yukarıdaki komutla açıkken:
python3 scripts/smoke_api.py
```

`scripts/smoke_api.py` gerçek `curl -N` çalıştırır, olayların geliş zamanlarını ve Türkçe içeriklerini doğrular.
`reports/` içinde gerçek komutlar, exit code'lar ve çıktılar bulunur; başarısız ilk denemeler de saklanır.
iOS bundle üretimi native cihaz gözlemi yerine geçmez. Kanıt haritası: [F01a kabul raporu](reports/f01a_acceptance.md).

## Kapsam ve düzen

- `apps/api`: `/health/live`, env ile açılan `/api/debug/stream-smoke`. `DEBUG_STREAM_SMOKE` yoksa/0 ise debug yolu yoktur;
  değişiklik API yeniden başlatılınca geçerli olur. Kök `.env` otomatik yüklenmez.
- `apps/mobile`: geçici Türkçe bağlantı ekranı, `expo/fetch`, ortak saf parser. Compose dışında çalışır.
- `packages/contracts`: testli SSE parser; gerçek DTO/event sözleşmeleri F05'te sabitlenecek.
- `apps/web`: henüz uygulanmadı. `data/source`: orijinal, değiştirilmedi.
- F01b: SSD sonrasında Compose/PostgreSQL 16, migration, JSON seed, `/health/ready`, restart kalıcılığı.
  **Bu oturumda Docker çalıştırılmadı ve F01b uygulanmadı.**

ADR-005 (indirimler toplanmaz, özel kural önceliği) ve ADR-007 (beklenen çağrı/kaynaklar minimum)
firma cevabı bekleyen **geçici yorumlardır**; fiyat/tool motoru henüz uygulanmadı.

[AI kullanımı](AI_USAGE.md) · [Bilinen sınırlamalar](KNOWN_LIMITATIONS.md)
