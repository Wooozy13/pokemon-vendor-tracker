import "jsr:@supabase/functions-js/edge-runtime.d.ts"

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
}
const jsonHeaders = { ...cors, "Content-Type": "application/json", "Connection": "keep-alive" }
const UA = "VendorTracker/1.1 (sealed catalog search)"
const TCGPLAYER_BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
const CACHE_MS = 24 * 60 * 60 * 1000
const LISTING_CACHE_MS = 15 * 60 * 1000
const groupCatalogCache = new Map<number, { time: number; products: any[]; prices: any[] }>()
const groupCatalogJobs = new Map<number, Promise<{ products: any[]; prices: any[] }>>()
const listingCache = new Map<number, { time: number; value: any }>()
const listingJobs = new Map<number, Promise<any>>()
let groupsCache: { time: number; groups: any[] } | null = null
let groupsJob: Promise<any[]> | null = null

function norm(value: unknown) {
  return String(value ?? "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim().replace(/\s+/g, " ")
}

function tokens(value: string) {
  return norm(value).split(" ").filter((token) => token.length >= 2)
}

function scoreText(text: string, query: string) {
  const normalizedText = norm(text)
  const normalizedQuery = norm(query)
  if (!normalizedText || !normalizedQuery) return 0
  let score = 0
  if (normalizedText === normalizedQuery) score += 500
  if (normalizedText.includes(normalizedQuery)) score += 220
  for (const token of tokens(normalizedQuery)) {
    if (normalizedText.split(" ").includes(token)) score += 35
    else if (normalizedText.includes(token)) score += 18
  }
  return score
}

function looksSealed(product: any) {
  const extended = Array.isArray(product?.extendedData) ? product.extendedData : []
  const fields = new Set(extended.map((item: any) => String(item?.name || "").toLowerCase()))
  if (fields.has("number") || fields.has("rarity")) return false
  const name = norm(product?.name)
  const words = ["booster box", "booster pack", "booster bundle", "elite trainer box", "etb", "collection", "box", "tin", "blister", "bundle", "display", "case", "deck", "kit", "poster", "binder", "sticker", "premium collection", "ultra premium", "upc"]
  return words.some((word) => name.includes(norm(word)))
}

async function fetchJson(url: string) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 12_000)
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: { "User-Agent": UA, "Accept": "application/json", "Connection": "keep-alive" },
    })
    if (!response.ok) throw new Error(`TCGCSV ${response.status}`)
    return await response.json()
  } finally {
    clearTimeout(timeout)
  }
}

function finiteMoney(value: unknown) {
  const amount = Number(value)
  return Number.isFinite(amount) && amount >= 0 ? Math.round(amount * 100) / 100 : null
}

