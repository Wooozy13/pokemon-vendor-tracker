from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v12.0.6";','const APP_VERSION="v12.0.7";',1).replace('<span id="appVersionLabel">v12.0.6</span>','<span id="appVersionLabel">v12.0.7</span>',1)
old='''const sb=supabase.createClient(SUPABASE_URL,SUPABASE_ANON_KEY,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storage:window.localStorage}});'''
new=r'''const VT_AUTH_DB="vendortracker_auth_v1";
const VT_AUTH_STORE="kv";
function vtAuthDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(VT_AUTH_DB,1);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(VT_AUTH_STORE))r.result.createObjectStore(VT_AUTH_STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
async function vtIdbGet(key){try{const db=await vtAuthDb();return await new Promise((resolve,reject)=>{const tx=db.transaction(VT_AUTH_STORE,'readonly'),r=tx.objectStore(VT_AUTH_STORE).get(key);r.onsuccess=()=>resolve(r.result??null);r.onerror=()=>reject(r.error)})}catch(e){return null}}
async function vtIdbSet(key,value){try{const db=await vtAuthDb();await new Promise((resolve,reject)=>{const tx=db.transaction(VT_AUTH_STORE,'readwrite');tx.objectStore(VT_AUTH_STORE).put(value,key);tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error)})}catch(e){}}
async function vtIdbRemove(key){try{const db=await vtAuthDb();await new Promise((resolve,reject)=>{const tx=db.transaction(VT_AUTH_STORE,'readwrite');tx.objectStore(VT_AUTH_STORE).delete(key);tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error)})}catch(e){}}
const vtAuthStorage={
 async getItem(key){let v=null;try{v=localStorage.getItem(key)}catch(e){};if(v!=null){vtIdbSet(key,v);return v}v=await vtIdbGet(key);if(v!=null){try{localStorage.setItem(key,v)}catch(e){}}return v},
 async setItem(key,value){try{localStorage.setItem(key,value)}catch(e){};await vtIdbSet(key,value)},
 async removeItem(key){try{localStorage.removeItem(key)}catch(e){};await vtIdbRemove(key)}
};
const sb=supabase.createClient(SUPABASE_URL,SUPABASE_ANON_KEY,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,storage:vtAuthStorage,storageKey:'vendortracker-auth-session'}});'''
if old not in s: raise SystemExit('supabase client target not found')
s=s.replace(old,new,1)
start=s.index('function init(){')
end=s.index('function showPublic(){',start)
newinit=r'''async function init(){
 const h=location.hash;
 recoveryMode=h.includes("type=recovery")||h.includes("access_token=");
 const {data:{session},error}=await sb.auth.getSession();
 if(recoveryMode){
   if(session?.user){user=session.user;showReset()}else showPublic();
 }else if(session?.user){
   user=session.user;await enterApp();
 }else{
   showPublic();
 }
 sb.auth.onAuthStateChange((ev,s)=>{
   if(ev==="PASSWORD_RECOVERY"){recoveryMode=true;if(s?.user)user=s.user;showReset();return}
   if((ev==="SIGNED_IN"||ev==="TOKEN_REFRESHED"||ev==="USER_UPDATED")&&s?.user&&!recoveryMode){user=s.user;if(document.getElementById("app").classList.contains("hidden"))setTimeout(()=>enterApp(),0);return}
   if(ev==="SIGNED_OUT"){user=null;showPublic()}
 });
}
'''
s=s[:start]+newinit+s[end:]
p.write_text(s,encoding='utf-8')
