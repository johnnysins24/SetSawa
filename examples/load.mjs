// Run from any directory: node examples/load.mjs. No npm dependencies.
import { readFile } from 'node:fs/promises';
const records = JSON.parse(await readFile(new URL('../data/processed/clean/records.json', import.meta.url), 'utf8'));
const provenance = JSON.parse(await readFile(new URL('../data/processed/clean/provenance.json', import.meta.url), 'utf8'));
const byRecord = new Map();
for (const source of provenance) {
  if (!byRecord.has(source.record_id)) byRecord.set(source.record_id, []);
  byRecord.get(source.record_id).push(source);
}
if (records.length !== 3963 || provenance.length !== 3966) throw new Error('Unexpected snapshot');
console.log(`Loaded ${records.length} records and ${provenance.length} source locations`);
console.log(byRecord.get(records[0].record_id).map(source => ({ document: source.document_id, page: source.page_number })));
