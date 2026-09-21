# F02 — Kaynaklı okuma araçları

2026-09-21: F02 passed. `docker compose --profile test run --build --rm test` exit 0,
**47 passed** (F01 regresyonları dahil; unit + gerçek PostgreSQL integration).
`reports/f02_tests.txt`; çalışan API HTTP kontrolü `f02_http_smoke.txt`; lint `f02_lint.txt`;
kaynak/secret taraması `f02_delivery.txt`; Compose rebuild `f02_stack.txt`: tümü exit 0.
İlk test-first collection (eksik implementation) exit 2: `f02_red_tests.txt`; başarı sayılmadı.

| Gereksinim | Test/kanıt |
|---|---|
| Türkçe İ/I/ı/i, USB-C/QR/2D/4G; fiyat/adet ayrımı | tests/unit/test_normalization.py (14 cases) |
| 8500/9000/tam 7990 ve 7989.99 alt sınırı; hard özellikler | test_hard_price_features_and_base_variant |
| Stok 0 yalnız unavailable; açık Plus/SKU/base sınırı | test_unavailable_does_not_become_plus_recommendation |
| USB-C/4G/offline/şube/kılıf alias | test_alias_and_separate_feature_searches |
| Return/delivery/service + SUP | test_policy_includes_supplement_and_exact_source |
| Yeni DB ürünü ve knowledge görünür; inactive/future dışarı; sahte kaynak reddi | test_live_catalog_add_update_delete_and_knowledge_dates; test_explicit_model_over_budget_and_inactive_knowledge |
| Snapshot fiyat, Q-2003 4480.00/268.80/4211.20; geçmiş; read-only | test_quote_snapshot_totals_and_reads_do_not_mutate (tüm tablolar before/after eşit) |
| Readiness gate, HTTP 422/404/200; kanonik GET | test_read_http_gate_validation_and_canonical_quote; smoke_reads.py |
| Saf fiyat: partner, Plus önceliği, aksesuar eşiği, bundle/urgent, software, HALF_UP | tests/unit/test_pricing.py (10 cases) |

Üç read tool gerçek DB'yi okur; katalog/knowledge cache'i yok. 48 ürün için normalize Python
sıralaması kullanılır; büyük katalogda DB arama indeksi gerekecektir. SQLAlchemy parameterized sorgular.
Açık fiyat/özellik/model ve varyant koşulları eleme kuralıdır; stok 0 in_stock_only=false olsa bile
recommendations listesine girmez. Knowledge tarihte Europe/Istanbul günü kullanır; body güvenilmeyen veridir.
HTTP teklif okuması REPEATABLE READ ile version ve kalemleri aynı snapshot'tan alır.

Fiyatlama F02 get_quote toplamları için F03'ten çekilen saf bağımlılıktır; executor/mutation idempotency
henüz uygulanmadı. ADR-005 kabul edilmiş aday kararı: en özel tek kural, toplam stacking yok.
Alternatif toplamsal %13 yorumunda 4 × 9430 net 32816.40 olurdu; seçilen Plus %6 net 35456.80.
Bu tercih şirketin belirlediği stacking kuralı olarak sunulmaz.

Self-review: kesin ID/para, tam JSON/body ve tüm DB snapshot assertionları; mutation runner not_run.
Typed input ek alanları reddeder. Source/test pairing aracının eksik tree-sitter önkoşulu devam ediyor.
Admin CRUD henüz yok; yeni veri görünürlüğü doğrudan gerçek DB eklemesiyle doğrulandı.
22 golden chat senaryosu **not_run**; gerçek orkestrasyon/SSE ve native ortak teklif sonraki kapılardır.
