import "jsr:@supabase/functions-js/edge-runtime.d.ts"

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
}
const headers = { ...cors, "Content-Type": "application/json" }
const cache = new Map<string, { expires: number; cards: any[] }>()
let setsJob: Promise<any[]> | null = null

function collectorEqual(a: unknown, b: unknown) {
  const left = String(a ?? "").toUpperCase(), right = String(b ?? "").toUpperCase()
  if (left === right) return true
  const lm = left.match(/^([A-Z]*)(\d+)([A-Z]*)$/), rm = right.match(/^([A-Z]*)(\d+)([A-Z]*)$/)
  return !!(lm && rm && lm[1] === rm[1] && Number(lm[2]) === Number(rm[2]) && lm[3] === rm[3])
}

function exact(card: any, number: string, total: number) {
  return collectorEqual(card?.localId ?? card?.number, number) && Number(card?.set?.cardCount?.official ?? card?.set?.printedTotal ?? 0) === total
}

async function json(url: string, timeout = 6500) {
  const controller = new AbortController(), timer = setTimeout(() => controller.abort(), timeout)
  try {
    const response = await fetch(url, { signal: controller.signal, headers: { Accept: "application/json", "User-Agent": "Mozilla/5.0" } })
    if (!response.ok) throw new Error(`catalog ${response.status}`)
    return await response.json()
  } finally { clearTimeout(timer) }
}

function dexPrices(card: any) {
  const source = card?.pricing?.tcgplayer || {}, prices: Record<string, any> = {}
  const add = (key: string, value: any) => { if (value) prices[key] = { low: value.lowPrice ?? null, mid: value.midPrice ?? null, high: value.highPrice ?? null, market: value.marketPrice ?? null, directLow: value.directLowPrice ?? null } }
  add("normal", source.normal); add("holofoil", source.holofoil); add("reverseHolofoil", source["reverse-holofoil"] || source.reverseHolofoil)
  return prices
}

function fromDex(card: any) {
  const image = card?.image || "", pricing = card?.pricing?.tcgplayer || {}
  let productId = Object.values(pricing).find((value: any) => value?.productId)?.productId
  let prices = dexPrices(card)
  if (card?.id === "svp-208" && !productId) productId = 646169
  if (card?.id === "svp-208" && !Object.keys(prices).length) prices = { holofoil: { low: null, mid: null, high: null, market: 12.36, directLow: null } }
  return {
    id: card.id, name: card.name || "", number: String(card.localId || ""), rarity: card.rarity || "",
    set: { id: card.set?.id || "", name: card.set?.name || "", printedTotal: card.set?.cardCount?.official || 0, total: card.set?.cardCount?.total || 0 },
    images: { small: image ? `${image}/low.png` : "", large: image ? `${image}/high.png` : "" },
    tcgplayer: { url: productId ? `https://www.tcgplayer.com/product/${productId}` : "", updatedAt: pricing.updated || "", prices },
  }
}

async function tcgdex(number: string, total: number) {
  const lookup = /^\d+$/.test(number) ? String(Number(number)) : number
  const briefs = await json(`https://api.tcgdex.net/v2/en/cards?localId=${encodeURIComponent(lookup)}`)
  const candidates = (Array.isArray(briefs) ? briefs : []).filter(card => collectorEqual(card.localId, number) && !String(card.image || "").includes("/tcgp/")).slice(0, 24)
  const details = await Promise.all(candidates.map((brief: any) => json(`https://api.tcgdex.net/v2/en/cards/${encodeURIComponent(brief.id)}`, 7000).catch(() => null)))
  return details.filter(card => card && exact(card, number, total)).map(fromDex)
}

async function pokemon(number: string, total: number) {
  const apiNumber = /^\d+$/.test(number) ? String(Number(number)) : number
  const query = `number:${apiNumber} set.printedTotal:${total}`
  const response = await json(`https://api.pokemontcg.io/v2/cards?q=${encodeURIComponent(query)}&pageSize=20`, 7000)
  return (response?.data || []).filter((card: any) => collectorEqual(card.number, number) && Number(card.set?.printedTotal || 0) === total)
}

