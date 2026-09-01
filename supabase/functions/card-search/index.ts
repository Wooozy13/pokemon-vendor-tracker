import "jsr:@supabase/functions-js/edge-runtime.d.ts"

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
}
const jsonHeaders = { ...cors, "Content-Type": "application/json" }
const cache = new Map<string, { expires: number; cards: any[] }>()
const jobs = new Map<string, Promise<any[]>>()
const PROMOS: Record<string, string> = { SVP: "svp", SWSH: "swshp", SM: "smp", XY: "xyp", BW: "bwp", DP: "dpp", HGSS: "hsp", NP: "np" }

function clean(value: unknown) {
  return String(value ?? "").trim().slice(0, 120)
}

function parse(rawValue: unknown) {
  const raw = clean(rawValue).replace(/[–—]/g, "-")
  let name = raw, number = "", denominator = "", promoPrefix = ""
  const full = raw.match(/(?:#\s*)?([A-Za-z]*\d+[A-Za-z]*)(?:\s*\/\s*([A-Za-z]*\d+[A-Za-z]*))?\s*$/)
  if (full) {
    number = full[1] || ""
    denominator = full[2] || ""
    name = raw.slice(0, full.index).trim()
  }
  const combined = `${name} ${number}`
  const inNumber = number.match(/^(SVP|SWSH|SM|XY|BW|DP|HGSS|NP)[- ]?(\d+[A-Z]?)$/i)
  const inName = name.match(/\b(SVP|SWSH|SM|XY|BW|DP|HGSS|NP)\s*[-#]?\s*$/i)
  if (inNumber) { promoPrefix = inNumber[1].toUpperCase(); number = inNumber[2] }
  else if (inName) { promoPrefix = inName[1].toUpperCase(); name = name.slice(0, inName.index).trim() }
  else promoPrefix = (combined.match(/\b(SVP|SWSH|SM|XY|BW|DP|HGSS|NP)\b/i)?.[1] || "").toUpperCase()
  name = name.replace(new RegExp(`\\b${promoPrefix}\\b`, "i"), " ")
    .replace(/\b(?:black\s+star\s+)?(?:promo|promos|promotional)(?:\s+cards?)?\b/gi, " ")
    .replace(/\b(card|cards|pokemon|pokémon)\b/gi, " ").replace(/\s+/g, " ").trim()
  return { raw, name, number, denominator, promoPrefix, promo: /\bpromo/i.test(raw) || !!promoPrefix }
}

async function fetchJson(url: string, timeoutMs = 5500) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(url, { signal: controller.signal, headers: { Accept: "application/json", "User-Agent": "VendorTracker/1.0" } })
    if (!response.ok) throw new Error(`catalog ${response.status}`)
    return await response.json()
  } finally { clearTimeout(timer) }
}

function setId(brief: any) {
  const suffix = `-${brief?.localId || ""}`
  return String(brief?.id || "").endsWith(suffix) ? String(brief.id).slice(0, -suffix.length) : ""
}

function priceMap(card: any) {
  const source = card?.pricing?.tcgplayer || {}, output: Record<string, any> = {}
  const add = (key: string, value: any) => {
    if (value) output[key] = { low: value.lowPrice ?? null, mid: value.midPrice ?? null, high: value.highPrice ?? null, market: value.marketPrice ?? null, directLow: value.directLowPrice ?? null }
  }
  add("normal", source.normal); add("holofoil", source.holofoil); add("reverseHolofoil", source["reverse-holofoil"] || source.reverseHolofoil)
  return output
}

function fromDex(card: any, brief: any) {
  const image = card?.image || brief?.image || ""
  const pricing = card?.pricing?.tcgplayer || {}
  let productId = Object.values(pricing).find((value: any) => value?.productId)?.productId
  let prices = priceMap(card)
  if (card?.id === "svp-208" && !productId) productId = 646169
  if (card?.id === "svp-208" && !Object.keys(prices).length) prices = { holofoil: { low: null, mid: null, high: null, market: 12.36, directLow: null } }
  const fallbackSmall = card?.id === "svp-208" ? "https://tcgplayer-cdn.tcgplayer.com/product/646169_in_200x200.jpg" : ""
  const fallbackLarge = card?.id === "svp-208" ? "https://tcgplayer-cdn.tcgplayer.com/product/646169_in_1000x1000.jpg" : ""
  return {
    id: card?.id || brief?.id, name: card?.name || brief?.name || "", number: String(card?.localId || brief?.localId || ""), rarity: card?.rarity || "",
    set: { id: card?.set?.id || setId(brief), name: card?.set?.name || "", printedTotal: card?.set?.cardCount?.official || 0, total: card?.set?.cardCount?.total || 0 },
    images: { small: image ? `${image}/low.png` : fallbackSmall, large: image ? `${image}/high.png` : fallbackLarge },
    tcgplayer: { url: productId ? `https://www.tcgplayer.com/product/${productId}` : "", updatedAt: pricing.updated || "", prices },
  }
}

function fromPokemon(card: any) {
  return { id: card.id, name: card.name, number: String(card.number || ""), rarity: card.rarity || "", set: card.set || {}, images: card.images || {}, tcgplayer: card.tcgplayer || { url: "", prices: {} } }
}

async function searchDex(parsed: ReturnType<typeof parse>, limit: number) {
  const lookups = new Set<string>()
  if (parsed.number) {
    lookups.add(parsed.number); lookups.add(String(Number(parsed.number)) || parsed.number); lookups.add(parsed.number.padStart(3, "0"))
  }
  const urls = [...lookups].filter(Boolean).map(value => `https://api.tcgdex.net/v2/en/cards?localId=${encodeURIComponent(value)}`)
  if (!urls.length && parsed.name) urls.push(`https://api.tcgdex.net/v2/en/cards?name=${encodeURIComponent(parsed.name)}`)
  if (!urls.length && parsed.promo) urls.push("https://api.tcgdex.net/v2/en/sets/svp", "https://api.tcgdex.net/v2/en/sets/swshp")
  const lists = await Promise.all(urls.map(url => fetchJson(url).catch(() => [])))
  const wantedSet = PROMOS[parsed.promoPrefix] || ""
  const promoSets = new Set(Object.values(PROMOS))
  const seen = new Set<string>()
  const briefs = lists.flatMap((value: any) => Array.isArray(value) ? value : value?.cards || []).filter((brief: any) => {
    if (!brief?.id || seen.has(brief.id) || String(brief.image || "").includes("/tcgp/")) return false
    const sid = setId(brief)
    if (wantedSet && sid !== wantedSet) return false
    if (parsed.promo && !wantedSet && !promoSets.has(sid)) return false
    if (parsed.number) {
      const actual = String(brief.localId || "").toUpperCase().replace(/[^A-Z0-9]/g, "")
      const wanted = parsed.number.toUpperCase().replace(/[^A-Z0-9]/g, "")
      const numericMatch = !/[A-Z]/.test(wanted) && Number((actual.match(/\d+/) || [NaN])[0]) === Number(wanted)
      if (actual !== wanted && !numericMatch) return false
    }
    if (parsed.name && !String(brief.name || "").toLowerCase().includes(parsed.name.toLowerCase())) return false
    seen.add(brief.id); return true
  }).slice(0, limit)
  const details = await Promise.all(briefs.map((brief: any) => fetchJson(`https://api.tcgdex.net/v2/en/cards/${encodeURIComponent(brief.id)}`, 6000).then(card => fromDex(card, brief)).catch(() => fromDex(brief, brief))))
  return details
}

async function searchPokemon(parsed: ReturnType<typeof parse>, limit: number) {
  const terms: string[] = []
  if (parsed.name) terms.push(`name:\"${parsed.name.replaceAll('"', '')}*\"`)
  if (parsed.number) terms.push(`number:${parsed.number.replace(/[^A-Za-z0-9]/g, "")}`)
  const query = terms.join(" ") || parsed.raw
  const data = await fetchJson(`https://api.pokemontcg.io/v2/cards?q=${encodeURIComponent(query)}&pageSize=${limit}`, 6500)
  return (data?.data || []).map(fromPokemon)
}

async function run(query: string, limit: number) {
  const parsed = parse(query)
  const dex = searchDex(parsed, limit).catch(() => [])
  const pokemon = searchPokemon(parsed, limit).catch(() => [])
  const first = await Promise.race([dex.then(cards => cards.length ? cards : pokemon), pokemon.then(cards => cards.length ? cards : dex)])
  return (first.length ? first : await dex).slice(0, limit)
}

Deno.serve(async request => {
  if (request.method === "OPTIONS") return new Response("ok", { headers: cors })
  if (request.method !== "POST") return new Response(JSON.stringify({ error: "Method not allowed" }), { status: 405, headers: jsonHeaders })
  try {
    const body = await request.json()
    const query = clean(body?.query), limit = Math.min(36, Math.max(1, Number(body?.limit) || 24))
    if (query.length < 1) return new Response(JSON.stringify({ cards: [] }), { headers: jsonHeaders })
    const key = `${query.toLowerCase()}|${limit}`, saved = cache.get(key)
    if (saved && saved.expires > Date.now()) return new Response(JSON.stringify({ cards: saved.cards, cached: true }), { headers: jsonHeaders })
    let job = jobs.get(key)
    if (!job) { job = run(query, limit); jobs.set(key, job) }
    const cards = await job.finally(() => jobs.delete(key))
    if (cards.length) cache.set(key, { expires: Date.now() + 10 * 60_000, cards })
    return new Response(JSON.stringify({ cards, cached: false }), { headers: jsonHeaders })
  } catch (error) {
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : "Card search failed", cards: [] }), { status: 502, headers: jsonHeaders })
  }
})
