# AI kullanımı

F00 kaynak analizi ve plan denetimi önceki Claude Code oturumunda yapıldı; uygulama testi sayılmaz.
F01a'da Codex, Mustafa'nın kapsamıyla API debug SSE, Expo ekranı, ortak parser, test ve belgeleri yazdı;
uv/npm kurulumlarını, curl zamanlı aktarımı, TypeScript/lint/parser ve iOS bundle kontrollerini çalıştırdı.
Gerçek komut/sonuçlar `reports/` altında. Expo SDK seçimi resmî sürüm ve App Store kayıtlarıyla kontrol edildi.

İnsan girdisi: Mustafa kapsamı ve Docker yasağını belirledi; fiziksel iPhone debug gözlemini ekran görüntüsüyle doğruladı.
Manuel insan kod denetimi veya native başarı yapılmış gibi gösterilmez. Uygulama ücretli API/provider çağırmaz.

F01b'de Codex PostgreSQL şeması, Alembic revision, JSON importer, readiness, sınırlı DB rolü,
Compose ve React/Vite iskeletini yazdı. Gerçek PostgreSQL'de 7 integration testi, restart snapshot
karşılaştırması, boş volume başlangıcı, build/lint ve tarayıcı smoke çalıştırıldı. İlk init izin
hatası veriyi silmeden düzeltildi; başarısız çıktılar raporlarda korundu. AI testleri insan
kod denetimi yerine sunulmaz; golden/tool/chat kabulü bu checkpoint'te henüz yapılmadı.

F02: Codex Türkçe normalizasyon, read DTO/araçlar, EvidenceBundle, snapshot quote ve saf fiyatlamayı geliştirdi. 47 unit/PostgreSQL testi, gerçek HTTP smoke ve lint exit 0. Firma cevabı vault güncellemesiyle okundu; ADR-005/007 accepted aday tercihi olarak belgelendi. Golden/chat henüz çalıştırılmadı.

F03: Codex tek transaction executor, üç gerçek mutation wrapper, server key/receipt ve DB lock
korumalarını yazdı. Aynı/farklı key yarışları, stale replay, atomik grup rollback, admin fiyat/stok
kilidi, backorder, replacement ve restart sonrası gerçek wrapper replay PostgreSQL üzerinde test edildi.
Salt okunur ikinci AI incelemesinde kanıtlanmış önemli kusur bulunmadı; altı test açığı raporlandı.
Bu açıklar için eklenen testler dahil son gerçek PostgreSQL/unit koşusu 94 passed; ayrıntı reports/f03_acceptance.md.
Bu inceleme insan denetimi veya ampirik mutation score değildir.

F04: Codex genel Türkçe niyet/slot planlayıcı, kalıcı mesaj planı, kaynaklı template yanıtı ve
HTTP golden runner yazdı. Bağımsız salt-okunur AI incelemesinin dört somut parser/guard bulgusu
regresyonlarla düzeltildi; ilk negatif testlerdeki sayı ayrıştırma hataları da giderildi.
Son gerçek koşu 136 passed (22 golden dahil); gerçek HTTP smoke/lint/delivery exit0.
Sistem LLM tool calling yaptığını iddia etmez; provider adaptörü ve API harcaması yoktur.
