from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v12.0.1";','const APP_VERSION="v12.0.2";',1).replace('<span id="appVersionLabel">v12.0.1</span>','<span id="appVersionLabel">v12.0.2</span>',1)
s=s.replace('const sb=supabase.createClient(SUPABASE_URL,SUPABASE_ANON_KEY);',"const sb=supabase.createClient(SUPABASE_URL,SUPABASE_ANON_KEY,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storage:window.localStorage}});",1)
old='sb.auth.onAuthStateChange(async(ev,s)=>{if(ev==="PASSWORD_RECOVERY"){recoveryMode=true;showReset()}else if(ev==="SIGNED_OUT"){user=null;showPublic()}else if(s?.user&&!recoveryMode){user=s.user;await enterApp()}});'
new='''sb.auth.onAuthStateChange(async(ev,s)=>{\n  if(ev==="PASSWORD_RECOVERY"){recoveryMode=true;showReset();return}\n  if(ev==="SIGNED_OUT"){\n    await new Promise(r=>setTimeout(r,450));\n    const {data:{session:check}}=await sb.auth.getSession();\n    if(check?.user){user=check.user;if(!recoveryMode)await enterApp();return}\n    user=null;showPublic();return\n  }\n  if(s?.user&&!recoveryMode){user=s.user;await enterApp()}\n});'''
if old not in s: raise SystemExit('auth listener pattern not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
