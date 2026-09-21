# Bilinen sinirlamalar - F07 checkpoint

- F00-F06 gates passed. Backend 144 tests includes 22 HTTP golden scenarios; web CRUD/chat/canonical quote/replay and offline recovery verified.
- F01 native debug stream passed by Mustafa. Full F07 native chat, keyboard, source sheet and web/mobile shared quote remain **not_verified** until physical observation. Device/iOS/Expo Go metadata pending.
- No production authentication/RBAC. Customer selection is demo context, not authentication; do not expose this local demo publicly. PostgreSQL has no host port; runtime DB role cannot change schema.
- Web Compose currently serves Vite development mode; production bundle build is verified, production hosting is not claimed.
- Turkish deterministic intent/slot grammar is bounded. No external LLM provider adapter or paid API calls; this is not LLM tool calling. Source-backed fallback and all six real wrappers run through the backend.
- Full token/Last-Event-ID replay is outside scope. A disconnected accepted request may commit; retry the same message and refetch canonical quote. Mobile conversation is in memory; app restart clears local messages/session, but not DB quote or receipts.
- Native dark mode, large text and tablet layout are implemented but visually **not_verified**.

- Test veritabanları ve ayrı fresh-start volume teşhis için tutulur; zamanla yer kaplar. Otomatik yıkıcı temizlik yoktur.
- Debug endpoint yalnız yerel bağlantı testi; `DEBUG_STREAM_SMOKE=1` ile açılır. Gerçek iş akışı değildir.
- SSE parser UTF-8 ve SSE çerçevesini çözer; uygulama JSON şeması, reconnect/replay ve
  sınırsız kötü amaçlı akışa karşı buffer sınırı F05 sertleştirmesinin konusudur.
- `npm audit` exit 1: Expo geliştirme araçlarının `xcode → uuid` zincirinde 10 orta seviye bildirim.
  Önerilen `--force` çözümü Expo 46'ya gerilettiği için uygulanmadı. SDK uyumluluğunu bozan override eklenmedi.
  Ayrıntı ve advisory: `reports/f01a_npm_audit.txt`. Paket ağacı native prebuild araçlarını da içerir;
  bu oturumda prebuild/EAS/mağaza yayını yapılmadı.

- Retrieval scans the small catalogue; large catalogue performance has not been benchmarked. New admin rows are visible to retrieval; inactive explicitly named models do not fall back to unrelated products.
- ADR-005/007 are accepted candidate choices after the company delegated the decision, not company-provided business rules.
- F08 independent acceptance/security review and F09 clean-install/delivery gates are not complete. Public sharing, video recording/delivery and repository visibility changes need human authorization.

SSE text delivery is deliberately paced after the deterministic answer is ready (50ms/frame, at most80 frames). This is template delivery, not LLM token generation. Physical keyboard/source interactions passed; latest mobile scroll/visible-stream changes still await Mustafa.
