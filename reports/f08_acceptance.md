# F08 kabul checkpoint — 2026-09-21

Durum: **done (uygulama kabul kapısı)**. F09 temiz kurulum/video/erişim/gönderim açık.
Test edilen runtime commit: `e84b2a6749b99c3af935a4a42174bad71eac7248`.

- Tam gerçek PostgreSQL/backend: **204passed42.98s, exit0**, `f08_release_backend.txt`.
- Golden JSON:22passed/0failed/0error/0skipped/0not_run; her senaryo ayrı seed DB.
- 36 negatif hedef: `negative_acceptance.md`; opsiyonel provider adapter/timeout NEG10 uygulanmadı/not_run.
- Bağımsız Opus5/xhigh iki salt okunur review: `f08_claude_review.md`, `f08_claude_followup.md`.
  İkisi de inceledikleri eski sürümleri reddetti; Claude son sürümü onayladı denmez.
  Bildirilen somut P1/hipotezler Codex tarafından başarısız→başarılı regresyonlarla düzeltildi;
  kapsam ve exact test eşlemesi `f08_review_resolution.md`. Bilinen çözülmemiş somut P1 bırakılmadı.
  Bu sınırlı Türkçe dilbilgisinin bütün olası ifadelerde doğru olduğunun kanıtı değildir.
- API yeni runtime ile build/healthy exit0: `f08_release_api_build.txt`; DB/volume korunur.
- Gerçek curl-N doğrudan API16text/0.779s, webproxy16text/0.766s, exit0: `f08_release_stream.txt`.
- Web/native ortak state ve fiziksel temel akış F06/F07 raporlarında; aynı UI sürümü korunur.
  Son backend patch için yeni fiziksel gözlem iddia edilmez. Cihaz/iOS/Expo Go metadatası not_verified.
- Source12aynı, working files/iOS verification bundle key kontrolü exit0: `f08_release_delivery.txt`.
- Reachable Git533blob/32commit key/private path/current-local-value taraması exit0:
  `f08_release_history.txt`; bilinmeyen secret biçimleri/unreachable/yerelde olmayan ref'ler kapsam dışı.

P2 snapshot-log ayrılığı ve eski retry notice, auth/RBAC yokluğu, provider adapter yokluğu,
parser sınırları, native geniş erişilebilirlik kapsamı KNOWN_LIMITATIONS içinde açıklanır.
Özellik kapsamı donduruldu; F09 sırasında yalnız kurulum/kabul hataları giderilir.
