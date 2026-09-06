# Security policy

## Supported release

Version 1.x is the supported data-pipeline line. Report vulnerabilities privately through GitHub's **Security → Report a vulnerability** for this repository. Do not place credentials, full personal identifiers, or working exploit details in public issues. Source corrections can use public issues with a PDF/page reference.

## Threat boundaries

Threats considered: malicious PDFs, memory/CPU exhaustion, path traversal, altered source or generated data, spreadsheet formula injection, HTML/script injection, compromised dependencies, malicious pull requests and workflow credential theft. The future website additionally needs availability, browser and deployment defenses.

The parser runs one file per process, with a minimal environment, Python networking/process audit restrictions, input/page/output limits, wall-time enforcement, POSIX resource limits or Windows Job Object memory limits. PDF action/attachment checks reject unexpected content. This does **not** make Python a native-exploit sandbox. Process genuinely hostile new files in a disposable OS/container with no credentials, restricted network and no sensitive mounted directories. Current public CI uses ephemeral hosted runners without publication credentials during parsing.

## Repository controls

- CI tokens default to `contents: read`. Release permission exists only in the separately triggered trusted release job.
- Pin actions to reviewed full commit SHAs. Do not use privileged PR triggers to run contributor code.
- Require validation before merging; block force pushes and branch deletion. Apply equivalent immutable-tag protection to releases.
- Lock dependencies with uv; use pip-audit for known vulnerabilities and Dependabot for dependency updates.
- The release scanner rejects common secret patterns, credential-bearing URLs, key files, symlinks and environment files. It is not proof that every possible secret or malware pattern is absent.
- Checksums detect byte changes against a trusted manifest; they are not an independent signature or proof of source authenticity.

## Output safety

JSONL preserves original strings. CSV export fails on formula-like text instead of silently changing canonical values. XLSX writes all text through a literal-string API and contains no formulas or automatic external hyperlinks. The HTML report uses the validated portable renderer; injected source text is tested as inert text. Never evaluate source fields or concatenate them into shell, SQL or HTML code.

## Response and rollback

For a security incident, stop publication, revoke exposed credentials, preserve relevant logs without copying secrets into public reports, identify affected commits/assets, publish a corrected version and an advisory, and restore the last validated deployment when the website exists. Disable compromised workflows until fixed. Previously downloaded or forked public data cannot be recalled; document corrections and affected versions.

No service can be promised attack-proof. Static delivery reduces application attack surface but does not eliminate account compromise, malicious dependencies, denial of service or hosting costs. Website security must be verified against the actual implementation before deployment.
