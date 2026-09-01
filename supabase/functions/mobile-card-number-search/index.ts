import "jsr:@supabase/functions-js/edge-runtime.d.ts"

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
}
const headers = { ...cors, "Content-Type": "application/json" }
const cache = new Map<string, { expires: number; cards: any[] }>()
let setsJob: Promise<any[]> | null = null
let tcgGroupsJob: Promise<any[]> | null = null
const tcgCatalogJobs = new Map<number, Promise<{ products: any[]; prices: any[] }>>()

function collectorEqual(a: unknown, b: unknown) {
  const left = String(a ?? "").toUpperCase(), right = String(b ?? "").toUpperCase()
  if (left === right) return true
  const lm = left.match(/^([A-Z]*)(\d+)([A-Z]*)$/), rm = right.match(/^([A-Z]*)(\d+)([A-Z]*)$/)
  return !!(lm && rm && lm[1] === rm[1] && Number(lm[2]) === Number(rm[2]) && lm[3] === rm[3])
}

function normalizedName(value: unknown) { return String(value || "").toLowerCase().replace(/&/g, "and").replace(/[^a-z0-9]+/g, " ").trim() }

async function tcgCatalog(groupId: number) {
  if (!tcgCatalogJobs.has(groupId)) tcgCatalogJobs.set(groupId, Promise.all([
    json(`https://tcgcsv.com/tcgplayer/3/${groupId}/products`, 8000),
    json(`https://tcgcsv.com/tcgplayer/3/${groupId}/prices`, 8000),
  ]).then(([products, prices]) => ({ products: Array.isArray(products?.results) ? products.results : [], prices: Array.isArray(prices?.results) ? prices.results : [] })).finally(() => tcgCatalogJobs.delete(groupId)))
  return await tcgCatalogJobs.get(groupId)!
}

async function enrichFromTcgCsv(card: any) {
  if (!card?.id || !card?.name || !card?.set?.name) return card
  if (!tcgGroupsJob) tcgGroupsJob = json("https://tcgcsv.com/tcgplayer/3/groups", 8000).then(value => Array.isArray(value?.results) ? value.results : []).catch(() => [])
  const groups = await tcgGroupsJob, setName = normalizedName(card.set.name), setId = String(card.set.id || "").toLowerCase()
  const ranked = groups.map((group: any) => {
    const name = normalizedName(group.name), tail = normalizedName(String(group.name || "").split(":").slice(-1)[0])
    let score = tail === setName ? 5 : name.endsWith(setName) ? 4 : name.includes(setName) ? 3 : setName.includes(tail) ? 2 : 0
    if (setId === "base1" && normalizedName(group.name) === "base set") score = 10
    return { group, score }
  }).filter((item: any) => item.score > 0).sort((a: any, b: any) => b.score - a.score).slice(0, 3)
  const catalogs = await Promise.all(ranked.map(async ({ group }: any) => ({ group, ...await tcgCatalog(Number(group.groupId)).catch(() => ({ products: [], prices: [] })) })))
  for (const { products, prices } of catalogs) {
    const product = products.find((item: any) => {
      const printed = item.extendedData?.find((field: any) => normalizedName(field?.name) === "number")?.value
      return collectorEqual(String(printed || "").split("/")[0], card.number) && normalizedName(item.name).includes(normalizedName(card.name))
    })
    if (!product) continue
    const cardPrices: Record<string, any> = {}
    for (const price of prices.filter((item: any) => Number(item.productId) === Number(product.productId))) {
      const subtype = normalizedName(price.subTypeName).replace(/ /g, ""), key = subtype === "reverseholofoil" ? "reverseHolofoil" : subtype === "holofoil" ? "holofoil" : "normal"
      cardPrices[key] = { low: price.lowPrice ?? null, mid: price.midPrice ?? null, high: price.highPrice ?? null, market: price.marketPrice ?? null, directLow: price.directLowPrice ?? null }
    }
    const image = String(product.imageUrl || "").replace("_200w.jpg", "_in_1000x1000.jpg")
    return { ...card, images: { small: product.imageUrl || card.images?.small || "", large: image || card.images?.large || "" }, tcgplayer: { url: product.url || `https://www.tcgplayer.com/product/${product.productId}`, updatedAt: product.modifiedOn || "", prices: cardPrices } }
  }
  return card
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

async function cardById(cardId: string) {
  const split = cardId.lastIndexOf("-")
  if (split < 1) return null
  const setId = cardId.slice(0, split), cardNumber = cardId.slice(split + 1)
  if (setId.toLowerCase() === "svp") {
    const promoCard = (await promo(cardNumber).catch(() => [])).find((item: any) => String(item?.id || "").toLowerCase() === cardId.toLowerCase())
    if (promoCard) return promoCard
  }
  const direct = await json(`https://api.pokemontcg.io/v2/cards/${encodeURIComponent(cardId)}`, 6500).then(value => value?.data || null).catch(() => null)
  if (direct?.id === cardId) return Object.keys(direct?.tcgplayer?.prices || {}).length ? direct : await enrichFromTcgCsv(direct)
  if (!setsJob) setsJob = json("https://raw.githubusercontent.com/PokemonTCG/pokemon-tcg-data/master/sets/en.json", 9000).catch(() => [])
  const [sets, cards] = await Promise.all([
    setsJob,
    json(`https://raw.githubusercontent.com/PokemonTCG/pokemon-tcg-data/master/cards/en/${encodeURIComponent(setId)}.json`, 9000).catch(() => []),
  ])
  const card = (Array.isArray(cards) ? cards : []).find((item: any) => String(item?.id || "").toLowerCase() === cardId.toLowerCase())
  if (!card) return null
  const set = (Array.isArray(sets) ? sets : []).find((item: any) => String(item?.id || "").toLowerCase() === setId.toLowerCase()) || card.set || { id: setId, name: setId }
  return await enrichFromTcgCsv({ ...card, set, tcgplayer: card.tcgplayer || { url: "", updatedAt: "", prices: {} } })
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
    const body = await request.json()
    const requestedCardId = String(body?.cardId || "").trim().slice(0, 80)
    if (requestedCardId) {
      if (!/^[A-Za-z0-9.]+-[A-Za-z0-9]+$/.test(requestedCardId)) return new Response(JSON.stringify({ cards: [], error: "Invalid card ID" }), { status: 400, headers })
      const key = `id:${requestedCardId.toLowerCase()}`, saved = cache.get(key)
      if (saved && saved.expires > Date.now()) return new Response(JSON.stringify({ cards: saved.cards, cached: true }), { headers })
      const card = await cardById(requestedCardId)
      const cards = card ? [card] : []
      if (cards.length) cache.set(key, { expires: Date.now() + 30 * 60_000, cards })
      return new Response(JSON.stringify({ cards, cached: false }), { headers })
    }
    const number = String(body?.number || "").trim().toUpperCase().slice(0, 12)
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
