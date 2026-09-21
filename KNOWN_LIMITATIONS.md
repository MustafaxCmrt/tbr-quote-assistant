# Bilinen sınırlamalar — F01

- Native debug stream testi **passed** (Mustafa onayı + ekran görüntüsü). Tam cihaz/iOS/Expo Go sürümü henüz bildirilmedi. Gerçek chat ve ortak teklif doğrulaması henüz yok.
- F01b DB/Compose/migration/seed/readiness/kalıcılık passed; 7 gerçek PostgreSQL testi geçti. Altı tool, gerçek chat/quote, web admin ve ortak teklif durumu henüz yok. Golden senaryolar **not_run**.
- Web yalnız bağlantı iskeleti, yerel Vite sunucusudur. Auth/public deployment bu kapının kapsamı değildir.
- Test veritabanları ve ayrı fresh-start volume teşhis için tutulur; zamanla yer kaplar. Otomatik yıkıcı temizlik yoktur.
- Debug endpoint yalnız yerel bağlantı testi; `DEBUG_STREAM_SMOKE=1` ile açılır. Gerçek iş akışı değildir.
- SSE parser UTF-8 ve SSE çerçevesini çözer; uygulama JSON şeması, reconnect/replay ve
  sınırsız kötü amaçlı akışa karşı buffer sınırı F05 sertleştirmesinin konusudur.
- `npm audit` exit 1: Expo geliştirme araçlarının `xcode → uuid` zincirinde 10 orta seviye bildirim.
  Önerilen `--force` çözümü Expo 46'ya gerilettiği için uygulanmadı. SDK uyumluluğunu bozan override eklenmedi.
  Ayrıntı ve advisory: `reports/f01a_npm_audit.txt`. Paket ağacı native prebuild araçlarını da içerir;
  bu oturumda prebuild/EAS/mağaza yayını yapılmadı.
- SDK 57 için App Store Expo Go 57.0.9 kaydı esas alındı; telefondaki gerçek sürüm Mustafa tarafından doğrulanacak.
- ADR-005/007 şirket cevabı gelene kadar geçici yorum; şirkete ait kesin kural gibi sunulmaz.
