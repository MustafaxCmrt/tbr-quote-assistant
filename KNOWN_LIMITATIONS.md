# Bilinen sınırlamalar — F01a

- Native iPhone testi **not_verified**. Typecheck/iOS export, cihazda artımlı gösterim kanıtı değildir.
- F01b ve sonraki fazlar henüz uygulanmadı: DB, Compose, migration, seed, kalıcılık, altı tool,
  gerçek chat/quote, web admin ve ortak teklif durumu yok. Golden/DB testleri **not_run**.
- Debug endpoint yalnız yerel bağlantı testi; `DEBUG_STREAM_SMOKE=1` ile açılır. Gerçek iş akışı değildir.
- SSE parser UTF-8 ve SSE çerçevesini çözer; uygulama JSON şeması, reconnect/replay ve
  sınırsız kötü amaçlı akışa karşı buffer sınırı F05 sertleştirmesinin konusudur.
- `npm audit` exit 1: Expo geliştirme araçlarının `xcode → uuid` zincirinde 10 orta seviye bildirim.
  Önerilen `--force` çözümü Expo 46'ya gerilettiği için uygulanmadı. SDK uyumluluğunu bozan override eklenmedi.
  Ayrıntı ve advisory: `reports/f01a_npm_audit.txt`. Paket ağacı native prebuild araçlarını da içerir;
  bu oturumda prebuild/EAS/mağaza yayını yapılmadı.
- SDK 57 için App Store Expo Go 57.0.9 kaydı esas alındı; telefondaki gerçek sürüm Mustafa tarafından doğrulanacak.
- ADR-005/007 şirket cevabı gelene kadar geçici yorum; şirkete ait kesin kural gibi sunulmaz.
