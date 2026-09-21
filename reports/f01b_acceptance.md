# F01b — PostgreSQL, Compose ve kalıcılık

2026-09-21. F01b kapısı passed. Kod SHA: d8102ee (şema/seed/test); altyapı ve rapor commit'i bu dosyanın git geçmişindedir.
Gerçek komutlar, exit code ve stdout ilgili `f01b_*.txt` dosyalarında tutulur. Base commit alanı
komut çalışırken HEAD'i gösterir; pending değişikliklerin olmadığı iddiası değildir.

| Gereksinim | Kanıt | Sonuç |
|---|---|---|
| Boş PostgreSQL 16.15, migration → seed → API → web sırası | f01b_fresh_stack.txt, f01b_full_stack.txt | exit 0, healthy |
| 48/22/6/10/8/6 ve her kaynak alanı | test_seed_preserves_all_original_fields_and_counts | passed |
| Düzenlemeler korunur; eşzamanlı iki seed | test_repeated_seed_preserves_edits_and_concurrent_calls | passed |
| Son tabloda hata, tüm seed + marker rollback | test_seed_failure_rolls_back_every_table_and_marker | passed |
| FK, miktar/fiyat check, tek aktif ürün, geçmiş satırı | test_unique_active_item_and_history_and_checks | passed |
| Şemasız/seed'siz/eski revision 503, hazır 200 | test_ready_requires_migration_and_seed_and_safe_http | passed |
| Ulaşılamayan DB güvenli not_ready | test_unavailable_database_is_not_ready | passed |
| Runtime read/write; DDL ve bootstrap değişimi yasak | test_runtime_role_can_read_but_cannot_change_schema_or_marker | passed |
| Restart sonrası tüm tablolar, ürün düzenlemesi, miktar, receipt; tekrar seed | f01b_persistence_prepare/postgres_restart/persistence_check.txt | exit 0 |
| Alembic/model drift | f01b_migration_drift.txt | exit 0, fark yok |
| Python lint, web tsc/build/lint | f01b_python_lint/web_build/web_lint.txt | exit 0 |
| Kaynak byte bütünlüğü ve stageable secret/IP taraması | f01b_delivery.txt | exit 0 |

Final integration: `docker compose --profile test run --rm test` → **7 passed**, exit 0,
`f01b_final_integration.txt`. Testler gerçek ayrı PostgreSQL servisine bağlanır; her test yeni DB oluşturur.
Test DB'leri ve restart probe snapshot'u teşhis için saklanır; demo DB resetlenmez. SQL DROP çalıştırılmadı.
Receipt burada yalnız kalıcılık kaydıdır; F03 tool executor/replay davranışı henüz uygulanmadı.

Web CUA gözlemi: http://localhost:5173 üzerinde “Teklif asistanı”, “Yönetim ekranı hazırlanıyor.”,
“Bağlantı hazır”; “Bağlantıyı kontrol et” tıklandıktan sonra yine “Bağlantı hazır”. Bu F06 admin kabulü değildir.

İlk kurulumda host bind-mount init script `Permission denied` verdi; role oluşturulamadı ve migration durdu.
Script pinned PostgreSQL imajına 0644 ile kopyalandı. Mevcut volume silinmeden rol tamamlandı.
Ardından ayrı `tbr-f01b-fresh` projesinde tamamen yeni volume ile tam başlangıç exit 0 doğrulandı.
İlk başarısız raporlar saklandı; başarı diye sayılmadı.

Test öz-denetimi: assertion-quality ve test-gap-analysis ile scoped statik inceleme yapıldı.
Kaynak beklentisi production loader'dan bağımsız JSON okur. Negatif constraint testleri duplicate insert
hatasıyla yanlış yeşil olmaması için geçerli mevcut satırı update eder. Derin DB snapshot, kesin miktar,
HTTP status/body, rollback ve yetki reddi gözlemleri var; null-only/always-true assertion yok.
Mutation runner çalıştırılmadı; mutation-score iddiası yok. Otomatik source/test pairing yardımcı aracı
`tree-sitter-language-pack` eksikliğiyle exit 2 verdi; test başarıları yerine sayılmadı.

F01a native debug kanıtı reports/native_smoke.md içinde passed. Gerçek mobil chat/ortak teklif ve 22 golden
senaryo F03–F08 kapılarıdır; henüz not_run. ADR-005/007 provisional kalır.
