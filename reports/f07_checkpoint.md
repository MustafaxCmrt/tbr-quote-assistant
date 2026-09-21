# F07 — native uygulama, cihaz kapısı açık

Base SHA `ecfc5dfd3320ef34a52b40a688da1def7b6a64b0`; F07 değişiklikleri bu raporla aynı commit'tedir.

- Typed client `expo/fetch`, POST reader, ortak parser/reducer; kaynak sheet, Türkçe tool özetleri,
  retry aynı UUID, yeni mesaj Expo Crypto UUID. Teklif backend'den yeniden okunur; istemci hesap yapmaz.
- `f07_client_tests.txt`: transport/UTF-8/terminal hata/hostname maskeleme + shared parser/reducer + web race.
- `f07_typecheck_verified.txt`: uygulama ve ayrı Node test tsconfig typecheck exit0. Önce test Node tipleri
  eksikti; ilk failure `f07_typecheck_final.txt` korundu, test kapsamı dışlanarak gizlenmedi.
- `f07_ios_export_final.txt`: iOS Hermes export exit0, placeholder API adresiyle. İlk export yanlış kök
  çalışma dizininden çağrılmıştı (`f07_ios_export.txt`, exit1); workspace komutuyla düzeltildi.
- `f07_doctor.txt`: 21/21, exit0. `f07_lint.txt` exit0. `f07_delivery.txt`: source bytes ve secret/IP kontrolü exit0.
- `f07_lan_api.txt`: yerel LAN demo API bind exit0; PostgreSQL host'a açılmadı. Gerçek adres yalnız
  ignore'lu apps/mobile/.env; rapora yazılmadı. Metro npm start ile 8081'de yeniden açıldı.
- `f07_npm_audit.txt` exit1: mevcut Expo → xcode → uuid zincirinde 10 moderate bildirim; önerilen
  force çözümü SDK46'ya gerilettiği için uygulanmadı. Önceki F01 sınırlaması devam ediyor.
- Son kod: `f07_final_tests.txt` 17 passed; `f07_final_typecheck.txt`, `f07_final_lint.txt`,
  `f07_final_ios_bundle.txt`, `f07_final_delivery.txt` exit0. Bunlar son kaynak sürümünün teknik kanıtıdır.

F01 debug ekranı DebugSmoke.tsx içinde korunur; EXPO_PUBLIC_DEBUG_STREAM_SMOKE=1 ile seçilir.
Tam uygulama varsayılandır. Fiziksel iPhone sonucu **not_verified**; test adımları apps/mobile/README.md.
Native görsel review henüz yapılmadı; web görüntüsü native kanıtı olarak kullanılmaz.
