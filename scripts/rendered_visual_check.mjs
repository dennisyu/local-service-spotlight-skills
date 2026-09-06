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
  const elementRect = el.getBoundingClientRect();
  const bbox = { x: elementRect.x, y: elementRect.y, width: elementRect.width, height: elementRect.height };
  let rect = elementRect;
  let imagePaint = null;
  if (el.tagName === 'IMG' && el.naturalWidth && el.naturalHeight) {
    const css = getComputedStyle(el);
    const px = name => Number.parseFloat(css[name]) || 0;
    const scaleX = elementRect.width / Math.max(1, el.offsetWidth), scaleY = elementRect.height / Math.max(1, el.offsetHeight);
    const insetLeft = (px('borderLeftWidth') + px('paddingLeft')) * scaleX;
    const insetTop = (px('borderTopWidth') + px('paddingTop')) * scaleY;
    const contentWidth = Math.max(0, elementRect.width - insetLeft - (px('borderRightWidth') + px('paddingRight')) * scaleX);
    const contentHeight = Math.max(0, elementRect.height - insetTop - (px('borderBottomWidth') + px('paddingBottom')) * scaleY);
    const content = {left:elementRect.left+insetLeft,top:elementRect.top+insetTop,width:contentWidth,height:contentHeight};
    const intrinsicWidth = el.naturalWidth * scaleX, intrinsicHeight = el.naturalHeight * scaleY;
    let width = contentWidth, height = contentHeight;
    if (['contain','cover','scale-down','none'].includes(css.objectFit)) {
      let scale = Math.min(contentWidth/intrinsicWidth,contentHeight/intrinsicHeight);
      if (css.objectFit === 'cover') scale = Math.max(contentWidth/intrinsicWidth,contentHeight/intrinsicHeight);
      if (css.objectFit === 'none') scale = 1;
      if (css.objectFit === 'scale-down') scale = Math.min(1,scale);
      width = intrinsicWidth * scale; height = intrinsicHeight * scale;
    }
    const positions = css.objectPosition.match(/calc\([^)]*\)|[^\s]+/g) || [];
    const position = (value, freeSpace, unitScale) => {
      const simple = /^(-?[\d.]+)(%|px)$/.exec(value || '');
      if (simple) return Number(simple[1]) * (simple[2] === '%' ? freeSpace/100 : unitScale);
      const calculated = /^calc\(\s*(-?[\d.]+)%\s*([+-])\s*([\d.]+)px\s*\)$/.exec(value || '');
      if (calculated) return Number(calculated[1])*freeSpace/100 + Number(calculated[3])*unitScale*(calculated[2] === '+' ? 1 : -1);
      if (value === 'center') return freeSpace/2;
      if (['left','top'].includes(value)) return 0;
      if (['right','bottom'].includes(value)) return freeSpace;
      return null;
    };
    const x = position(positions[0],contentWidth-width,scaleX), y = position(positions[1],contentHeight-height,scaleY);
    if (x === null || y === null) reasons.push('unsupported image object-position; painted bounds need explicit review');
    else {
      // Replaced content is clipped to its content box, including object-fit:none
      // or object-position values that intentionally push some pixels out of it.
      const left=Math.max(content.left,content.left+x),top=Math.max(content.top,content.top+y);
      const right=Math.min(content.left+contentWidth,content.left+x+width),bottom=Math.min(content.top+contentHeight,content.top+y+height);
      rect={left,top,right,bottom,x:left,y:top,width:Math.max(0,right-left),height:Math.max(0,bottom-top)};
    }
    imagePaint = {objectFit:css.objectFit,objectPosition:css.objectPosition,naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight,
      x:rect.x,y:rect.y,width:rect.width,height:rect.height};
  }
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
    if (match) {
      kind = 'css-background'; src = match[1]; loaded = await imageReady(src);
      // Only cover guarantees that the single image fills this element's box.
      // contain/auto/explicit sizes can leave vast blank areas; until their
      // painted geometry is measured, never promote the container box to PASS.
      if (getComputedStyle(el).backgroundSize.trim() !== 'cover')
        reasons.push('CSS background painted bounds are unmeasured for non-cover sizing; explicit rendered review required');
    }
    else reasons.push('select the actual image, diagram, video poster or single photographic background');
  }
  // Hit testing alone ignores pointer-events:none and returns a parent for its
  // pseudo-elements. Inspect painted descendant layers for photographic backgrounds.
  const alpha = color => {
    if (color === 'transparent') return 0;
    const slash = color.match(/\/\s*([\d.]+)(%)?\s*\)/);
    if (slash) return Number(slash[1]) / (slash[2] ? 100 : 1);
    const rgba = color.match(/^rgba\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\)/);
    return rgba ? Number(rgba[1]) : 1;
  };
  const paintAlpha = css => css.backgroundImage !== 'none' ? 1 : alpha(css.backgroundColor);
  const pointIn = (box, x, y) => x >= box.left && x < box.right && y >= box.top && y < box.bottom;
  const effectiveOpacity = (node, boundary) => {
    let opacity = 1;
    for (; node && node !== boundary; node = node.parentElement) {
      const css = getComputedStyle(node);
      if (css.display === 'none' || css.visibility !== 'visible') return 0;
      opacity *= Number(css.opacity);
    }
    return opacity;
  };
  const paintedLayers = boundary => {
    const layers = [];
    for (const node of [boundary, ...boundary.querySelectorAll('*')]) {
      const css = getComputedStyle(node), opacity = effectiveOpacity(node, boundary);
      if (opacity === 0) continue;
      if (node !== boundary && !(Number(css.zIndex) < 0)) {
        const replaced = /^(IMG|VIDEO|CANVAS|IFRAME|SVG)$/.test(node.tagName);
        const amount = opacity * (replaced ? 1 : paintAlpha(css));
        if (amount) layers.push({ box: node.getBoundingClientRect(), alpha: amount });
      }
      for (const pseudo of ['::before', '::after']) {
        const ps = getComputedStyle(node, pseudo);
        if (ps.content === 'none' || ps.content === 'normal' || ps.display === 'none' || ps.visibility !== 'visible' || Number(ps.zIndex) < 0) continue;
        const amount = opacity * Number(ps.opacity) * paintAlpha(ps);
        if (!amount) continue;
        // Absolute/fixed overlays have resolved dimensions; do not invent a box
        // for inline generated text. Unknown clipping/crops still need image review.
        if (!['absolute', 'fixed'].includes(ps.position)) continue;
        const base = ps.position === 'fixed' ? {left:0,top:0,width:innerWidth,height:innerHeight} : node.getBoundingClientRect();
        const w = Number.parseFloat(ps.width), h = Number.parseFloat(ps.height);
        const left = ps.left !== 'auto' ? base.left + Number.parseFloat(ps.left) : base.left + base.width - Number.parseFloat(ps.right) - w;
        const top = ps.top !== 'auto' ? base.top + Number.parseFloat(ps.top) : base.top + base.height - Number.parseFloat(ps.bottom) - h;
        if ([w,h,left,top].every(Number.isFinite)) layers.push({ box: {left,top,right:left+w,bottom:top+h}, alpha: amount });
      }
    }
    return layers;
  };
  const backgroundLayers = kind === 'css-background' ? paintedLayers(el) : [];
  let unobscured = 0;
  for (let row = 0; row < 10; row++) for (let col = 0; col < 10; col++) {
    const x = clip.left + width * (col + 0.5) / 10, y = clip.top + height * (row + 0.5) / 10;
    const top = document.elementFromPoint(x,y);
    let transmitted = 1;
    for (const layer of backgroundLayers) if (pointIn(layer.box,x,y)) transmitted *= 1 - layer.alpha;
    if (top && (top === el || el.contains(top)) && transmitted > 0.1) unobscured++;
  }
  const unoccludedFraction = unobscured / 100;
  if (unoccludedFraction < policy.min_unoccluded_fraction) reasons.push('visual is covered or clipped by other content');

  // Require one readable title line beside the first-screen visual. Measure text
  // ranges, not the full H1 box: a natural multiline heading can clear this gate.
  const headings = [];
  for (const heading of document.querySelectorAll('h1,[role="heading"][aria-level="1"]')) {
    if (heading.closest('nav,footer,[role="banner"],[role="navigation"]')) continue;
    const record = { text: heading.textContent.trim(), readableLine: false, lines: [] };
    if (!record.text || effectiveOpacity(heading, null) < 0.1) { headings.push(record); continue; }
    const walker = document.createTreeWalker(heading, NodeFilter.SHOW_TEXT);
    for (let textNode = walker.nextNode(); textNode; textNode = walker.nextNode()) {
      if (!textNode.textContent.trim()) continue;
      const textParent = textNode.parentElement;
      const textCss = getComputedStyle(textParent);
      if (effectiveOpacity(textParent, null) < 0.1 || alpha(textCss.color) < 0.1) continue;
      const fontSize = Number.parseFloat(textCss.fontSize);
      const range = document.createRange(); range.selectNodeContents(textNode);
      for (const line of range.getClientRects()) {
        const box = {left:Math.max(0,line.left),top:Math.max(0,line.top),right:Math.min(innerWidth,line.right),bottom:Math.min(innerHeight,line.bottom)};
        for (let ancestor = textParent; ancestor; ancestor = ancestor.parentElement) {
          const css = getComputedStyle(ancestor), rect = ancestor.getBoundingClientRect();
          if (/(hidden|clip|scroll|auto)/.test(css.overflowX)) {box.left=Math.max(box.left,rect.left);box.right=Math.min(box.right,rect.right);}
          if (/(hidden|clip|scroll|auto)/.test(css.overflowY)) {box.top=Math.max(box.top,rect.top);box.bottom=Math.min(box.bottom,rect.bottom);}
        }
        const visibleFraction = Math.max(0,box.right-box.left)*Math.max(0,box.bottom-box.top)/Math.max(1,line.width*line.height);
        let clear = 0;
        for (let point=0;point<10;point++) {
          const top=document.elementFromPoint(box.left+(box.right-box.left)*(point+0.5)/10,(box.top+box.bottom)/2);
          if (top===textParent || (top && heading.contains(top) &&
            (effectiveOpacity(top,heading)<0.1 || (!top.textContent.trim() && paintAlpha(getComputedStyle(top))<0.1)))) clear++;
        }
        const readable = fontSize >= policy.min_heading_font_size && visibleFraction >= policy.min_heading_line_visible_fraction && clear/10 >= policy.min_unoccluded_fraction;
        record.lines.push({x:line.x,y:line.y,width:line.width,height:line.height,fontSize,visibleFraction,unoccludedFraction:clear/10,readable});
        if (readable) record.readableLine = true;
      }
    }
    headings.push(record);
  }
  if (!headings.some(heading => heading.readableLine)) reasons.push('no readable page-title line is visible above the fold');
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
    selector, kind, src, label: label.trim(), loaded, bbox, imagePaint, visible: { width, height, fraction, viewportFraction, unoccludedFraction }, headings, overflow,
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
