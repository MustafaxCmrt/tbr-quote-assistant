# F08 dar sohbet kabul ekleri

Mevcut test_chat.py içine beş gerçek PostgreSQL/HTTP kabul örneği eklendi; runtime ve source değiştirilmedi.
`docker compose --profile test run --build --rm test pytest -q tests/test_chat.py`:20passed exit0.
İlk dar koşu3passed/15deselected idi; daha sonra miktarsız komutun netleştirme metni kesinleştirildi ve iki yeni vaka eklendi.
Son20test koşusu güncel assertion'ları içerir. Tam backend regresyonu bu adımda tekrar çalıştırılmadı.

| Gereksinim | Kesin test kanıtı |
|---|---|
| NEG-33 “RedScan Mini Plus ekle” gerçek mutasyon | `test_acceptance_explicit_plus_and_offline_license_through_chat[RedScan Mini Plus ekle.-PRD-BC-130-PLUS-1]`: exactproduct/quantity, kaynak ve gerçek mutation logu |
| NEG-35 “offline senkron lisansı” SW-520 | Aynı parametreli testin Offline senkron lisansı vakası: SW-520, SW-510 önerilmez, gerçek add logu |
| NEG-36 sayısız “Yazıcıyı çıkar” | `test_quantityless_printer_cikar_asks_without_removing_existing_line`: açık miktar sorusu, teklif/version aynı, mutation tool/receipt yok |
| NEG-20 miktar eşik altına düşünce yeniden fiyatlama | `test_partner_discount_is_removed_after_chat_quantity_drops_below_threshold`: partner3→2, net22292.10→15980.00, rule_ids boş, indirim0, version+1 |
| NEG-22 kullanıcı kural/fiyat override ve kesin tavan | `test_user_override_instruction_cannot_bypass_explicit_price_ceiling`: 1TL altında BlueScanAir eklenmez, öneri/mutation/receipt yok, teklif aynı |

Kanıt: f08_chat_acceptance_tests.txt; f08_chat_test_lint.txt. Source incelemede exact değer/negatif yan etki assertion'ları kontrol edildi; test sayısı tek başına başarı ölçütü sayılmadı.

İkinci kabul eki: `test_negative_update_quantity_does_not_change_quote_or_receipts` negatif update reddi ve sıfır yan etkiyi; `test_software_bundle_discount_removed_after_chat_removes_paired_item` kaldırılmış geçmiş satırını ve kalan lisansın indirimden çıkmasını doğrular. Son bütünleşik koşu f08_full_backend.txt:151passed exit0; golden22 ayrı DB.
