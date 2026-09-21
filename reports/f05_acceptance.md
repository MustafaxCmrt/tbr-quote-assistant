# F05 — Audited SSE and recovery

- Full PostgreSQL/unit/golden suite: **142 passed**, exit0, [f05_full_tests.txt](f05_full_tests.txt). After restricting the envelope tool-name enum, the six stream tests passed again: [f05_final_stream_tests.txt](f05_final_stream_tests.txt).
- Shared TypeScript parser/reducer: **12 passed**, exit0, [f05_parser_tests.txt](f05_parser_tests.txt). Every UTF-8 boundary, CRLF, multiple/unfinished frames, context/sequence/schema errors, partial text and replay refetch are asserted.
- TypeScript, client lint, API lint and source/secret checks exit0: f05_typecheck.txt, f05_client_lint.txt, f05_lint_final.txt, f05_delivery.txt.
- Backend-owned JSON Schema exported for quote DTO and discriminated SSE envelope: f05_schema_export_final.txt. First command used an incorrect relative PYTHONPATH; failed output retained.
- Real `curl -N` via API and web proxy: [f05_curl_incremental.txt](f05_curl_incremental.txt), exit0. Each delivered 8 text chunks over 0.084 seconds. These are paced template chunks, not LLM tokens. Tool starts are emitted at actual invocation; successful results only after the atomic transaction commits.

| Requirement | Executed test |
| --- | --- |
| Base/Plus replay with actual wrapper, exact event/log output and key correlation | `test_stream_retry_actual_wrapper_and_log_correlation` (2 cases) |
| Failed guard, no done/success, real failed log, unchanged quote | `test_stream_guard_error_no_success_or_partial_commit` |
| No successful result from rolled-back atomic group | `test_executor_emits_no_success_from_rolled_back_group` |
| Disconnect after commit, same message reconnect, one receipt/effect | `test_disconnect_after_commit_and_reconnect_keeps_single_effect` |
| Rendering error after DB commit, controlled error, committed=true, retry receipt | `test_error_after_commit_reports_truth_and_masks_exception` |

Accepted finite background work continues if the consumer disconnects; disconnect is not a transaction cancellation command. The message history stores the completed response, and retry invokes persisted tools/receipts. Process death before completion leaves a bounded 60-second message lease; a later retry can claim it. Existing restart receipt tests cover durable mutations; every-token durable replay/Last-Event-ID is deliberately unsupported.

Clients never apply quote_delta as arithmetic. Result/replay/done requests a canonical quote refetch; duplicate same-sequence events are ignored, out-of-order/mismatched events rejected. The common reducer is ready; actual web/mobile screens are F06/F07. Native full chat remains not_verified. The prior physical debug stream evidence remains valid for F01 only.
