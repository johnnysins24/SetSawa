# Portable report build

`uv run --locked python scripts/generate_report.py` reproduces `reports/artifact.json` from the validated tables, and regenerates the inspection notebook. It does not modify the source data.

The committed `reports/quality-report.html` is a portable, read-only export of that artifact, produced with the Data Analytics 0.2.10 report renderer. It includes the chart, exact province table, methods, limitations and source metadata. It is a snapshot, not a live connection. Download and open the HTML locally; GitHub does not render it in the repository file browser.

For maintainers with the Data Analytics plugin installed, run from that plugin's root:

```sh
npm run report:deliver -- --input /absolute/path/to/SetSawa/reports/artifact.json --output /absolute/path/to/SetSawa/reports/quality-report.html
```

The upstream 0.2.10 exporter exposes a sticky-header overflow on Windows browsers with visible scrollbars. For this release, run `node scripts/export_report.mjs --renderer-root /path/to/data-analytics-plugin` from SetSawa instead. This wraps the same exported renderer and delivery verifier with one scoped CSS fix: the sticky header uses its parent width rather than viewport width. It does not hide overflow or relax verification. Review the actual HTML in light/dark modes and at desktop/mobile widths, including source details and the 77-row table. Record the renderer version, artifact hash, output hash and visual scope in the release evidence.

The presentation renderer is an optional authoring dependency, not needed to read the HTML or rebuild PDF extraction, clean data, schemas, notebook or Excel. If it is unavailable when data changes, retain an explicitly historical report rather than falsely relabeling it for new data; block packaging until an updated report is reviewed. The generated report input remains usable by another compatible renderer.
