# Subsequent Vercel website phase

The current deliverable is the data release. No website is built or deployed in v1.

## Data contract

Consume a pinned validated release at build time. Use record IDs and provenance for source-page links. Display source claims neutrally; distinguish reported adjustments from verified facts. Preserve explicit zero-record provinces and geographically scoped groups. Never use masked IDs as entity keys. Data corrections require a new version and visible change notes.

## Intended improvements

- Accessible Thai-first search and filters with clear empty states and keyboard navigation.
- Province/district/agency navigation that does not combine unrelated same-name locations.
- Source links for each record, including both locations for duplicate source rows.
- Clearly distinguished source-row and distinct-record totals; no inferred misconduct rates.
- Download center, developer schema/examples, methodology, version and correction history.
- Browser-side search with no query collection by default, small static indexes and performance checks on mobile.

## Security defaults

Start with static pages and local browser filtering, without uploads, accounts, admin panels, database writes or public proxy/fetch endpoints. Treat every source field as text. Enforce a restrictive Content Security Policy, anti-framing policy, no MIME sniffing, conservative referrer/permissions policies and safe external links. Serve PDFs as downloads or through a deliberately isolated viewer.

Protect preview deployments using the Vercel project's available protection controls. Keep production public. Pin trusted deployment inputs, separate preview and production credentials, limit who can deploy, verify actual headers in production, and keep rollback instructions. Confirm current Vercel protection and abuse/cost controls during implementation; do not claim they are enabled from this document alone.

Any backend, user input persistence, external URL fetcher or server-side search requires a specific threat model, authorization/input-validation design, resource/rate limits and adversarial tests before deployment. Static delivery does not eliminate denial-of-service, account compromise or supply-chain risk.
