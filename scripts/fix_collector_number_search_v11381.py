from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
s=s.replace('const APP_VERSION="v11.38";','const APP_VERSION="v11.38.1";',1).replace('<span id="appVersionLabel">v11.38</span>','<span id="appVersionLabel">v11.38.1</span>',1)
# Preserve the known-working search flow, but add exact collector-number queries such as GG56/GG70.
needle='async function searchPokemonCards(){'
patch=r'''
/* Collector-number search support v11.38.1 — leaves existing Find Card flow intact. */
function vtCollectorParts(raw){
  const m=String(raw||'').trim().toUpperCase().match(/\b([A-Z]*\d+[A-Z]*)\s*\/\s*([A-Z]*\d+[A-Z]*)\b/);
  return m?{number:m[1],printed:m[0].replace(/\s+/g,'')} : null;
}
async function vtExactCollectorLookup(raw){
  const c=vtCollectorParts(raw); if(!c)return [];
  const qs=[`number:${c.number}`,`number:${c.number.toLowerCase()}`];
  for(const q of qs){
    try{
      const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),2800);
      const r=await fetch(`https://api.pokemontcg.io/v2/cards?q=${encodeURIComponent(q)}&pageSize=40`,{signal:ctrl.signal});clearTimeout(timer);
      if(!r.ok)continue;const j=await r.json();
      const exact=(j.data||[]).filter(x=>String(fullCardNumber(x)||'').toUpperCase()===c.printed || String(x.number||'').toUpperCase()===c.number);
      if(exact.length)return exact;
    }catch(e){}
  }
  return [];
}
const vtOriginalSearchPokemonCards = searchPokemonCards;
searchPokemonCards = async function(){
  const raw=document.getElementById('pName')?.value?.trim()||'';
  if(vtCollectorParts(raw)){
    const status=document.getElementById('cardLookupStatus'); if(status)status.textContent='Searching collector number…';
    const exact=await vtExactCollectorLookup(raw);
    if(exact.length){currentLookupResults=exact;renderCardLookup(exact);document.getElementById('cardLookupModal')?.classList.remove('hidden');if(status)status.textContent=`Found ${exact.length} exact collector-number match${exact.length===1?'':'es'}.`;return;}
  }
  return vtOriginalSearchPokemonCards();
};
'''
# Insert after all original function declarations, immediately before dashboard rendering, avoiding hoisting/redefinition issues.
if 'Collector-number search support v11.38.1' not in s:
    s=s.replace('function renderDashboard(){',patch+'\nfunction renderDashboard(){',1)
p.write_text(s,encoding='utf-8')