async function fetchLowestActualListing(productId: number) {
  if (!Number.isInteger(productId) || productId <= 0) throw new Error("Invalid TCGplayer product ID")
  const cached = listingCache.get(productId)
  if (cached && Date.now() - cached.time < LISTING_CACHE_MS) return cached.value
  const running = listingJobs.get(productId)
  if (running) return running

  const job = (async () => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 12_000)
    try {
      const response = await fetch(`https://mp-search-api.tcgplayer.com/v1/product/${productId}/listings`, {
        method: "POST",
        signal: controller.signal,
        headers: {
          "User-Agent": TCGPLAYER_BROWSER_UA,
          "Accept": "application/json",
          "Content-Type": "application/json",
          "Origin": "https://www.tcgplayer.com",
          "Referer": `https://www.tcgplayer.com/product/${productId}/`,
        },
        body: JSON.stringify({
          from: 0,
          size: 50,
          sort: { field: "price+shipping", order: "asc" },
        }),
      })
      if (!response.ok) throw new Error(`TCGplayer listings ${response.status}`)
      const json = await response.json()
      const raw = Array.isArray(json?.results?.[0]?.results) ? json.results[0].results : []

      // A standard catalog listing has no seller-written replacement title. Requiring
      // it prevents cheap custom listings such as empty boxes, dice-only, damaged seals,
      // foreign substitutes, or products broken down into individual contents.
      const candidates = raw.filter((listing: any) => {
        if (Number(listing?.productId) !== productId) return false
        if (String(listing?.listingType || "").toLowerCase() !== "standard") return false
        if (listing?.languageId != null && Number(listing.languageId) !== 1) return false
        if (listing?.language && String(listing.language).toLowerCase() !== "english") return false
        if (String(listing?.condition || "").toLowerCase() !== "unopened") return false
        return finiteMoney(listing?.price ?? listing?.sellerPrice) != null
      }).map((listing: any) => {
        const price = finiteMoney(listing.price ?? listing.sellerPrice)!
        const shipping = finiteMoney(listing.shippingPrice ?? listing.sellerShippingPrice ?? listing.rankedShippingPrice) ?? 0
        return {
          price,
          shipping,
          delivered: Math.round((price + shipping) * 100) / 100,
          seller: String(listing.sellerName || ""),
          sellerRating: finiteMoney(listing.sellerRating),
          sellerSales: String(listing.sellerSales || ""),
          quantity: Math.max(0, Number(listing.quantity || 0)),
          condition: "Unopened",
          listingId: listing.listingId ?? null,
          checkedAt: new Date().toISOString(),
          source: "TCGplayer standard unopened listing",
        }
      }).sort((a: any, b: any) => a.delivered - b.delivered || a.price - b.price)

      const value = candidates[0] || null
      listingCache.set(productId, { time: Date.now(), value })
      return value
    } finally {
      clearTimeout(timeout)
    }
  })().finally(() => listingJobs.delete(productId))

  listingJobs.set(productId, job)
  return job
}

async function getGroups() {
  if (groupsCache && Date.now() - groupsCache.time < CACHE_MS) return groupsCache.groups
  if (groupsJob) return groupsJob
  groupsJob = fetchJson("https://tcgcsv.com/tcgplayer/3/groups").then((json) => {
    const groups = Array.isArray(json?.results) ? json.results : []
    if (!groups.length) throw new Error("No Pokemon groups returned")
    groupsCache = { time: Date.now(), groups }
    return groups
  }).finally(() => { groupsJob = null })
  return groupsJob
}

async function getGroupCatalog(groupId: number) {
  const cached = groupCatalogCache.get(groupId)
  if (cached && Date.now() - cached.time < CACHE_MS) return cached
  const running = groupCatalogJobs.get(groupId)
  if (running) return running
  const job = Promise.all([
    fetchJson(`https://tcgcsv.com/tcgplayer/3/${groupId}/products`),
    fetchJson(`https://tcgcsv.com/tcgplayer/3/${groupId}/prices`),
  ]).then(([productsJson, pricesJson]) => {
    const value = {
      time: Date.now(),
      products: Array.isArray(productsJson?.results) ? productsJson.results : [],
      prices: Array.isArray(pricesJson?.results) ? pricesJson.results : [],
    }
    groupCatalogCache.set(groupId, value)
    return value
  }).finally(() => groupCatalogJobs.delete(groupId))
  groupCatalogJobs.set(groupId, job)
  return job
}

async function mapLimit<T, R>(items: T[], limit: number, worker: (item: T) => Promise<R>) {
  const results = new Array<R>(items.length)
  let next = 0
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (true) {
      const index = next++
      if (index >= items.length) return
      results[index] = await worker(items[index])
    }
  }))
  return results
}

function newestGroups(groups: any[], count: number) {
  return [...groups].sort((a, b) => Date.parse(b.publishedOn || "") - Date.parse(a.publishedOn || "")).slice(0, count)
}