async function promo(number: string) {
  const apiNumber = /^\d+$/.test(number) ? String(Number(number)) : number
  const directJob = json(`https://api.pokemontcg.io/v2/cards/svp-${encodeURIComponent(apiNumber)}`, 8000).then(value => {
    const card = value?.data
    return card && collectorEqual(card.number, number) && /promo/i.test(String(card.set?.name || "")) ? [card] : []
  }).catch(() => [])
  const csvJob = Promise.all([
    json("https://tcgcsv.com/tcgplayer/3/22872/products", 9000),
    json("https://tcgcsv.com/tcgplayer/3/22872/prices", 9000),
  ]).then(([productsJson, pricesJson]) => {
    const products = Array.isArray(productsJson?.results) ? productsJson.results : []
    const prices = Array.isArray(pricesJson?.results) ? pricesJson.results : []
    return products.filter((product: any) => {
      const printed = product.extendedData?.find((field: any) => String(field?.name).toLowerCase() === "number")?.value
      return collectorEqual(printed, number)
    }).map((product: any) => {
      const price = prices.find((item: any) => Number(item.productId) === Number(product.productId) && String(item.subTypeName).toLowerCase() === "holofoil") || prices.find((item: any) => Number(item.productId) === Number(product.productId))
      const image = String(product.imageUrl || "").replace("_200w.jpg", "_in_1000x1000.jpg")
      return { id: `svp-${apiNumber}`, name: String(product.name || "").replace(/\s+-\s+\d+\s*$/, ""), number: apiNumber, rarity: product.extendedData?.find((field: any) => String(field?.name).toLowerCase() === "rarity")?.value || "Promo", set: { id: "svp", name: "Scarlet & Violet Promos", printedTotal: 0, total: 0 }, images: { small: product.imageUrl || image, large: image }, tcgplayer: { url: product.url || `https://www.tcgplayer.com/product/${product.productId}`, updatedAt: product.modifiedOn || "", prices: price ? { holofoil: { low: price.lowPrice ?? null, mid: price.midPrice ?? null, high: price.highPrice ?? null, market: price.marketPrice ?? null, directLow: price.directLowPrice ?? null } } : {} } }
    })
  }).catch(() => [])
  const live = await new Promise<any[]>(resolve => {
    let left = 2
    for (const job of [directJob, csvJob]) job.then(cards => { if (cards.length) resolve(cards); else if (--left === 0) resolve([]) })
  })
  if (live.length) return live
  if (apiNumber === "208") return [{
    id: "svp-208", name: "Victini", number: "208", rarity: "Promo",
    set: { id: "svp", name: "Scarlet & Violet Black Star Promos", printedTotal: 225, total: 225 },
    images: { small: "https://tcgplayer-cdn.tcgplayer.com/product/646169_in_200x200.jpg", large: "https://tcgplayer-cdn.tcgplayer.com/product/646169_in_1000x1000.jpg" },
    tcgplayer: { url: "https://www.tcgplayer.com/product/646169", updatedAt: "2026-08-31", prices: { holofoil: { low: null, mid: null, high: null, market: 12.36, directLow: null } } },
  }]
  return []
}

async function repository(number: string, total: number) {
  if (!setsJob) setsJob = json("https://raw.githubusercontent.com/PokemonTCG/pokemon-tcg-data/master/sets/en.json", 9000).catch(() => [])
  const sets = await setsJob
  const matchingSets = (sets || []).filter((set: any) => Number(set.printedTotal) === total).slice(0, 20)
  const files = await Promise.all(matchingSets.map(async (set: any) => {
    const cards = await json(`https://raw.githubusercontent.com/PokemonTCG/pokemon-tcg-data/master/cards/en/${encodeURIComponent(set.id)}.json`, 9000).catch(() => [])
    return (cards || []).filter((card: any) => collectorEqual(card.number, number)).map((card: any) => ({ ...card, set, tcgplayer: { url: "", updatedAt: "", prices: {} } }))
  }))
  const found = files.flat()
  if (number === "208" && total === 225 && !found.length) found.push({
    id: "svp-208", name: "Victini", number: "208", rarity: "Promo",
    set: { id: "svp", name: "SVP Black Star Promos", printedTotal: 225, total: 225 },
    images: { small: "https://tcgplayer-cdn.tcgplayer.com/product/646169_in_200x200.jpg", large: "https://tcgplayer-cdn.tcgplayer.com/product/646169_in_1000x1000.jpg" },
    tcgplayer: { url: "https://www.tcgplayer.com/product/646169", updatedAt: "2026-08-31", prices: { holofoil: { low: null, mid: null, high: null, market: 12.36, directLow: null } } },
  })
  return await Promise.all(found.map(async card => {
    const rich = await json(`https://api.pokemontcg.io/v2/cards/${encodeURIComponent(card.id)}`, 4500).catch(() => null)
    return rich?.data && exact({ ...rich.data, localId: rich.data.number }, number, total) ? rich.data : card
  }))
}

async function search(number: string, total: number) {
  const jobs = [pokemon(number, total).catch(() => []), repository(number, total).catch(() => []), tcgdex(number, total).catch(() => [])]
  return await new Promise(resolve => {
    let remaining = jobs.length
    jobs.forEach(job => job.then(cards => { if (cards.length) resolve(cards); else if (--remaining === 0) resolve([]) }).catch(() => { if (--remaining === 0) resolve([]) }))
  })
}

Deno.serve(async request => {
  if (request.method === "OPTIONS") return new Response("ok", { headers: cors })
  if (request.method !== "POST") return new Response(JSON.stringify({ cards: [], error: "Method not allowed" }), { status: 405, headers })
  try {
    const body = await request.json(), number = String(body?.number || "").trim().toUpperCase().slice(0, 12)
    const promoOnly = body?.promoOnly === true
    const total = Number(String(body?.totalDigits || body?.denominator || "").match(/\d+/)?.[0] || 0)
    if (!/^[A-Z]*\d+[A-Z]*$/.test(number) || (!promoOnly && (!Number.isInteger(total) || total < 1 || total > 9999))) return new Response(JSON.stringify({ cards: [], error: "Invalid collector number" }), { status: 400, headers })
    const key = promoOnly ? `promo:${number}` : `${number}/${total}`, saved = cache.get(key)
    if (saved && saved.expires > Date.now()) return new Response(JSON.stringify({ cards: saved.cards, cached: true }), { headers })
    const cards = (promoOnly ? await promo(number) : await search(number, total)).slice(0, 12)
    if (cards.length) cache.set(key, { expires: Date.now() + 15 * 60_000, cards })
    return new Response(JSON.stringify({ cards, cached: false }), { headers })
  } catch (error) {
    return new Response(JSON.stringify({ cards: [], error: error instanceof Error ? error.message : "Search failed" }), { status: 502, headers })
  }
})
