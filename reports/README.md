# Test kanıtları

Bu klasörde teslim edilen kodun son doğrulama çıktıları var. Her kayıt `scripts/record_command.py` ile
alındı: dosyanın başında zaman (UTC), commit, komut ve çıkış kodu yazar; altında komutun değiştirilmemiş
çıktısı vardır.

| Dosya | İçerik | Sonuç |
|---|---|---|
| [backend_tests.txt](backend_tests.txt) | Backend test paketinin tamamı, README'deki komutla | 1015 passed, exit 0 |
| [golden_results.json](golden_results.json) | 22 golden senaryonun ayrıntılı sonucu: beklenen ve gerçek araç çağrıları, kaynaklar, teklifin önceki ve sonraki hâli | 22/22 passed |
| [checks.txt](checks.txt) | İstemci testleri, TypeScript tip kontrolü, ESLint, web üretim derlemesi, Python lint (ruff), teslim taraması | 6 komutun hepsi exit 0 |
| [npm_audit.txt](npm_audit.txt) | Üretim bağımlılıklarının güvenlik taraması | 10 orta seviye bildirim ([açıklama](../KNOWN_LIMITATIONS.md#güvenlik-ve-dağıtım)) |

Kanıtlar 23 Eylül 2026'da `c41e70f` commit'inde üretildi. Sonraki commit'ler uygulama davranışını
değiştirmez; yalnız belgeleri ve test dosyalarının açıklama satırlarını günceller:

```sh
git diff --stat c41e70f HEAD -- apps packages scripts compose.yaml
```

## Yeniden üretme

```sh
# Backend testlerinin tamamı
docker compose --profile test run --build --rm test

# Golden sonuç dosyası (reports/golden_results.json üzerine yazar)
docker compose --profile test run --rm -v "$PWD/reports:/evidence" \
  -e GOLDEN_REPORT_PATH=/evidence/golden_results.json -e EVIDENCE_COMMIT_SHA="$(git rev-parse HEAD)" \
  test pytest -q tests/golden/test_chat_golden.py
```

İstemci ve teslim kontrollerinin komutları [README](../README.md#testler) içindedir. Bir komutun çıktısını
aynı biçimde kaydetmek için: `python3 scripts/record_command.py <dosya-adı> <komut…>` (kayıt bu klasöre
yazılır). Çok sayıda tam koşudan sonra `DiskFullError` görülürse
[temizlik komutu](../README.md#sorun-giderme) yalnız geçici test veritabanlarını siler.
