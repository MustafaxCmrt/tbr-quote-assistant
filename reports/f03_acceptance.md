# F03 — Transactional mutations and receipts

Verified on real PostgreSQL 16.15. `docker compose --profile test run --build --rm test` exited 0: **94 passed**, including F01/F02 regressions. Full output: [f03_review_complete_suite.txt](f03_review_complete_suite.txt). Earlier failures remain as diagnostic evidence; they are not passing gates.

| Requirement | Executed evidence / exact test |
| --- | --- |
| Actual add, retry wrapper, new message | `test_add_retry_new_message_and_real_wrapper_logs` |
| Same and different key races | `test_same_and_distinct_key_concurrency` |
| Payload conflict and stale update | `test_changed_payload_conflict_and_stale_update_replay` |
| Atomic group and distinct action keys | `test_group_rollback_and_two_distinct_action_keys` |
| Trusted price/features/stock, eligible customer AND consent | `test_mutation_guards_cannot_be_bypassed`, `test_backorder_requires_eligible_customer_and_explicit_consent` |
| Concurrent admin changes | `test_admin_update_lock_cannot_race_price_or_stock_guard` (observes PostgreSQL blocking, then current-value rejection) |
| Replace history, merge, zero quantity | `test_replace_history_merge_and_removal_ignores_source_guards`, `test_replace_merges_and_rejects_backorder_even_with_consent` |
| Forged context / invalid input | `test_forged_input_and_invalid_quantity_leave_quote_unchanged` |
| Positive update guards | `test_positive_update_rechecks_guards`, `test_positive_update_insufficient_stock_preserves_receipts_and_version` |
| Inclusive ceiling / stock and snapshot preservation | `test_mutation_accepts_exact_price_and_stock_boundaries`, `test_add_preserves_existing_snapshot_after_catalog_price_change` |
| Explicit replacement quantity | `test_explicit_replacement_quantity_overrides_source_quantity` (new and merged target) |
| Category vs same-product thresholds; missing rule | `test_partner_aggregates_category_but_accessories_require_same_product`, `test_missing_required_rate_fails_closed` |
| Domain examples and actual runtime role | `test_domain_examples_with_exact_net_totals`, `test_runtime_db_role_executes_atomic_mutation` |
| Server restart followed by seed and real wrapper replay | [prepare](f03_restart_prepare.txt), [restart](f03_postgres_restart.txt), [replay](f03_restart_replay.txt): all exit 0 |
| All six names / fields preserved as real JSON Schema | [schema export](f03_tool_schemas.txt): exit 0 |
| Lint / immutable source and delivery checks | [lint](f03_final_lint.txt), [delivery](f03_final_delivery.txt): exit 0 |

The executor owns one short transaction. Quote locking precedes receipt lookup to serialize concurrent same-quote writes. Customer/product/rule rows are also locked for consistent guards and pricing. Every replay invokes the real wrapper; committed receipts return replayed=true, mutation_applied=false without modifying the quote. Stock is not reserved. The persisted plan and constraints are server-owned; no public endpoint accepts mutation context.

A separate read-only AI reviewer found no source-proven material defect in the bounded mutation/pricing review, but identified six test gaps. The added positive-update, boundary, snapshot, aggregation, missing-rule and explicit-replacement tests above close those gaps; the final 94-test run executed them. This is AI static review plus actual tests, not a human audit or an empirical mutation score. The source-to-test scanner previously lacked its tree-sitter prerequisite; no scanner success is claimed.

Domain scenarios are not full chat golden acceptance. Chat routing, the 22-scenario runner and real SSE are F04/F05 work; native shared quote remains not_verified. Test databases and volumes were retained; no destructive reset was run.
