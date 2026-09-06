#!/usr/bin/env node
/** Read-only first-screen measurement. A geometry pass always requires editorial review.
 * CLI: node scripts/rendered_visual_check.mjs --url https://example.com/ \
 *        --selector 'main .opening-photo' --output /absolute/receipt-directory
 * Set PLAYWRIGHT_MODULE to an installed playwright module if it is not local.
 * No click, scroll, consent dismissal or playback is performed.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export async function loadPolicy() {
  const text = await fs.readFile(path.join(root, 'standards/visuals-above-the-fold.md'), 'utf8');
  const header = JSON.parse(text.split(/^---\s*$/m)[1]);
  if (header.rendered_gate?.version !== 1) throw new Error('Missing supported rendered_gate');
  return header.rendered_gate;
}

// Self-contained so an existing Playwright publisher can call page.evaluate(measureVisual, ...).
export async function measureVisual({ selector, policy }) {
  const fail = (reason, extra = {}) => ({ geometry: 'FAIL', reasons: [reason], ...extra });
  const nodes = document.querySelectorAll(selector);
  if (nodes.length !== 1) return fail(`selector matched ${nodes.length} elements; expected exactly one`);
  const el = nodes[0];
  if (scrollX || scrollY) return fail('measurement requires the unscrolled first visit');
  const reasons = [];
  const rect = el.getBoundingClientRect();
  const bbox = { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
  if (el.closest('nav,footer,[role="banner"],[role="navigation"],[role="dialog"],[aria-modal="true"]'))
    reasons.push('navigation, footer, banner or overlay does not count as page proof');
  const identity = `${el.id} ${el.className?.baseVal ?? el.className} ${el.getAttribute('alt') || ''} ${el.getAttribute('aria-label') || ''}`;
  if (/(?:^|[\s_-])(logo|icon|avatar|cookie|placeholder|spinner)(?:$|[\s_-])/i.test(identity))
    reasons.push('logo, icon, cookie UI or loading placeholder does not count');
  let clip = { left: Math.max(0, rect.left), top: Math.max(0, rect.top), right: Math.min(innerWidth, rect.right), bottom: Math.min(innerHeight, rect.bottom) };
  for (let node = el; node; node = node.parentElement) {
    const css = getComputedStyle(node);
    if (css.display === 'none' || css.visibility !== 'visible' || Number(css.opacity) < 0.1)
      reasons.push('visual or ancestor is hidden');
    if (node !== el) {
      const a = node.getBoundingClientRect();
      if (/(hidden|clip|scroll|auto)/.test(css.overflowX)) { clip.left = Math.max(clip.left, a.left); clip.right = Math.min(clip.right, a.right); }
      if (/(hidden|clip|scroll|auto)/.test(css.overflowY)) { clip.top = Math.max(clip.top, a.top); clip.bottom = Math.min(clip.bottom, a.bottom); }
    }
  }
  const width = Math.max(0, clip.right - clip.left), height = Math.max(0, clip.bottom - clip.top);
  const area = width * height, fraction = area / Math.max(1, rect.width * rect.height);
  const viewportFraction = area / (innerWidth * innerHeight);
  if (width < policy.min_visible_width || height < policy.min_visible_height) reasons.push('visible width/height below the minimum');
  if (fraction < policy.min_visible_fraction) reasons.push('too little of the visual is visible');
  if (viewportFraction < policy.min_viewport_fraction) reasons.push('visual occupies too little of the viewport');
  let unobscured = 0;
  for (let row = 0; row < 10; row++) for (let col = 0; col < 10; col++) {
    const top = document.elementFromPoint(clip.left + width * (col + 0.5) / 10, clip.top + height * (row + 0.5) / 10);
    if (top && (top === el || el.contains(top))) unobscured++;
  }
  const unoccludedFraction = unobscured / 100;
  if (unoccludedFraction < policy.min_unoccluded_fraction) reasons.push('visual is covered or clipped by other content');
  const tag = el.tagName.toLowerCase();
  let loaded = false, src = '', kind = tag;
  const imageReady = async (src) => {
    if (!src) return false;
    const img = new Image(); img.src = src;
    try { await Promise.race([img.decode(), new Promise((_, reject) => setTimeout(() => reject(new Error('image timeout')), 5000))]); return img.naturalWidth >= 160 && img.naturalHeight >= 90; } catch { return false; }
  };
  if (tag === 'img') {
    loaded = el.complete && el.naturalWidth >= 160 && el.naturalHeight >= 90;
    src = el.currentSrc || el.src;
  } else if (tag === 'svg') {
    loaded = el.querySelectorAll('path,rect,circle,line,polyline,polygon,text,image').length >= 2;
    // Empty SVG and an icon with no useful accessible label cannot pass silently.
  } else if (tag === 'video') {
    kind = 'video-poster'; src = el.poster; loaded = await imageReady(src);
    if (el.autoplay) reasons.push('autoplay is not allowed on first paint');
    if (!el.paused) reasons.push('media played during the first-screen test');
  } else if (tag === 'iframe') {
    src = el.src;
    reasons.push('opaque iframe needs a verified loaded poster or independent rendered-player review');
  } else {
    const background = getComputedStyle(el).backgroundImage;
    const match = /^url\(["']?(.*?)["']?\)$/.exec(background);
    if (match) { kind = 'css-background'; src = match[1]; loaded = await imageReady(src); }
    else reasons.push('select the actual image, diagram, video poster or single photographic background');
  }
  const label = el.getAttribute('alt') || el.getAttribute('aria-label') ||
    (el.getAttribute('aria-labelledby') || '').split(/\s+/).map(id => document.getElementById(id)?.textContent || '').join(' ').trim() ||
    el.querySelector('title')?.textContent || el.closest('figure')?.querySelector('figcaption')?.textContent || '';
  if (!label.trim()) reasons.push('missing meaningful accessible description or caption');
  if (!loaded) reasons.push('image/poster is not loaded, image is tiny, or SVG is empty');
  const overflow = document.documentElement.scrollWidth > innerWidth + 1;
  if (overflow) reasons.push('horizontal page overflow');
  const mediaViolations = [];
  for (const frame of document.querySelectorAll('iframe[src]')) {
    let url; try { url = new URL(frame.src); } catch { continue; }
    if (/(^|\.)youtube(?:-nocookie)?\.com$/.test(url.hostname) && url.pathname.startsWith('/embed/')) {
      if (url.hostname !== 'www.youtube-nocookie.com' && url.hostname !== 'youtube-nocookie.com') mediaViolations.push('YouTube privacy host missing');
      for (const [key, value] of [['rel','0'], ['cc_load_policy','1']]) if (url.searchParams.get(key) !== value) mediaViolations.push(`YouTube ${key}=${value} missing`);
      if (!/^[a-z]{2}(?:-[a-zA-Z]{2})?$/.test(url.searchParams.get('cc_lang_pref') || '')) mediaViolations.push('YouTube caption language missing');
      if (url.searchParams.get('autoplay') === '1') mediaViolations.push('YouTube autoplays before a click');
    }
  }
  if (document.querySelector('video[autoplay],audio[autoplay]')) mediaViolations.push('native media autoplays before a click');
  reasons.push(...mediaViolations);
  return { geometry: reasons.length ? 'FAIL' : 'PASS', semanticReview: 'REQUIRED', reasons: [...new Set(reasons)],
    selector, kind, src, label: label.trim(), loaded, bbox, visible: { width, height, fraction, viewportFraction, unoccludedFraction }, overflow,
    viewport: { width: innerWidth, height: innerHeight }, finalUrl: location.href };
}

export async function auditPage(browser, { url, selector, output }, policy) {
  const receipt = { version: 1, requestedUrl: url, selector, observedAt: new Date().toISOString(),
    semanticReview: 'REQUIRED', sourceReview: 'REQUIRED', playbackReview: 'NOT_TESTED', policy, observations: [] };
  await fs.mkdir(output, { recursive: true });
  for (const viewport of policy.viewports) for (const javaScriptEnabled of [true, false]) {
    const context = await browser.newContext({ viewport, javaScriptEnabled, reducedMotion: 'reduce', serviceWorkers: 'block' });
    const page = await context.newPage();
    try {
      // Abort audio/video bytes. Posters remain loadable. Never click a player.
      await context.route('**/*', route => route.request().resourceType() === 'media' ? route.abort() : route.continue());
      await context.addInitScript(() => {
        const silence = () => document.querySelectorAll('video,audio').forEach(el => { el.muted = true; el.volume = 0; el.pause(); });
        new MutationObserver(silence).observe(document, { childList: true, subtree: true });
        document.addEventListener('play', silence, true); silence();
      });
      const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.evaluate(() => Promise.race([document.fonts.ready, new Promise(resolve => setTimeout(resolve, 3000))]));
      await page.waitForFunction(selector => {
        const image = document.querySelector(selector);
        return !image || image.tagName !== 'IMG' || image.complete;
      }, selector, { timeout: 10000 }).catch(() => {});
      const result = await page.evaluate(measureVisual, { selector, policy });
      const name = `${viewport.width}x${viewport.height}-js-${javaScriptEnabled ? 'on' : 'off'}.png`;
      const bytes = await page.screenshot({ path: path.join(output, name), fullPage: false, animations: 'disabled' });
      receipt.observations.push({ ...result, httpStatus: response?.status() ?? null, javaScriptEnabled,
        screenshot: name, screenshotSha256: createHash('sha256').update(bytes).digest('hex') });
      if (response?.status() !== 200) { result.geometry = 'FAIL'; receipt.observations.at(-1).geometry = 'FAIL'; receipt.observations.at(-1).reasons.push('page did not return HTTP 200'); }
    } catch (error) {
      receipt.observations.push({ geometry: 'ERROR', viewport, javaScriptEnabled, reasons: [String(error.message || error)] });
    } finally { await context.close(); }
  }
  receipt.geometry = receipt.observations.every(o => o.geometry === 'PASS') ? 'PASS' : 'FAIL';
  receipt.compliance = receipt.geometry === 'PASS' ? 'REVIEW_REQUIRED' : 'FAIL';
  await fs.writeFile(path.join(output, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
  return receipt;
}

async function main() {
  const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, i, all) => value.startsWith('--') ? [...pairs, [value.slice(2), all[i+1]]] : pairs, []));
  if (!args.url || !args.selector || !args.output) throw new Error('Required: --url URL --selector CSS --output DIRECTORY');
  const url = new URL(args.url); if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Only http(s) URLs are supported');
  const modulePath = process.env.PLAYWRIGHT_MODULE;
  const { chromium } = await import(modulePath ? pathToFileURL(path.resolve(modulePath)).href : 'playwright');
  const browser = await chromium.launch({ headless: true, args: ['--mute-audio', '--autoplay-policy=user-gesture-required'], ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
  try {
    const receipt = await auditPage(browser, { url: args.url, selector: args.selector, output: path.resolve(args.output) }, await loadPolicy());
    console.log(JSON.stringify({ geometry: receipt.geometry, compliance: receipt.compliance, receipt: path.resolve(args.output, 'receipt.json') }));
    process.exitCode = receipt.geometry === 'PASS' ? 0 : 1;
  } finally { await browser.close(); }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(error => { console.error(error.message); process.exitCode = 2; });
