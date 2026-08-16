from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

s=s.replace('const APP_VERSION="v11.36";','const APP_VERSION="v11.37";',1)
s=s.replace('<span id="appVersionLabel">v11.36</span> · Updated Aug 15, 2026','<span id="appVersionLabel">v11.37</span> · Updated Aug 15, 2026',1)

js=r'''
/* Fast product search v11.37 */
const fastCardQueryCache=new Map();
const fastCardResolveCache=new Map();
const fastSealedSearchCache=new Map();
function fastCacheKey(v){return String(v||'').trim().toLowerCase()}

async function fetchCardQuery(q,pageSize=36){
  const key=q+'|'+pageSize;
  if(fastCardQueryCache.has(key))return fastCardQueryCache.get(key);
  const job=(async()=>{
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),4500);
    try{
      const url='https://api.pokemontcg.io/v2/cards?pageSize='+Math.min(pageSize,48)+'&orderBy=-set.releaseDate&q='+encodeURIComponent(q);
      const r=await fetch(url,{signal:controller.signal});
      if(!r.ok)throw new Error('HTTP '+r.status);
      const j=await r.json();
      return j.data||[];
    }finally{clearTimeout(timeout)}
  })();
  fastCardQueryCache.set(key,job);
  try{return await job}catch(e){fastCardQueryCache.delete(key);throw e}
}

function buildFastCardQueries(raw){
  const parsed=parseCardSearch(raw),qs=[];
  if(parsed.name&&parsed.apiNumber&&parsed.denominator)qs.push(`name:"${escapeQueryPhrase(parsed.name)}" number:${parsed.apiNumber} set.printedTotal:${parseInt(parsed.denominator,10)}`);
  if(parsed.name&&parsed.apiNumber)qs.push(`name:"${escapeQueryPhrase(parsed.name)}" number:${parsed.apiNumber}`);
  if(parsed.apiNumber&&parsed.denominator)qs.push(`number:${parsed.apiNumber} set.printedTotal:${parseInt(parsed.denominator,10)}`);
  if(parsed.name)qs.push(`name:"${escapeQueryPhrase(parsed.name)}"`);
  const useful=(parsed.tokens||[]).filter(t=>t.length>=3);
  if(useful.length&&parsed.apiNumber)qs.push(`name:${escapeQueryPhrase(useful[0])}* number:${parsed.apiNumber}`);
  if(parsed.apiNumber)qs.push(`number:${parsed.apiNumber}`);
  if(useful.length)qs.push(`name:${escapeQueryPhrase(useful[0])}*`);
  return {parsed,queries:[...new Set(qs)]};
}

async function resolveCardText(raw,limit=8){
  const ck=fastCacheKey(raw)+'|'+limit;
  if(fastCardResolveCache.has(ck))return fastCardResolveCache.get(ck);
  const job=(async()=>{
    const {parsed,queries}=buildFastCardQueries(raw);
    if(!queries.length)return [];
    // Run strongest queries together instead of waiting on each request serially.
    const first=queries.slice(0,3);
    let batches=await Promise.all(first.map(q=>fetchCardQuery(q,30).catch(()=>[])));
    let cards=uniqueCards(batches.flat());
    // Only broaden the search if the exact pass did not produce enough choices.
    if(cards.length<Math.min(6,limit)&&queries.length>3){
      const extra=await Promise.all(queries.slice(3,6).map(q=>fetchCardQuery(q,28).catch(()=>[])));
      cards=uniqueCards(cards.concat(extra.flat()));
    }
    cards.sort((a,b)=>scoreCardResult(b,parsed)-scoreCardResult(a,parsed));
    return cards.slice(0,limit);
  })();
  fastCardResolveCache.set(ck,job);
  try{return await job}catch(e){fastCardResolveCache.delete(ck);throw e}
}

async function searchPokemonCards(){
  const raw=document.getElementById('pName').value.trim();
  const status=document.getElementById('cardLookupStatus');
  if(!raw){status.textContent='Enter a card name first.';return}
  status.textContent='Finding best matches…';
  try{
    const cards=await resolveCardText(raw,36);
    currentLookupResults=cards;
    if(!cards.length){status.textContent='No match found. Try the Pokémon name plus collector number, like 032/182.';return}
    status.textContent=`Found ${cards.length} likely match${cards.length===1?'':'es'}.`;
    renderCardLookup(cards);
    document.getElementById('cardLookupModal').classList.remove('hidden');
  }catch(e){status.textContent='Card service is temporarily unavailable. Try again in a moment.'}
}

async function fastSealedProductSearch(q){
  const key=fastCacheKey(q);
  if(fastSealedSearchCache.has(key))return fastSealedSearchCache.get(key);
  const job=(async()=>{
    const {data,error}=await sb.functions.invoke('sealed-product-search',{body:{query:q}});
    if(error)throw error;
    return data?.results||[];
  })();
  fastSealedSearchCache.set(key,job);
  try{return await job}catch(e){fastSealedSearchCache.delete(key);throw e}
}

async function searchPurchaseItem(){
  const q=document.getElementById('buySearch')?.value.trim(),status=document.getElementById('buyLookupStatus'),box=document.getElementById('buyLookupResults');
  if(!q)return toast('Enter something to search');
  status.textContent='Finding best matches…';box.innerHTML='';purchaseSelectedItem=null;document.getElementById('buyNewItemFields')?.classList.add('hidden');
  try{
    if(purchaseLookupType==='card'){
      const cards=await resolveCardText(q,18);purchaseLookupResults=cards;
      if(!cards.length){status.textContent='No cards found. Try the name plus collector number.';return}
      status.textContent=`Found ${cards.length} card${cards.length===1?'':'s'}. Select the exact printing.`;
      box.innerHTML=cards.map((c,i)=>{const prices=c.tcgplayer?.prices||{},m=Object.values(prices).map(v=>v?.market).find(v=>v!=null);return `<button class="purchaseLookupCard" onclick="selectPurchaseLookup(${i})"><img src="${esc(c.images?.small||c.images?.large||'')}"><strong>${esc(c.name)}</strong><div class="small">${esc(c.set?.name||'')} #${esc(fullCardNumber(c))}</div><div class="marketGood" style="margin-top:5px">${m!=null?money(m):'Market unavailable'}</div></button>`}).join('');
    }else{
      const items=await fastSealedProductSearch(q);purchaseLookupResults=items;
      if(!items.length){status.textContent='No sealed products found.';return}
      status.textContent=`Found ${items.length} sealed product${items.length===1?'':'s'}.`;
      box.innerHTML=items.map((x,i)=>`<button class="purchaseLookupCard" onclick="selectPurchaseLookup(${i})"><img src="${esc(x.imageUrl||'')}"><strong>${esc(x.name||'')}</strong><div class="small">${esc(x.groupName||'')}</div><div class="marketGood" style="margin-top:5px">${x.marketPrice!=null?money(x.marketPrice):'Market unavailable'}</div></button>`).join('');
    }
  }catch(e){status.textContent='Lookup failed. Try again in a moment.'}
}
'''

if '/* Fast product search v11.37 */' not in s:
    s=s.replace('function renderDashboard(){',js+'\nfunction renderDashboard(){',1)

p.write_text(s,encoding='utf-8')
