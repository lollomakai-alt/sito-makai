## engram

For codebase or architecture questions, when `.engram/graph.json` exists, first run `engram query "<question>"` (or `engram path "<A>" "<B>"` / `engram explain "<concept>"`); these return a scoped subgraph, usually much smaller than `GRAPH_REPORT.md` or raw grep output.
If `.engram/wiki/index.md` exists, navigate it for deep questions.
If `.engram/graph.json` is missing but `graphify-out/graph.json` exists, run `engram migrate-state --dry-run` before relying on legacy state.
Read `.engram/GRAPH_REPORT.md` only for broad architecture review or when `query` / `path` / `explain` do not surface enough context.
Type `/engram` in Copilot Chat to build or update the knowledge graph.

## Makai project architecture and workflow

- `sito-makai` (`lollomakai-alt/sito-makai`) and `makai-agenda` (`lollomakai-alt/agenda-makai`) are separate applications and GitHub repositories. Check the correct repository before editing, committing, pushing, or describing a deployment.
- Both applications use the shared Supabase project `fignmtkbwpbrmllbxoct` for bookings/database, ADMIN authentication, and Edge Functions. Keep booking validation, capacity, privacy, and status rules consistent across both codebases.
- The Site backend writes online bookings directly to Supabase. After a new confirmed booking commits, it calls `web-push-admin` with `new-online-booking`. Keep privileged credentials server-side; push errors must not undo a saved booking. A replayed request must not send again.
- Agenda is a separate React/Vite PWA and can be installed on iPhone. Operational in-app notifications and system Web Push are distinct mechanisms. Apple Web Push subscriptions are managed through Supabase; actual delivery also depends on Edge Function and VAPID configuration.
- Operational production-domain mapping: `sito-makai` → `www.makaipigneto.it`; `makai-agenda` → `agenda-makai.vercel.app`. Treat this as the declared mapping and verify current domains in each Vercel project before operational changes; source files do not prove live domain assignment.
- Ordinary Vercel release is a commit and push to the matching GitHub repository, which is expected to trigger its linked Vercel project. Do not use Vercel CLI for manual deploys unless explicitly requested. Never mix the two repositories in one release.
- Before changes, inspect the current code and graph artifacts, but prefer verified current code over stale graph data. Preserve pre-existing worktree changes. Do not commit, push, deploy, or modify live Supabase unless explicitly requested. Verify any proposed database/Edge operation first.
- Never record passwords, tokens, API keys, or other secrets in documentation, graph artifacts, or tests.
- Treat graph JSON as generated data, not the source of truth. The local graph artifacts are currently in nonstandard directory names; do not rename, delete, or hand-edit them. If the Engram CLI is unavailable, update source documentation/instructions and later regenerate in this repository with `/engram . --update` when the graph setup is available.
