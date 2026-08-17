#!/usr/bin/env node
/**
 * Build VendorTracker's free on-device Pokémon card embedding index.
 *
 * The browser and this builder both use TensorFlow.js MobileNet V2 (alpha .5).
 * Official card-image embeddings are feature-hashed to 256 dimensions, L2
 * normalized, and quantized to int8. The resulting VTE1 file is small enough
 * to cache on a phone and lets scans be shortlisted locally without a paid API.
 */

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import {fileURLToPath} from "node:url";
import * as tf from "@tensorflow/tfjs-node";
import * as mobilenet from "@tensorflow-models/mobilenet";
import sharp from "sharp";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUTPUT = path.join(ROOT, "pokemon-card-embedding-index.bin");
const API = "https://api.pokemontcg.io/v2/cards";
const PAGE_SIZE = 250;
const EMBEDDING_DIMENSION = 256;
const BATCH_SIZE = 24;
const MINIMUM_COVERAGE = 0.96;

const delay = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));

async function fetchBytes(url, accept, attempts = 4) {
  let lastError;
  for (let attempt = 0; attempt < attempts; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30_000);
    try {
      const response = await fetch(url, {
        headers: {Accept: accept, "User-Agent": "VendorTracker embedding-index builder/1.0"},
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      return Buffer.from(await response.arrayBuffer());
    } catch (error) {
      lastError = error;
      if (attempt + 1 < attempts) await delay(600 * (attempt + 1));
    } finally {
      clearTimeout(timer);
    }
  }
  throw lastError || new Error("Request failed");
}

async function fetchJson(url) {
  return JSON.parse((await fetchBytes(url, "application/json")).toString("utf8"));
}

async function loadCards() {
  const firstUrl = `${API}?${new URLSearchParams({page: "1", pageSize: String(PAGE_SIZE), select: "id,images"})}`;
  const first = await fetchJson(firstUrl);
  const total = Number(first.totalCount || first.data?.length || 0);
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const payloads = new Array(pages);
  payloads[0] = first;
  let nextPage = 2;
  await Promise.all(Array.from({length: Math.min(8, Math.max(0, pages - 1))}, async () => {
    while (nextPage <= pages) {
      const page = nextPage++;
      const url = `${API}?${new URLSearchParams({page: String(page), pageSize: String(PAGE_SIZE), select: "id,images"})}`;
      payloads[page - 1] = await fetchJson(url);
    }
  }));
  const cards = payloads.flatMap(payload => payload?.data || []).filter(card => card?.id && card?.images?.small);
  console.log(`metadata ${cards.length}/${total}`);
  return cards;
}

function parseExisting(buffer) {
  if (!buffer || buffer.length < 16 || buffer.subarray(0, 4).toString("ascii") !== "VTE1") return new Map();
  const count = buffer.readUInt32LE(4);
  const dimension = buffer.readUInt16LE(8);
  if (dimension !== EMBEDDING_DIMENSION) return new Map();
  const records = new Map();
  let offset = 16;
  for (let index = 0; index < count; index++) {
    const idLength = buffer.readUInt8(offset++);
    const id = buffer.subarray(offset, offset + idLength).toString("utf8");
    offset += idLength;
    const norm = buffer.readUInt32LE(offset);
    offset += 4;
    const vector = Buffer.from(buffer.subarray(offset, offset + dimension));
    offset += dimension;
    records.set(id, {norm, vector});
  }
  return records;
}

async function loadExisting() {
  try {
    return parseExisting(await fs.readFile(OUTPUT));
  } catch (error) {
    if (error?.code === "ENOENT") return new Map();
    throw error;
  }
}

function featureHash(index) {
  let hash = Math.imul(index + 1, 0x9e3779b1) >>> 0;
  hash ^= hash >>> 16;
  return hash >>> 0;
}

function quantizeEmbedding(values) {
  const projected = new Float32Array(EMBEDDING_DIMENSION);
  for (let index = 0; index < values.length; index++) {
    const hash = featureHash(index);
    projected[hash % EMBEDDING_DIMENSION] += (hash & 1 ? 1 : -1) * values[index];
  }
  let magnitude = 0;
  for (const value of projected) magnitude += value * value;
  magnitude = Math.sqrt(magnitude) || 1;
  const vector = Buffer.alloc(EMBEDDING_DIMENSION);
  let norm = 0;
  for (let index = 0; index < projected.length; index++) {
    const value = Math.max(-127, Math.min(127, Math.round(projected[index] / magnitude * 127)));
    vector.writeInt8(value, index);
    norm += value * value;
  }
  return {norm, vector};
}

async function cardPixels(card) {
  const source = card.images.small || card.images.large;
  const bytes = await fetchBytes(source, "image/*");
  return sharp(bytes, {failOn: "none"})
    .resize(224, 224, {fit: "fill", kernel: sharp.kernel.lanczos3})
    .removeAlpha()
    .toColorspace("srgb")
    .raw()
    .toBuffer();
}

async function embedBatch(model, cards) {
  const settled = await Promise.allSettled(cards.map(cardPixels));
  const usable = [];
  const buffers = [];
  settled.forEach((result, index) => {
    if (result.status === "fulfilled" && result.value.length === 224 * 224 * 3) {
      usable.push(cards[index]);
      buffers.push(result.value);
    }
  });
  if (!usable.length) return {records: [], failed: cards.map(card => card.id)};
  const input = tf.tensor4d(new Uint8Array(Buffer.concat(buffers)), [usable.length, 224, 224, 3], "int32");
  const output = model.infer(input, true);
  const shape = output.shape;
  const values = await output.data();
  input.dispose();
  output.dispose();
  const sourceDimension = shape[shape.length - 1];
  const records = usable.map((card, row) => ({
    id: card.id,
    ...quantizeEmbedding(values.subarray(row * sourceDimension, (row + 1) * sourceDimension)),
  }));
  const succeeded = new Set(usable.map(card => card.id));
  return {records, failed: cards.filter(card => !succeeded.has(card.id)).map(card => card.id), sourceDimension};
}

function serialize(records, sourceDimension) {
  const ids = [...records.keys()].sort();
  const size = 16 + ids.reduce((sum, id) => sum + 1 + Buffer.byteLength(id) + 4 + EMBEDDING_DIMENSION, 0);
  const output = Buffer.allocUnsafe(size);
  output.write("VTE1", 0, "ascii");
  output.writeUInt32LE(ids.length, 4);
  output.writeUInt16LE(EMBEDDING_DIMENSION, 8);
  output.writeUInt16LE(sourceDimension || 0, 10);
  output.writeUInt32LE(205, 12); // MobileNet V2 alpha .5
  let offset = 16;
  for (const id of ids) {
    const encoded = Buffer.from(id, "utf8");
    if (encoded.length > 255) throw new Error(`Card id is too long: ${id}`);
    output.writeUInt8(encoded.length, offset++);
    encoded.copy(output, offset);
    offset += encoded.length;
    const record = records.get(id);
    output.writeUInt32LE(record.norm, offset);
    offset += 4;
    record.vector.copy(output, offset);
    offset += EMBEDDING_DIMENSION;
  }
  return output;
}

async function main() {
  const cards = await loadCards();
  const officialIds = new Set(cards.map(card => card.id));
  const records = new Map([...await loadExisting()].filter(([id]) => officialIds.has(id)));
  const missing = cards.filter(card => !records.has(card.id));
  console.log(`existing ${records.size}, new ${missing.length}`);
  if (!missing.length) return console.log("Embedding index is current.");

  const model = await mobilenet.load({version: 2, alpha: 0.5});
  let sourceDimension = 0;
  let failed = [];
  for (let start = 0; start < missing.length; start += BATCH_SIZE) {
    const result = await embedBatch(model, missing.slice(start, start + BATCH_SIZE));
    sourceDimension ||= result.sourceDimension || 0;
    for (const record of result.records) records.set(record.id, {norm: record.norm, vector: record.vector});
    failed.push(...result.failed);
    if ((start / BATCH_SIZE) % 10 === 0 || start + BATCH_SIZE >= missing.length) {
      console.log(`embedded ${Math.min(start + BATCH_SIZE, missing.length)}/${missing.length}; failed ${failed.length}`);
    }
  }
  model.model?.dispose?.();

  // Retry transient image failures once after the main pass.
  if (failed.length) {
    const failedSet = new Set(failed);
    failed = [];
    const retryCards = cards.filter(card => failedSet.has(card.id));
    const retryModel = await mobilenet.load({version: 2, alpha: 0.5});
    for (let start = 0; start < retryCards.length; start += BATCH_SIZE) {
      const result = await embedBatch(retryModel, retryCards.slice(start, start + BATCH_SIZE));
      sourceDimension ||= result.sourceDimension || 0;
      for (const record of result.records) records.set(record.id, {norm: record.norm, vector: record.vector});
      failed.push(...result.failed);
    }
    retryModel.model?.dispose?.();
  }

  const coverage = records.size / Math.max(1, cards.length);
  if (coverage < MINIMUM_COVERAGE) {
    throw new Error(`Refusing to publish incomplete index: ${(coverage * 100).toFixed(2)}% coverage (${failed.length} failures)`);
  }
  const output = serialize(records, sourceDimension);
  await fs.writeFile(OUTPUT, output);
  console.log(`wrote ${records.size} records, ${(coverage * 100).toFixed(2)}% coverage, ${output.length.toLocaleString()} bytes`);
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
