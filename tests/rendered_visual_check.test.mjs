import test from 'node:test';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import http from 'node:http';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { loadPolicy, measureVisual, auditPage } from '../scripts/rendered_visual_check.mjs';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href : 'playwright');
const policy = await loadPolicy();
const browser = await chromium.launch({ headless: true, args: ['--mute-audio', '--autoplay-policy=user-gesture-required'], ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
const image = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500"><rect width="800" height="500" fill="navy"/><text x="50" y="150" fill="white" font-size="42">Actual roof inspection</text></svg>');
const img = `<img id="proof" src="${image}" alt="A documented roof inspection" style="display:block;width:100%;height:250px;object-fit:cover">`;
async function check(body, { width=390, height=844, js=true, heading='<h1>How the inspection works</h1>' }={}) {
  const page = await browser.newPage({ viewport:{width,height}, javaScriptEnabled:js });
  await page.route('**/*', route => /^https?:/.test(route.request().url()) ? route.abort() : route.continue());
  await page.setContent(`<style>*{box-sizing:border-box}body{margin:0}main{width:min(100%,800px);margin:auto}</style><main>${heading}${body}</main>`);
  await page.locator('#proof').first().evaluate(async el => { if(el.tagName==='IMG') try { await el.decode(); } catch {} });
  try { return await page.evaluate(measureVisual, {selector:'#proof',policy}); } finally { await page.close(); }
}
try {
  await test('actual loaded meaningful image clears both viewport gates with/without JS', async () => {
    for (const viewport of policy.viewports) for (const js of [true,false]) {
      const result = await check(img, {...viewport,js});
      assert.equal(result.geometry,'PASS',JSON.stringify(result)); assert.equal(result.semanticReview,'REQUIRED');
    }
  });
  await test('buried picture fails despite source-order appearance before h2', async () => {
    assert.equal((await check(`<p style="height:750px">A long opening</p>${img}`)).geometry,'FAIL');
  });
  await test('thin visible strip fails', async () => {
    assert.equal((await check(`<div style="height:650px"></div>${img}`)).geometry,'FAIL');
  });
  await test('broken image fails', async () => {
    assert.equal((await check(img.replace(image,'data:image/png;base64,broken'))).geometry,'FAIL');
  });
  await test('hidden ancestor fails', async () => {
    assert.equal((await check(`<div style="opacity:0">${img}</div>`)).geometry,'FAIL');
  });
  await test('ancestor clipping fails', async () => {
    assert.equal((await check(`<div style="height:40px;overflow:hidden">${img}</div>`)).geometry,'FAIL');
  });
  await test('fixed overlay fails without closing the overlay', async () => {
    assert.equal((await check(`${img}<div style="position:fixed;inset:0;background:white;z-index:999">Consent</div>`)).geometry,'FAIL');
  });
  await test('logo and navigation visual fail', async () => {
    assert.equal((await check(img.replace('id="proof"','id="proof" class="logo"'))).geometry,'FAIL');
    assert.equal((await check(`<nav>${img}</nav>`)).geometry,'FAIL');
  });
  await test('SVG shell, unlabeled image and opaque iframe fail', async () => {
    assert.equal((await check('<svg id="proof" aria-label="A diagram" style="width:100%;height:250px"></svg>')).geometry,'FAIL');
    assert.equal((await check(img.replace('alt="A documented roof inspection"','alt=""'))).geometry,'FAIL');
    assert.equal((await check('<iframe id="proof" title="Interview" style="width:100%;height:250px" src="about:blank"></iframe>')).geometry,'FAIL');
  });
  await test('real labeled SVG diagram passes geometry and still requires review', async () => {
    const result = await check('<svg id="proof" role="img" aria-label="Inspection feeds the roof repair estimate" style="width:100%;height:250px" viewBox="0 0 390 250"><rect x="10" y="50" width="160" height="100" fill="navy"/><text x="20" y="100" fill="white">Inspection</text><path d="M180 100 L350 100" stroke="black"/></svg>');
    assert.equal(result.geometry,'PASS'); assert.equal(result.semanticReview,'REQUIRED');
  });
  await test('bad YouTube caption/privacy/autoplay parameters fail even with good image', async () => {
    const result = await check(`${img}<iframe src="https://www.youtube.com/embed/test?autoplay=1" style="display:none"></iframe>`);
    assert.equal(result.geometry,'FAIL'); assert.ok(result.reasons.some(x=>x.includes('cc_load_policy')));
  });
  await test('loaded meaningful CSS photo background passes while decorative gradient fails', async () => {
    const photo = `<section id="proof" aria-label="Documented roof inspection" style="height:250px;background-image:url('${image}');background-size:cover"></section>`;
    assert.equal((await check(photo)).geometry,'PASS');
    assert.equal((await check('<section id="proof" aria-label="Decorative gradient" style="height:250px;background:linear-gradient(red,blue)"></section>')).geometry,'FAIL');
  });
  await test('opaque descendant hides a loaded CSS photo even with pointer events disabled', async () => {
    for (const pointer of ['auto','none']) {
      const photo = `<section id="proof" aria-label="Documented inspection" style="position:relative;height:300px;background-image:url('${image}');background-size:cover"><div style="position:absolute;inset:0;background:white;z-index:1;pointer-events:${pointer}"></div></section>`;
      const result = await check(photo);
      assert.equal(result.loaded,true); assert.equal(result.geometry,'FAIL'); assert.equal(result.visible.unoccludedFraction,0);
    }
  });
  await test('opaque pseudo-element covers the photo although hit testing returns its parent', async () => {
    for (const pseudo of ['before','after']) {
      const photo = `<style>#proof::${pseudo}{content:"";position:absolute;inset:0;background:white;z-index:1;pointer-events:none}</style><section id="proof" aria-label="Documented inspection" style="position:relative;height:300px;background-image:url('${image}');background-size:cover"></section>`;
      const result = await check(photo);
      assert.equal(result.geometry,'FAIL'); assert.equal(result.visible.unoccludedFraction,0);
    }
  });
  await test('transparent text, invisible overlay and a light tint preserve the actual photo', async () => {
    for (const overlay of ['<div style="position:absolute;inset:0;background:white;opacity:0"></div>','<div style="position:absolute;inset:0;background:rgba(0,0,0,.2)"><span style="color:white">The inspection moment</span></div>']) {
      const photo = `<section id="proof" aria-label="Documented inspection" style="position:relative;height:300px;background-image:url('${image}');background-size:cover">${overlay}</section>`;
      assert.equal((await check(photo)).geometry,'PASS');
    }
  });
  await test('large visible photo does not pass when the title is missing, hidden or below the fold', async () => {
    for (const heading of ['', '<h1 style="display:none">Roof inspection</h1>', '<h1 style="position:absolute;top:900px">Roof inspection</h1>', '<h1 style="font-size:8px">Roof inspection</h1>']) {
      const result = await check(img,{heading});
      assert.equal(result.geometry,'FAIL'); assert.ok(result.reasons.some(reason=>reason.includes('page-title')));
    }
  });
  await test('natural multiline title passes with one complete visible text line', async () => {
    const heading = '<h1 style="font-size:32px;line-height:36px;position:absolute;top:788px;margin:0;width:390px">Inspecting the roof<br>with the homeowner</h1>';
    const result=await check(img,{heading});
    assert.equal(result.geometry,'PASS',JSON.stringify(result));
    assert.equal(result.headings[0].readableLine,true);
    assert.ok(result.headings[0].lines.some(line=>!line.readable));
  });
  await test('title line hidden by an unrelated panel or clipped to a thin strip fails', async () => {
    for (const heading of ['<h1 style="position:relative">Roof inspection<div style="position:absolute;inset:0;background:white"></div></h1>', '<div style="height:8px;overflow:hidden"><h1>Roof inspection</h1></div>']) {
      const result=await check(img,{heading}); assert.equal(result.geometry,'FAIL');
      assert.ok(result.reasons.some(reason=>reason.includes('page-title')));
    }
  });
  await test('publisher adapter records four screenshots and never upgrades geometry to compliance', async () => {
    const html = `<style>*{box-sizing:border-box}body{margin:0}main{width:min(100%,800px);margin:auto}</style><main><h1>Roof inspection</h1>${img}</main>`;
    const server = http.createServer((req,res) => {res.writeHead(200,{'Content-Type':'text/html'});res.end(html);});
    await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
    const directory = await fs.mkdtemp(path.join(os.tmpdir(),'lss-visual-gate-'));
    try {
      const receipt = await auditPage(browser, {url:`http://127.0.0.1:${server.address().port}/`,selector:'#proof',output:directory},policy);
      assert.equal(receipt.geometry,'PASS',JSON.stringify(receipt));
      assert.equal(receipt.compliance,'REVIEW_REQUIRED');
      assert.equal(receipt.observations.length,4);
      for (const observation of receipt.observations) {
        const bytes=await fs.readFile(path.join(directory,observation.screenshot));
        assert.equal(createHash('sha256').update(bytes).digest('hex'),observation.screenshotSha256);
        assert.equal(observation.httpStatus,200);
      }
      assert.equal(JSON.parse(await fs.readFile(path.join(directory,'receipt.json'),'utf8')).playbackReview,'NOT_TESTED');
    } finally { await new Promise(resolve=>server.close(resolve)); await fs.rm(directory,{recursive:true,force:true}); }
  });
  await test('ambiguous selector cannot silently choose the first matching image', async () => {
    assert.equal((await check(img+img)).geometry,'FAIL');
  });
} finally { await browser.close(); }
