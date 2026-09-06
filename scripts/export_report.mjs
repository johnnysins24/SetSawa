// Optional maintainer tool: uses the installed Data Analytics portable renderer.
// Fixes its viewport-width top bar on browsers with non-overlay scrollbars.
import { resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { writeFile } from 'node:fs/promises';
const args = process.argv.slice(2);
const index = args.indexOf('--renderer-root');
if (index < 0 || !args[index + 1]) throw new Error('Provide --renderer-root /path/to/data-analytics-plugin');
const renderer = resolve(args[index + 1]);
const root = fileURLToPath(new URL('../', import.meta.url));
const { buildPortableArtifact } = await import(pathToFileURL(resolve(renderer, 'skills/build-report/scripts/build_portable_artifact.mjs')));
const { deliverPortableArtifact } = await import(pathToFileURL(resolve(renderer, 'skills/build-report/scripts/deliver_portable_artifact.mjs')));
const style = '<style id="setsawa-scrollbar-layout-fix">#data-analytics-portable-reader .analytics-top-bar{width:100%;margin-left:0;margin-right:0}</style>';
const result = await deliverPortableArtifact({
  inputPath: resolve(root, 'reports/artifact.json'),
  outputPath: resolve(root, 'reports/quality-report.html'),
  screenshotPath: resolve(root, '.cache/report-verification-failure.png'),
}, {build: (input, options) => buildPortableArtifact(input, options).replace('</head>', style + '</head>')});
const {html, ...evidence} = result;
await writeFile(resolve(root, 'reports/html-verification.json'), JSON.stringify({...evidence, rendererVersion:'0.2.10', layoutFix:'Constrain sticky top bar to its parent width; no overflow hiding or relaxed verifier'}, null, 2) + '\n');
console.log(JSON.stringify(evidence));
