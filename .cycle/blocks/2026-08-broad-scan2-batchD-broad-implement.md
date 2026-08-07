---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch D — editor write-safety, scripts/app.py):
- BS2-26 | deck save was a blind whole-document overwrite — no staleness check, so an open tab silently reverted a CLI `swap --apply` and poisoned recommendations.csv with a decision against a vanished deck state
- BS2-27 | add()'s INV-02 rollback restored via bare copy2 over card-library.csv — non-atomic exactly on the failure branch (disk-full/permissions) where a partial write is likeliest
- BS2-28 | editor metadata keys were unvalidated: a key META_RE can't parse ("tier2", "uncastable ok") saved fine, toasted success, then silently demoted to a comment deck.py never reads
- (minor) | _render_template's local `html` shadowed the html MODULE imported for escaping — an AttributeError trap in the one function whose job is emitting HTML
- (RETRACTED) | the collection editor's dirty-key join('') collision — a NON-FINDING: the file already delimits with an invisible \x01 control character, which both the scan's reader and a later grep rendered as an empty string. The same invisible-character trap, one level up. No change made.

Files modified: scripts/app.py, templates/deck.html, tests/test_app_editor.py (NEW)

CHANGES:
BS2-26 | app.py, templates/deck.html | `_doc_token` = 16-hex content hash (content, not mtime — the F-04 lesson: a revert restores old-mtime bytes). The token rides in the page payload, the save POST echoes it, and a mismatch 409s with "the deck file CHANGED since this page loaded it … reload, re-apply, save again" — the same contract the CSV save() has had all along. A successful save returns the fresh token. Token absent (a cached pre-token page) keeps the old contract, so the gate is opt-in by presence and every freshly-served page carries one.
BS2-27 | app.py | the rollback stages the .bak into a mkstemp sibling and os.replace()s it — revert()'s own idiom, whose comment states the reason ("an interruption mid-restore can't leave a truncated CSV"); this was the one restore path that didn't.
BS2-28 | app.py | new `_validate_meta`, wired into deck_save AND deck_create before any write: a key outside META_RE's grammar (letters/underscores/hyphens, letter-first) is a 400 naming the field and suggesting a fixed spelling; a nameless field with a value (which _serialize_doc would silently drop) is a 400 too.
(minor) | app.py | _render_template's local renamed `html` → `src`.

TEST RESULTS: 1018 passed (1012 + 6 new in tests/test_app_editor.py — importorskip'd on Flask, matching the editor's optional-dependency split), 0 failed. check_all green, zero soft warnings. End-to-end walk via Flask's test client (the programmatic half of Scenario 4): fresh-token save 200 + new token; concurrent-change save 409 with the CLI's change surviving; invalid header key 400 with the file untouched. Scenario 4/8's browser halves remain the operator's walk (the failure-toast path is unchanged — a 409 renders through the same "Save failed:" toast that test_templates pins as a live region).
NOT APPLICABLE: Scenarios 1-3, 5-7 (no ingest/analysis/dashboard files touched).

REGRESSION RISKS:
- deck.html and app.py ship together, so the token handshake has no version-skew window; a hard-cached page (no token) still saves under the old contract.
- A user who WANTS to clobber a concurrent change now needs one reload first — accepted cost, message says exactly what to do.
- _validate_meta rejects saves that previously "succeeded" by silently disabling the field — stricter on purpose; the error names the fix.
- No other callers: _render_template/_doc_token/_validate_meta are module-private; deck_create passes meta through the same validation as deck_save.

INVARIANTS AT RISK: None — INV-02's rollback is strictly safer, INV-04's write gate unchanged, and the staleness 409 happens before any write.

NET SCORE: 3 − 0 = +3
(BS2-26 fires on the documented tune workflow — editor open while /apply-changes runs swap --apply — which happened this cycle by construction of the workflows; BS2-27/28 are latent-but-adjacent hardening on the same endpoints. The retraction is honest bookkeeping, not a fix.)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: commit/push is the deploy (the editor is a local tool; `make app` picks the change up on next launch).

FOLLOW-ON ITEMS:
- Batches E–H unchanged (Batch E — interface access — is next).
- BS2-07 header-consumer sweep, still standing.
- The scan's B-5 documented the metadata demotion; its sibling observation (the flex panel's owned badge, B-1) was fixed in the follow-on batch — templates/deck.html now has both fixes; Scenario 4's browser walk would confirm the toasts visually.

DOCUMENTATION UPDATES NEEDED:
- docs/cycle-config.md [C-11]/Scenario 4: the deck editor now 409s on a concurrent file change — one line in the expected outcomes.
- C-07 test inventory: tests/ is now 27 files (test_check_all.py, test_app_editor.py added this session).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
