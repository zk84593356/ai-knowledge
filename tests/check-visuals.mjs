/** Local rendering checks for example topic images. Outputs only tests/.tmp/visuals.
 * Renders every image embedded in article.md plus every generated/approved manifest asset
 * (including editable SVG sources) at 720px and 390px; no network, no approval changes.
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const topics = ['concept-sso', 'feature-oidc-demo'];
const resolveModule = createRequire(path.join(
  process.env.AI_KNOWLEDGE_NODE_MODULES || path.join(root, '.test-tools/node_modules'), '__resolver__.cjs'));
let chromium;
try { ({ chromium } = resolveModule('playwright')); }
catch { console.error('SKIP: Playwright unavailable; see tests/README.md'); process.exit(2); }

function articleImages(folder) {
  const file = path.join(folder, 'article.md');
  if (!fs.existsSync(file)) return [];
  const text = fs.readFileSync(file, 'utf8').replace(/^(`{3,}|~{3,})[\s\S]*?^\1\s*$/gm, '');
  return [...text.matchAll(/!\[([^\]\n]+)\]\((\.\/assets\/[^)\s]+)\)/g)].map(m => ({ id: 'article:' + path.basename(m[2]), path: m[2] }));
}
function manifestAssets(folder) {
  const file = path.join(folder, 'assets/manifest.json');
  if (!fs.existsSync(file)) return [];
  return JSON.parse(fs.readFileSync(file, 'utf8')).assets
    .filter(a => a.status === 'generated' || a.status === 'approved')
    .map(a => ({ id: a.id, path: a.path }));
}
const items = [];
for (const topic of topics) {
  const folder = path.join(root, 'examples', topic);
  const seen = new Set();
  for (const item of [...articleImages(folder), ...manifestAssets(folder)]) {
    const file = path.resolve(folder, item.path);
    if (!file.startsWith(path.join(folder, 'assets') + path.sep)) throw Error(topic + ': escaping asset ' + item.path);
    if (!fs.existsSync(file)) throw Error(topic + ': missing image ' + item.path);
    if (seen.has(file)) continue;
    seen.add(file);
    items.push({ topic, id: item.id.replace(/[^\w.-]+/g, '-'), file });
  }
}
if (!items.length) { console.error('FAIL: no example images found; cannot report a pass.'); process.exit(1); }

let browser;
try { browser = await chromium.launch({headless:true, ...(process.platform === 'win32' ? {channel:'msedge'} : {})}); }
catch { console.error('SKIP: local browser unavailable'); process.exit(2); }
const output = path.join(root, 'tests/.tmp/visuals');
fs.mkdirSync(output, {recursive:true});
const mime = {'.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg'};
const results = [];
try {
  const page = await browser.newPage();
  await page.route('**/*', route => route.abort());
  for (const {topic, id, file} of items) {
    const ext = path.extname(file).toLowerCase();
    const bytes = fs.readFileSync(file);
    const markup = ext === '.svg' ? bytes.toString('utf8')
      : '<img alt="local asset" src="data:' + mime[ext] + ';base64,' + bytes.toString('base64') + '">';
    for (const width of [720, 390]) {
      await page.setViewportSize({width, height:1000});
      await page.setContent('<!doctype html><meta charset="utf-8"><style>body{margin:0}svg,img{display:block;width:100%;height:auto}</style><main>' + markup + '</main>');
      await page.evaluate(async () => { await document.fonts.ready; for (const img of document.images) await img.decode(); });
      const failures = await page.evaluate(() => {
        const art = document.querySelector('svg,img'), box = art.getBoundingClientRect(), bad = [];
        if (!box.width || !box.height) bad.push('zero image size');
        for (const el of document.querySelectorAll('text')) {
          const b = el.getBoundingClientRect();
          if (b.left < box.left-1 || b.right > box.right+1 || b.top < box.top-1 || b.bottom > box.bottom+1) bad.push(el.textContent);
        }
        return bad;
      });
      if (failures.length) throw Error(topic + '/' + id + ' text outside canvas: ' + failures.join(','));
      const name = topic + '-' + id + '-' + width + '.png';
      await page.locator('main').screenshot({path:path.join(output, name)});
      results.push({topic, id, file:path.relative(root, file).split(path.sep).join('/'), width, decoded:true, textWithinCanvas:true, screenshot:name});
    }
  }
  fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({
    browser: await browser.version(), results, limitations: 'No automatic semantic, identity, rights or aesthetic approval'
  }, null, 2) + '\n');
  console.log('PASS: ' + results.length + ' local renders at 720/390px; image decode and text bounds checked.');
} finally { await browser.close(); }
