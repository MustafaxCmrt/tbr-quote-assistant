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

## Golden senaryo özeti

`golden_results.json` dosyasından üretildi. Her senaryo taze bir veritabanında gerçek sohbet uç noktasından
geçer. "Yazma çağrıları" teklifi değiştiren araç çağrılarıdır; okuma çağrıları (`search_products`,
`get_knowledge_entries`, `get_quote`) ve her çağrının girdi/çıktısı JSON dosyasındadır. "Kanal" senaryonun
`channel` alanıdır; web ve mobil senaryolar aynı sohbet uç noktasından koşar. SCN-010 ve SCN-013'te aynı
mesaj ikinci kez gönderilir: ikinci çağrı tekrar olarak tanınır ve teklif yalnız bir kez değişir.

| Senaryo | Konu | Kanal | Yazma çağrıları | Teklif sürümü | Sonuç |
|---|---|---|---|---|---|
| SCN-001 | Kesin fiyat limiti altında stoklu kablosuz okuyucu ekleme | mobil | `add_to_quote` | 1 → 2 | passed |
| SCN-002 | Stokta olmayan ürünü varsayılan eklemeyi reddedip geçerli alternatif sunma | mobil | yok | değişmedi | passed |
| SCN-003 | Tekrar eklemede ikinci satır açmadan miktarı artırma | mobil | `add_to_quote` | 1 → 2 | passed |
| SCN-004 | Mevcut teklif kalemi miktarını güncelleme | web | `update_quote_item` | 1 → 2 | passed |
| SCN-005 | Pahalı teklif kalemini daha ucuz alternatifle değiştirme | mobil | `replace_with_alternative` | 1 → 2 | passed |
| SCN-006 | Stok dışı teklif kalemini stoklu alternatifle değiştirme | web | `replace_with_alternative` | 1 → 2 | passed |
| SCN-007 | Mutasyonsuz, kaynaklı politika cevabı verme | mobil | yok | değişmedi | passed |
| SCN-008 | Uyumluluk cevabıyla birden fazla gerekli ürün ekleme | mobil | `add_to_quote`, `add_to_quote` | 1 → 3 | passed |
| SCN-009 | Yedek modda güvensiz mutasyon yapmadan kaynaklı cevap dönme | web | yok | değişmedi | passed |
| SCN-010 | Tekrarlı akış isteğinde miktarı iki kez artırmama | mobil | `add_to_quote`, `add_to_quote` (tekrar, uygulanmadı) | 1 → 2 | passed |
| SCN-011 | Ekleme sonrası iş ortağı miktar indirimini yeniden hesaplama | web | `add_to_quote` | 1 → 2 | passed |
| SCN-012 | Türkçe fiyat limitli aksesuar ekleme | mobil | `add_to_quote` | 1 → 2 | passed |
| SCN-013 | Plus üründe tekrar ekleme tekrarsızlığı | mobil | `add_to_quote`, `add_to_quote` (tekrar, uygulanmadı) | 1 → 2 | passed |
| SCN-014 | Stok dışı mobil yazıcıyı stoklu yazıcıyla değiştirme | web | `replace_with_alternative` | 1 → 2 | passed |
| SCN-015 | Kurulum hizmeti miktarını güncelleme | web | `update_quote_item` | 1 → 2 | passed |
| SCN-016 | Aktive lisans için Türkçe iade politikası cevabı | mobil | yok | değişmedi | passed |
| SCN-017 | Yazılım uyumluluğuna göre modül ekleme | web | `add_to_quote`, `add_to_quote` | 1 → 3 | passed |
| SCN-018 | Acil kurulum bölge kuralını kaynakla açıklama | mobil | yok | değişmedi | passed |
| SCN-019 | Plus ürün hacim indirimi için miktar ekleme | web | `add_to_quote` | 1 → 2 | passed |
| SCN-020 | Fiyat üst limiti altında Plus yerine temel ürün seçme | mobil | `add_to_quote` | 1 → 2 | passed |
| SCN-021 | Yedek modda Türkçe kaynaklı teslimat cevabı | web | yok | değişmedi | passed |
| SCN-022 | Araç şarj stok dışıysa USB-C alternatif ekleme | mobil | `add_to_quote` | 1 → 2 | passed |

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
