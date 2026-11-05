// Inert response doubles only. No browser or network is launched by these tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {retainResponseSource} from '../scripts/rendered_visual_check.mjs';

test('retains actual response bytes with exact hash and refuses stale overwrite', async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'source-capture-'));
  try {
    const bytes = Buffer.from('<!doctype html>\n<h1>Source</h1>\n');
    const result = await retainResponseSource({body: async () => bytes}, directory, 'source.html');
    assert.deepEqual(await fs.readFile(path.join(directory, result.path)), bytes);
    assert.equal(result.sha256, createHash('sha256').update(bytes).digest('hex'));
    assert.equal(result.bytes, bytes.length);
    await assert.rejects(retainResponseSource({body: async () => bytes}, directory, 'source.html'), /EEXIST/);
    assert.deepEqual(await fs.readFile(path.join(directory, result.path)), bytes);
  } finally { await fs.rm(directory, {recursive: true, force: true}); }
});

test('missing response, non-bytes and escaping capture filename hold', async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'source-capture-'));
  try {
    await assert.rejects(retainResponseSource(null, directory, 'source.html'), /unavailable/);
    await assert.rejects(retainResponseSource({body: async () => 'not raw bytes'}, directory, 'source.html'), /contract/);
    await assert.rejects(retainResponseSource({body: async () => Buffer.from('x')}, directory, '../source.html'), /filename/);
    assert.deepEqual(await fs.readdir(directory), []);
  } finally { await fs.rm(directory, {recursive: true, force: true}); }
});
