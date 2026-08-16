from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
start=s.index('const VT_AUTH_DB="vendortracker_auth_v1";')
end=s.index('const LOCAL_PREFIX=',start)
replacement='''const VT_AUTH_STORAGE_KEY="vendortracker-auth-session";\n// v12.0.8: use Supabase's native browser localStorage persistence only.\nconst sb=supabase.createClient(SUPABASE_URL,SUPABASE_ANON_KEY,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storage:window.localStorage,storageKey:VT_AUTH_STORAGE_KEY}});\n'''
s=s[:start]+replacement+s[end:]
s=s.replace('const APP_VERSION="v12.0.7";','const APP_VERSION="v12.0.8";',1).replace('<span id="appVersionLabel">v12.0.7</span>','<span id="appVersionLabel">v12.0.8</span>',1)
old='''async function init(){\n const h=location.hash;\n recoveryMode=h.includes("type=recovery")||h.includes("access_token=");\n const {data:{session},error}=await sb.auth.getSession();'''
new='''async function init(){\n const h=location.hash;\n recoveryMode=h.includes("type=recovery")||h.includes("access_token=");\n // Wait for the native Supabase client to recover the persisted browser session.\n const {data:{session},error}=await sb.auth.getSession();\n console.info("VendorTracker auth startup",{version:APP_VERSION,hasStoredSession:!!localStorage.getItem(VT_AUTH_STORAGE_KEY),hasSession:!!session,error:error?.message||null});'''
if old not in s: raise SystemExit('init target not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
