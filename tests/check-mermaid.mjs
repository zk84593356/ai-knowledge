/** Optional local-only Mermaid parse/render smoke test; no external diagram uploads. */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const localRequire = createRequire(path.join(root, '.test-tools', 'package.json'));
const externalRequire = process.env.AI_KNOWLEDGE_NODE_MODULES
  ? createRequire(path.join(path.resolve(process.env.AI_KNOWLEDGE_NODE_MODULES), '__resolver__.cjs'))
  : localRequire;
let chromium, mermaidPath;
try {
  ({ chromium } = externalRequire('playwright'));
  mermaidPath = localRequire.resolve('mermaid/dist/mermaid.js');
} catch {
  console.error('SKIP: install local Mermaid and Playwright as described in tests/README.md');
  process.exit(2);
}
const files = [];
function collect(dir) {
  if (!fs.existsSync(dir)) return;
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, item.name);
    if (item.isDirectory() && item.name !== 'templates') collect(full);
    else if (item.isFile() && item.name.endsWith('.md')) files.push(full);
  }
}
for (const dir of ['docs', 'examples', 'skills']) collect(path.join(root, dir));
if (fs.existsSync(path.join(root, 'README.md'))) files.push(path.join(root, 'README.md'));
const diagrams = files.sort().flatMap(file => {
  const text = fs.readFileSync(file, 'utf8');
  return [...text.matchAll(/^```mermaid\s*\r?\n([\s\S]*?)^```\s*$/gm)]
    .map((m, index) => ({ file: path.relative(root, file).split(path.sep).join('/'), index, code: m[1] }));
});
if (!diagrams.length) throw new Error('No Mermaid blocks found; cannot report a pass.');
let browser;
try {
  browser = await chromium.launch({ headless: true,
    ...(process.platform === 'win32' ? { channel: 'msedge' } : {}) });
} catch (error) {
  console.error(`SKIP: no usable local browser (${error.message.split('\n')[0]})`);
  process.exit(2);
}
const output = path.join(root, 'tests', '.tmp', 'mermaid');
fs.mkdirSync(output, { recursive: true });
const results = [];
try {
  const page = await browser.newPage({ viewport: { width: 1500, height: 1200 } });
  await page.route('**/*', route => route.abort());
  await page.setContent('<!doctype html><meta charset="utf-8"><style>body{background:white;padding:20px}svg{max-width:none!important}</style><main id="diagram"></main>');
  await page.addScriptTag({ path: mermaidPath });
  await page.evaluate(() => mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'default' }));
  const rejectsInvalid = await page.evaluate(async () => {
    try { await mermaid.parse('flowchart TD\nA[unclosed'); return false; }
    catch { return true; }
  });
  if (!rejectsInvalid) throw new Error('Parser negative control did not fail');
  for (const [number, diagram] of diagrams.entries()) {
    const svg = await page.evaluate(async ({ code, id }) => {
      await mermaid.parse(code);
      const rendered = await mermaid.render(id, code);
      document.getElementById('diagram').innerHTML = rendered.svg;
      return rendered.svg;
    }, { code: diagram.code, id: `diagram${number}` });
    if (!svg.includes('<svg')) throw new Error('Renderer returned no SVG');
    const stem = `${String(number + 1).padStart(2, '0')}-${path.basename(diagram.file, '.md')}`;
    fs.writeFileSync(path.join(output, `${stem}.svg`), svg, 'utf8');
    await page.locator('#diagram').screenshot({ path: path.join(output, `${stem}.png`) });
    results.push({ file: diagram.file, block: diagram.index + 1, parsed: true, rendered: true });
    console.log(`PASS ${diagram.file} block ${diagram.index + 1}`);
  }
  fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({
    mermaid: localRequire('mermaid/package.json').version,
    browser: await browser.version(), invalidSyntaxRejected: true, diagrams: results,
  }, null, 2) + '\n');
  console.log(`PASS: ${results.length} diagrams parsed and rendered locally; invalid syntax rejected.`);
} finally {
  await browser.close();
}
