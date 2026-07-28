# ADR 0003: Defer centralizing transaction boundaries

## Status
Accepted

## Context
`docs/backend/database/transaction-boundaries.md` (written during the final documentation pass) found that every domain in this codebase commits directly inside `services/*_service.py` methods, not at a control/application-service boundary — the target architecture's stated intent ("application services should control business transaction boundaries... do not commit independently inside every repository method") is not what the codebase actually does anywhere, including in the 13 domains refactored in this engagement. A concrete inconsistency window exists: `UrlReportService.update_report` does two sequential `db.commit()` calls (the report update, then the audit-row insert) with no atomicity between them.

## Decision
Leave the per-service commit pattern as-is across all 13 domains touched in this refactor. Document the gap and the specific inconsistency window precisely (see `transaction-boundaries.md`) rather than fixing it as a side effect of unrelated domain work.

## Alternatives rejected
- **Fix it opportunistically in each domain as it's touched.** Rejected: every domain's actual charter in this pass was a specific authorization/error-handling/security fix; folding a transaction-boundary refactor into e.g. the Domain 2 IDOR fix would conflate two unrelated changes in one diff, making both harder to review and revert independently — directly against the mandate's migration rule ("avoid combining... behavior changes... in one change unless unavoidable").
- **Do a dedicated transaction-boundary pass across all services now, as part of Phase 4/6.** Rejected: this touches commit logic in every service file across every domain — a wide-blast-radius change with no scoped acceptance test proving it doesn't introduce a new bug (e.g. a service method currently relied upon elsewhere to commit independently). Needs its own dedicated pass with forced-failure tests (inject a failure between two commits, prove the fix actually closes the window), not a rushed pass at the end of a 13-domain engagement.

## Consequences
- The inconsistency window (e.g. report updates without a matching audit row on partial failure) remains open. Low observed-impact so far (no incident evidence), but real.
- Whoever picks up `transaction-boundaries.md`'s recommendation gets a precise starting point (the exact pattern, one concrete example, and the reasoning for why it wasn't rolled into this engagement) rather than having to rediscover the gap from scratch.
