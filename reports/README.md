# reports/

Güncel kabul durumu: [acceptance.md](acceptance.md).

Gerçek test kanıtları burada tutulur:

- `golden_results.json` — 22 senaryonun gerçek sonucu (scenario_id, status, expected/actual tools, source_ids, before/after snapshot, commit SHA, timestamp)
- `test_output.txt` — mevcut gerçek koşuların komut/sonuç indeksi (yeni koşu değildir)
- `acceptance.md` — zorunlu gereksinim → kanıt yolu
- `native_smoke.md` — cihaz/Expo sürümü, adımlar, gözlem, ekran görüntüsü yolu

Kurallar: `not_run` / `skipped` / `not_verified` **passed değildir**. Secret, gerçek IP veya kişisel yol
içeren çıktı redakte edilir ve redaksiyon belirtilir. Şablon: vault `Sablonlar/golden_results_template.json`.
