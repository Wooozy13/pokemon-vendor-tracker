from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v12.0.3";','const APP_VERSION="v12.0.4";',1).replace('<span id="appVersionLabel">v12.0.3</span>','<span id="appVersionLabel">v12.0.4</span>',1)
# Session backup helpers
anchor='const LOCAL_PREFIX="vendortracker_data_v3_";'
insert='''const VT_AUTH_BACKUP_KEY="vendortracker_auth_backup_v1";\nfunction vtSaveAuthBackup(session){try{if(session?.access_token&&session?.refresh_token)localStorage.setItem(VT_AUTH_BACKUP_KEY,JSON.stringify({access_token:session.access_token,refresh_token:session.refresh_token}))}catch(e){}}\nfunction vtReadAuthBackup(){try{return JSON.parse(localStorage.getItem(VT_AUTH_BACKUP_KEY)||"null")}catch(e){return null}}\nfunction vtClearAuthBackup(){try{localStorage.removeItem(VT_AUTH_BACKUP_KEY)}catch(e){}}\n'''
if insert not in s:s=s.replace(anchor,insert+anchor,1)
# Save after successful sign in/signup with session
old='''if(r.error)return setMsg(authMsg,r.error.message,"error");if(authMode==="signup"&&!r.data.session)return setMsg(authMsg,"Account created. Check your email to confirm your address, then sign in.","success");user=r.data.user;await enterApp()'''
new='''if(r.error)return setMsg(authMsg,r.error.message,"error");if(authMode==="signup"&&!r.data.session)return setMsg(authMsg,"Account created. Check your email to confirm your address, then sign in.","success");if(r.data.session)vtSaveAuthBackup(r.data.session);user=r.data.user;await enterApp()'''
s=s.replace(old,new,1)
# explicit signout clears backup
s=s.replace('async function signOut(){await sb.auth.signOut();showPublic()}','async function signOut(){vtClearAuthBackup();await sb.auth.signOut();showPublic()}',1)
# Replace init session acquisition with fallback restoration
old2=''' const {data:{session}}=await sb.auth.getSession();\n sb.auth.onAuthStateChange(async(ev,s)=>{'''
new2=''' let {data:{session}}=await sb.auth.getSession();\n if(!session){\n  const backup=vtReadAuthBackup();\n  if(backup?.access_token&&backup?.refresh_token){\n   const restored=await sb.auth.setSession({access_token:backup.access_token,refresh_token:backup.refresh_token});\n   if(!restored.error&&restored.data?.session){session=restored.data.session;vtSaveAuthBackup(session)}\n  }\n }\n sb.auth.onAuthStateChange(async(ev,s)=>{\n  if(s)vtSaveAuthBackup(s);'''
if old2 not in s: raise SystemExit('init session anchor not found')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
