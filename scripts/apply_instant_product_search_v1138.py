from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.37";','const APP_VERSION="v11.38";',1)
s=s.replace('<span id="appVersionLabel">v11.37</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.38</span> · Updated Aug 15, 2026',1)

js=r'''
/* Instant staged product search v11.38 */
const instantCardCache=new Map();
const instantResolveCache=new Map();
const PRODUCT_CACHE_PREFIX='vendortracker_lookup_v1138_';
function lookupCacheRead(key,maxAge=86400000){
  try{const raw=localStorage.getItem(PRODUCT_CACHE_PREFIX+key);if(!raw)return null;const obj=JSON.parse(raw);if(!obj?.time||Date.now()-obj.time>maxAge){localStorage.removeItem(PRODUCT_CACHE_PREFIX+key);return null}return obj.data||null}catch(e){return null}
}
function lookupCacheWrite(key,data){try{localStorage.setItem(PRODUCT_CACHE_PREFIX+key,JSON.stringify({time:Date.now(),data}))}catch(e){}}
function firstNonEmpty(jobs){
  return new Promise(resolve=>{
    let left=jobs.length,done=false;
    if(!left)return resolve([]);
    jobs.forEach(job=>Promise.resolve(job).then(v=>{if(done)return;if(v?.length){done=true;resolve(v);return}if(--left===0){done=true;resolve([])}}).catch(()=>{if(done)return;if(--left===0){done=true;resolve([])}}));
  });
}
async function fetchCardQuery(q,pageSize=18){
  const key=q+'|'+pageSize;
  if(instantCardCache.has(key))return instantCardCache.get(key);
  const persisted=lookupCacheRead('cardq_'+fastCacheKey(key));
  if(persisted){instantCardCache.set(key,Promise.resolve(persisted));return persisted}
  const job=(async()=>{
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),2600);
    try{
      const url='https://api.pokemontcg.io/v2/cards?pageSize='+Math.min(pageSize,24)+'&q='+encodeURIComponent(q);
      const r=await fetch(url,{signal:controller.signal,cache:'force-cache'});
      if(!r.ok)throw new Error('HTTP '+r.status);
      const j=await r.json();const out=j.data||[];
      lookupCacheWrite('cardq_'+fastCacheKey(key),out);
      return out;
    }finally{clearTimeout(timeout)}
  })();
  instantCardCache.set(key,job);
  try{return await job}catch(e){instantCardCache.delete(key);throw e}
}
function buildInstantQueries(raw){
  const {parsed,queries}=buildFastCardQueries(raw);
  const exact=[],fallback=[];
  if(parsed.name&&parsed.apiNumber&&parsed.denominator)exact.push(`name:"${escapeQueryPhrase(parsed.name)}" number:${parsed.apiNumber} set.printedTotal:${parseInt(parsed.denominator,10)}`);
  if(parsed.name&&parsed.apiNumber)exact.push(`name:"${escapeQueryPhrase(parsed.name)}" number:${parsed.apiNumber}`);
  if(parsed.apiNumber&&parsed.denominator)exact.push(`number:${parsed.apiNumber} set.printedTotal:${parseInt(parsed.denominator,10)}`);
  if(parsed.name)exact.push(`name:"${escapeQueryPhrase(parsed.name)}"`);
  for(const q of queries)if(!exact.includes(q))fallback.push(q);
  return {parsed,exact:[...new Set(exact)].slice(0,3),fallback:[...new Set(fallback)].slice(0,3)};
}
function rankInstant(cards,parsed,limit){
  const out=uniqueCards(cards||[]);out.sort((a,b)=>scoreCardResult(b,parsed)-scoreCardResult(a,parsed));return out.slice(0,limit);
}
async function resolveCardText(raw,limit=8){
  const ck=fastCacheKey(raw)+'|'+limit;
  const persisted=lookupCacheRead('resolve_'+ck);
  if(persisted?.length)return persisted.slice(0,limit);
  if(instantResolveCache.has(ck))return instantResolveCache.get(ck);
  const job=(async()=>{
    const {parsed,exact,fallback}=buildInstantQueries(raw);
    const exactJobs=exact.map(q=>fetchCardQuery(q,18).catch(()=>[]));
    let first=await firstNonEmpty(exactJobs);
    if(!first.length&&fallback.length)first=await firstNonEmpty(fallback.map(q=>fetchCardQuery(q,16).catch(()=>[])));
    let ranked=rankInstant(first,parsed,limit);
    if(ranked.length<Math.min(4,limit)){
      const all=await Promise.all([...exactJobs,...fallback.map(q=>fetchCardQuery(q,16).catch(()=>[]))]);
      ranked=rankInstant(all.flat(),parsed,limit);
    }
    if(ranked.length)lookupCacheWrite('resolve_'+ck,ranked);
    return ranked;
  })();
  instantResolveCache.set(ck,job);
  try{return await job}catch(e){instantResolveCache.delete(ck);throw e}
}
async function searchPokemonCards(){
  const raw=document.getElementById('pName').value.trim(),status=document.getElementById('cardLookupStatus');
  if(!raw){status.textContent='Enter a card name first.';return}
  const cacheKey='ui_'+fastCacheKey(raw),cached=lookupCacheRead(cacheKey);
  if(cached?.length){
    currentLookupResults=cached;renderCardLookup(cached);document.getElementById('cardLookupModal').classList.remove('hidden');status.textContent=`Found ${cached.length} match${cached.length===1?'':'es'} instantly.`;
  }else status.textContent='Finding matches…';
  const {parsed,exact,fallback}=buildInstantQueries(raw);
  const exactJobs=exact.map(q=>fetchCardQuery(q,18).catch(()=>[]));
  try{
    const first=rankInstant(await firstNonEmpty(exactJobs),parsed,20);
    if(first.length&&!cached){currentLookupResults=first;renderCardLookup(first);document.getElementById('cardLookupModal').classList.remove('hidden');status.textContent=`Found ${first.length} match${first.length===1?'':'es'}.`}
    const background=Promise.all([...exactJobs,...fallback.slice(0,2).map(q=>fetchCardQuery(q,14).catch(()=>[]))]);
    background.then(parts=>{
      const all=rankInstant(parts.flat(),parsed,30);if(!all.length)return;
      lookupCacheWrite(cacheKey,all);currentLookupResults=all;
      if(!document.getElementById('cardLookupModal').classList.contains('hidden'))renderCardLookup(all);
      status.textContent=`Found ${all.length} likely match${all.length===1?'':'es'}.`;
    });
    if(!first.length&&!cached){
      const extra=rankInstant(await firstNonEmpty(fallback.map(q=>fetchCardQuery(q,14).catch(()=>[]))),parsed,20);
      if(extra.length){currentLookupResults=extra;renderCardLookup(extra);document.getElementById('cardLookupModal').classList.remove('hidden');status.textContent=`Found ${extra.length} match${extra.length===1?'':'es'}.`;lookupCacheWrite(cacheKey,extra)}
      else status.textContent='No match found. Try the card name plus collector number.';
    }
  }catch(e){if(!cached)status.textContent='Card service is slow right now. Try again or use a more exact card number.'}
}
async function fastSealedProductSearch(q){
  const key=fastCacheKey(q),persisted=lookupCacheRead('sealed_'+key,6*60*60*1000);
  if(persisted?.length)return persisted;
  if(fastSealedSearchCache.has(key))return fastSealedSearchCache.get(key);
  const job=(async()=>{const {data,error}=await sb.functions.invoke('sealed-product-search',{body:{query:q}});if(error)throw error;const out=data?.results||[];if(out.length)lookupCacheWrite('sealed_'+key,out);return out})();
  fastSealedSearchCache.set(key,job);
  try{return await job}catch(e){fastSealedSearchCache.delete(key);throw e}
}
async function searchPurchaseItem(){
  const q=document.getElementById('buySearch')?.value.trim(),status=document.getElementById('buyLookupStatus'),box=document.getElementById('buyLookupResults');
  if(!q)return toast('Enter something to search');
  box.innerHTML='';purchaseSelectedItem=null;document.getElementById('buyNewItemFields')?.classList.add('hidden');
  try{
    if(purchaseLookupType==='card'){
      status.textContent='Finding matches…';
      const key='purchase_'+fastCacheKey(q),cached=lookupCacheRead(key);
      if(cached?.length){purchaseLookupResults=cached;status.textContent=`Found ${cached.length} card${cached.length===1?'':'s'} instantly.`;box.innerHTML=cached.map((c,i)=>{const prices=c.tcgplayer?.prices||{},m=Object.values(prices).map(v=>v?.market).find(v=>v!=null);return `<button class="purchaseLookupCard" onclick="selectPurchaseLookup(${i})"><img src="${esc(c.images?.small||c.images?.large||'')}"><strong>${esc(c.name)}</strong><div class="small">${esc(c.set?.name||'')} #${esc(fullCardNumber(c))}</div><div class="marketGood" style="margin-top:5px">${m!=null?money(m):'Market unavailable'}</div></button>`}).join('');return}
      const cards=await resolveCardText(q,14);purchaseLookupResults=cards;if(cards.length)lookupCacheWrite(key,cards);
      if(!cards.length){status.textContent='No cards found. Try the name plus collector number.';return}
      status.textContent=`Found ${cards.length} card${cards.length===1?'':'s'}. Select the exact printing.`;
      box.innerHTML=cards.map((c,i)=>{const prices=c.tcgplayer?.prices||{},m=Object.values(prices).map(v=>v?.market).find(v=>v!=null);return `<button class="purchaseLookupCard" onclick="selectPurchaseLookup(${i})"><img src="${esc(c.images?.small||c.images?.large||'')}"><strong>${esc(c.name)}</strong><div class="small">${esc(c.set?.name||'')} #${esc(fullCardNumber(c))}</div><div class="marketGood" style="margin-top:5px">${m!=null?money(m):'Market unavailable'}</div></button>`}).join('');
    }else{
      const key='sealed_'+fastCacheKey(q),cached=lookupCacheRead(key,6*60*60*1000);status.textContent=cached?.length?'Loading saved results…':'Searching sealed products…';
      const items=cached?.length?cached:await fastSealedProductSearch(q);purchaseLookupResults=items;
      if(!items.length){status.textContent='No sealed products found.';return}
      status.textContent=`Found ${items.length} sealed product${items.length===1?'':'s'}${cached?.length?' instantly':''}.`;
      box.innerHTML=items.map((x,i)=>`<button class="purchaseLookupCard" onclick="selectPurchaseLookup(${i})"><img src="${esc(x.imageUrl||'')}"><strong>${esc(x.name||'')}</strong><div class="small">${esc(x.groupName||'')}</div><div class="marketGood" style="margin-top:5px">${x.marketPrice!=null?money(x.marketPrice):'Market unavailable'}</div></button>`).join('');
    }
  }catch(e){status.textContent='Lookup failed. Try again in a moment.'}
}
'''

if '/* Instant staged product search v11.38 */' not in s:
    s=s.replace('function renderDashboard(){',js+'\nfunction renderDashboard(){',1)

p.write_text(s,encoding='utf-8')
