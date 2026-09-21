# F01a kabul kanıtı — 21 Eylül 2026

Yerel uygulama/otomatik kontroller tamamlandı. Native **not_verified**; F01 çıkış kapısı açık.
F01b **not_run** (SSD bekleniyor; bu oturumda Docker kullanılmadı).

| Gereksinim | Kanıt |
|---|---|
| Python 3.12 + kilitli FastAPI/uvicorn | apps/api/pyproject.toml, uv.lock; f01a_uv_sync.txt exit 0 |
| GET /health/live; iki kademeli Türkçe event + done | f01a_curl_stream.txt exit 0; 0.055 / 1.056 / 2.057 saniye |
| Env ile debug kapatma | f01a_debug_flag.txt exit 0; unset/0/false/invalid kapalı, 1/true açık |
| UTF-8 çok baytlı karakterin iki chunk'a bölünmesi | `utf8_multibyte_split`, `all_byte_boundaries_preserve_frames` |
| CRLF | `crlf_across_chunks` |
| bir chunk'ta birden çok event | `multiple_events_in_one_chunk` |
| yarım kalan son event | `unfinished_final_event_is_discarded` |
| Ek parser sınırları | `comments_multiline_data_and_persistent_id`, `empty_stream_and_bare_cr`, `truncated_utf8_is_rejected` |
| Parser test sonucu | f01a_final_tests.txt: `npm test`, 8 passed / 0 failed / 0 skipped, exit 0 |
| Mobil + contracts tip/lint | f01a_final_typecheck.txt ve f01a_final_lint.txt, exit 0 |
| Kilitten temiz npm kurulum | f01a_npm_ci.txt exit 0 |
| Expo SDK uyumu | f01a_expo_check_retry.txt exit 0; f01a_expo_doctor.txt 21/21, exit 0 |
| Metro başlangıcı | f01a_metro_start_retry.txt exit 0; localhost /status doğrulandı; süreç kontrollü kapatıldı |
| iOS bundle | f01a_ios_export.txt exit 0, 591 modül; fiziksel cihaz kanıtı değildir |
| POST + expo/fetch + getReader + ortak parser | apps/mobile/App.tsx; derleme doğrulandı, native çalışma **not_verified** |
| Orijinal kaynak + teslim taraması | f01a_delivery_check.txt exit 0; 12/12 kaynak aynı, yerel env/talimatlar ignore altında |
| iPhone gözlemi | native_smoke.md: **not_verified**, Mustafa bekleniyor |

SDK dayanağı: [App Store Expo Go](https://apps.apple.com/us/app/expo-go/id982107779) 57.0.9,
[Expo SDK 57](https://expo.dev/changelog/sdk-57), [Expo fetch](https://docs.expo.dev/versions/v57.0.0/sdk/expo/).
API aktarımı: [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse).

Başarısız ilk denemeler saklandı: uv `--exact` yerine `--bounds exact`; contracts Node types;
Expo React types 19.2.2 yerine 19.2.4. Sonraki exit 0 raporları yukarıda.
`npm audit` **exit 1**: 10 moderate bildirim; KNOWN_LIMITATIONS.md. Audit yeşil sayılmadı.
Test assertion'ları/şirket fixture'ları gevşetilmedi. Parser testleri kaynak karşısında gözden geçirildi:
çıktı eşitliği, tamamlanmadan event çıkmaması ve EOF davranışı doğrudan assertion içerir.

Raporlardaki SHA komut anındaki HEAD'dir; pending çalışma ağacı açıkça belirtilir.
API uygulama commit'i: `adefc3967c95446584812d569bdfa308e413ace1` (push exit 0).
Bu raporu içeren commit, mobil/parser uygulamasını ve raporları birlikte taşır; son SHA vault'ta kaydedilir.

Metro ilk deneme 127.0.0.1 sorgusunda timeout (exit 1); Expo’nun bildirdiği localhost ile tekrar exit 0. Native/LAN erişimi olarak sayılmadı.

Mobil/parser uygulama commit’i: `db1a17b3637bac99fd872be6ffa5bafcab4ad43e` (push exit 0). Çıktı dosyalarında yalnız satır sonu/EOF boşlukları normalize edildi; komut/exit/sonuç metni korunmuştur.
