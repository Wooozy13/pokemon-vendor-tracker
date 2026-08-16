from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v12.0.5";','const APP_VERSION="v12.0.6";',1).replace('<span id="appVersionLabel">v12.0.5</span>','<span id="appVersionLabel">v12.0.6</span>',1)
# Remove manual backup-token layer; rely on Supabase's persisted storage.
start=s.find('const VT_AUTH_BACKUP_KEY="vendortracker_auth_backup_v1";')
if start!=-1:
    end=s.find('const LOCAL_PREFIX=',start)
    s=s[:start]+s[end:]
old='''async function init(){
 const h=location.hash;
 if(h.includes("type=recovery")||h.includes("access_token="))recoveryMode=true;
 let {data:{session}}=await sb.auth.getSession();
 if(!session){
  const backup=vtReadAuthBackup();
  if(backup?.access_token&&backup?.refresh_token){
   const restored=await sb.auth.setSession({access_token:backup.access_token,refresh_token:backup.refresh_token});
   if(!restored.error&&restored.data?.session){session=restored.data.session;vtSaveAuthBackup(session)}
  }
 }
 sb.auth.onAuthStateChange(async(ev,s)=>{
  if(s)vtSaveAuthBackup(s);
  if(ev==="PASSWORD_RECOVERY"){recoveryMode=true;showReset();return}
  if(ev==="SIGNED_OUT"){
    await new Promise(r=>setTimeout(r,450));
    const {data:{session:check}}=await sb.auth.getSession();
    if(check?.user){user=check.user;if(!recoveryMode)await enterApp();return}
    user=null;showPublic();return
  }
  if(s?.user&&!recoveryMode){user=s.user;await enterApp()}
});
 if(recoveryMode&&session){user=session.user;showReset()}else if(session?.user){user=session.user;await enterApp()}else showPublic();
}'''
new='''function init(){
 const h=location.hash;
 recoveryMode=h.includes("type=recovery")||h.includes("access_token=");
 let initialHandled=false;
 const applySession=(session)=>{
   if(recoveryMode){if(session?.user){user=session.user;showReset()}else showPublic();return}
   if(session?.user){user=session.user;setTimeout(()=>enterApp(),0)}else{user=null;showPublic()}
 };
 sb.auth.onAuthStateChange((ev,session)=>{
   if(ev==="PASSWORD_RECOVERY"){recoveryMode=true;if(session?.user)user=session.user;showReset();return}
   if(ev==="INITIAL_SESSION"){initialHandled=true;applySession(session);return}
   if(ev==="SIGNED_IN"||ev==="TOKEN_REFRESHED"||ev==="USER_UPDATED"){
     if(session?.user&&!recoveryMode){user=session.user;if(document.getElementById("app").classList.contains("hidden"))setTimeout(()=>enterApp(),0)}
     return
   }
   if(ev==="SIGNED_OUT"){user=null;showPublic()}
 });
 // Fallback only if INITIAL_SESSION is unexpectedly delayed; do not manipulate tokens.
 setTimeout(()=>{
   if(initialHandled)return;
   sb.auth.getSession().then(({data})=>{initialHandled=true;applySession(data?.session||null)}).catch(()=>showPublic());
 },1200);
}'''
if old not in s: raise SystemExit('old init block not found')
s=s.replace(old,new,1)
s=s.replace('if(r.data.session)vtSaveAuthBackup(r.data.session);user=r.data.user;await enterApp()','user=r.data.user;await enterApp()',1)
s=s.replace('async function signOut(){vtClearAuthBackup();await sb.auth.signOut();showPublic()}','async function signOut(){await sb.auth.signOut({scope:"local"});showPublic()}',1)
p.write_text(s,encoding='utf-8')
