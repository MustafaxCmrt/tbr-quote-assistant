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
