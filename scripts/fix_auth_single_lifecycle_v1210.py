from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v12.0.9";','const APP_VERSION="v12.1.0";',1)
s=s.replace('<span id="appVersionLabel">v12.0.9</span>','<span id="appVersionLabel">v12.1.0</span>',1)
old='''async function init(){
 const h=location.hash;
 if(h.includes("type=recovery")||h.includes("access_token="))recoveryMode=true;
 const {data:{session}}=await sb.auth.getSession();
 sb.auth.onAuthStateChange(async(ev,s)=>{if(ev==="PASSWORD_RECOVERY"){recoveryMode=true;showReset()}else if(ev==="SIGNED_OUT"){user=null;showPublic()}else if(s?.user&&!recoveryMode){user=s.user;await enterApp()}});
 if(recoveryMode&&session){user=session.user;showReset()}else if(session?.user){user=session.user;await enterApp()}else showPublic();
}'''
new='''async function init(){
 const h=location.hash;
 if(h.includes("type=recovery")||h.includes("access_token="))recoveryMode=true;
 let initialHandled=false;
 sb.auth.onAuthStateChange((ev,s)=>{
   if(ev==="PASSWORD_RECOVERY"){
     recoveryMode=true;
     if(s?.user)user=s.user;
     initialHandled=true;
     showReset();
     return;
   }
   if(ev==="INITIAL_SESSION"){
     initialHandled=true;
     if(recoveryMode&&s?.user){user=s.user;showReset();return;}
     if(s?.user){user=s.user;queueMicrotask(()=>enterApp());}
     else if(!recoveryMode){user=null;showPublic();}
     return;
   }
   if(ev==="SIGNED_IN"&&s?.user){
     user=s.user;
     if(!recoveryMode && document.getElementById("app")?.classList.contains("hidden"))queueMicrotask(()=>enterApp());
     return;
   }
   if(ev==="SIGNED_OUT"){
     user=null;
     showPublic();
   }
 });
}'''
if old not in s:
    raise SystemExit('Expected auth init block not found; refusing unsafe edit')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
