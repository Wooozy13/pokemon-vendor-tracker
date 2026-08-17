#!/usr/bin/env python3
"""Update VendorTracker's compact, artwork-only Pokémon card scan index.

The committed RBX1 file contains one 64-bit dHash and one 64-bit pHash for
each official card image. Re-running this script keeps existing fingerprints
and downloads only cards that are new to the Pokémon TCG API.
"""

from __future__ import annotations

import io
import base64
import json
import math
import struct
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image


API = "https://api.pokemontcg.io/v2/cards"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "pokemon-card-visual-index.bin"
CACHE_DIR = Path("/tmp/vendortracker-card-index-pages")
FINGERPRINT_CACHE_DIR = Path("/tmp/vendortracker-card-rbx1-fingerprints")
FAILED_OUTPUT = OUTPUT.with_name("pokemon-card-visual-index-failed.txt")
WEB_PART_SIZE = 96_000
PAGE_SIZE = 250
WORKERS = 32


def request_bytes(url: str, timeout: int = 30) -> bytes:
    last_error: Exception | None = None
    for attempt in range(4):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "VendorTracker visual-index builder/2.0", "Accept": "application/json,image/*"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as error:
            last_error = error
            if attempt < 3:
                time.sleep(0.75 * (attempt + 1))
    raise last_error or RuntimeError("request failed")


def load_cards() -> list[dict]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def load_page(page: int) -> dict:
        params = urllib.parse.urlencode({"page": page, "pageSize": PAGE_SIZE, "select": "id,images"})
        cache_file = CACHE_DIR / f"page-{page}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
        raw = request_bytes(f"{API}?{params}")
        cache_file.write_bytes(raw)
        return json.loads(raw.decode("utf-8"))

    first = load_page(1)
    total = int(first.get("totalCount") or len(first.get("data") or []))
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    payloads: dict[int, dict] = {1: first}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(load_page, page): page for page in range(2, pages + 1)}
        for future in as_completed(futures):
            payloads[futures[future]] = future.result()
    cards: list[dict] = []
    for page in range(1, pages + 1):
        cards.extend(payloads[page].get("data") or [])
    print(f"metadata {len(cards)}/{total}", flush=True)
    return cards


def load_existing() -> dict[str, tuple[int, int]]:
    if OUTPUT.exists():
        data = OUTPUT.read_bytes()
    else:
        parts = sorted(
            OUTPUT.parent.glob("pokemon-card-visual-index.part*.txt"),
            key=lambda path: int(path.stem.split("part")[-1]),
        )
        if not parts:
            return {}
        data = base64.b64decode("".join(path.read_text(encoding="ascii") for path in parts))
    if data[:4] != b"RBX1" or len(data) < 8:
        raise ValueError(f"Unsupported visual index: {OUTPUT}")
    count = struct.unpack_from("<I", data, 4)[0]
    offset = 8
    records: dict[str, tuple[int, int]] = {}
    for _ in range(count):
        id_length = data[offset]
        offset += 1
        card_id = data[offset:offset + id_length].decode("utf-8")
        offset += id_length
        dhash, phash = struct.unpack_from("<QQ", data, offset)
        offset += 16
        records[card_id] = (dhash, phash)
    return records


def grayscale(image: Image.Image, width: int, height: int) -> list[list[float]]:
    resized = image.resize((width, height), Image.Resampling.BILINEAR)
    pixels = resized.load()
    return [
        [0.299 * pixels[x, y][0] + 0.587 * pixels[x, y][1] + 0.114 * pixels[x, y][2] for x in range(width)]
        for y in range(height)
    ]


def dhash64(image: Image.Image) -> int:
    gray = grayscale(image, 9, 8)
    value = 0
    for y in range(8):
        for x in range(8):
            value = (value << 1) | int(gray[y][x] > gray[y][x + 1])
    return value


COSINES = [[math.cos((2 * x + 1) * u * math.pi / 64) for x in range(32)] for u in range(8)]


def phash64(image: Image.Image) -> int:
    gray = grayscale(image, 32, 32)
    block: list[float] = []
    for v in range(8):
        for u in range(8):
            block.append(sum(gray[y][x] * COSINES[u][x] * COSINES[v][y] for y in range(32) for x in range(32)))
    median = sorted(block[1:])[len(block[1:]) // 2]
    value = 0
    for coefficient in block:
        value = (value << 1) | int(coefficient > median)
    return value


def fingerprint(card: dict) -> tuple[str, int, int] | None:
    card_id = str(card.get("id") or "").strip()
    source = str((card.get("images") or {}).get("small") or "").strip()
    if not card_id or not source:
        return None
    FINGERPRINT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = FINGERPRINT_CACHE_DIR / (urllib.parse.quote(card_id, safe="") + ".json")
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(cached, list) and len(cached) == 3 and cached[0] == card_id:
                return card_id, int(cached[1]), int(cached[2])
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    source_without_scheme = source.removeprefix("https://").removeprefix("http://")
    thumbnail = "https://images.weserv.nl/?" + urllib.parse.urlencode(
        {"url": source_without_scheme, "w": 192, "h": 268, "fit": "cover", "output": "webp", "q": 70}
    )
    for candidate in (thumbnail, source):
        try:
            image = Image.open(io.BytesIO(request_bytes(candidate))).convert("RGB")
            result = card_id, dhash64(image), phash64(image)
            cache_file.write_text(json.dumps(result, separators=(",", ":")), encoding="utf-8")
            return result
        except Exception:
            continue
    return None


def write_index(records: dict[str, tuple[int, int]]) -> None:
    output = bytearray(b"RBX1")
    output.extend(struct.pack("<I", len(records)))
    for card_id in sorted(records):
        encoded = card_id.encode("utf-8")
        if len(encoded) > 255:
            raise ValueError(f"Card id is too long: {card_id}")
        output.extend(struct.pack("<B", len(encoded)))
        output.extend(encoded)
        output.extend(struct.pack("<QQ", *records[card_id]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(output)
    encoded = base64.b64encode(output).decode("ascii")
    parts = [encoded[index:index + WEB_PART_SIZE] for index in range(0, len(encoded), WEB_PART_SIZE)]
    for old_part in OUTPUT.parent.glob("pokemon-card-visual-index.part*.txt"):
        old_part.unlink()
    for index, part in enumerate(parts):
        OUTPUT.with_name(f"pokemon-card-visual-index.part{index}.txt").write_text(part, encoding="ascii")
    print(f"wrote {len(parts)} web parts", flush=True)


def main() -> None:
    cards = load_cards()
    official = {str(card.get("id") or ""): card for card in cards if card.get("id")}
    records = {card_id: hashes for card_id, hashes in load_existing().items() if card_id in official}
    missing = [card for card_id, card in official.items() if card_id not in records]
    print(f"existing {len(records)}, new {len(missing)}", flush=True)
    failed: list[str] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(fingerprint, card): card for card in missing}
        for completed, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                records[result[0]] = (result[1], result[2])
            else:
                failed.append(str(futures[future].get("id") or ""))
            if completed % 25 == 0 or completed == len(missing):
                print(f"new images {completed}/{len(missing)}, failed {len(failed)}", flush=True)
    write_index(records)
    print(f"wrote {len(records)} records -> {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)", flush=True)
    if failed:
        FAILED_OUTPUT.write_text("\n".join(failed) + "\n", encoding="utf-8")
    elif FAILED_OUTPUT.exists():
        FAILED_OUTPUT.unlink()


if __name__ == "__main__":
    main()