async function searchGroups(groups: any[], query: string) {
  const batches = await mapLimit(groups, 5, async (group) => {
    try {
      const { products, prices } = await getGroupCatalog(Number(group.groupId))
      return { group, products, prices }
    } catch {
      return { group, products: [], prices: [] }
    }
  })
  const results: any[] = []
  for (const { group, products, prices } of batches) {
    const priceMap = new Map<number, any[]>()
    for (const price of prices) {
      if (!priceMap.has(price.productId)) priceMap.set(price.productId, [])
      priceMap.get(price.productId)!.push(price)
    }
    for (const product of products) {
      if (!looksSealed(product)) continue
      const score = scoreText(product.name, query) + scoreText(group.name, query) * 0.35
      if (score < 35) continue
      const productPrices = priceMap.get(product.productId) || []
      const best = productPrices.find((item: any) => norm(item.subTypeName) === "normal" && item.marketPrice != null)
        || productPrices.find((item: any) => item.marketPrice != null)
        || productPrices[0]
        || null
      results.push({
        productId: product.productId,
        name: product.name,
        groupId: group.groupId,
        groupName: group.name,
        imageUrl: String(product.imageUrl || "").replace("_200w.jpg", "_in_1000x1000.jpg"),
        url: product.url,
        marketPrice: best?.marketPrice ?? null,
        lowPrice: best?.lowPrice ?? null,
        subTypeName: best?.subTypeName ?? "Normal",
        updatedAt: product.modifiedOn ?? null,
        score,
      })
    }
  }
  return results
}

function finalize(results: any[]) {
  results.sort((a, b) => b.score - a.score)
  const unique: any[] = []
  const seen = new Set<number>()
  for (const result of results) {
    if (seen.has(result.productId)) continue
    seen.add(result.productId)
    unique.push(result)
    if (unique.length >= 40) break
  }
  return unique
}

Deno.serve(async (request: Request) => {
  if (request.method === "OPTIONS") return new Response("ok", { headers: cors })
  const started = Date.now()
  try {
    const body = await request.json()
    const { query } = body
    const productId = Number(body?.productId)
    if (body?.action === "lowest-listing") {
      const lowestActual = await fetchLowestActualListing(productId)
      return Response.json({ success: true, lowestActual, checkedAt: new Date().toISOString() }, { headers: jsonHeaders })
    }
    if (!query || !String(query).trim()) return Response.json({ success: false, error: "Missing query" }, { status: 400, headers: jsonHeaders })
    const cleanQuery = String(query).trim()
    const groups = await getGroups()
    const ranked = groups.map((group: any) => ({ ...group, _score: scoreText(group.name, cleanQuery) })).sort((a: any, b: any) => b._score - a._score)
    const likely = ranked.filter((group: any) => group._score > 0).slice(0, 8)
    const selected = new Map<number, any>()
    for (const group of likely) selected.set(group.groupId, group)
    for (const group of newestGroups(groups, likely.length ? 6 : 24)) selected.set(group.groupId, group)
    let chosen = [...selected.values()]
    let results = await searchGroups(chosen, cleanQuery)

    // If a vague query did not produce enough choices, broaden once without making exact set searches wait.
    if (results.length < 6) {
      const already = new Set(chosen.map((group: any) => group.groupId))
      const fallback = ranked.filter((group: any) => !already.has(group.groupId)).slice(0, 16)
      results = results.concat(await searchGroups(fallback, cleanQuery))
      chosen = chosen.concat(fallback)
    }

    const finalResults = finalize(results)
    let lowestActual = null
    let lowestActualCheckedAt = null
    if (body?.includeLowest && Number.isInteger(productId) && productId > 0) {
      try {
        lowestActual = await fetchLowestActualListing(productId)
        lowestActualCheckedAt = new Date().toISOString()
      } catch {
        lowestActual = null
      }
    }
    return Response.json({ success: true, results: finalResults, lowestActual, lowestActualCheckedAt, meta: { groupsScanned: chosen.length, durationMs: Date.now() - started } }, { headers: jsonHeaders })
  } catch (error) {
    return Response.json({ success: false, error: error instanceof Error ? error.message : String(error) }, { status: 500, headers: jsonHeaders })
  }
})
