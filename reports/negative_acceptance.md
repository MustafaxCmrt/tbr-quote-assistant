# F08 negatif kabul eşlemesi

36 hedef, 36 bağımsız test sayısı demek değildir; parametrik örnekler ve gerçek restart/cihaz gözlemleri birlikte kullanılır.
Aşağıda testlerin doğruladığı davranış belirtilir. Tam son koşu `f08_full_backend.txt`; istemci koşusu
`f07_retry_fix_tests.txt`; restart kanıtı `f03_restart_replay.txt` içindedir. Bu tablo kendi başına bir test koşusu değildir.
NEG-10 opsiyonel provider adapter'ı olmadığı için **uygulanmadı/not_run**; geçmiş sayılmaz.

| Hedef | Somut kanıt / sınır |
|---|---|
| NEG-01 yeni message_id ikinci kasıtlı ekleme | `test_add_retry_new_message_and_real_wrapper_logs`: aynı wrapper retry'da adet3, yeni mesajda adet5 |
| NEG-02 aynı key farklı payload, eski update replay | `test_changed_payload_conflict_and_stale_update_replay`, `test_retry_persists_plan_stale_update_and_actual_receipt_logs`: conflict ve yeni adet2 korunur |
| NEG-03 aynı key eşzamanlı | `test_same_and_distinct_key_concurrency`: replay bayrakları False/True, tek etki |
| NEG-04 farklı key aynı ürün eşzamanlı | Aynı concurrency testi: tek aktif satır, adet4/version4 |
| NEG-05 commit sonrası bağlantı kopması | `test_disconnect_after_commit_and_reconnect_keeps_single_effect`: receipt ve quote korunur |
| NEG-06 PostgreSQL restart sonrası retry | `f03_restart_prepare.txt`, `f03_postgres_restart.txt`, `f03_restart_replay.txt`: gerçek restart + gerçek wrapper, 1 receipt/2 attempt |
| NEG-07 ikinci mutasyon geçersiz | `test_group_rollback_and_two_distinct_action_keys`, `test_executor_emits_no_success_from_rolled_back_group`: ilk etki/receipt/success result rollback |
| NEG-08 anahtarsız açık add | Golden mutasyon örnekleri: fallback/provider_calls0, gerçek DB etkisi; `test_context_conflict_and_read_only_retrieved_instructions` dış HTTP çağrısını ayrıca engeller |
| NEG-09 belirsiz “onu ekle” sınıfı | `test_ambiguous_negated_or_invalid_input_never_mutates`, `test_ambiguous_current_items_do_not_pick_arbitrarily`: netleştirme/quote aynı/receipt0 |
| NEG-10 provider timeout→fallback | **not_run / uygulanmadı:** harici provider adapter'ı yok; keyless fallback başarısı bu hedef yerine sayılmaz |
| NEG-11 fiyat tavanını executor'dan aşma / admin yarışı | `test_mutation_guards_cannot_be_bypassed`, `test_admin_update_lock_cannot_race_price_or_stock_guard`, `test_active_minimum_and_existing_snapshot_guard` |
| NEG-12 para biçimi ve tam sınır | `test_money_formats`, `test_price_is_not_quantity`, `test_mutation_accepts_exact_price_and_stock_boundaries`, `test_hard_price_features_and_base_variant` |
| NEG-13 QR şartında 1D alternatif | `test_replace_alternative_constraints`: REQUIRED_FEATURE_MISSING ve aynı teklif |
| NEG-14 uygun müşteri ama açık bekleme yok | `test_backorder_requires_eligible_customer_and_explicit_consent[False]`: OUT_OF_STOCK, boş teklif |
| NEG-15 bekleme var ama müşteri uygun değil | `test_mutation_guards_cannot_be_bypassed` explicit_backorder_consent=True/PRD-BC-130 örneği: ret ve aynı teklif |
| NEG-16 iki koşul doğru | `test_backorder_requires_eligible_customer_and_explicit_consent[True]`: backorder/adet1 |
| NEG-17 pozitif stok üstü toplam adet / admin yarışı | `test_mutation_guards_cannot_be_bypassed`, `test_positive_update_insufficient_stock_preserves_receipts_and_version`, admin lock testi |
| NEG-18 quantity0 ve negatif; pasif/stoksuz kalemi kaldırma | `test_replace_history_merge_and_removal_ignores_source_guards`: removed/net0; `test_negative_update_quantity_does_not_change_quote_or_receipts`: chat'te kontrollü netleştirme ve sıfır etki; tool schema negatifleri ayrıca reddeder |
| NEG-19 replace hedefi aktif | `test_replace_merges_and_rejects_backorder_even_with_consent`: tek hedef satır/adet3/geçmiş |
| NEG-20 update/remove sonrası indirim kalkar | `test_partner_discount_is_removed_after_chat_quantity_drops_below_threshold`: 3→2/rule yok/net15980; `test_software_bundle_discount_removed_after_chat_removes_paired_item`: SW530removed, kalan SW520net14900/rule yok |
| NEG-21 indirim çakışması | `test_plus_is_specific_even_when_partner_rate_is_larger`, `test_specificity_and_accessory_product_threshold`: adayın belgelenmiş most-specific politikası |
| NEG-22 kullanıcı/knowledge talimat enjeksiyonu | `test_user_override_instruction_cannot_bypass_explicit_price_ceiling`: 1TL tavan aşılmaz; `test_context_conflict_and_read_only_retrieved_instructions`: knowledge komutu mutasyon yaptıramaz |
| NEG-23 quote/customer/session | `test_context_conflict_and_read_only_retrieved_instructions`, `test_forged_input_and_invalid_quantity_leave_quote_unchanged`: mismatch/forged context ve değişmeyen teklif; üretim authentication testi değildir |
| NEG-24 canlı CRUD/retrieval | `test_live_catalog_add_update_delete_and_knowledge_dates`, test_admin.py HTTP CRUD örnekleri; `f06_demo_api.txt` gerçek UI kayıtlarının retrieval kanıtı |
| NEG-25 ekleme, yalnız fiyat | `test_ambiguous_negated_or_invalid_input_never_mutates[BlueScan Air ekleme, sadece fiyatını söyle.]`: quote aynı, receipt0 |
| NEG-26 bölünmüş UTF-8/JSON | `utf8_multibyte_split`, `all_byte_boundaries_preserve_frames`, `actual envelope survives every UTF-8 split and reducer completes once`; native transport her byte testi |
| NEG-27 CRLF/çoklu/error | `crlf_across_chunks`, `multiple_events_in_one_chunk`, `unfinished_final_event_is_discarded`, `error preserves partial text and signals committed-state refetch` |
| NEG-28 stale web/native quote | `late poll cannot replace new version or changed quote context`, `mobile canonical quote ignores stale versions and responses from another selection` |
| NEG-29 secret/exception sızıntısı | `test_error_after_commit_reports_truth_and_masks_exception`; native transport maskeleme testi; delivery/history scan. Tanınmayan tüm secret biçimleri için garanti verilmez. |
| NEG-30 iki mutasyon farklı key | `test_group_rollback_and_two_distinct_action_keys`: iki unique receipt; golden SCN-008/017 gerçek iki add ve beklenmeyen mutation reddi |
| NEG-31 yeni ürün/parafraz | `test_new_live_alias_and_rephrase_are_not_golden_lookup`: MorMartı canlı eklenir, adet2/net2468 |
| NEG-32 tekrarlı seed kullanıcı verisini korur | `test_repeated_seed_preserves_edits_and_concurrent_calls`; `f01b_persistence_check.txt` tüm tablolar/edit/receipt; `f03_restart_replay.txt` tekrar seed sonrası aynı receipt/quote |
| NEG-33 açık RedScan Mini Plus | `test_acceptance_explicit_plus_and_offline_license_through_chat` Plus örneği: PRD-BC-130-PLUS/adet1, gerçek add ve kaynak |
| NEG-34 Q2003 başlangıç fiyatlama | `test_quote_snapshot_totals_and_reads_do_not_mutate`: brüt4480/indirim268.80/net4211.20, RUL-PLUS-QTY; katalog değişse snapshot korunur |
| NEG-35 offline senkron lisansı | `test_acceptance_explicit_plus_and_offline_license_through_chat` offline örneği: SW520, Starter önerilmez, gerçek add ve kaynak |
| NEG-36 miktarsız yazıcıyı çıkar | `test_quantityless_printer_cikar_asks_without_removing_existing_line`: hedef miktarı sorar, quote/version aynı, mutation tool/receipt yok |

Test kaynakları: `apps/api/tests/test_mutations.py`, `test_chat.py`, `test_stream.py`, `test_bootstrap.py`,
`test_reads.py`, `test_admin.py`, `unit/`, `golden/`; TS testleri `packages/contracts/tests`,
`apps/mobile/tests`, `apps/web/tests`. F08 bağımsız inceleme bulguları bu listeye ek regresyonlar gerektirebilir.
