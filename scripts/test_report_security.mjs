// Optional renderer/browser integration test. Never executes scripts from source data.
// Arguments: --renderer-root DIR --playwright-root DIR --browser EXE
import fs from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
const args = process.argv.slice(2);
const get = key => {const i=args.indexOf(key);if(i<0||!args[i+1])throw new Error(`Missing ${key}`);return resolve(args[i+1]);};
const root = fileURLToPath(new URL('../',import.meta.url));
const {buildPortableArtifact} = await import(pathToFileURL(resolve(get('--renderer-root'),'skills/build-report/scripts/build_portable_artifact.mjs')));
const {chromium} = await import(pathToFileURL(resolve(get('--playwright-root'),'index.mjs')));
const artifact = JSON.parse(await fs.readFile(resolve(root,'reports/artifact.json'),'utf8'));
const attack = '</script><script>globalThis.__SETS_TEST_XSS__=1</script><img src="https://example.invalid/x" onerror="globalThis.__SETS_TEST_XSS__=1">';
artifact.manifest.blocks[1].body += '\n\n' + attack;
artifact.snapshot.datasets.provinces[0].province_name_th = attack;
artifact.snapshot.datasets.top_provinces[0].province_name_th = attack;
const testPath=resolve(root,'.cache/report-xss.html');
await fs.mkdir(resolve(root,'.cache'),{recursive:true});
await fs.writeFile(testPath,buildPortableArtifact(artifact));
const browser=await chromium.launch({executablePath:get('--browser'),headless:true});
const page=await browser.newPage();
const external=[];
await page.route(/^https?:\/\//,route=>{external.push(route.request().url());return route.abort();});
await page.goto(pathToFileURL(testPath).href);
await page.waitForFunction(()=>!!document.querySelector('#data-analytics-portable-reader h1'));
const result=await page.evaluate(()=>({executed:globalThis.__SETS_TEST_XSS__===1,unsafeNodes:document.querySelectorAll('img[onerror],script[src^="http"],iframe[src^="http"]').length}));
await browser.close();
if(result.executed||result.unsafeNodes||external.length)throw new Error('Report injection test failed');
await fs.writeFile(resolve(root,'reports/html-security-test.json'),JSON.stringify({status:'passed',contexts:['markdown body','chart label','table cell'],payload:'script-closing tag, script element and image onerror handler',scriptExecuted:false,unsafeDomNodes:0,externalRequests:0},null,2)+'\n');
console.log('Report HTML injection test passed in Chromium');
