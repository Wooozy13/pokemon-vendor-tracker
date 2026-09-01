import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from "npm:@supabase/supabase-js@2.57.4"

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
}
const headers = { ...cors, "Content-Type": "application/json", "Cache-Control": "public, max-age=30" }

Deno.serve(async request => {
  if (request.method === "OPTIONS") return new Response("ok", { headers: cors })
  if (request.method !== "POST") return new Response(JSON.stringify({ found: false }), { status: 405, headers })
  try {
    const { token } = await request.json()
    const shareToken = String(token || "").trim()
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(shareToken)) return new Response(JSON.stringify({ found: false }), { status: 404, headers })
    const url = Deno.env.get("SUPABASE_URL"), serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")
    if (!url || !serviceKey) throw new Error("Server configuration unavailable")
    const admin = createClient(url, serviceKey, { auth: { persistSession: false, autoRefreshToken: false } })
    const { data, error } = await admin.from("inventory_shares").select("inventory,updated_at").eq("token", shareToken).maybeSingle()
    if (error) throw error
    if (!data) return new Response(JSON.stringify({ found: false }), { status: 404, headers })
    return new Response(JSON.stringify({ found: true, inventory: Array.isArray(data.inventory) ? data.inventory : [], updatedAt: data.updated_at }), { headers })
  } catch {
    return new Response(JSON.stringify({ found: false }), { status: 500, headers })
  }
})
