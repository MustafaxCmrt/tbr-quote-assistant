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
