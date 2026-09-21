# Bilinen sınırlamalar — F01

- Native debug stream testi **passed** (Mustafa onayı + ekran görüntüsü). Tam cihaz/iOS/Expo Go sürümü henüz bildirilmedi. Gerçek chat ve ortak teklif doğrulaması henüz yok.
- F01b DB/Compose/migration/seed/readiness/kalıcılık passed; 7 gerçek PostgreSQL testi geçti. Üç read tool ve kanonik quote okuması hazır; mutation tool’ları domain düzeyinde uygulandı; gerçek chat, web admin ve ortak teklif ekranları henüz yok. Golden senaryolar **not_run**.
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
- ADR-005/007 firma kararı adaya bıraktıktan sonra accepted; adayın gerekçeli tercihi olarak sunulur.

- Retrieval küçük katalog için tüm aktif adayları normalize ederek tarar; büyük katalog ölçek testi yapılmadı. Admin CRUD henüz yok; canlı DB kaydının retrieval görünürlüğü test edildi.

F04 güncellemesi: altı araç artık gerçek HTTP sohbet üzerinden çağrılıyor; 22 golden passed.
Türkçe parser sınırlı niyet/slot grameridir; açık olmayan miktar/ürün referansında netleştirme ister.
Genel LLM dil anlama veya provider tool calling yoktur. SSE, istemci chat ve native ortak quote
kabulü henüz tamamlanmadı; final teslim olarak yorumlanmamalıdır.

F05 güncellemesi: gerçek SSE, denetim logları ve message retry uygulanıp doğrulandı. Her token'ı
Last-Event-ID ile kalıcı replay kapsam dışıdır. İstemci iptali kabul edilmiş sonlu işi durdurmaz;
kanonik teklifi yenilemek gerekir. Tam web/mobil sohbet ekranları F06/F07 kapsamında devam ediyor.
