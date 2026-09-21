# F04 — Grounded deterministic chat

Final suite: **136 passed**, real PostgreSQL 16.15; [f04_review_tests.txt](f04_review_tests.txt), exit 0. This includes all **22 company golden scenarios through POST /api/chat**, unchanged source JSON, independent fresh DB per scenario. Repeated-message scenarios use the same session/message and invoke actual wrappers twice.

| Requirement | Executed evidence |
| --- | --- |
| Ordered expected calls, exact mutation count/order, flat-filter adapter | `tests/golden/test_chat_golden.py::test_golden_message_through_http[SCN-001..022]` |
| Final product/quantity/history, other quotes unchanged, stock unreserved | Same golden runner; explicit assertion registry, not runtime fixture matching |
| Source IDs are actual attempt log evidence; forbidden recommendations | Same golden runner |
| Partner/software/Plus exact totals | SCN-011 / 017 / 019: 22292.10 / 22816.00 / 35456.80 |
| Negation, ambiguity, signed/fractional quantities | `test_ambiguous_negated_or_invalid_input_never_mutates`, `test_signed_or_fractional_quantities_rejected` |
| Context mismatch, changed message conflict, knowledge injection, no outbound provider request | `test_context_conflict_and_read_only_retrieved_instructions` |
| Live new alias and non-golden phrasing | `test_new_live_alias_and_rephrase_are_not_golden_lookup` |
| Persisted plan and stale retry | `test_retry_persists_plan_stale_update_and_actual_receipt_logs` |
| Ambiguous current reference | `test_ambiguous_current_items_do_not_pick_arbitrarily` |
| Independent review regression cases | `test_explicit_reference_cannot_remove_other_product`, `test_conjoined_features_preserved_and_read_ceiling_enforced`, `test_explicit_replacement_target_is_not_substitute_default` |
| Real running HTTP process | [f04_http_smoke.txt](f04_http_smoke.txt), exit 0; source-bearing fallback, unchanged quote |
| Compose / lint / delivery | f04_compose.txt, f04_lint.txt, f04_delivery.txt: exit 0 |

Initial golden run: 20 passed / 2 failed (generic alternative search lost its category); fixed by explicit category browse when no target descriptor exists. Negative tests caught signed/fractional quantity truncation. The independent read-only AI reviewer found four unsafe planning cases: wrong explicit reference, conjunction feature loss, read-only ceiling omission, explicit replacement target ignored. Production fixes and named regressions above passed in the final suite. All failed outputs retained; no source fixture or acceptance assertion was weakened. No human review or empirical mutation score is claimed.

Runtime contains no scenario IDs/golden messages and ships only the six business seed JSON files. Golden JSON is copied into the Docker **test stage only**. Planner previews live DB reads and persists a server-owned plan; executor invokes the real tools and rechecks guards. Per-requirement feature tags are merged with common trusted constraints, preventing a terminal's 4G requirement being incorrectly applied to its software license.

Provider calls are disabled in this implementation, including if a key exists. Supported explicit mutations work without a key; unsupported/ambiguous requests ask for clarification. This is a bounded Turkish deterministic parser, not general language understanding or LLM tool calling. Actual SSE/error audit/history endpoints and client integration remain F05–F07. Native chat/shared quote not_verified.
